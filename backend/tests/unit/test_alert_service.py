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
