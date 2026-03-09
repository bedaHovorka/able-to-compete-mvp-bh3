"""
Unit tests for AuditMiddleware
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.requests import Request
from app.utils.middleware import AuditMiddleware


def _make_request(method="GET", path="/api/boards"):
    """Build a minimal mock Request."""
    req = MagicMock(spec=Request)
    req.method = method
    req.url = MagicMock()
    req.url.path = path
    req.client = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers = MagicMock()
    req.headers.get = MagicMock(return_value="pytest-agent")
    req.body = AsyncMock(return_value=b'{"name": "test"}')
    return req


def _make_mock_session_local():
    mock_db = AsyncMock()
    mock_session_local = MagicMock()
    mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_session_local, mock_db


@pytest.mark.asyncio
class TestAuditMiddleware:

    async def test_dispatch_calls_call_next_and_returns_response(self):
        """dispatch() must call call_next and return its response."""
        middleware = AuditMiddleware(app=MagicMock())
        request = _make_request("GET", "/api/boards")
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.status_code = 200
        mock_session_local, _ = _make_mock_session_local()

        async def mock_call_next(req):
            return mock_response

        with patch("app.utils.middleware.AsyncSessionLocal", mock_session_local):
            result = await middleware.dispatch(request, mock_call_next)

        assert result is mock_response

    async def test_dispatch_adds_process_time_header(self):
        """dispatch() must add X-Process-Time header to the response."""
        middleware = AuditMiddleware(app=MagicMock())
        request = _make_request("GET", "/api/boards")
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.status_code = 200
        mock_session_local, _ = _make_mock_session_local()

        async def mock_call_next(req):
            return mock_response

        with patch("app.utils.middleware.AsyncSessionLocal", mock_session_local):
            await middleware.dispatch(request, mock_call_next)

        assert "X-Process-Time" in mock_response.headers

    async def test_dispatch_writes_audit_log_for_api_endpoint(self):
        """dispatch() must call AsyncSessionLocal for non-websocket API endpoints."""
        middleware = AuditMiddleware(app=MagicMock())
        request = _make_request("POST", "/api/boards")
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.status_code = 201
        mock_session_local, mock_db = _make_mock_session_local()

        async def mock_call_next(req):
            return mock_response

        with patch("app.utils.middleware.AsyncSessionLocal", mock_session_local):
            await middleware.dispatch(request, mock_call_next)

        mock_session_local.assert_called_once()

    async def test_dispatch_skips_audit_log_for_websocket(self):
        """dispatch() must NOT call AsyncSessionLocal for /ws endpoints."""
        middleware = AuditMiddleware(app=MagicMock())
        request = _make_request("GET", "/ws/boards/123")
        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.status_code = 200
        mock_session_local, _ = _make_mock_session_local()

        async def mock_call_next(req):
            return mock_response

        with patch("app.utils.middleware.AsyncSessionLocal", mock_session_local):
            await middleware.dispatch(request, mock_call_next)

        mock_session_local.assert_not_called()
