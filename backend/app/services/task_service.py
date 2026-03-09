from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload
from app.models import Board, List, Card, Activity, Label
from app.models.task import card_labels
from app.utils.logger import logger
from typing import Optional, List as ListType, Union
from datetime import datetime
import uuid


class TaskService:
    @staticmethod
    async def create_board(db: AsyncSession, name: str, description: Optional[str] = None, user_id: Optional[uuid.UUID] = None) -> Board:
        """Create a new board"""
        board = Board(name=name, description=description, user_id=user_id)
        db.add(board)
        await db.flush()

        # Log activity
        activity = Activity(
            board_id=board.id,
            user_id=user_id,
            action="create",
            entity_type="board",
            entity_id=board.id,
            details=f"Created board: {name}"
        )
        db.add(activity)
        await db.commit()
        await db.refresh(board)

        logger.info(f"Created board: {board.id}")
        return board

    @staticmethod
    async def get_boards(db: AsyncSession, user_id: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 100) -> ListType[Board]:
        """Get all boards"""
        query = select(Board).where(Board.deleted_at.is_(None))
        if user_id:
            query = query.where(Board.user_id == user_id)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_board(db: AsyncSession, board_id: uuid.UUID) -> Optional[Board]:
        """Get board with all lists and cards"""
        query = select(Board).where(
            and_(Board.id == board_id, Board.deleted_at.is_(None))
        ).options(
            selectinload(Board.lists).selectinload(List.cards).selectinload(Card.labels)
        )
        result = await db.execute(query.execution_options(populate_existing=True))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_board(db: AsyncSession, board_id: uuid.UUID, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Board]:
        """Update board"""
        board = await TaskService.get_board(db, board_id)
        if not board:
            return None

        if name:
            board.name = name
        if description is not None:
            board.description = description
        board.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(board)
        return board

    @staticmethod
    async def delete_board(db: AsyncSession, board_id: uuid.UUID) -> bool:
        """Soft delete board and cascade delete child Lists and Cards"""
        board = await TaskService.get_board(db, board_id)
        if not board:
            return False

        now = datetime.utcnow()

        # Collect list IDs for this board
        lists_result = await db.execute(select(List.id).where(List.board_id == board_id))
        list_ids = lists_result.scalars().all()

        # Bulk hard-delete all Cards and Lists (neither has deleted_at)
        if list_ids:
            await db.execute(delete(Card).where(Card.list_id.in_(list_ids)))
            await db.execute(delete(List).where(List.board_id == board_id))

        # Soft-delete the board itself
        board.deleted_at = now
        await db.commit()
        logger.info(f"Deleted board: {board_id}")
        return True

    @staticmethod
    async def create_list(db: AsyncSession, board_id: uuid.UUID, name: str, position: int = 0) -> Optional[List]:
        """Create a new list"""
        board = await TaskService.get_board(db, board_id)
        if not board:
            return None

        list_obj = List(board_id=board_id, name=name, position=position)
        db.add(list_obj)
        await db.commit()
        await db.refresh(list_obj)

        logger.info(f"Created list: {list_obj.id} in board {board_id}")
        return list_obj

    @staticmethod
    async def create_card(db: AsyncSession, list_id: uuid.UUID, title: str, description: Optional[str] = None, position: int = 0) -> Optional[Card]:
        """Create a new card"""
        query = select(List).where(List.id == list_id)
        result = await db.execute(query)
        list_obj = result.scalar_one_or_none()

        if not list_obj:
            return None

        card = Card(list_id=list_id, title=title, description=description, position=position)
        db.add(card)
        await db.commit()

        # Reload with labels eagerly loaded
        card_query = select(Card).where(Card.id == card.id).options(selectinload(Card.labels))
        result = await db.execute(card_query)
        card = result.scalar_one()

        logger.info(f"Created card: {card.id} in list {list_id}")
        return card

    @staticmethod
    async def move_card(db: AsyncSession, card_id: uuid.UUID, new_list_id: uuid.UUID, new_position: int) -> Optional[Card]:
        """Move card to different list"""
        query = select(Card).where(Card.id == card_id)
        result = await db.execute(query)
        card = result.scalar_one_or_none()

        if not card:
            return None

        card.list_id = new_list_id
        card.position = new_position
        card.updated_at = datetime.utcnow()

        await db.commit()

        # Reload with labels eagerly loaded
        card_query = select(Card).where(Card.id == card_id).options(selectinload(Card.labels))
        result = await db.execute(card_query)
        card = result.scalar_one()

        logger.info(f"Moved card: {card_id} to list {new_list_id}")
        return card

    @staticmethod
    async def get_board_activity(db: AsyncSession, board_id: uuid.UUID, limit: int = 50) -> ListType[Activity]:
        """Get board activity log"""
        query = select(Activity).where(Activity.board_id == board_id).order_by(Activity.timestamp.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_label(db: AsyncSession, board_id: uuid.UUID, name: str, color: str) -> Optional[Label]:
        """Create a new label for a board"""
        board = await TaskService.get_board(db, board_id)
        if not board:
            return None

        label = Label(board_id=board_id, name=name, color=color)
        db.add(label)
        await db.commit()
        await db.refresh(label)

        logger.info(f"Created label: {label.id} in board {board_id}")
        return label

    @staticmethod
    async def get_labels_for_board(db: AsyncSession, board_id: uuid.UUID) -> ListType[Label]:
        """Get all labels for a board"""
        query = select(Label).where(Label.board_id == board_id)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def delete_label(db: AsyncSession, label_id: uuid.UUID) -> bool:
        """Delete a label"""
        query = select(Label).where(Label.id == label_id)
        result = await db.execute(query)
        label = result.scalar_one_or_none()

        if not label:
            return False

        await db.delete(label)
        await db.commit()
        logger.info(f"Deleted label: {label_id}")
        return True

    @staticmethod
    async def add_label_to_card(
        db: AsyncSession, card_id: uuid.UUID, label_id: uuid.UUID
    ) -> Union[Card, str, None]:
        """Attach a label to a card. Returns Card on success, 'cross_board' or 'duplicate' on error, None if not found."""
        # Load card with its list
        card_query = select(Card).where(Card.id == card_id).options(
            selectinload(Card.list),
            selectinload(Card.labels)
        )
        card_result = await db.execute(card_query)
        card = card_result.scalar_one_or_none()

        if not card:
            return None

        # Load label
        label_query = select(Label).where(Label.id == label_id)
        label_result = await db.execute(label_query)
        label = label_result.scalar_one_or_none()

        if not label:
            return None

        # Validate label belongs to the same board as the card
        if label.board_id != card.list.board_id:
            return "cross_board"

        # Check for duplicate
        if any(lbl.id == label_id for lbl in card.labels):
            return "duplicate"

        card.labels.append(label)
        await db.commit()

        # Reload card with labels
        card_query = select(Card).where(Card.id == card_id).options(selectinload(Card.labels))
        card_result = await db.execute(card_query)
        card = card_result.scalar_one()

        logger.info(f"Added label {label_id} to card {card_id}")
        return card

    @staticmethod
    async def remove_label_from_card(db: AsyncSession, card_id: uuid.UUID, label_id: uuid.UUID) -> bool:
        """Remove a label from a card"""
        # Check if the association exists
        assoc_query = select(card_labels).where(
            and_(
                card_labels.c.card_id == card_id,
                card_labels.c.label_id == label_id
            )
        )
        result = await db.execute(assoc_query)
        row = result.first()

        if not row:
            return False

        await db.execute(
            delete(card_labels).where(
                and_(
                    card_labels.c.card_id == card_id,
                    card_labels.c.label_id == label_id
                )
            )
        )
        await db.commit()
        logger.info(f"Removed label {label_id} from card {card_id}")
        return True
