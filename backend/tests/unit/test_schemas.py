"""
Unit tests for Pydantic schemas (no database required)
"""
import pytest
from pydantic import ValidationError
from app.api.tasks import (
    BoardCreate, BoardResponse,
    ListCreate, ListResponse,
    CardCreate, CardResponse,
    CardMove
)
import uuid
from datetime import datetime


class TestBoardSchemas:
    """Tests for Board Pydantic schemas"""

    def test_board_create_valid(self):
        """Test creating a valid BoardCreate schema"""
        data = {
            "name": "My Project",
            "description": "A test project"
        }
        board = BoardCreate(**data)

        assert board.name == "My Project"
        assert board.description == "A test project"

    def test_board_create_without_description(self):
        """Test BoardCreate without optional description"""
        data = {"name": "Simple Board"}
        board = BoardCreate(**data)

        assert board.name == "Simple Board"
        assert board.description is None

    def test_board_create_empty_name_allowed(self):
        """Test that empty name is allowed (validation happens at business layer)"""
        board = BoardCreate(name="", description="Test")
        assert board.name == ""

    def test_board_response_serialization(self):
        """Test BoardResponse can be created and serialized"""
        board_data = {
            "id": uuid.uuid4(),
            "name": "Test Board",
            "description": "Description",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        board = BoardResponse(**board_data)

        assert board.name == "Test Board"
        assert isinstance(board.id, uuid.UUID)
        assert isinstance(board.created_at, datetime)

    def test_board_response_to_dict(self):
        """Test BoardResponse can be converted to dict"""
        board_data = {
            "id": uuid.uuid4(),
            "name": "Test Board",
            "description": "Description",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        board = BoardResponse(**board_data)
        board_dict = board.model_dump()

        assert board_dict["name"] == "Test Board"
        assert "id" in board_dict
        assert "created_at" in board_dict


class TestListSchemas:
    """Tests for List Pydantic schemas"""

    def test_list_create_valid(self):
        """Test creating a valid ListCreate schema"""
        data = {
            "name": "To Do",
            "position": 0
        }
        list_schema = ListCreate(**data)

        assert list_schema.name == "To Do"
        assert list_schema.position == 0

    def test_list_create_default_position(self):
        """Test ListCreate with default position"""
        data = {"name": "Backlog"}
        list_schema = ListCreate(**data)

        assert list_schema.name == "Backlog"
        assert list_schema.position == 0

    def test_list_create_negative_position(self):
        """Test that negative position is allowed (business logic handles this)"""
        data = {"name": "Test", "position": -1}
        list_schema = ListCreate(**data)

        assert list_schema.position == -1

    def test_list_response_serialization(self):
        """Test ListResponse serialization"""
        list_data = {
            "id": uuid.uuid4(),
            "board_id": uuid.uuid4(),
            "name": "Done",
            "position": 2,
            "created_at": datetime.utcnow()
        }
        list_response = ListResponse(**list_data)

        assert list_response.name == "Done"
        assert list_response.position == 2
        assert isinstance(list_response.id, uuid.UUID)


class TestCardSchemas:
    """Tests for Card Pydantic schemas"""

    def test_card_create_valid(self):
        """Test creating a valid CardCreate schema"""
        data = {
            "title": "Implement feature X",
            "description": "Add new functionality",
            "position": 0
        }
        card = CardCreate(**data)

        assert card.title == "Implement feature X"
        assert card.description == "Add new functionality"
        assert card.position == 0

    def test_card_create_without_description(self):
        """Test CardCreate without description"""
        data = {"title": "Quick task"}
        card = CardCreate(**data)

        assert card.title == "Quick task"
        assert card.description is None
        assert card.position == 0  # default

    def test_card_create_long_title(self):
        """Test card with very long title"""
        long_title = "A" * 500
        data = {"title": long_title}
        card = CardCreate(**data)

        assert len(card.title) == 500

    def test_card_response_serialization(self):
        """Test CardResponse serialization"""
        card_data = {
            "id": uuid.uuid4(),
            "list_id": uuid.uuid4(),
            "title": "Test Card",
            "description": "Test description",
            "position": 0,
            "completed": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        card = CardResponse(**card_data)

        assert card.title == "Test Card"
        assert card.completed is False
        assert isinstance(card.id, uuid.UUID)

    def test_card_response_completed_status(self):
        """Test card with completed status"""
        card_data = {
            "id": uuid.uuid4(),
            "list_id": uuid.uuid4(),
            "title": "Completed Task",
            "description": None,
            "position": 0,
            "completed": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        card = CardResponse(**card_data)

        assert card.completed is True


class TestCardMoveSchema:
    """Tests for CardMove schema"""

    def test_card_move_valid(self):
        """Test valid card move schema"""
        data = {
            "list_id": str(uuid.uuid4()),
            "position": 3
        }
        move = CardMove(**data)

        assert isinstance(move.list_id, uuid.UUID)
        assert move.position == 3

    def test_card_move_position_zero(self):
        """Test moving card to position 0"""
        data = {
            "list_id": str(uuid.uuid4()),
            "position": 0
        }
        move = CardMove(**data)

        assert move.position == 0

    def test_card_move_invalid_uuid_fails(self):
        """Test that invalid UUID fails validation"""
        with pytest.raises(ValidationError):
            CardMove(list_id="not-a-uuid", position=0)


class TestSchemaValidation:
    """Tests for schema validation edge cases"""

    def test_board_create_with_extra_fields(self):
        """Test that extra fields are ignored"""
        data = {
            "name": "Board",
            "description": "Desc",
            "extra_field": "should be ignored"
        }
        board = BoardCreate(**data)

        assert board.name == "Board"
        assert not hasattr(board, "extra_field")

    def test_list_create_type_coercion(self):
        """Test that string position is coerced to int"""
        data = {
            "name": "List",
            "position": "5"  # string
        }
        list_schema = ListCreate(**data)

        assert list_schema.position == 5
        assert isinstance(list_schema.position, int)

    def test_card_create_whitespace_title(self):
        """Test card with whitespace-only title"""
        data = {"title": "   Test   "}
        card = CardCreate(**data)

        # Pydantic doesn't strip by default
        assert card.title == "   Test   "

    def test_uuid_string_conversion(self):
        """Test UUID can be created from string"""
        uuid_str = str(uuid.uuid4())
        data = {
            "list_id": uuid_str,
            "position": 0
        }
        move = CardMove(**data)

        assert isinstance(move.list_id, uuid.UUID)
        assert str(move.list_id) == uuid_str


class TestSchemaEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_board_very_long_name(self):
        """Test board with very long name"""
        long_name = "A" * 255
        data = {"name": long_name}
        board = BoardCreate(**data)

        assert len(board.name) == 255

    def test_card_zero_position(self):
        """Test card at position 0"""
        data = {"title": "First card", "position": 0}
        card = CardCreate(**data)

        assert card.position == 0

    def test_list_high_position_number(self):
        """Test list with very high position"""
        data = {"name": "List", "position": 999999}
        list_schema = ListCreate(**data)

        assert list_schema.position == 999999

    def test_board_none_description(self):
        """Test board with explicitly None description"""
        data = {"name": "Board", "description": None}
        board = BoardCreate(**data)

        assert board.description is None

    def test_card_empty_description(self):
        """Test card with empty string description"""
        data = {"title": "Card", "description": ""}
        card = CardCreate(**data)

        assert card.description == ""
