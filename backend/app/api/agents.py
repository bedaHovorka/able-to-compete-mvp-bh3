"""Agents API router — exposes SpecAgent, TestAgent, and DevAgent over HTTP."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Literal, Optional
from app.utils.auth import get_current_active_user
from app.agents import SpecAgent, TestAgent, DevAgent

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
