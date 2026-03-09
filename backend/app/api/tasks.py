from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.database import get_db
from app.utils.auth import get_current_active_user
from app.services import TaskService, CommentService, DeleteResult
from pydantic import BaseModel, ConfigDict, Field
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


class ListWithCardsResponse(BaseModel):
    id: uuid.UUID
    board_id: uuid.UUID
    name: str
    position: int
    created_at: datetime
    cards: List[CardResponse] = []

    class Config:
        from_attributes = True


class BoardWithListsResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    lists: List[ListWithCardsResponse] = []

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


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class CommentResponse(BaseModel):
    id: uuid.UUID
    card_id: uuid.UUID
    user_id: Optional[uuid.UUID]
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentListResponse(BaseModel):
    comments: List[CommentResponse]
    total: int
    skip: int
    limit: int


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


@router.get("/boards/{board_id}")
async def get_board(
    board_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get board by ID with lists and cards"""
    board = await TaskService.get_board(db, board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    return BoardWithListsResponse.model_validate(board)


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


# Comment endpoints
@router.post("/cards/{card_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    card_id: uuid.UUID,
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a comment on a card"""
    user_id = uuid.UUID(current_user["id"]) if current_user.get("id") else None
    comment = await CommentService.create_comment(
        db,
        card_id=card_id,
        content=comment_data.content,
        user_id=user_id,
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return comment


@router.get("/cards/{card_id}/comments", response_model=CommentListResponse)
async def list_comments(
    card_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """List comments on a card"""
    comments, total = await CommentService.get_comments_for_card(
        db, card_id=card_id, skip=skip, limit=limit
    )
    return CommentListResponse(comments=comments, total=total, skip=skip, limit=limit)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a comment (owner only)"""
    user_id = uuid.UUID(current_user["id"]) if current_user.get("id") else None
    result = await CommentService.delete_comment(db, comment_id=comment_id, user_id=user_id)
    if result == DeleteResult.NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if result == DeleteResult.FORBIDDEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this comment")
