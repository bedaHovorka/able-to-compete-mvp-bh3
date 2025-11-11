from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models import Monitor, Check, Incident, Metric, MonitorStatus, IncidentStatus, IncidentSeverity
from app.utils.logger import logger
from typing import Optional, List as ListType, Dict
from datetime import datetime, timedelta
import httpx
import asyncio
import uuid


class MonitorService:
    def __init__(self):
        self.active_monitors = {}
        self.failure_counts = {}

    async def create_monitor(self, db: AsyncSession, name: str, url: str, interval: int = 60, monitor_type: str = "https") -> Monitor:
        """Create a new monitor"""
        monitor = Monitor(name=name, url=url, interval=interval, type=monitor_type)
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

    async def execute_check(self, db: AsyncSession, monitor: Monitor) -> Check:
        """Execute a single health check"""
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

    async def handle_incident(self, db: AsyncSession, monitor: Monitor, status: MonitorStatus):
        """Handle incident creation and resolution"""
        monitor_id_str = str(monitor.id)

        # Initialize failure count if needed
        if monitor_id_str not in self.failure_counts:
            self.failure_counts[monitor_id_str] = 0

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
            self.failure_counts[monitor_id_str] += 1

            # Create incident after 3 consecutive failures
            if self.failure_counts[monitor_id_str] >= 3 and not existing_incident:
                incident = Incident(
                    monitor_id=monitor.id,
                    title=f"{monitor.name} is down",
                    description=f"Monitor {monitor.name} has failed {self.failure_counts[monitor_id_str]} consecutive checks",
                    severity=IncidentSeverity.CRITICAL,
                    status=IncidentStatus.INVESTIGATING
                )
                db.add(incident)
                await db.commit()
                logger.warning(f"Created incident for monitor {monitor.id}")

        elif status == MonitorStatus.UP:
            self.failure_counts[monitor_id_str] = 0

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
            return {"uptime_percentage": 100.0, "total_checks": 0, "failed_checks": 0}

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
        if monitor_id_str in self.active_monitors:
            return

        async def monitor_loop():
            while monitor_id_str in self.active_monitors:
                try:
                    await self.execute_check(db, monitor)
                    await asyncio.sleep(monitor.interval)
                except Exception as e:
                    logger.error(f"Error in monitor loop for {monitor_id}: {e}")
                    await asyncio.sleep(monitor.interval)

        task = asyncio.create_task(monitor_loop())
        self.active_monitors[monitor_id_str] = task
        logger.info(f"Started monitoring for {monitor_id}")

    async def stop_monitoring(self, monitor_id: uuid.UUID):
        """Stop monitoring loop for a monitor"""
        monitor_id_str = str(monitor_id)
        if monitor_id_str in self.active_monitors:
            task = self.active_monitors.pop(monitor_id_str)
            task.cancel()
            logger.info(f"Stopped monitoring for {monitor_id}")
