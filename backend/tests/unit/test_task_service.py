"""
Unit tests for TaskService
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.task_service import TaskService
from app.models import Board, List, Card, Activity
import uuid


@pytest.mark.asyncio
class TestTaskServiceBoard:
    """Tests for TaskService board operations"""

    async def test_create_board(self, db_session: AsyncSession, sample_user_id: uuid.UUID):
        """Test creating a board"""
        board = await TaskService.create_board(
            db_session,
            name="New Project",
            description="Project description",
            user_id=sample_user_id
        )

        assert board is not None
        assert board.id is not None
        assert board.name == "New Project"
        assert board.description == "Project description"
        assert board.user_id == sample_user_id
        assert board.deleted_at is None

    async def test_create_board_without_description(
        self, db_session: AsyncSession, sample_user_id: uuid.UUID
    ):
        """Test creating a board without description"""
        board = await TaskService.create_board(
            db_session,
            name="Simple Board",
            user_id=sample_user_id
        )

        assert board is not None
        assert board.name == "Simple Board"
        assert board.description is None

    async def test_get_boards(self, db_session: AsyncSession, sample_user_id: uuid.UUID):
        """Test getting all boards"""
        # Create multiple boards
        for i in range(3):
            await TaskService.create_board(
                db_session,
                name=f"Board {i}",
                user_id=sample_user_id
            )

        boards = await TaskService.get_boards(db_session, user_id=sample_user_id)

        assert len(boards) == 3
        assert all(board.user_id == sample_user_id for board in boards)

    async def test_get_boards_pagination(
        self, db_session: AsyncSession, sample_user_id: uuid.UUID
    ):
        """Test getting boards with pagination"""
        # Create 5 boards
        for i in range(5):
            await TaskService.create_board(
                db_session,
                name=f"Board {i}",
                user_id=sample_user_id
            )

        # Get first 2
        boards_page1 = await TaskService.get_boards(
            db_session, user_id=sample_user_id, skip=0, limit=2
        )
        assert len(boards_page1) == 2

        # Get next 2
        boards_page2 = await TaskService.get_boards(
            db_session, user_id=sample_user_id, skip=2, limit=2
        )
        assert len(boards_page2) == 2

        # Ensure different boards
        assert boards_page1[0].id != boards_page2[0].id

    async def test_get_board_by_id(self, db_session: AsyncSession, sample_board: Board):
        """Test getting a specific board"""
        board = await TaskService.get_board(db_session, sample_board.id)

        assert board is not None
        assert board.id == sample_board.id
        assert board.name == sample_board.name

    async def test_get_board_with_nested_data(
        self, db_session: AsyncSession, sample_board: Board
    ):
        """Test getting board with lists and cards"""
        # Create list with cards
        list_obj = await TaskService.create_list(
            db_session, sample_board.id, "Test List"
        )
        await TaskService.create_card(
            db_session, list_obj.id, "Card 1", "Description 1"
        )
        await TaskService.create_card(
            db_session, list_obj.id, "Card 2", "Description 2"
        )

        # Get board with nested data
        board = await TaskService.get_board(db_session, sample_board.id)

        assert board is not None
        assert len(board.lists) == 1
        assert len(board.lists[0].cards) == 2

    async def test_get_nonexistent_board(self, db_session: AsyncSession):
        """Test getting a board that doesn't exist"""
        fake_id = uuid.uuid4()
        board = await TaskService.get_board(db_session, fake_id)

        assert board is None

    async def test_update_board(self, db_session: AsyncSession, sample_board: Board):
        """Test updating a board"""
        updated_board = await TaskService.update_board(
            db_session,
            sample_board.id,
            name="Updated Name",
            description="Updated Description"
        )

        assert updated_board is not None
        assert updated_board.name == "Updated Name"
        assert updated_board.description == "Updated Description"
        assert updated_board.updated_at > sample_board.created_at

    async def test_update_board_partial(self, db_session: AsyncSession, sample_board: Board):
        """Test updating only board name"""
        original_description = sample_board.description
        updated_board = await TaskService.update_board(
            db_session,
            sample_board.id,
            name="New Name Only"
        )

        assert updated_board is not None
        assert updated_board.name == "New Name Only"
        assert updated_board.description == original_description

    async def test_update_nonexistent_board(self, db_session: AsyncSession):
        """Test updating a board that doesn't exist"""
        fake_id = uuid.uuid4()
        result = await TaskService.update_board(
            db_session, fake_id, name="Should Fail"
        )

        assert result is None

    async def test_delete_board(self, db_session: AsyncSession, sample_board: Board):
        """Test soft deleting a board"""
        result = await TaskService.delete_board(db_session, sample_board.id)

        assert result is True

        # Verify board is soft deleted
        board = await TaskService.get_board(db_session, sample_board.id)
        assert board is None  # Soft deleted boards not returned

    async def test_delete_nonexistent_board(self, db_session: AsyncSession):
        """Test deleting a board that doesn't exist"""
        fake_id = uuid.uuid4()
        result = await TaskService.delete_board(db_session, fake_id)

        assert result is False


@pytest.mark.asyncio
class TestTaskServiceList:
    """Tests for TaskService list operations"""

    async def test_create_list(self, db_session: AsyncSession, sample_board: Board):
        """Test creating a list"""
        list_obj = await TaskService.create_list(
            db_session,
            sample_board.id,
            "To Do",
            position=0
        )

        assert list_obj is not None
        assert list_obj.id is not None
        assert list_obj.name == "To Do"
        assert list_obj.board_id == sample_board.id
        assert list_obj.position == 0

    async def test_create_list_default_position(
        self, db_session: AsyncSession, sample_board: Board
    ):
        """Test creating list with default position"""
        list_obj = await TaskService.create_list(
            db_session,
            sample_board.id,
            "New List"
        )

        assert list_obj is not None
        assert list_obj.position == 0

    async def test_create_list_on_nonexistent_board(self, db_session: AsyncSession):
        """Test creating list on board that doesn't exist"""
        fake_board_id = uuid.uuid4()
        list_obj = await TaskService.create_list(
            db_session,
            fake_board_id,
            "Should Fail"
        )

        assert list_obj is None

    async def test_create_multiple_lists(
        self, db_session: AsyncSession, sample_board: Board
    ):
        """Test creating multiple lists with different positions"""
        list_names = ["Backlog", "In Progress", "Done"]

        for i, name in enumerate(list_names):
            list_obj = await TaskService.create_list(
                db_session,
                sample_board.id,
                name,
                position=i
            )
            assert list_obj is not None
            assert list_obj.position == i

        # Verify all lists exist
        board = await TaskService.get_board(db_session, sample_board.id)
        assert len(board.lists) == 3


@pytest.mark.asyncio
class TestTaskServiceCard:
    """Tests for TaskService card operations"""

    async def test_create_card(self, db_session: AsyncSession, sample_list: List):
        """Test creating a card"""
        card = await TaskService.create_card(
            db_session,
            sample_list.id,
            "New Task",
            "Task description",
            position=0
        )

        assert card is not None
        assert card.id is not None
        assert card.title == "New Task"
        assert card.description == "Task description"
        assert card.list_id == sample_list.id
        assert card.position == 0

    async def test_create_card_without_description(
        self, db_session: AsyncSession, sample_list: List
    ):
        """Test creating card without description"""
        card = await TaskService.create_card(
            db_session,
            sample_list.id,
            "Simple Task"
        )

        assert card is not None
        assert card.title == "Simple Task"
        assert card.description is None

    async def test_create_card_on_nonexistent_list(self, db_session: AsyncSession):
        """Test creating card on list that doesn't exist"""
        fake_list_id = uuid.uuid4()
        card = await TaskService.create_card(
            db_session,
            fake_list_id,
            "Should Fail"
        )

        assert card is None

    async def test_create_multiple_cards(
        self, db_session: AsyncSession, sample_list: List
    ):
        """Test creating multiple cards"""
        for i in range(5):
            card = await TaskService.create_card(
                db_session,
                sample_list.id,
                f"Task {i}",
                f"Description {i}",
                position=i
            )
            assert card is not None
            assert card.position == i

    async def test_move_card(
        self, db_session: AsyncSession, sample_board: Board, sample_list: List, sample_card: Card
    ):
        """Test moving card to different list"""
        # Create new list
        new_list = await TaskService.create_list(
            db_session,
            sample_board.id,
            "New List",
            position=1
        )

        # Move card
        moved_card = await TaskService.move_card(
            db_session,
            sample_card.id,
            new_list.id,
            new_position=0
        )

        assert moved_card is not None
        assert moved_card.list_id == new_list.id
        assert moved_card.position == 0

    async def test_move_card_change_position(
        self, db_session: AsyncSession, sample_list: List, sample_card: Card
    ):
        """Test changing card position within same list"""
        # Create more cards
        card2 = await TaskService.create_card(
            db_session, sample_list.id, "Card 2", position=1
        )
        card3 = await TaskService.create_card(
            db_session, sample_list.id, "Card 3", position=2
        )

        # Move first card to last position
        moved_card = await TaskService.move_card(
            db_session,
            sample_card.id,
            sample_list.id,
            new_position=2
        )

        assert moved_card is not None
        assert moved_card.position == 2

    async def test_move_nonexistent_card(self, db_session: AsyncSession, sample_list: List):
        """Test moving card that doesn't exist"""
        fake_card_id = uuid.uuid4()
        result = await TaskService.move_card(
            db_session,
            fake_card_id,
            sample_list.id,
            new_position=0
        )

        assert result is None


@pytest.mark.asyncio
class TestTaskServiceActivity:
    """Tests for TaskService activity operations"""

    async def test_get_board_activity(
        self, db_session: AsyncSession, sample_board: Board, sample_user_id: uuid.UUID
    ):
        """Test getting board activity log"""
        # Create some activities
        activities = [
            Activity(
                board_id=sample_board.id,
                user_id=sample_user_id,
                action="create",
                entity_type="list",
                entity_id=uuid.uuid4(),
                details=f"Activity {i}"
            )
            for i in range(3)
        ]

        db_session.add_all(activities)
        await db_session.commit()

        # Get activities
        result = await TaskService.get_board_activity(db_session, sample_board.id)

        assert len(result) == 4  # 3 new + 1 from board creation in fixture
        assert all(activity.board_id == sample_board.id for activity in result)

    async def test_get_board_activity_with_limit(
        self, db_session: AsyncSession, sample_board: Board, sample_user_id: uuid.UUID
    ):
        """Test getting board activity with limit"""
        # Create 10 activities
        activities = [
            Activity(
                board_id=sample_board.id,
                user_id=sample_user_id,
                action="create",
                entity_type="card",
                entity_id=uuid.uuid4(),
                details=f"Activity {i}"
            )
            for i in range(10)
        ]

        db_session.add_all(activities)
        await db_session.commit()

        # Get only 5
        result = await TaskService.get_board_activity(
            db_session, sample_board.id, limit=5
        )

        assert len(result) == 5

    async def test_activity_order(
        self, db_session: AsyncSession, sample_board: Board, sample_user_id: uuid.UUID
    ):
        """Test that activities are returned in descending order by timestamp"""
        result = await TaskService.get_board_activity(db_session, sample_board.id)

        # Verify descending order
        for i in range(len(result) - 1):
            assert result[i].timestamp >= result[i + 1].timestamp
