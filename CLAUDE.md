# CLAUDE.md — able-to-compete-mvp-bh3

## Project Overview

MVP combining three features in one FastAPI + React application:
- **Trello-like task management** — boards, lists, cards with drag-and-drop
- **Uptime monitoring** — monitors, checks, incidents, status pages
- **AI agents** — spec, test, dev, and monitor agents (currently simulate LLM responses)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy (async), PostgreSQL |
| Frontend | React, TypeScript |
| Auth | JWT (demo mode: accepts any credentials) |
| AI | Custom agent base class; LLM calls simulated for MVP |
| Infra | Docker Compose |

## Running the Project

```bash
# Full stack (recommended)
docker compose up

# Backend only (local dev)
cd backend
uv run uvicorn app.main:app --reload

# Frontend only (local dev)
cd frontend
npm install
npm run dev
```

## Package Management

- **Backend**: `uv` — run `uv sync` from `backend/`, then `uv run <cmd>`
- **Frontend**: `npm` — run from `frontend/`

## Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
JWT_SECRET_KEY=<secret>
OPENAI_API_KEY=<key>          # Not yet used (agents simulate responses)
ALERT_COOLDOWN=300            # Seconds between repeated alerts
LLM_MODEL=gpt-4               # Model name (for future real LLM calls)
```

See `backend/.env.example` for full list.

## API Structure

Routers in `backend/app/api/`:

| Router | Prefix | Handles |
|--------|--------|---------|
| `auth.py` | `/api/auth` | Login, token refresh |
| `tasks.py` | `/api` | Boards, lists, cards, activity |
| `monitoring.py` | `/api` | Monitors, checks, incidents, status pages |
| `websocket.py` | `/ws` | Real-time updates |

## Key File Paths

```
backend/
  app/
    main.py                  # FastAPI app, router registration, lifespan
    config.py                # Settings (pydantic-settings)
    models/
      task.py                # Board, List, Card, Activity
      monitor.py             # Monitor, Check, Incident, StatusPage, Metric
    api/
      tasks.py               # Task management endpoints
      monitoring.py          # Monitoring endpoints
      auth.py                # Auth endpoints
      websocket.py           # WebSocket endpoint
    services/
      task_service.py        # Board/list/card business logic
      monitor_service.py     # Monitor checking logic
      alert_service.py       # Alert routing (email/webhook/sms — simulated)
    agents/
      base_agent.py          # Abstract base with call_llm() + simulate_response()
      spec_agent.py          # Generates feature specs
      test_agent.py          # Generates test cases
      dev_agent.py           # Generates implementation code
      monitor_agent.py       # Analyzes monitoring incidents
    utils/
      database.py            # Async engine, get_db dependency
      auth.py                # JWT helpers, get_current_active_user
      logger.py              # Shared logger
  tests/
    unit/                    # pytest unit tests (in-memory SQLite)
    integration/             # Integration tests
```

## AI Agents

Four agents extend `BaseAgent`:

| Agent | Class | Purpose |
|-------|-------|---------|
| Spec | `SpecAgent` | Writes feature specifications |
| Test | `TestAgent` | Generates test cases from specs |
| Dev | `DevAgent` | Generates implementation from specs |
| Monitor | `MonitorAgent` | Analyzes incidents, suggests fixes |

All currently return simulated responses via `simulate_response()`. To wire up a real LLM, implement `call_llm()` in `BaseAgent` using the OpenAI-compatible API pattern.

## Testing

```bash
cd backend
uv run pytest tests/          # All tests
uv run pytest tests/unit/     # Unit tests only
```

Tests use an in-memory SQLite database via `conftest.py` fixtures.

## Architecture Notes

- **Async throughout**: all DB access uses `AsyncSession`; route handlers are `async def`
- **Soft delete**: `Board` has `deleted_at` column; queries filter `deleted_at IS NULL`
- **WebSocket**: broadcasts board updates to connected clients
- **JWT auth**: demo mode accepts any username/password and issues a token
- **Alembic**: migrations in `backend/alembic/`; run `uv run alembic upgrade head`
