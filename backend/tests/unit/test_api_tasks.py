"""
Unit tests for Task API endpoints
"""
import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.task_service import TaskService
import uuid


# Mock authentication for testing
async def override_get_current_active_user():
    """Override auth dependency for testing"""
    return {"sub": str(uuid.uuid4()), "email": "test@example.com"}


@pytest.mark.asyncio
class TestBoardAPI:
    """Tests for Board API endpoints"""

    async def test_create_board_success(self, db_session: AsyncSession):
        """Test creating a board via API"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/boards",
                json={
                    "name": "API Test Board",
                    "description": "Created via API"
                }
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "API Test Board"
        assert data["description"] == "Created via API"
        assert "id" in data

        # Cleanup
        app.dependency_overrides.clear()

    async def test_create_board_without_description(self, db_session: AsyncSession):
        """Test creating a board without description via API"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/boards",
                json={"name": "Simple Board"}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Simple Board"

        app.dependency_overrides.clear()

    async def test_get_boards(self, db_session: AsyncSession, sample_board):
        """Test getting all boards via API"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/boards")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        app.dependency_overrides.clear()

    async def test_get_board_by_id(self, db_session: AsyncSession, sample_board):
        """Test getting specific board by ID via API"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/boards/{sample_board.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_board.id)
        assert data["name"] == sample_board.name

        app.dependency_overrides.clear()

    async def test_get_board_with_nested_data(
        self, db_session: AsyncSession, sample_board
    ):
        """Test getting board with lists and cards"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        # Create list and cards
        list_obj = await TaskService.create_list(db_session, sample_board.id, "Test List")
        await TaskService.create_card(db_session, list_obj.id, "Card 1")
        await TaskService.create_card(db_session, list_obj.id, "Card 2")

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/boards/{sample_board.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "lists" in data
        assert len(data["lists"]) == 1
        assert len(data["lists"][0]["cards"]) == 2

        app.dependency_overrides.clear()

    async def test_get_nonexistent_board(self, db_session: AsyncSession):
        """Test getting board that doesn't exist"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        fake_id = uuid.uuid4()

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/boards/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()

    async def test_update_board(self, db_session: AsyncSession, sample_board):
        """Test updating a board via API"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                f"/api/boards/{sample_board.id}",
                json={
                    "name": "Updated Board Name",
                    "description": "Updated Description"
                }
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Board Name"
        assert data["description"] == "Updated Description"

        app.dependency_overrides.clear()

    async def test_delete_board(self, db_session: AsyncSession, sample_board):
        """Test deleting a board via API"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(f"/api/boards/{sample_board.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Board deleted successfully"

        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestListAPI:
    """Tests for List API endpoints"""

    async def test_create_list(self, db_session: AsyncSession, sample_board):
        """Test creating a list via API"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/boards/{sample_board.id}/lists",
                json={"name": "To Do", "position": 0}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "To Do"
        assert data["board_id"] == str(sample_board.id)
        assert data["position"] == 0

        app.dependency_overrides.clear()

    async def test_create_list_on_nonexistent_board(self, db_session: AsyncSession):
        """Test creating list on board that doesn't exist"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        fake_board_id = uuid.uuid4()

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/boards/{fake_board_id}/lists",
                json={"name": "Should Fail", "position": 0}
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestCardAPI:
    """Tests for Card API endpoints"""

    async def test_create_card(self, db_session: AsyncSession, sample_list):
        """Test creating a card via API"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/lists/{sample_list.id}/cards",
                json={
                    "title": "New Task",
                    "description": "Task description",
                    "position": 0
                }
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "New Task"
        assert data["description"] == "Task description"
        assert data["list_id"] == str(sample_list.id)

        app.dependency_overrides.clear()

    async def test_create_card_on_nonexistent_list(self, db_session: AsyncSession):
        """Test creating card on list that doesn't exist"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        fake_list_id = uuid.uuid4()

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/lists/{fake_list_id}/cards",
                json={"title": "Should Fail", "position": 0}
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

        app.dependency_overrides.clear()

    async def test_move_card(self, db_session: AsyncSession, sample_board, sample_list, sample_card):
        """Test moving a card via API"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        # Create new list
        new_list = await TaskService.create_list(db_session, sample_board.id, "Done", position=1)

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                f"/api/cards/{sample_card.id}/move",
                json={
                    "new_list_id": str(new_list.id),
                    "new_position": 0
                }
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["list_id"] == str(new_list.id)
        assert data["position"] == 0

        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestActivityAPI:
    """Tests for Activity API endpoints"""

    async def test_get_board_activity(
        self, db_session: AsyncSession, sample_board, sample_user_id
    ):
        """Test getting board activity via API"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/boards/{sample_board.id}/activity")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the board creation activity

        app.dependency_overrides.clear()

    async def test_get_board_activity_with_limit(
        self, db_session: AsyncSession, sample_board
    ):
        """Test getting board activity with limit parameter"""
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/boards/{sample_board.id}/activity?limit=5"
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 5

        app.dependency_overrides.clear()
