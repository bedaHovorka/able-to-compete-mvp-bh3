from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.utils.database import get_db
from app.utils.auth import get_current_active_user
from app.services import MonitorService
from app.agents import MonitorAgent
from app.models import Check, MonitorStatus, MonitorType
from app.api.websocket import broadcast_update
from pydantic import AnyUrl, BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api", tags=["monitoring"])

# Initialize services
monitor_service = MonitorService()
monitor_agent = MonitorAgent()


# Schemas
class MonitorCreate(BaseModel):
    name: str
    url: AnyUrl
    interval: int = 60
    type: str = "https"
    timeout: int = 10
    expected_status_code: int = 200


class MonitorResponse(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    interval: int
    type: str
    status: str
    enabled: bool
    created_at: datetime
    last_checked_at: Optional[datetime]
    ssl_expiry_days: Optional[int] = None

    class Config:
        from_attributes = True


class UptimeResponse(BaseModel):
    uptime_percentage: float
    total_checks: int
    failed_checks: int
    avg_response_time: Optional[float]


class ResponseTimePoint(BaseModel):
    checked_at: datetime
    response_time_ms: Optional[float]
    status: str


class ResponseTimeHistory(BaseModel):
    monitor_id: uuid.UUID
    total: int
    data: List[ResponseTimePoint]


class DashboardMetrics(BaseModel):
    total_monitors: int
    monitors_up: int
    monitors_down: int
    monitors_degraded: int
    active_incidents: int
    avg_uptime: float


class IncidentResponse(BaseModel):
    id: uuid.UUID
    monitor_id: uuid.UUID
    title: str
    description: Optional[str]
    status: str
    severity: str
    started_at: datetime
    resolved_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[uuid.UUID]

    class Config:
        from_attributes = True


async def _get_ssl_expiry_days(db: AsyncSession, monitor_id: uuid.UUID) -> Optional[int]:
    """Return ssl_expiry_days from the latest check for an SSL monitor, or None."""
    query = (
        select(Check.ssl_expiry_days)
        .where(Check.monitor_id == monitor_id)
        .order_by(Check.checked_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    row = result.scalar_one_or_none()
    return row


async def _build_monitor_response(db: AsyncSession, monitor) -> MonitorResponse:
    """Build a MonitorResponse, populating ssl_expiry_days for SSL monitors."""
    ssl_expiry_days = None
    if monitor.type == MonitorType.SSL:
        ssl_expiry_days = await _get_ssl_expiry_days(db, monitor.id)
    return MonitorResponse(
        id=monitor.id,
        name=monitor.name,
        url=monitor.url,
        interval=monitor.interval,
        type=monitor.type,
        status=monitor.status,
        enabled=monitor.enabled,
        created_at=monitor.created_at,
        last_checked_at=monitor.last_checked_at,
        ssl_expiry_days=ssl_expiry_days,
    )


# Monitor endpoints
@router.post("/monitors", response_model=MonitorResponse, status_code=status.HTTP_201_CREATED)
async def create_monitor(
    monitor_data: MonitorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new monitor"""
    monitor = await monitor_service.create_monitor(
        db,
        name=monitor_data.name,
        url=str(monitor_data.url),
        interval=monitor_data.interval,
        monitor_type=monitor_data.type,
        timeout=monitor_data.timeout,
        expected_status_code=monitor_data.expected_status_code,
    )
    return await _build_monitor_response(db, monitor)


@router.get("/monitors", response_model=List[MonitorResponse])
async def list_monitors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """List all monitors"""
    monitors = await monitor_service.get_monitors(db, skip=skip, limit=limit)
    return [await _build_monitor_response(db, m) for m in monitors]


@router.get("/monitors/{monitor_id}", response_model=MonitorResponse)
async def get_monitor(
    monitor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get monitor by ID"""
    monitor = await monitor_service.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return await _build_monitor_response(db, monitor)


@router.get("/monitors/{monitor_id}/uptime", response_model=UptimeResponse)
async def get_monitor_uptime(
    monitor_id: uuid.UUID,
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Calculate monitor uptime percentage"""
    uptime_data = await monitor_service.calculate_uptime(db, monitor_id, hours=hours)
    return uptime_data


@router.get("/monitors/{monitor_id}/response-times", response_model=ResponseTimeHistory)
async def get_response_time_history(
    monitor_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get response time history for a monitor"""
    monitor = await monitor_service.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    checks, total = await monitor_service.get_response_time_history(
        db, monitor_id, limit=limit, offset=offset
    )

    data = [
        ResponseTimePoint(
            checked_at=check.checked_at,
            response_time_ms=check.response_time,
            status=check.status.value,
        )
        for check in checks
    ]

    return ResponseTimeHistory(monitor_id=monitor_id, total=total, data=data)


@router.post("/monitors/{monitor_id}/check")
async def trigger_check(
    monitor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Manually trigger a health check"""
    monitor = await monitor_service.get_monitor(db, monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    check = await monitor_service.execute_check(db, monitor)
    await broadcast_update("monitor_updated", MonitorResponse.model_validate(monitor).model_dump(mode="json"))
    return {"status": "success", "check_id": check.id}


@router.get("/status-page")
async def get_status_page(db: AsyncSession = Depends(get_db)):
    """Public status page data - no authentication required"""
    monitors = await monitor_service.get_monitors(db)

    status_data = {
        "overall_status": "operational",
        "monitors": [],
        "last_updated": datetime.utcnow().isoformat()
    }

    if not monitors:
        return status_data

    # Batch load all checks for all monitors in the last 24 hours (single query)
    monitor_ids = [m.id for m in monitors]
    since = datetime.utcnow() - timedelta(hours=24)
    checks_query = select(Check).where(
        and_(
            Check.monitor_id.in_(monitor_ids),
            Check.checked_at >= since
        )
    )
    checks_result = await db.execute(checks_query)
    all_checks = checks_result.scalars().all()

    # Group checks by monitor_id in Python
    checks_by_monitor: Dict = {}
    for check in all_checks:
        mid = check.monitor_id
        if mid not in checks_by_monitor:
            checks_by_monitor[mid] = []
        checks_by_monitor[mid].append(check)

    # Calculate uptime per monitor in Python (no additional DB queries)
    for monitor in monitors:
        monitor_checks = checks_by_monitor.get(monitor.id, [])
        if not monitor_checks:
            uptime_percentage = 100.0
        else:
            total = len(monitor_checks)
            up_count = sum(1 for c in monitor_checks if c.status == MonitorStatus.UP)
            uptime_percentage = round((up_count / total) * 100, 2)

        status_data["monitors"].append({
            "name": monitor.name,
            "status": monitor.status,
            "uptime_24h": uptime_percentage
        })

    return status_data


@router.get("/metrics/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get dashboard metrics"""
    from sqlalchemy import select, func
    from app.models import Monitor, Incident, MonitorStatus, IncidentStatus

    # Count monitors by status via DB aggregation
    status_result = await db.execute(
        select(Monitor.status, func.count(Monitor.id).label("count"))
        .group_by(Monitor.status)
    )
    status_counts = {row.status: row.count for row in status_result}

    monitors_up = status_counts.get(MonitorStatus.UP, 0)
    monitors_down = status_counts.get(MonitorStatus.DOWN, 0)
    monitors_degraded = status_counts.get(MonitorStatus.DEGRADED, 0)
    total_monitors = sum(status_counts.values())

    # Still fetch monitors for per-monitor uptime calculation
    monitors = await monitor_service.get_monitors(db)

    # Count active incidents
    query = select(func.count()).select_from(Incident).where(
        Incident.status.in_([IncidentStatus.INVESTIGATING, IncidentStatus.IDENTIFIED])
    )
    result = await db.execute(query)
    active_incidents = result.scalar()

    # Calculate average uptime
    total_uptime = 0
    for monitor in monitors:
        uptime_data = await monitor_service.calculate_uptime(db, monitor.id, hours=24)
        total_uptime += uptime_data["uptime_percentage"]

    avg_uptime = total_uptime / total_monitors if total_monitors > 0 else 100.0

    return DashboardMetrics(
        total_monitors=total_monitors,
        monitors_up=monitors_up,
        monitors_down=monitors_down,
        monitors_degraded=monitors_degraded,
        active_incidents=active_incidents,
        avg_uptime=round(avg_uptime, 2)
    )


# Incidents endpoints
@router.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents(
    monitor_id: Optional[uuid.UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """List incidents, optionally filtered by monitor"""
    from app.models import Incident
    query = select(Incident)
    if monitor_id:
        query = query.where(Incident.monitor_id == monitor_id)
    query = query.order_by(Incident.started_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# AI-powered analysis
@router.post("/ai/analyze-incident")
async def analyze_incident(
    incident_id: uuid.UUID,
    analysis_type: str = "general",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze incident using AI agent"""
    from sqlalchemy import select
    from app.models import Incident

    query = select(Incident).where(Incident.id == incident_id)
    result = await db.execute(query)
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get monitor details
    monitor = await monitor_service.get_monitor(db, incident.monitor_id)

    incident_data = {
        "incident_id": str(incident.id),
        "title": incident.title,
        "description": incident.description,
        "monitor_name": monitor.name if monitor else "Unknown",
        "duration": str(datetime.utcnow() - incident.started_at) if not incident.resolved_at else str(incident.resolved_at - incident.started_at)
    }

    analysis = await monitor_agent.process({
        "incident": incident_data,
        "type": analysis_type
    })

    return analysis
