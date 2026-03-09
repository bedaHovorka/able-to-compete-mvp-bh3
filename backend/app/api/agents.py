from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Literal
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
    type: Literal["api", "service", "general"] = "general"


# --- Endpoints ---

@router.post("/spec", dependencies=[Depends(get_current_active_user)])
async def generate_spec(body: SpecRequest):
    agent = SpecAgent()
    return await agent.process(body.model_dump())


@router.post("/test", dependencies=[Depends(get_current_active_user)])
async def generate_test(body: TestRequest):
    agent = TestAgent()
    return await agent.process(body.model_dump())


@router.post("/dev", dependencies=[Depends(get_current_active_user)])
async def generate_dev(body: DevRequest):
    agent = DevAgent()
    return await agent.process(body.model_dump())
