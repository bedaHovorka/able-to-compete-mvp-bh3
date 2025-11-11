"""
Test configuration and fixtures for pytest
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.utils.database import Base
from app.models import Board, List, Card
import uuid

# Test database URL (using SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_user_id() -> uuid.UUID:
    """Sample user ID for testing"""
    return uuid.uuid4()


@pytest_asyncio.fixture
async def sample_board(db_session: AsyncSession, sample_user_id: uuid.UUID) -> Board:
    """Create a sample board for testing"""
    board = Board(
        name="Test Board",
        description="A test board for unit testing",
        user_id=sample_user_id
    )
    db_session.add(board)
    await db_session.commit()
    await db_session.refresh(board)
    return board


@pytest_asyncio.fixture
async def sample_list(db_session: AsyncSession, sample_board: Board) -> List:
    """Create a sample list for testing"""
    list_obj = List(
        board_id=sample_board.id,
        name="Test List",
        position=0
    )
    db_session.add(list_obj)
    await db_session.commit()
    await db_session.refresh(list_obj)
    return list_obj


@pytest_asyncio.fixture
async def sample_card(db_session: AsyncSession, sample_list: List) -> Card:
    """Create a sample card for testing"""
    card = Card(
        list_id=sample_list.id,
        title="Test Card",
        description="A test card",
        position=0,
        completed=False
    )
    db_session.add(card)
    await db_session.commit()
    await db_session.refresh(card)
    return card
