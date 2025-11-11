from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models import Board, List, Card, Activity
from app.utils.logger import logger
from typing import Optional, List as ListType
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
            selectinload(Board.lists).selectinload(List.cards)
        )
        result = await db.execute(query)
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
        """Soft delete board"""
        board = await TaskService.get_board(db, board_id)
        if not board:
            return False

        board.deleted_at = datetime.utcnow()
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
        await db.refresh(card)

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
        await db.refresh(card)

        logger.info(f"Moved card: {card_id} to list {new_list_id}")
        return card

    @staticmethod
    async def get_board_activity(db: AsyncSession, board_id: uuid.UUID, limit: int = 50) -> ListType[Activity]:
        """Get board activity log"""
        query = select(Activity).where(Activity.board_id == board_id).order_by(Activity.timestamp.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
