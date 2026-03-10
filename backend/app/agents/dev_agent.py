from app.agents.base_agent import BaseAgent
from typing import Dict, Any


class DevAgent(BaseAgent):
    """Agent for code generation and development assistance"""

    def simulate_response(self, prompt: str) -> str:
        """Simulate code generation"""
        specification = prompt.split("for: ", 1)[-1] if "for: " in prompt else prompt
        resource = specification.replace(" ", "_").replace("-", "_").lower()[:30]
        prompt_prefix = prompt.split("for:")[0].lower() if "for:" in prompt else prompt.lower()
        if "api" in prompt_prefix or "endpoint" in prompt_prefix:
            return f"""
# API endpoints for: {specification}
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.database import get_db
from pydantic import BaseModel
from typing import List, Optional
import uuid

router = APIRouter(prefix="/api/{resource}s", tags=["{resource}s"])


class {resource.title()}Create(BaseModel):
    name: str
    description: Optional[str] = None


class {resource.title()}Response(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


@router.post("/", response_model={resource.title()}Response, status_code=status.HTTP_201_CREATED)
async def create_{resource}(
    data: {resource.title()}Create,
    db: AsyncSession = Depends(get_db)
):
    '''Create a new {resource} — {specification}'''
    item = await {resource.title()}Service.create(db, name=data.name, description=data.description)
    return item


@router.get("/", response_model=List[{resource.title()}Response])
async def list_{resource}s(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    '''List all {resource}s — {specification}'''
    return await {resource.title()}Service.list(db, skip=skip, limit=limit)


@router.get("/{{item_id}}", response_model={resource.title()}Response)
async def get_{resource}(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    '''Get {resource} by ID'''
    item = await {resource.title()}Service.get(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{resource.title()} not found")
    return item


@router.delete("/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{resource}(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    '''Delete {resource}'''
    if not await {resource.title()}Service.delete(db, item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{resource.title()} not found")
"""
        elif "service" in prompt_prefix:
            return f"""
# Service layer for: {specification}
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.utils.logger import logger
from typing import Optional, List
import uuid


class {resource.title()}Service:
    '''Service for {specification}'''

    @staticmethod
    async def create(db: AsyncSession, name: str, description: Optional[str] = None):
        '''Create a new {resource}'''
        from app.models import {resource.title()}
        item = {resource.title()}(name=name, description=description)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        logger.info(f"Created {resource}: {{item.id}}")
        return item

    @staticmethod
    async def get(db: AsyncSession, item_id: uuid.UUID):
        '''Get {resource} by ID'''
        from app.models import {resource.title()}
        query = select({resource.title()}).where({resource.title()}.id == item_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list(db: AsyncSession, skip: int = 0, limit: int = 100) -> List:
        '''List {resource}s with pagination'''
        from app.models import {resource.title()}
        query = select({resource.title()}).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def delete(db: AsyncSession, item_id: uuid.UUID) -> bool:
        '''Delete {resource}'''
        from app.models import {resource.title()}
        item = await {resource.title()}Service.get(db, item_id)
        if not item:
            return False
        await db.delete(item)
        await db.commit()
        return True
"""
        elif "model" in prompt_prefix:
            table_name = resource + "s"
            return f"""
# SQLAlchemy model for: {specification}
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.utils.database import Base
from pydantic import BaseModel
from typing import Optional
import uuid


class {resource.title()}(Base):
    '''ORM model for {specification}'''
    __tablename__ = "{table_name}"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<{resource.title()} id={{self.id}} name={{self.name!r}}>"


# Pydantic schemas
class {resource.title()}Base(BaseModel):
    name: str
    description: Optional[str] = None


class {resource.title()}Create({resource.title()}Base):
    pass


class {resource.title()}Update(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class {resource.title()}Response({resource.title()}Base):
    id: uuid.UUID
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
"""
        elif "util" in prompt_prefix:
            return f"""
# Utility helpers for: {specification}
import re
import asyncio
import httpx
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from app.utils.logger import logger


def validate_{resource}(data: Dict[str, Any]) -> bool:
    '''Validate input data for {specification}'''
    if not data:
        return False
    if "name" in data and (not data["name"] or not isinstance(data["name"], str)):
        return False
    if "name" in data and len(data["name"]) > 255:
        raise ValueError("name exceeds maximum length of 255 characters")
    return True


def format_{resource}_name(raw: str) -> str:
    '''Normalise a {resource} name — strips extra whitespace and lowercases'''
    cleaned = re.sub(r"\\s+", " ", raw.strip())
    return cleaned.lower()


def to_utc_iso(dt: Optional[datetime] = None) -> str:
    '''Return an ISO-8601 UTC timestamp string'''
    if dt is None:
        dt = datetime.now(tz=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


async def fetch_{resource}_data(url: str, timeout: float = 10.0) -> Dict[str, Any]:
    '''Async HTTP helper — fetches JSON from *url* for {specification}'''
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        logger.info(f"Fetched {resource} data from {{url}}: {{response.status_code}}")
        return response.json()


def paginate(items: list, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    '''Return a page of *items* with pagination metadata'''
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {{
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }}
"""
        else:
            return f"""
# Generated implementation for: {specification}
from typing import Any, Dict, Optional


class {resource.title()}Component:
    '''Component implementing: {specification}'''

    def __init__(self):
        self.initialized = True
        self.spec = "{specification}"

    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        '''Process request for {specification}'''
        if not data:
            raise ValueError("Input data is required")
        return {{"status": "success", "spec": self.spec, "data": data}}

    async def validate(self, data: Dict[str, Any]) -> bool:
        '''Validate input for {specification}'''
        return bool(data)
"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code from specification"""
        specification = input_data.get("specification", "")
        code_type = input_data.get("type", "general")  # api, service, model, util

        system_prompt = """You are a code generation agent. Generate clean,
        production-ready Python code following best practices. Include proper
        error handling, type hints, docstrings, and logging."""

        prompt = f"Generate {code_type} code for: {specification}"

        result = await self.call_llm(prompt, system_prompt)

        return {
            "code": result,
            "code_type": code_type,
            "specification": specification,
            "language": "python"
        }
