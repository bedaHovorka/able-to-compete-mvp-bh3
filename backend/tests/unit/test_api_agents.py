"""
Unit tests for agents API endpoints (backend/app/api/agents.py)
"""
import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import status
from app.main import app
import uuid


@asynccontextmanager
async def _noop_lifespan(app):
    """Replace real lifespan so tests don't connect to PostgreSQL."""
    yield


@pytest.fixture(autouse=True)
def patch_app_for_testing():
    """Patch lifespan and AuditMiddleware to avoid real PostgreSQL connections."""
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


async def override_get_current_active_user():
    """Override auth dependency for testing."""
    return {"id": str(uuid.uuid4()), "email": "test@example.com", "is_active": True}


@pytest.mark.asyncio
class TestSpecEndpoint:
    """Tests for POST /api/agents/spec"""

    async def test_requires_auth(self):
        """Returns 403 when no JWT is provided (HTTPBearer returns 403 on missing token)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/agents/spec",
                json={"requirements": "build a login page"},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_valid_body_calls_spec_agent(self):
        """Calls SpecAgent.process() with correct keys and returns its result."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        fake_result = {"specification": "spec text", "type": "general", "requirements": "req"}
        with patch("app.api.agents.SpecAgent") as MockSpecAgent:
            mock_instance = MockSpecAgent.return_value
            mock_instance.process = AsyncMock(return_value=fake_result)

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/agents/spec",
                    json={"requirements": "build a login page", "type": "user_story"},
                )

        assert response.status_code == status.HTTP_200_OK
        mock_instance.process.assert_awaited_once_with(
            {"requirements": "build a login page", "type": "user_story"}
        )
        assert response.json() == fake_result

        app.dependency_overrides.clear()

    async def test_default_type_is_general(self):
        """type defaults to 'general' when not provided."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        with patch("app.api.agents.SpecAgent") as MockSpecAgent:
            mock_instance = MockSpecAgent.return_value
            mock_instance.process = AsyncMock(return_value={})

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post(
                    "/api/agents/spec",
                    json={"requirements": "some requirement"},
                )

        mock_instance.process.assert_awaited_once_with(
            {"requirements": "some requirement", "type": "general"}
        )
        app.dependency_overrides.clear()

    async def test_invalid_type_value_returns_422(self):
        """Returns 422 when an invalid type value is provided."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/agents/spec",
                json={"requirements": "req", "type": "invalid_type"},
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()

    async def test_missing_requirements_returns_422(self):
        """Returns 422 when required 'requirements' field is missing."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/agents/spec", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestTestEndpoint:
    """Tests for POST /api/agents/test"""

    async def test_requires_auth(self):
        """Returns 403 when no JWT is provided (HTTPBearer returns 403 on missing token)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/agents/test",
                json={"specification": "some spec"},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_valid_body_calls_test_agent(self):
        """Calls TestAgent.process() with correct keys and returns its result."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        fake_result = {"test_code": "def test_foo(): pass", "test_type": "unit", "specification": "spec"}
        with patch("app.api.agents.TestAgent") as MockTestAgent:
            mock_instance = MockTestAgent.return_value
            mock_instance.process = AsyncMock(return_value=fake_result)

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/agents/test",
                    json={"specification": "board management spec", "type": "integration"},
                )

        assert response.status_code == status.HTTP_200_OK
        mock_instance.process.assert_awaited_once_with(
            {"specification": "board management spec", "type": "integration"}
        )
        assert response.json() == fake_result

        app.dependency_overrides.clear()

    async def test_default_type_is_unit(self):
        """type defaults to 'unit' when not provided."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        with patch("app.api.agents.TestAgent") as MockTestAgent:
            mock_instance = MockTestAgent.return_value
            mock_instance.process = AsyncMock(return_value={})

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post(
                    "/api/agents/test",
                    json={"specification": "some spec"},
                )

        mock_instance.process.assert_awaited_once_with(
            {"specification": "some spec", "type": "unit"}
        )
        app.dependency_overrides.clear()

    async def test_invalid_type_value_returns_422(self):
        """Returns 422 when an invalid type value is provided."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/agents/test",
                json={"specification": "spec", "type": "invalid"},
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()

    async def test_missing_specification_returns_422(self):
        """Returns 422 when required 'specification' field is missing."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/agents/test", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestDevEndpoint:
    """Tests for POST /api/agents/dev"""

    async def test_requires_auth(self):
        """Returns 403 when no JWT is provided (HTTPBearer returns 403 on missing token)."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/agents/dev",
                json={"specification": "some spec"},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_valid_body_calls_dev_agent(self):
        """Calls DevAgent.process() with correct keys and returns its result."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        fake_result = {"code": "class Foo: pass", "code_type": "api", "specification": "spec", "language": "python"}
        with patch("app.api.agents.DevAgent") as MockDevAgent:
            mock_instance = MockDevAgent.return_value
            mock_instance.process = AsyncMock(return_value=fake_result)

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/agents/dev",
                    json={"specification": "REST API spec", "type": "api"},
                )

        assert response.status_code == status.HTTP_200_OK
        mock_instance.process.assert_awaited_once_with(
            {"specification": "REST API spec", "type": "api"}
        )
        assert response.json() == fake_result

        app.dependency_overrides.clear()

    async def test_default_type_is_general(self):
        """type defaults to 'general' when not provided."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        with patch("app.api.agents.DevAgent") as MockDevAgent:
            mock_instance = MockDevAgent.return_value
            mock_instance.process = AsyncMock(return_value={})

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.post(
                    "/api/agents/dev",
                    json={"specification": "some spec"},
                )

        mock_instance.process.assert_awaited_once_with(
            {"specification": "some spec", "type": "general"}
        )
        app.dependency_overrides.clear()

    async def test_invalid_type_value_returns_422(self):
        """Returns 422 when an invalid type value is provided."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/agents/dev",
                json={"specification": "spec", "type": "invalid"},
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()

    async def test_missing_specification_returns_422(self):
        """Returns 422 when required 'specification' field is missing."""
        from app.utils.auth import get_current_active_user

        app.dependency_overrides[get_current_active_user] = override_get_current_active_user

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/agents/dev", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        app.dependency_overrides.clear()
