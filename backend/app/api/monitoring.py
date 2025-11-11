from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.database import get_db
from app.utils.auth import get_current_active_user
from app.services import MonitorService
from app.agents import MonitorAgent
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uuid

router = APIRouter(prefix="/api", tags=["monitoring"])

# Initialize services
monitor_service = MonitorService()
monitor_agent = MonitorAgent()


# Schemas
class MonitorCreate(BaseModel):
    name: str
    url: str
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

    class Config:
        from_attributes = True


class UptimeResponse(BaseModel):
    uptime_percentage: float
    total_checks: int
    failed_checks: int
    avg_response_time: float


class DashboardMetrics(BaseModel):
    total_monitors: int
    monitors_up: int
    monitors_down: int
    monitors_degraded: int
    active_incidents: int
    avg_uptime: float


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
        url=monitor_data.url,
        interval=monitor_data.interval,
        monitor_type=monitor_data.type
    )
    return monitor


@router.get("/monitors", response_model=List[MonitorResponse])
async def list_monitors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """List all monitors"""
    monitors = await monitor_service.get_monitors(db, skip=skip, limit=limit)
    return monitors


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
    return monitor


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

    for monitor in monitors:
        uptime = await monitor_service.calculate_uptime(db, monitor.id, hours=24)
        status_data["monitors"].append({
            "name": monitor.name,
            "status": monitor.status,
            "uptime_24h": uptime["uptime_percentage"]
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

    # Count monitors by status
    monitors = await monitor_service.get_monitors(db)
    total_monitors = len(monitors)
    monitors_up = sum(1 for m in monitors if m.status == MonitorStatus.UP)
    monitors_down = sum(1 for m in monitors if m.status == MonitorStatus.DOWN)
    monitors_degraded = sum(1 for m in monitors if m.status == MonitorStatus.DEGRADED)

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
