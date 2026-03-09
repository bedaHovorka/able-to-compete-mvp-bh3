"""
Unit tests for AlertService._send_webhook_alert
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid

from app.services.alert_service import AlertService
from app.models.monitor import Monitor, Incident, IncidentSeverity, IncidentStatus, MonitorType, MonitorStatus


def make_monitor() -> Monitor:
    monitor = Monitor(
        id=uuid.uuid4(),
        name="Test Monitor",
        url="https://example.com",
        type=MonitorType.HTTPS,
        status=MonitorStatus.DOWN,
    )
    return monitor


def make_incident(severity: IncidentSeverity = IncidentSeverity.CRITICAL) -> Incident:
    incident = Incident(
        id=uuid.uuid4(),
        monitor_id=uuid.uuid4(),
        title="Service Down",
        description="The service is not responding.",
        status=IncidentStatus.INVESTIGATING,
        severity=severity,
        started_at=datetime(2026, 1, 1, 12, 0, 0),
    )
    return incident


@pytest.mark.asyncio
class TestSendWebhookAlert:
    """Tests for AlertService._send_webhook_alert"""

    async def test_webhook_url_set_posts_to_url(self):
        """When WEBHOOK_URL is configured, an HTTP POST should be made."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        service = AlertService()
        monitor = make_monitor()
        incident = make_incident()

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300

            await service._send_webhook_alert(incident, monitor)

        mock_client.post.assert_awaited_once()
        call_kwargs = mock_client.post.call_args
        assert call_kwargs[0][0] == "https://hooks.example.com/test"
        payload = call_kwargs[1]["json"]
        assert "INCIDENT" in payload["text"]
        assert payload["username"] == "AbleToCompete Alerts"

    async def test_webhook_url_empty_skips_post(self):
        """When WEBHOOK_URL is empty, no HTTP POST should be made."""
        mock_client = AsyncMock()

        service = AlertService()
        monitor = make_monitor()
        incident = make_incident()

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = ""
            mock_settings.ALERT_COOLDOWN = 300

            await service._send_webhook_alert(incident, monitor)

        mock_client.post.assert_not_called()

    async def test_webhook_url_none_skips_post(self):
        """When WEBHOOK_URL is None, no HTTP POST should be made."""
        mock_client = AsyncMock()

        service = AlertService()
        monitor = make_monitor()
        incident = make_incident()

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = None
            mock_settings.ALERT_COOLDOWN = 300

            await service._send_webhook_alert(incident, monitor)

        mock_client.post.assert_not_called()

    async def test_webhook_payload_critical_severity_uses_danger_color(self):
        """Critical severity incidents should use 'danger' color in the payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        service = AlertService()
        monitor = make_monitor()
        incident = make_incident(severity=IncidentSeverity.CRITICAL)

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300

            await service._send_webhook_alert(incident, monitor)

        payload = mock_client.post.call_args[1]["json"]
        assert payload["attachments"][0]["color"] == "danger"

    async def test_webhook_payload_non_critical_severity_uses_warning_color(self):
        """Non-critical severity incidents should use 'warning' color in the payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        service = AlertService()
        monitor = make_monitor()
        incident = make_incident(severity=IncidentSeverity.MEDIUM)

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300

            await service._send_webhook_alert(incident, monitor)

        payload = mock_client.post.call_args[1]["json"]
        assert payload["attachments"][0]["color"] == "warning"

    async def test_webhook_raise_for_status_called(self):
        """raise_for_status() should be called so non-2xx responses propagate."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        service = AlertService()
        monitor = make_monitor()
        incident = make_incident()

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300

            await service._send_webhook_alert(incident, monitor)

        mock_response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
class TestWebhookPayloadDeep:
    """Deep tests: payload completeness and timeout"""

    def _make_mock_client(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        return mock_client

    async def test_post_uses_timeout_5_seconds(self):
        """HTTP POST must use timeout=5.0 to prevent blocking."""
        mock_client = self._make_mock_client()
        service = AlertService()

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300
            await service._send_webhook_alert(make_incident(), make_monitor())

        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["timeout"] == 5.0

    async def test_payload_contains_all_required_fields(self):
        """Payload must include all Slack-compatible fields."""
        mock_client = self._make_mock_client()
        service = AlertService()
        monitor = make_monitor()
        incident = make_incident()

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300
            await service._send_webhook_alert(incident, monitor)

        payload = mock_client.post.call_args[1]["json"]
        assert payload["username"] == "AbleToCompete Alerts"
        assert "INCIDENT" in payload["text"]
        attachment = payload["attachments"][0]
        assert attachment["footer"] == "AbleToCompete Monitoring"
        assert attachment["ts"] == int(incident.started_at.timestamp())
        field_titles = {f["title"] for f in attachment["fields"]}
        assert field_titles == {"Monitor", "URL", "Severity", "Status", "Description"}

    async def test_payload_monitor_name_and_url_in_fields(self):
        """Payload fields must contain the monitor's name and URL."""
        mock_client = self._make_mock_client()
        service = AlertService()
        monitor = make_monitor()  # name="Test Monitor", url="https://example.com"
        incident = make_incident()

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300
            await service._send_webhook_alert(incident, monitor)

        fields = {f["title"]: f["value"] for f in mock_client.post.call_args[1]["json"]["attachments"][0]["fields"]}
        assert fields["Monitor"] == "Test Monitor"
        assert fields["URL"] == "https://example.com"

    async def test_payload_high_severity_uses_warning_color(self):
        """HIGH severity should use 'warning' color (not 'danger')."""
        mock_client = self._make_mock_client()
        service = AlertService()

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300
            await service._send_webhook_alert(make_incident(IncidentSeverity.HIGH), make_monitor())

        color = mock_client.post.call_args[1]["json"]["attachments"][0]["color"]
        assert color == "warning"

    async def test_payload_low_severity_uses_warning_color(self):
        """LOW severity should use 'warning' color."""
        mock_client = self._make_mock_client()
        service = AlertService()

        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300
            await service._send_webhook_alert(make_incident(IncidentSeverity.LOW), make_monitor())

        color = mock_client.post.call_args[1]["json"]["attachments"][0]["color"]
        assert color == "warning"


@pytest.mark.asyncio
class TestWebhookErrorHandling:
    """Tests for HTTP errors and network failures in _send_webhook_alert"""

    async def test_http_4xx_raises_exception(self):
        """A 4xx response should raise via raise_for_status."""
        import httpx as _httpx
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(
            side_effect=_httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)
        )
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        service = AlertService()
        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300
            with pytest.raises(_httpx.HTTPStatusError):
                await service._send_webhook_alert(make_incident(), make_monitor())

    async def test_http_5xx_raises_exception(self):
        """A 5xx response should raise via raise_for_status."""
        import httpx as _httpx
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status = MagicMock(
            side_effect=_httpx.HTTPStatusError("Server Error", request=MagicMock(), response=mock_response)
        )
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        service = AlertService()
        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300
            with pytest.raises(_httpx.HTTPStatusError):
                await service._send_webhook_alert(make_incident(), make_monitor())

    async def test_network_error_propagates(self):
        """Network errors (ConnectError) should propagate from _send_webhook_alert."""
        import httpx as _httpx
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=_httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        service = AlertService()
        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300
            with pytest.raises(_httpx.ConnectError):
                await service._send_webhook_alert(make_incident(), make_monitor())

    async def test_timeout_error_propagates(self):
        """Timeout errors should propagate from _send_webhook_alert."""
        import httpx as _httpx
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=_httpx.TimeoutException("Timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        service = AlertService()
        with patch("app.services.alert_service.settings") as mock_settings, \
             patch("app.services.alert_service.httpx.AsyncClient", return_value=mock_client):
            mock_settings.WEBHOOK_URL = "https://hooks.example.com/test"
            mock_settings.ALERT_COOLDOWN = 300
            with pytest.raises(_httpx.TimeoutException):
                await service._send_webhook_alert(make_incident(), make_monitor())


@pytest.mark.asyncio
class TestSendAlertIntegration:
    """Integration tests for send_alert() routing and error isolation"""

    async def test_send_alert_calls_webhook_channel(self):
        """send_alert() with 'webhook' channel must invoke _send_webhook_alert."""
        service = AlertService()
        service._send_webhook_alert = AsyncMock()
        service._send_email_alert = AsyncMock()
        monitor = make_monitor()
        incident = make_incident()

        with patch("app.services.alert_service.settings") as mock_settings:
            mock_settings.ALERT_COOLDOWN = 300
            await service.send_alert(incident, monitor, channels=["webhook"])

        service._send_webhook_alert.assert_awaited_once_with(incident, monitor)
        service._send_email_alert.assert_not_awaited()

    async def test_send_alert_webhook_error_does_not_block_email(self):
        """A webhook failure must NOT prevent email from being sent."""
        import httpx as _httpx
        service = AlertService()
        service._send_webhook_alert = AsyncMock(side_effect=_httpx.ConnectError("refused"))
        service._send_email_alert = AsyncMock()
        monitor = make_monitor()
        incident = make_incident()

        with patch("app.services.alert_service.settings") as mock_settings:
            mock_settings.ALERT_COOLDOWN = 300
            await service.send_alert(incident, monitor, channels=["webhook", "email"])

        # Email still called despite webhook failure
        service._send_email_alert.assert_awaited_once_with(incident, monitor)

    async def test_send_alert_cooldown_prevents_second_call(self):
        """Second send_alert() within cooldown period must not call channels."""
        service = AlertService()
        service._send_webhook_alert = AsyncMock()
        monitor = make_monitor()
        incident = make_incident()

        with patch("app.services.alert_service.settings") as mock_settings:
            mock_settings.ALERT_COOLDOWN = 300
            # First call — should send
            await service.send_alert(incident, monitor, channels=["webhook"])
            # Second call immediately — should be blocked by cooldown
            await service.send_alert(incident, monitor, channels=["webhook"])

        # Only called once
        assert service._send_webhook_alert.await_count == 1

    async def test_send_alert_after_clear_cooldown_sends_again(self):
        """After clearing cooldown, send_alert() must call channels again."""
        service = AlertService()
        service._send_webhook_alert = AsyncMock()
        monitor = make_monitor()
        incident = make_incident()

        with patch("app.services.alert_service.settings") as mock_settings:
            mock_settings.ALERT_COOLDOWN = 300
            await service.send_alert(incident, monitor, channels=["webhook"])
            await service.clear_cooldown(str(incident.id))
            await service.send_alert(incident, monitor, channels=["webhook"])

        assert service._send_webhook_alert.await_count == 2
