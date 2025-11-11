from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.database import get_db
from app.utils.auth import get_current_active_user
from app.services import TaskService
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api", tags=["tasks"])


# Pydantic schemas
class BoardCreate(BaseModel):
    name: str
    description: Optional[str] = None


class BoardResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ListCreate(BaseModel):
    name: str
    position: int = 0


class ListResponse(BaseModel):
    id: uuid.UUID
    board_id: uuid.UUID
    name: str
    position: int
    created_at: datetime

    class Config:
        from_attributes = True


class CardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    position: int = 0


class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class CardMove(BaseModel):
    list_id: uuid.UUID
    position: int


class CardResponse(BaseModel):
    id: uuid.UUID
    list_id: uuid.UUID
    title: str
    description: Optional[str]
    position: int
    completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActivityResponse(BaseModel):
    id: uuid.UUID
    action: str
    entity_type: str
    entity_id: uuid.UUID
    details: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


# Board endpoints
@router.post("/boards", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    board_data: BoardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new board"""
    board = await TaskService.create_board(
        db,
        name=board_data.name,
        description=board_data.description,
        user_id=uuid.UUID(current_user["id"]) if current_user["id"] else None
    )
    return board


@router.get("/boards", response_model=List[BoardResponse])
async def list_boards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """List all boards"""
    boards = await TaskService.get_boards(db, skip=skip, limit=limit)
    return boards


@router.get("/boards/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get board by ID"""
    board = await TaskService.get_board(db, board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    return board


@router.put("/boards/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: uuid.UUID,
    board_data: BoardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update board"""
    board = await TaskService.update_board(
        db,
        board_id,
        name=board_data.name,
        description=board_data.description
    )
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    return board


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Soft delete board"""
    success = await TaskService.delete_board(db, board_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )


# List endpoints
@router.post("/boards/{board_id}/lists", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    board_id: uuid.UUID,
    list_data: ListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new list in board"""
    list_obj = await TaskService.create_list(
        db,
        board_id,
        name=list_data.name,
        position=list_data.position
    )
    if not list_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    return list_obj


@router.put("/lists/{list_id}", response_model=ListResponse)
async def update_list(
    list_id: uuid.UUID,
    list_data: ListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update list"""
    # Implementation here
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Delete list"""
    # Implementation here
    raise HTTPException(status_code=501, detail="Not implemented")


# Card endpoints
@router.post("/lists/{list_id}/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    list_id: uuid.UUID,
    card_data: CardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new card in list"""
    card = await TaskService.create_card(
        db,
        list_id,
        title=card_data.title,
        description=card_data.description,
        position=card_data.position
    )
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    return card


@router.put("/cards/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: uuid.UUID,
    card_data: CardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update card"""
    # Implementation here
    raise HTTPException(status_code=501, detail="Not implemented")


@router.put("/cards/{card_id}/move", response_model=CardResponse)
async def move_card(
    card_id: uuid.UUID,
    move_data: CardMove,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Move card to different list"""
    card = await TaskService.move_card(
        db,
        card_id,
        new_list_id=move_data.list_id,
        new_position=move_data.position
    )
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return card


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Delete card"""
    # Implementation here
    raise HTTPException(status_code=501, detail="Not implemented")


# Activity log endpoint
@router.get("/boards/{board_id}/activity", response_model=List[ActivityResponse])
async def get_board_activity(
    board_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get activity log for board"""
    activities = await TaskService.get_board_activity(db, board_id, limit=limit)
    return activities
