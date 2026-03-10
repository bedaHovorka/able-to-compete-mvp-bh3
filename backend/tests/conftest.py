"""
BDD + unit test fixtures.
Uses testcontainers postgres:16-alpine (session-scoped, ~2-3s startup).

Key design decisions:
- BDD steps use sync TestClient (Starlette) — pytest-bdd does not await coroutines,
  so async step functions don't work reliably. Sync client lets steps be plain def.
- Unit tests that need a DB session still use async db_session + async engine.
- session-scoped event_loop fixture (pytest-asyncio 0.21 requirement for session
  scoped async fixtures).
- Per-test failure_counts reset prevents cross-test monitoring state pollution.
"""
import asyncio
import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from app.models import Board, Card
from app.models import List as ListModel
from app.models.monitor import Incident, IncidentSeverity, Monitor, MonitorType
from app.utils.database import Base, get_db


# ── Marker: skip @real_llm tests when ANTHROPIC_API_KEY is not set ────────────

def pytest_collection_modifyitems(items):
    skip_real_llm = pytest.mark.skip(reason="ANTHROPIC_API_KEY not set")
    for item in items:
        if "real_llm" in item.keywords and not os.getenv("ANTHROPIC_API_KEY"):
            item.add_marker(skip_real_llm)


# ── Session-scoped event loop (required for session-scoped async fixtures) ────

@pytest.fixture(scope="session")
def event_loop():
    """Override pytest-asyncio event_loop to be session-scoped."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Container (session-scoped: starts once for entire test run) ──────────────

@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_url(pg_container):
    # testcontainers returns psycopg2 URL; swap driver for asyncpg
    return pg_container.get_connection_url().replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://"
    )


# ── Engine + schema (session-scoped) ─────────────────────────────────────────

@pytest_asyncio.fixture(scope="session")
async def engine(db_url):
    eng = create_async_engine(db_url, echo=False, poolclass=NullPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture(scope="session")
def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── Per-test DB session with rollback (for unit tests) ────────────────────────

@pytest_asyncio.fixture(scope="function")
async def db_session(session_factory):
    async with session_factory() as session:
        yield session
        await session.rollback()


# ── Reset module-level monitor failure counters between tests ─────────────────

@pytest.fixture(autouse=True)
def reset_failure_counts():
    import app.services.monitor_service as ms
    ms.failure_counts.clear()
    yield
    ms.failure_counts.clear()


# ── Sync FastAPI test client (for BDD steps — pytest-bdd doesn't await coroutines) ──

@pytest.fixture(scope="function")
def client(session_factory):
    """
    Synchronous Starlette TestClient.
    All BDD step functions should be plain def (not async def).
    The lifespan is overridden to skip production DB setup.
    """
    from contextlib import asynccontextmanager
    from starlette.testclient import TestClient
    from app.main import app

    @asynccontextmanager
    async def noop_lifespan(app):
        """Skip production DB setup — tables already created by engine fixture."""
        yield

    app.router.lifespan_context = noop_lifespan

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app=app, base_url="http://test", raise_server_exceptions=True) as tc:
        yield tc

    app.dependency_overrides.clear()


# ── Auth helper ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def headers(client):
    """Obtain a JWT bearer token via demo login (sync)."""
    r = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "any"},
    )
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Shared domain fixtures ────────────────────────────────────────────────────

@pytest.fixture
def sample_user_id():
    return uuid.uuid4()


@pytest_asyncio.fixture
async def sample_board(db_session, sample_user_id):
    board = Board(name="Test Board", description="unit test board", user_id=sample_user_id)
    db_session.add(board)
    await db_session.commit()
    await db_session.refresh(board)
    return board


@pytest_asyncio.fixture
async def sample_list(db_session, sample_board):
    lst = ListModel(board_id=sample_board.id, name="Test List", position=0)
    db_session.add(lst)
    await db_session.commit()
    await db_session.refresh(lst)
    return lst


@pytest_asyncio.fixture
async def sample_card(db_session, sample_list):
    card = Card(list_id=sample_list.id, title="Test Card", position=0, completed=False)
    db_session.add(card)
    await db_session.commit()
    await db_session.refresh(card)
    return card


@pytest_asyncio.fixture
async def sample_monitor(db_session):
    monitor = Monitor(name="Test Monitor", url="https://example.com", type=MonitorType.HTTPS)
    db_session.add(monitor)
    await db_session.commit()
    await db_session.refresh(monitor)
    return monitor


@pytest_asyncio.fixture
async def sample_incident(db_session, sample_monitor):
    incident = Incident(
        monitor_id=sample_monitor.id,
        title="Test monitor is down",
        severity=IncidentSeverity.CRITICAL,
    )
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)
    return incident
