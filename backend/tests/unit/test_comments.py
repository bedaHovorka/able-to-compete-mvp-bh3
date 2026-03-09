"""
Unit tests for Comment model, CommentService, and comment API endpoints
"""
import pytest
from contextlib import asynccontextmanager
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.models import Card, Comment
from app.models.task import Board, List
from app.services.task_service import CommentService, DeleteResult
import uuid


# ---------------------------------------------------------------------------
# Helpers shared with the API tests
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _noop_lifespan(app):
    yield


async def override_get_current_active_user():
    return {"id": str(uuid.uuid4()), "email": "test@example.com", "is_active": True}


@pytest.fixture(autouse=True)
def patch_app_for_testing():
    from app.utils.middleware import AuditMiddleware

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan

    async def _passthrough_dispatch(self, request, call_next):
        return await call_next(request)

    try:
        with patch.object(AuditMiddleware, "dispatch", _passthrough_dispatch):
            yield
    finally:
        app.router.lifespan_context = original_lifespan


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestCommentModel:
    async def test_create_comment(self, db_session: AsyncSession, sample_card: Card):
        user_id = uuid.uuid4()
        comment = Comment(
            card_id=sample_card.id,
            content="This is a test comment",
            user_id=user_id,
        )
        db_session.add(comment)
        await db_session.commit()
        await db_session.refresh(comment)

        assert comment.id is not None
        assert comment.card_id == sample_card.id
        assert comment.user_id == user_id
        assert comment.content == "This is a test comment"
        assert comment.created_at is not None
        assert comment.updated_at is not None

    async def test_comment_without_user_id(
        self, db_session: AsyncSession, sample_card: Card
    ):
        comment = Comment(card_id=sample_card.id, content="Anonymous comment")
        db_session.add(comment)
        await db_session.commit()
        await db_session.refresh(comment)

        assert comment.id is not None
        assert comment.user_id is None


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestCommentService:
    async def test_create_comment(
        self, db_session: AsyncSession, sample_card: Card, sample_user_id: uuid.UUID
    ):
        comment = await CommentService.create_comment(
            db_session,
            card_id=sample_card.id,
            content="Hello from service",
            user_id=sample_user_id,
        )

        assert comment is not None
        assert comment.card_id == sample_card.id
        assert comment.content == "Hello from service"
        assert comment.user_id == sample_user_id

    async def test_create_comment_on_nonexistent_card(
        self, db_session: AsyncSession
    ):
        result = await CommentService.create_comment(
            db_session,
            card_id=uuid.uuid4(),
            content="Ghost comment",
        )
        assert result is None

    async def test_get_comments_for_card_empty(
        self, db_session: AsyncSession, sample_card: Card
    ):
        comments, total = await CommentService.get_comments_for_card(
            db_session, card_id=sample_card.id
        )
        assert comments == []
        assert total == 0

    async def test_get_comments_for_card(
        self, db_session: AsyncSession, sample_card: Card, sample_user_id: uuid.UUID
    ):
        for i in range(3):
            await CommentService.create_comment(
                db_session,
                card_id=sample_card.id,
                content=f"Comment {i}",
                user_id=sample_user_id,
            )

        comments, total = await CommentService.get_comments_for_card(
            db_session, card_id=sample_card.id
        )
        assert total == 3
        assert len(comments) == 3

    async def test_get_comments_pagination(
        self, db_session: AsyncSession, sample_card: Card, sample_user_id: uuid.UUID
    ):
        for i in range(5):
            await CommentService.create_comment(
                db_session,
                card_id=sample_card.id,
                content=f"Comment {i}",
                user_id=sample_user_id,
            )

        first_page, total = await CommentService.get_comments_for_card(
            db_session, card_id=sample_card.id, skip=0, limit=2
        )
        assert total == 5
        assert len(first_page) == 2

        second_page, _ = await CommentService.get_comments_for_card(
            db_session, card_id=sample_card.id, skip=2, limit=2
        )
        assert len(second_page) == 2
        assert first_page[0].id != second_page[0].id

    async def test_delete_comment_ok(
        self, db_session: AsyncSession, sample_card: Card, sample_user_id: uuid.UUID
    ):
        comment = await CommentService.create_comment(
            db_session,
            card_id=sample_card.id,
            content="To be deleted",
            user_id=sample_user_id,
        )

        result = await CommentService.delete_comment(
            db_session, comment_id=comment.id, user_id=sample_user_id
        )
        assert result == DeleteResult.OK

        comments, total = await CommentService.get_comments_for_card(
            db_session, card_id=sample_card.id
        )
        assert total == 0

    async def test_delete_comment_not_found(self, db_session: AsyncSession):
        result = await CommentService.delete_comment(
            db_session, comment_id=uuid.uuid4(), user_id=uuid.uuid4()
        )
        assert result == DeleteResult.NOT_FOUND

    async def test_delete_comment_forbidden(
        self, db_session: AsyncSession, sample_card: Card, sample_user_id: uuid.UUID
    ):
        comment = await CommentService.create_comment(
            db_session,
            card_id=sample_card.id,
            content="Owned comment",
            user_id=sample_user_id,
        )

        other_user_id = uuid.uuid4()
        result = await CommentService.delete_comment(
            db_session, comment_id=comment.id, user_id=other_user_id
        )
        assert result == DeleteResult.FORBIDDEN


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestCommentAPI:
    async def test_create_comment_success(
        self, db_session: AsyncSession, sample_card: Card
    ):
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/cards/{sample_card.id}/comments",
                json={"content": "Great card!"},
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == "Great card!"
        assert data["card_id"] == str(sample_card.id)

        app.dependency_overrides.clear()

    async def test_create_comment_on_nonexistent_card(
        self, db_session: AsyncSession
    ):
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/cards/{uuid.uuid4()}/comments",
                json={"content": "Ghost!"},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        app.dependency_overrides.clear()

    async def test_list_comments_empty(
        self, db_session: AsyncSession, sample_card: Card
    ):
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/cards/{sample_card.id}/comments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["comments"] == []
        assert data["skip"] == 0
        assert data["limit"] == 20

        app.dependency_overrides.clear()

    async def test_list_comments(
        self, db_session: AsyncSession, sample_card: Card, sample_user_id: uuid.UUID
    ):
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        # Pre-seed two comments
        for i in range(2):
            await CommentService.create_comment(
                db_session,
                card_id=sample_card.id,
                content=f"Comment {i}",
                user_id=sample_user_id,
            )

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/cards/{sample_card.id}/comments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert len(data["comments"]) == 2

        app.dependency_overrides.clear()

    async def test_delete_comment_success(
        self, db_session: AsyncSession, sample_card: Card
    ):
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        # Create comment via API so the user_id matches the mocked user
        fixed_user_id = str(uuid.uuid4())

        async def _fixed_user():
            return {"id": fixed_user_id, "email": "u@test.com", "is_active": True}

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = _fixed_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            create_resp = await client.post(
                f"/api/cards/{sample_card.id}/comments",
                json={"content": "Will be deleted"},
            )
            assert create_resp.status_code == status.HTTP_201_CREATED
            comment_id = create_resp.json()["id"]

            delete_resp = await client.delete(f"/api/comments/{comment_id}")

        assert delete_resp.status_code == status.HTTP_204_NO_CONTENT
        app.dependency_overrides.clear()

    async def test_delete_comment_not_found(self, db_session: AsyncSession):
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/comments/{uuid.uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        app.dependency_overrides.clear()

    async def test_delete_comment_forbidden(
        self, db_session: AsyncSession, sample_card: Card, sample_user_id: uuid.UUID
    ):
        from app.utils.database import get_db
        from app.utils.auth import get_current_active_user

        # Create comment owned by sample_user_id
        comment = await CommentService.create_comment(
            db_session,
            card_id=sample_card.id,
            content="Mine",
            user_id=sample_user_id,
        )

        # Try to delete as a different user
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(f"/api/comments/{comment.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        app.dependency_overrides.clear()
