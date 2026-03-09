"""Agents API router — exposes SpecAgent, TestAgent, DevAgent, and MonitorAgent over HTTP."""

import uuid
from datetime import datetime

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Literal, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.utils.auth import get_current_active_user
from app.utils.database import get_db
from app.agents import SpecAgent, TestAgent, DevAgent, MonitorAgent
from app.models.monitor import Incident, Monitor

router = APIRouter(prefix="/api/agents", tags=["agents"])


# --- Request models (field names match agent process() signatures) ---

class SpecRequest(BaseModel):
    requirements: str
    type: Literal["general", "user_story", "bdd"] = "general"


class TestRequest(BaseModel):
    specification: str
    type: Literal["unit", "integration", "bdd"] = "unit"


class DevRequest(BaseModel):
    specification: str
    type: Literal["api", "service", "general", "model", "util"] = "general"


# --- Response models ---

class SpecResponse(BaseModel):
    specification: str
    type: str
    requirements: str


class TestResponse(BaseModel):
    test_code: str
    test_type: str
    specification: str


class DevResponse(BaseModel):
    code: str
    code_type: str
    specification: str
    language: str


class MonitorAgentRequest(BaseModel):
    incident_id: uuid.UUID
    description: str
    analysis_type: Literal["general", "root_cause", "pattern"] = "general"


class MonitorAgentResponse(BaseModel):
    incident_id: uuid.UUID
    analysis_type: str
    result: dict


# --- Endpoints ---

@router.post("/spec", dependencies=[Depends(get_current_active_user)], response_model=SpecResponse)
async def generate_spec(body: SpecRequest):
    agent = SpecAgent()
    try:
        return await agent.process(body.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Agent processing failed") from exc


@router.post("/test", dependencies=[Depends(get_current_active_user)], response_model=TestResponse)
async def generate_test(body: TestRequest):
    agent = TestAgent()
    try:
        return await agent.process(body.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Agent processing failed") from exc


@router.post("/dev", dependencies=[Depends(get_current_active_user)], response_model=DevResponse)
async def generate_dev(body: DevRequest):
    agent = DevAgent()
    try:
        return await agent.process(body.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Agent processing failed") from exc


<<<<<<< HEAD
# --- Pipeline schemas ---

class PipelineRequest(BaseModel):
    requirements: str
    run_steps: List[Literal["spec", "test", "dev"]] = ["spec", "test", "dev"]


class PipelineResponse(BaseModel):
    spec: Optional[str] = None
    tests: Optional[str] = None
    code: Optional[str] = None
    errors: Dict[str, str] = {}


# --- Pipeline endpoint ---

_CANONICAL_STEPS = ["spec", "test", "dev"]


@router.post("/pipeline", response_model=PipelineResponse)
async def run_pipeline(
    body: PipelineRequest,
    current_user=Depends(get_current_active_user),
):
    """Run SpecAgent, then TestAgent + DevAgent in parallel, feeding spec output to both."""
    # Validate ordering: run_steps must follow canonical order
    ordered = [s for s in _CANONICAL_STEPS if s in body.run_steps]
    if ordered != body.run_steps:
        raise HTTPException(
            status_code=422,
            detail="run_steps must follow canonical order: spec, test, dev",
        )
    # test/dev require spec
    if ("test" in body.run_steps or "dev" in body.run_steps) and "spec" not in body.run_steps:
        raise HTTPException(
            status_code=422,
            detail="test/dev require spec to be included in run_steps",
        )

    errors: Dict[str, str] = {}
    response = PipelineResponse()

    # Step 1: Spec
    spec_text: Optional[str] = None
    if "spec" in body.run_steps:
        try:
            result = await asyncio.wait_for(
                SpecAgent().process({"requirements": body.requirements}),
                timeout=60.0,
            )
            spec_text = result.get("specification")
            response.spec = spec_text
        except asyncio.TimeoutError:
            errors["spec"] = "Step timed out after 60 seconds"
            response.errors = errors
            return response  # abort — no spec to pass downstream
        except Exception as exc:
            errors["spec"] = str(exc)
            response.errors = errors
            return response  # abort — no spec to pass downstream

    # Steps 2+3: Test and Dev in parallel (both consume spec_text independently)
    async def run_test() -> Optional[str]:
        result = await asyncio.wait_for(
            TestAgent().process({"specification": spec_text}),
            timeout=60.0,
        )
        return result.get("test_code")

    async def run_dev() -> Optional[str]:
        result = await asyncio.wait_for(
            DevAgent().process({"specification": spec_text}),
            timeout=60.0,
        )
        return result.get("code")

    tasks: Dict[str, asyncio.Task] = {}
    if "test" in body.run_steps and spec_text is not None:
        tasks["test"] = asyncio.create_task(run_test())
    if "dev" in body.run_steps and spec_text is not None:
        tasks["dev"] = asyncio.create_task(run_dev())

    for step, task in tasks.items():
        try:
            value = await task
            if step == "test":
                response.tests = value
            else:
                response.code = value
        except asyncio.TimeoutError:
            errors[step] = "Step timed out after 60 seconds"
        except Exception as exc:
            errors[step] = str(exc)

    response.errors = errors
    return response


@router.post("/monitor", response_model=MonitorAgentResponse, status_code=200)
async def analyze_incident(
    body: MonitorAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    # 1. Look up incident
    result = await db.execute(select(Incident).where(Incident.id == body.incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # 2. Resolve monitor name
    monitor_result = await db.execute(select(Monitor).where(Monitor.id == incident.monitor_id))
    monitor = monitor_result.scalar_one_or_none()
    monitor_name = monitor.name if monitor else "Unknown"

    # 3. Calculate duration (seconds from started_at to resolved_at or now)
    # Use timezone-naive utcnow() to stay consistent with the naive datetimes stored in the DB.
    end_time = incident.resolved_at or datetime.utcnow()  # noqa: DTZ003
    duration_seconds = (end_time - incident.started_at).total_seconds()

    # 4. Build context and run agent
    # NOTE: analysis_type="root_cause" won't match "root cause" in simulate_response()
    # because simulate_response() checks for "root cause" (with space) while the field
    # value is "root_cause" (with underscore). This is a known bug to fix in a follow-on issue.
    context = {
        "incident": {
            "title": incident.title,
            "description": body.description,
            "monitor_name": monitor_name,
            "duration": duration_seconds,
            "incident_id": str(body.incident_id),
        },
        "type": body.analysis_type,
    }
    agent = MonitorAgent()
    try:
        agent_result = await agent.process(context)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Agent processing failed") from exc

    return MonitorAgentResponse(
        incident_id=body.incident_id,
        analysis_type=body.analysis_type,
        result=agent_result,
    )
