# BDD Tests Design — 2026-03-09

## Goal

Implement real, runnable BDD tests using pytest-bdd + testcontainers-python against a real PostgreSQL database. Tests must be fully self-contained (no manual `docker compose up` required) and fast enough for demo/judge use.

## Approach

pytest-bdd with `testcontainers[postgres]` using `postgres:16-alpine`. A session-scoped fixture starts the container once per test run; transaction rollback resets state between tests.

## Feature Coverage

### task_management.feature (~6 scenarios)
- Create board, add list, add card
- Move card between lists
- Soft-delete board
- Audit log records card creation

### monitoring.feature (~6 scenarios)
- Create monitor, trigger check, verify status
- Auto-create incident after 3 consecutive failures
- Auto-resolve incident on recovery
- Status page shows correct uptime

### ai_agents.feature (2 scenarios)
- Analyze incident with simulated response (always runs)
- Analyze incident with real Anthropic API (skipped when `ANTHROPIC_API_KEY` not set)

## Test Infrastructure

```
backend/
  tests/
    conftest.py                    # testcontainers fixture, async app client
    features/
      task_management.feature
      monitoring.feature
      ai_agents.feature            # new
    step_defs/
      test_task_steps.py
      test_monitoring_steps.py
      test_ai_steps.py             # new
```

## Key Implementation Details

```python
# Session-scoped container — starts once, shared by all tests
@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

# Function-scoped rollback — fast state reset, no container restart
@pytest.fixture(scope="function", autouse=True)
async def rollback_after_test(db_session):
    yield
    await db_session.rollback()
```

## Dependencies Added

- `testcontainers[postgres]` — PostgreSQL container management

Already present:
- `pytest-bdd>=6.1.1`
- `httpx` (used by monitor service)

## Run Command

```bash
cd backend
uv run pytest tests/ --bdd -v
```

Startup time: ~2–3 seconds after first image pull (`postgres:16-alpine` ~100MB).

## Success Criteria

- All BDD scenarios pass with `pytest --bdd`
- No manual infrastructure setup required
- AI agent simulated scenario always passes
- AI agent real-LLM scenario auto-skips when `ANTHROPIC_API_KEY` absent
