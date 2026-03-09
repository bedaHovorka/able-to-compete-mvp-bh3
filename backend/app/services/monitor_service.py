from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models import Monitor, Check, Incident, MonitorStatus, MonitorType, IncidentStatus, IncidentSeverity
from app.utils.logger import logger
from app.utils.database import AsyncSessionLocal
from typing import Optional, List as ListType, Dict
from datetime import datetime, timedelta
import httpx
import asyncio
import uuid

# Module-level singletons so state survives multiple MonitorService instantiations
failure_counts: dict = {}
active_monitors: dict = {}


class MonitorService:
    def __init__(self):
        pass

    async def create_monitor(self, db: AsyncSession, name: str, url: str, interval: int = 60, monitor_type: str = "https", timeout: int = 10, expected_status_code: int = 200) -> Monitor:
        """Create a new monitor"""
        monitor = Monitor(name=name, url=url, interval=interval, type=monitor_type, timeout=timeout, expected_status_code=expected_status_code)
        db.add(monitor)
        await db.commit()
        await db.refresh(monitor)

        logger.info(f"Created monitor: {monitor.id} - {name}")
        return monitor

    async def get_monitors(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> ListType[Monitor]:
        """Get all monitors"""
        query = select(Monitor).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_monitor(self, db: AsyncSession, monitor_id: uuid.UUID) -> Optional[Monitor]:
        """Get monitor by ID"""
        query = select(Monitor).where(Monitor.id == monitor_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_response_time_history(
        self,
        db: AsyncSession,
        monitor_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[ListType[Check], int]:
        """Returns (checks ordered by checked_at DESC, total_count)"""
        count_query = select(func.count()).select_from(Check).where(Check.monitor_id == monitor_id)
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        query = (
            select(Check)
            .where(Check.monitor_id == monitor_id)
            .order_by(Check.checked_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(query)
        checks = result.scalars().all()

        return checks, total

    async def execute_check(self, db: AsyncSession, monitor: Monitor) -> Check:
        """Execute a single health check"""
        if monitor.type == MonitorType.SSL:
            return await self._execute_ssl_check_flow(db, monitor)

        start_time = datetime.utcnow()
        status = MonitorStatus.DOWN
        response_time = None
        status_code = None
        error_message = None

        try:
            async with httpx.AsyncClient(timeout=monitor.timeout) as client:
                response = await client.get(monitor.url, headers=monitor.headers or {})
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                status_code = response.status_code

                if status_code == monitor.expected_status_code:
                    status = MonitorStatus.UP
                else:
                    status = MonitorStatus.DEGRADED
                    error_message = f"Expected {monitor.expected_status_code}, got {status_code}"

        except httpx.TimeoutException:
            error_message = "Request timeout"
            status = MonitorStatus.DOWN
        except Exception as e:
            error_message = str(e)
            status = MonitorStatus.DOWN

        # Create check record
        check = Check(
            monitor_id=monitor.id,
            status=status,
            response_time=response_time,
            status_code=status_code,
            error_message=error_message
        )
        db.add(check)

        # Update monitor status
        monitor.status = status
        monitor.last_checked_at = datetime.utcnow()

        await db.commit()
        await db.refresh(check)

        logger.info(f"Check completed for monitor {monitor.id}: {status} ({response_time}ms)")

        # Handle incident creation/resolution
        await self.handle_incident(db, monitor, status)

        return check

    async def _execute_ssl_check(self, monitor: Monitor) -> int:
        """Execute an SSL certificate check and return days until expiry."""
        import ssl
        import socket
        from concurrent.futures import ThreadPoolExecutor
        from urllib.parse import urlparse

        def _check_sync():
            hostname = urlparse(monitor.url).hostname
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=monitor.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
            # notAfter format: "Nov 25 12:59:59 2024 GMT" — strip timezone suffix for naive UTC comparison
            not_after = cert["notAfter"].replace(" GMT", "")
            expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y")
            return (expiry - datetime.utcnow()).days

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, _check_sync)

    async def _execute_ssl_check_flow(self, db: AsyncSession, monitor: Monitor) -> Check:
        """Execute SSL check and persist a Check record; handle incidents immediately."""
        ssl_expiry_days = None
        status = MonitorStatus.DOWN
        error_message = None

        try:
            import ssl as ssl_module
            ssl_expiry_days = await self._execute_ssl_check(monitor)

            if ssl_expiry_days > 30:
                status = MonitorStatus.UP
            elif ssl_expiry_days >= 1:
                status = MonitorStatus.DEGRADED
            else:
                status = MonitorStatus.DOWN

        except ssl_module.SSLCertVerificationError:
            ssl_expiry_days = 0
            status = MonitorStatus.DOWN
            error_message = "SSL certificate verification failed"
        except Exception as e:
            status = MonitorStatus.DOWN
            error_message = str(e)

        check = Check(
            monitor_id=monitor.id,
            status=status,
            ssl_expiry_days=ssl_expiry_days,
            error_message=error_message
        )
        db.add(check)

        monitor.status = status
        monitor.last_checked_at = datetime.utcnow()

        await db.commit()
        await db.refresh(check)

        logger.info(f"SSL check completed for monitor {monitor.id}: {status} (expiry_days={ssl_expiry_days})")

        # SSL incidents are created immediately without the 3-failure wait
        await self.handle_ssl_incident(db, monitor, status, ssl_expiry_days)

        return check

    async def handle_ssl_incident(self, db: AsyncSession, monitor: Monitor, status: MonitorStatus, ssl_expiry_days: Optional[int]):
        """Handle incident creation and resolution for SSL monitors (no 3-failure wait)."""
        # Check for existing open incident
        query = select(Incident).where(
            and_(
                Incident.monitor_id == monitor.id,
                Incident.status.in_([IncidentStatus.INVESTIGATING, IncidentStatus.IDENTIFIED])
            )
        )
        result = await db.execute(query)
        existing_incident = result.scalar_one_or_none()

        if status == MonitorStatus.DOWN:
            if not existing_incident:
                if ssl_expiry_days is not None and ssl_expiry_days < 0:
                    days_msg = f" (expired {abs(ssl_expiry_days)} day(s) ago)"
                elif ssl_expiry_days == 0:
                    days_msg = " (expired today)"
                else:
                    days_msg = ""
                incident = Incident(
                    monitor_id=monitor.id,
                    title=f"{monitor.name} SSL certificate is expired or invalid",
                    description=f"SSL certificate for {monitor.name} has expired or failed verification{days_msg}",
                    severity=IncidentSeverity.CRITICAL,
                    status=IncidentStatus.INVESTIGATING
                )
                db.add(incident)
                await db.commit()
                logger.warning(f"Created critical SSL incident for monitor {monitor.id}")

        elif status == MonitorStatus.DEGRADED:
            if not existing_incident:
                incident = Incident(
                    monitor_id=monitor.id,
                    title=f"{monitor.name} SSL certificate expiring soon",
                    description=f"SSL certificate for {monitor.name} expires in {ssl_expiry_days} day(s)",
                    severity=IncidentSeverity.HIGH,
                    status=IncidentStatus.INVESTIGATING
                )
                db.add(incident)
                await db.commit()
                logger.warning(f"Created high SSL expiry incident for monitor {monitor.id}")

        elif status == MonitorStatus.UP:
            if existing_incident:
                existing_incident.status = IncidentStatus.RESOLVED
                existing_incident.resolved_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Auto-resolved SSL incident {existing_incident.id}")

    async def handle_incident(self, db: AsyncSession, monitor: Monitor, status: MonitorStatus):
        """Handle incident creation and resolution"""
        monitor_id_str = str(monitor.id)

        # Initialize failure count if needed
        if monitor_id_str not in failure_counts:
            failure_counts[monitor_id_str] = 0

        # Check for existing open incident
        query = select(Incident).where(
            and_(
                Incident.monitor_id == monitor.id,
                Incident.status.in_([IncidentStatus.INVESTIGATING, IncidentStatus.IDENTIFIED])
            )
        )
        result = await db.execute(query)
        existing_incident = result.scalar_one_or_none()

        if status == MonitorStatus.DOWN:
            failure_counts[monitor_id_str] += 1

            # Create incident after 3 consecutive failures
            if failure_counts[monitor_id_str] >= 3 and not existing_incident:
                incident = Incident(
                    monitor_id=monitor.id,
                    title=f"{monitor.name} is down",
                    description=f"Monitor {monitor.name} has failed {failure_counts[monitor_id_str]} consecutive checks",
                    severity=IncidentSeverity.CRITICAL,
                    status=IncidentStatus.INVESTIGATING
                )
                db.add(incident)
                await db.commit()
                logger.warning(f"Created incident for monitor {monitor.id}")

        elif status == MonitorStatus.UP:
            failure_counts[monitor_id_str] = 0

            # Auto-resolve incident if exists
            if existing_incident:
                existing_incident.status = IncidentStatus.RESOLVED
                existing_incident.resolved_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Auto-resolved incident {existing_incident.id}")

    async def calculate_uptime(self, db: AsyncSession, monitor_id: uuid.UUID, hours: int = 24) -> Dict:
        """Calculate uptime percentage"""
        since = datetime.utcnow() - timedelta(hours=hours)

        query = select(Check).where(
            and_(
                Check.monitor_id == monitor_id,
                Check.checked_at >= since
            )
        )
        result = await db.execute(query)
        checks = result.scalars().all()

        if not checks:
            return {"uptime_percentage": 100.0, "total_checks": 0, "failed_checks": 0, "avg_response_time": None}

        total_checks = len(checks)
        up_checks = sum(1 for check in checks if check.status == MonitorStatus.UP)
        failed_checks = total_checks - up_checks
        uptime_percentage = (up_checks / total_checks) * 100

        avg_response_time = sum(check.response_time for check in checks if check.response_time) / len([c for c in checks if c.response_time])

        return {
            "uptime_percentage": round(uptime_percentage, 2),
            "total_checks": total_checks,
            "failed_checks": failed_checks,
            "avg_response_time": round(avg_response_time, 2) if avg_response_time else 0
        }

    async def start_monitoring(self, db: AsyncSession, monitor_id: uuid.UUID):
        """Start monitoring loop for a monitor"""
        monitor = await self.get_monitor(db, monitor_id)
        if not monitor or not monitor.enabled:
            return

        monitor_id_str = str(monitor_id)
        if monitor_id_str in active_monitors:
            return

        async def monitor_loop():
            while monitor_id_str in active_monitors:
                try:
                    async with AsyncSessionLocal() as loop_db:
                        fresh_monitor = await self.get_monitor(loop_db, monitor_id)
                        if fresh_monitor is None or not fresh_monitor.enabled:
                            active_monitors.pop(monitor_id_str, None)
                            logger.info(f"Monitor {monitor_id} deleted or disabled — stopping loop")
                            break
                        await self.execute_check(loop_db, fresh_monitor)
                    await asyncio.sleep(fresh_monitor.interval)
                except Exception as e:
                    logger.error(f"Error in monitor loop for {monitor_id}: {e}")
                    await asyncio.sleep(monitor.interval)

        task = asyncio.create_task(monitor_loop())
        active_monitors[monitor_id_str] = task
        logger.info(f"Started monitoring for {monitor_id}")

    async def stop_monitoring(self, monitor_id: uuid.UUID):
        """Stop monitoring loop for a monitor"""
        monitor_id_str = str(monitor_id)
        if monitor_id_str in active_monitors:
            task = active_monitors.pop(monitor_id_str)
            task.cancel()
            logger.info(f"Stopped monitoring for {monitor_id}")
