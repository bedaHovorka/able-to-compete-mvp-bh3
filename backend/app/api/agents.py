"""Agents API router — exposes SpecAgent, TestAgent, and DevAgent over HTTP."""

from fastapi import APIRouter, Depends, HTTPException
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
