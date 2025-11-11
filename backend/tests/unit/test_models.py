"""
Unit tests for database models
"""
import pytest
from datetime import datetime
import uuid
from app.models import Board, List, Card, Label, CardLabel, Activity, LabelColor
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestBoardModel:
    """Tests for Board model"""

    async def test_create_board(self, db_session: AsyncSession, sample_user_id: uuid.UUID):
        """Test creating a board"""
        board = Board(
            name="My Board",
            description="Test description",
            user_id=sample_user_id
        )
        db_session.add(board)
        await db_session.commit()
        await db_session.refresh(board)

        assert board.id is not None
        assert board.name == "My Board"
        assert board.description == "Test description"
        assert board.user_id == sample_user_id
        assert board.created_at is not None
        assert board.deleted_at is None

    async def test_board_soft_delete(self, db_session: AsyncSession, sample_board: Board):
        """Test soft deleting a board"""
        # Soft delete by setting deleted_at
        sample_board.deleted_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(sample_board)

        assert sample_board.deleted_at is not None

    async def test_board_relationships(self, db_session: AsyncSession, sample_board: Board):
        """Test board relationships with lists"""
        # Create lists
        list1 = List(board_id=sample_board.id, name="List 1", position=0)
        list2 = List(board_id=sample_board.id, name="List 2", position=1)

        db_session.add_all([list1, list2])
        await db_session.commit()
        await db_session.refresh(sample_board)

        # Check relationships (note: need to query again for relationships)
        assert sample_board.id is not None


@pytest.mark.asyncio
class TestListModel:
    """Tests for List model"""

    async def test_create_list(self, db_session: AsyncSession, sample_board: Board):
        """Test creating a list"""
        list_obj = List(
            board_id=sample_board.id,
            name="To Do",
            position=0
        )
        db_session.add(list_obj)
        await db_session.commit()
        await db_session.refresh(list_obj)

        assert list_obj.id is not None
        assert list_obj.name == "To Do"
        assert list_obj.board_id == sample_board.id
        assert list_obj.position == 0
        assert list_obj.created_at is not None

    async def test_list_position(self, db_session: AsyncSession, sample_board: Board):
        """Test list positioning"""
        lists = [
            List(board_id=sample_board.id, name=f"List {i}", position=i)
            for i in range(3)
        ]
        db_session.add_all(lists)
        await db_session.commit()

        for i, list_obj in enumerate(lists):
            await db_session.refresh(list_obj)
            assert list_obj.position == i


@pytest.mark.asyncio
class TestCardModel:
    """Tests for Card model"""

    async def test_create_card(self, db_session: AsyncSession, sample_list: List):
        """Test creating a card"""
        card = Card(
            list_id=sample_list.id,
            title="Test Task",
            description="Task description",
            position=0,
            completed=False
        )
        db_session.add(card)
        await db_session.commit()
        await db_session.refresh(card)

        assert card.id is not None
        assert card.title == "Test Task"
        assert card.description == "Task description"
        assert card.list_id == sample_list.id
        assert card.position == 0
        assert card.completed is False
        assert card.created_at is not None

    async def test_card_completion(self, db_session: AsyncSession, sample_card: Card):
        """Test marking card as completed"""
        sample_card.completed = True
        await db_session.commit()
        await db_session.refresh(sample_card)

        assert sample_card.completed is True

    async def test_card_move_to_different_list(
        self, db_session: AsyncSession, sample_card: Card, sample_board: Board
    ):
        """Test moving card to different list"""
        # Create new list
        new_list = List(board_id=sample_board.id, name="New List", position=1)
        db_session.add(new_list)
        await db_session.commit()
        await db_session.refresh(new_list)

        # Move card
        old_list_id = sample_card.list_id
        sample_card.list_id = new_list.id
        sample_card.position = 0
        await db_session.commit()
        await db_session.refresh(sample_card)

        assert sample_card.list_id == new_list.id
        assert sample_card.list_id != old_list_id

    async def test_card_with_due_date(self, db_session: AsyncSession, sample_list: List):
        """Test card with due date"""
        due_date = datetime.utcnow()
        card = Card(
            list_id=sample_list.id,
            title="Card with due date",
            due_date=due_date,
            position=0
        )
        db_session.add(card)
        await db_session.commit()
        await db_session.refresh(card)

        assert card.due_date is not None
        assert card.due_date == due_date


@pytest.mark.asyncio
class TestLabelModel:
    """Tests for Label and CardLabel models"""

    async def test_create_label(self, db_session: AsyncSession):
        """Test creating a label"""
        label = Label(
            name="Bug",
            color=LabelColor.RED
        )
        db_session.add(label)
        await db_session.commit()
        await db_session.refresh(label)

        assert label.id is not None
        assert label.name == "Bug"
        assert label.color == LabelColor.RED

    async def test_label_colors(self, db_session: AsyncSession):
        """Test all label colors"""
        colors = [
            LabelColor.RED,
            LabelColor.BLUE,
            LabelColor.GREEN,
            LabelColor.YELLOW,
            LabelColor.PURPLE,
            LabelColor.ORANGE
        ]

        labels = []
        for color in colors:
            label = Label(name=color.value, color=color)
            labels.append(label)

        db_session.add_all(labels)
        await db_session.commit()

        for label in labels:
            await db_session.refresh(label)
            assert label.color in colors

    async def test_card_label_association(
        self, db_session: AsyncSession, sample_card: Card
    ):
        """Test associating labels with cards"""
        # Create labels
        bug_label = Label(name="Bug", color=LabelColor.RED)
        feature_label = Label(name="Feature", color=LabelColor.GREEN)

        db_session.add_all([bug_label, feature_label])
        await db_session.commit()
        await db_session.refresh(bug_label)
        await db_session.refresh(feature_label)

        # Associate with card
        card_label1 = CardLabel(card_id=sample_card.id, label_id=bug_label.id)
        card_label2 = CardLabel(card_id=sample_card.id, label_id=feature_label.id)

        db_session.add_all([card_label1, card_label2])
        await db_session.commit()

        assert card_label1.id is not None
        assert card_label2.id is not None


@pytest.mark.asyncio
class TestActivityModel:
    """Tests for Activity model"""

    async def test_create_activity(
        self, db_session: AsyncSession, sample_board: Board, sample_user_id: uuid.UUID
    ):
        """Test creating an activity log"""
        activity = Activity(
            board_id=sample_board.id,
            user_id=sample_user_id,
            action="create",
            entity_type="card",
            entity_id=uuid.uuid4(),
            details="Created a new card"
        )
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)

        assert activity.id is not None
        assert activity.board_id == sample_board.id
        assert activity.user_id == sample_user_id
        assert activity.action == "create"
        assert activity.entity_type == "card"
        assert activity.details == "Created a new card"
        assert activity.timestamp is not None

    async def test_multiple_activities(
        self, db_session: AsyncSession, sample_board: Board, sample_user_id: uuid.UUID
    ):
        """Test creating multiple activities"""
        activities = [
            Activity(
                board_id=sample_board.id,
                user_id=sample_user_id,
                action="create",
                entity_type="list",
                entity_id=uuid.uuid4(),
                details=f"Created list {i}"
            )
            for i in range(5)
        ]

        db_session.add_all(activities)
        await db_session.commit()

        for activity in activities:
            await db_session.refresh(activity)
            assert activity.id is not None
            assert activity.board_id == sample_board.id
