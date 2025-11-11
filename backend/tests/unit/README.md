# Unit Tests

This directory contains comprehensive unit tests for the AbleToCompete MVP backend.

## Test Files

### test_models.py
Tests for SQLAlchemy database models:
- **BoardModel**: Creating, updating, soft-deleting boards and relationships
- **ListModel**: Creating lists with positions
- **CardModel**: Creating, completing, moving cards between lists
- **LabelModel**: Creating labels and associating with cards
- **ActivityModel**: Logging board activities

### test_task_service.py
Tests for TaskService business logic:
- **Board Operations**: create, get, update, delete boards with pagination
- **List Operations**: create lists, handle nonexistent boards
- **Card Operations**: create, move cards between lists
- **Activity Operations**: get board activity logs with limits

### test_api_tasks.py
Tests for FastAPI API endpoints:
- **Board API**: POST, GET, PUT, DELETE endpoints
- **List API**: Creating lists on boards
- **Card API**: Creating and moving cards
- **Activity API**: Getting board activity logs

## Running Tests

### With PostgreSQL Test Database (Recommended)

The models use PostgreSQL-specific types (UUID), so tests require a PostgreSQL database:

```bash
# Option 1: Run with existing test database
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/test_db"
python3.11 -m pytest tests/unit/ -v

# Option 2: Use Docker for isolated test database
docker run --name postgres-test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test_db -p 5433:5432 -d postgres:15
export DATABASE_URL="postgresql+asyncpg://postgres:test@localhost:5433/test_db"
python3.11 -m pytest tests/unit/ -v
```

### Test Coverage

```bash
python3.11 -m pytest tests/unit/ --cov=app --cov-report=html
```

## Test Structure

```
tests/
├── conftest.py                    # Fixtures and test configuration
├── pytest.ini                     # Pytest configuration
└── unit/
    ├── test_models.py            # Model layer tests (14 tests)
    ├── test_task_service.py      # Service layer tests (28 tests)
    └── test_api_tasks.py         # API layer tests (15 tests)
```

## Test Coverage Summary

- **Total Tests**: 57 unit tests
- **Models**: 14 tests covering all model CRUD operations
- **Services**: 28 tests covering business logic
- **API**: 15 tests covering HTTP endpoints

## Fixtures

Defined in `conftest.py`:
- `test_engine`: Async SQLAlchemy engine
- `db_session`: Async database session
- `sample_user_id`: Test user UUID
- `sample_board`: Pre-created test board
- `sample_list`: Pre-created test list
- `sample_card`: Pre-created test card

## Note on SQLite

The tests were initially designed for SQLite in-memory testing, but the models use PostgreSQL-specific `UUID` types that aren't compatible with SQLite. To run tests:

1. Use PostgreSQL (recommended)
2. Or modify models to use String type for IDs (not recommended for production)
3. Or use mocking for database layer

## Dependencies

```bash
pip3 install pytest pytest-asyncio pytest-cov aiosqlite httpx
```

For PostgreSQL testing:
```bash
pip3 install asyncpg psycopg2-binary
```
