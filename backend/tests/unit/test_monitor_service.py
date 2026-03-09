"""
Unit tests for MonitorService
"""
import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.monitor_service import MonitorService
import app.services.monitor_service as monitor_service_module
from app.models.monitor import Monitor, Check, MonitorStatus, MonitorType


@pytest.fixture(autouse=True)
def reset_module_state():
    """Reset module-level dicts between tests to avoid state bleed."""
    monitor_service_module.failure_counts.clear()
    monitor_service_module.active_monitors.clear()
    yield
    monitor_service_module.failure_counts.clear()
    monitor_service_module.active_monitors.clear()


def _make_monitor(monitor_id=None, url="https://example.com", expected_status_code=200, timeout=10):
    """Build a minimal Monitor-like object without DB."""
    monitor = MagicMock(spec=Monitor)
    monitor.id = monitor_id or uuid.uuid4()
    monitor.name = "Test Monitor"
    monitor.url = url
    monitor.expected_status_code = expected_status_code
    monitor.timeout = timeout
    monitor.headers = {}
    monitor.status = MonitorStatus.PAUSED
    monitor.last_checked_at = None
    return monitor


@pytest.mark.asyncio
class TestExecuteCheckSuccess:
    """execute_check creates a Check with status UP when the request returns expected code."""

    async def test_execute_check_success(self, db_session):
        """Mock httpx 200 response → check stored with status UP."""
        service = MonitorService()

        # Persist a real Monitor so FK constraints are satisfied
        monitor = Monitor(
            name="Healthy Site",
            url="https://example.com",
            expected_status_code=200,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)

        mock_async_client_cm = AsyncMock()
        mock_async_client_cm.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_async_client_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.monitor_service.httpx.AsyncClient", return_value=mock_async_client_cm):
            check = await service.execute_check(db_session, monitor)

        assert check.status == MonitorStatus.UP
        assert check.monitor_id == monitor.id
        assert check.status_code == 200
        assert check.error_message is None


@pytest.mark.asyncio
class TestExecuteCheckFailure:
    """execute_check creates a Check with status DOWN on network error or non-200."""

    async def test_execute_check_failure_on_exception(self, db_session):
        """Exception raised during HTTP request → check stored with status DOWN."""
        service = MonitorService()

        monitor = Monitor(
            name="Down Site",
            url="https://down.example.com",
            expected_status_code=200,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=Exception("connection refused"))

        mock_async_client_cm = AsyncMock()
        mock_async_client_cm.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_async_client_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.monitor_service.httpx.AsyncClient", return_value=mock_async_client_cm):
            check = await service.execute_check(db_session, monitor)

        assert check.status == MonitorStatus.DOWN
        assert check.monitor_id == monitor.id
        assert check.error_message == "connection refused"

    async def test_execute_check_failure_on_non_200(self, db_session):
        """500 response (non-expected code) → check stored with status DEGRADED."""
        service = MonitorService()

        monitor = Monitor(
            name="Error Site",
            url="https://error.example.com",
            expected_status_code=200,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)

        mock_async_client_cm = AsyncMock()
        mock_async_client_cm.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_async_client_cm.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.monitor_service.httpx.AsyncClient", return_value=mock_async_client_cm):
            check = await service.execute_check(db_session, monitor)

        assert check.status == MonitorStatus.DEGRADED
        assert check.status_code == 500


@pytest.mark.asyncio
class TestGetResponseTimeHistory:
    """get_response_time_history returns checks ordered by checked_at DESC with total count."""

    async def test_returns_checks_newest_first(self, db_session):
        """Checks are returned in descending checked_at order."""
        service = MonitorService()

        monitor = Monitor(name="History Monitor", url="https://history.example.com")
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        now = datetime.utcnow()
        for i in range(3):
            check = Check(
                monitor_id=monitor.id,
                status=MonitorStatus.UP,
                response_time=float(100 + i * 10),
                status_code=200,
                checked_at=now - timedelta(minutes=i * 5),
            )
            db_session.add(check)
        await db_session.commit()

        checks, total = await service.get_response_time_history(db_session, monitor.id, limit=10)

        assert total == 3
        assert len(checks) == 3
        # Verify descending order
        assert checks[0].checked_at >= checks[1].checked_at >= checks[2].checked_at

    async def test_limit_caps_results(self, db_session):
        """limit parameter restricts the number of checks returned."""
        service = MonitorService()

        monitor = Monitor(name="Limit Monitor", url="https://limit.example.com")
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        now = datetime.utcnow()
        for i in range(10):
            check = Check(
                monitor_id=monitor.id,
                status=MonitorStatus.UP,
                response_time=50.0,
                status_code=200,
                checked_at=now - timedelta(minutes=i),
            )
            db_session.add(check)
        await db_session.commit()

        checks, total = await service.get_response_time_history(db_session, monitor.id, limit=5)

        assert total == 10
        assert len(checks) == 5

    async def test_offset_paginates_results(self, db_session):
        """offset parameter paginates through checks."""
        service = MonitorService()

        monitor = Monitor(name="Offset Monitor", url="https://offset.example.com")
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        now = datetime.utcnow()
        for i in range(6):
            check = Check(
                monitor_id=monitor.id,
                status=MonitorStatus.UP,
                response_time=50.0,
                status_code=200,
                checked_at=now - timedelta(minutes=i),
            )
            db_session.add(check)
        await db_session.commit()

        checks_page1, total = await service.get_response_time_history(
            db_session, monitor.id, limit=3, offset=0
        )
        checks_page2, _ = await service.get_response_time_history(
            db_session, monitor.id, limit=3, offset=3
        )

        assert total == 6
        assert len(checks_page1) == 3
        assert len(checks_page2) == 3
        # Pages should not overlap
        page1_ids = {c.id for c in checks_page1}
        page2_ids = {c.id for c in checks_page2}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_no_checks_returns_empty(self, db_session):
        """Returns empty list and zero total when monitor has no checks."""
        service = MonitorService()

        monitor = Monitor(name="Empty Monitor", url="https://empty.example.com")
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        checks, total = await service.get_response_time_history(db_session, monitor.id)

        assert total == 0
        assert checks == []

    async def test_null_response_time_included(self, db_session):
        """Checks with null response_time (DOWN) are included in results."""
        service = MonitorService()

        monitor = Monitor(name="Down Monitor", url="https://down2.example.com")
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        now = datetime.utcnow()
        check = Check(
            monitor_id=monitor.id,
            status=MonitorStatus.DOWN,
            response_time=None,
            status_code=None,
            checked_at=now,
        )
        db_session.add(check)
        await db_session.commit()

        checks, total = await service.get_response_time_history(db_session, monitor.id)

        assert total == 1
        assert checks[0].response_time is None
        assert checks[0].status == MonitorStatus.DOWN


@pytest.mark.asyncio
class TestUptimeCalculation:
    """calculate_uptime returns correct percentages based on Check records."""

    async def test_uptime_all_up(self, db_session):
        """100% uptime when all checks are UP."""
        service = MonitorService()

        monitor = Monitor(name="Always Up", url="https://up.example.com")
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        now = datetime.utcnow()
        for i in range(5):
            check = Check(
                monitor_id=monitor.id,
                status=MonitorStatus.UP,
                response_time=50.0,
                status_code=200,
                checked_at=now - timedelta(minutes=i * 5),
            )
            db_session.add(check)
        await db_session.commit()

        result = await service.calculate_uptime(db_session, monitor.id, hours=24)

        assert result["uptime_percentage"] == 100.0
        assert result["total_checks"] == 5
        assert result["failed_checks"] == 0

    async def test_uptime_mixed(self, db_session):
        """Correct percentage when some checks are DOWN."""
        service = MonitorService()

        monitor = Monitor(name="Flaky Site", url="https://flaky.example.com")
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        now = datetime.utcnow()
        # 3 UP, 1 DOWN = 75% uptime
        statuses = [MonitorStatus.UP, MonitorStatus.UP, MonitorStatus.UP, MonitorStatus.DOWN]
        for i, status in enumerate(statuses):
            check = Check(
                monitor_id=monitor.id,
                status=status,
                response_time=50.0 if status == MonitorStatus.UP else None,
                status_code=200 if status == MonitorStatus.UP else 500,
                checked_at=now - timedelta(minutes=i * 5),
            )
            db_session.add(check)
        await db_session.commit()

        result = await service.calculate_uptime(db_session, monitor.id, hours=24)

        assert result["uptime_percentage"] == 75.0
        assert result["total_checks"] == 4
        assert result["failed_checks"] == 1

    async def test_uptime_no_checks(self, db_session):
        """Returns 100% uptime and zero counts when no checks exist."""
        service = MonitorService()

        monitor = Monitor(name="New Monitor", url="https://new.example.com")
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        result = await service.calculate_uptime(db_session, monitor.id, hours=24)

        assert result["uptime_percentage"] == 100.0
        assert result["total_checks"] == 0
        assert result["failed_checks"] == 0


@pytest.mark.asyncio
class TestSSLCheckExecution:
    """Tests for SSL certificate monitoring (_execute_ssl_check_flow)."""

    def _make_ssl_monitor(self, db_session=None, monitor_id=None):
        monitor = MagicMock(spec=Monitor)
        monitor.id = monitor_id or uuid.uuid4()
        monitor.name = "SSL Monitor"
        monitor.url = "https://example.com"
        monitor.type = MonitorType.SSL
        monitor.timeout = 10
        monitor.headers = {}
        monitor.status = MonitorStatus.PAUSED
        monitor.last_checked_at = None
        return monitor

    async def test_ssl_check_healthy_cert_creates_up_check(self, db_session):
        """Certificate with > 30 days remaining → UP status check."""
        service = MonitorService()

        monitor = Monitor(
            name="SSL Healthy",
            url="https://ssl.example.com",
            type=MonitorType.SSL,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        with patch.object(service, "_execute_ssl_check", return_value=60):
            check = await service._execute_ssl_check_flow(db_session, monitor)

        assert check.status == MonitorStatus.UP
        assert check.ssl_expiry_days == 60
        assert check.error_message is None

    async def test_ssl_check_expiring_soon_creates_degraded_check(self, db_session):
        """Certificate with 1–29 days remaining → DEGRADED status check."""
        service = MonitorService()

        monitor = Monitor(
            name="SSL Expiring",
            url="https://ssl.example.com",
            type=MonitorType.SSL,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        with patch.object(service, "_execute_ssl_check", return_value=15):
            check = await service._execute_ssl_check_flow(db_session, monitor)

        assert check.status == MonitorStatus.DEGRADED
        assert check.ssl_expiry_days == 15

    async def test_ssl_check_expired_cert_creates_down_check(self, db_session):
        """Certificate with 0 or negative days → DOWN status check."""
        service = MonitorService()

        monitor = Monitor(
            name="SSL Expired",
            url="https://ssl.example.com",
            type=MonitorType.SSL,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        with patch.object(service, "_execute_ssl_check", return_value=0):
            check = await service._execute_ssl_check_flow(db_session, monitor)

        assert check.status == MonitorStatus.DOWN
        assert check.ssl_expiry_days == 0

    async def test_ssl_check_verification_error_creates_down_check(self, db_session):
        """SSLCertVerificationError → DOWN with ssl_expiry_days=0."""
        import ssl as ssl_module

        service = MonitorService()

        monitor = Monitor(
            name="SSL Invalid",
            url="https://ssl.example.com",
            type=MonitorType.SSL,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        with patch.object(
            service,
            "_execute_ssl_check",
            side_effect=ssl_module.SSLCertVerificationError("cert verify failed"),
        ):
            check = await service._execute_ssl_check_flow(db_session, monitor)

        assert check.status == MonitorStatus.DOWN
        assert check.ssl_expiry_days == 0
        assert check.error_message is not None

    async def test_ssl_check_connection_error_creates_down_check(self, db_session):
        """Generic connection error → DOWN with descriptive error message."""
        service = MonitorService()

        monitor = Monitor(
            name="SSL Unreachable",
            url="https://unreachable.example.com",
            type=MonitorType.SSL,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        with patch.object(
            service,
            "_execute_ssl_check",
            side_effect=ConnectionRefusedError("Connection refused"),
        ):
            check = await service._execute_ssl_check_flow(db_session, monitor)

        assert check.status == MonitorStatus.DOWN
        assert "Connection refused" in check.error_message

    async def test_execute_check_dispatches_ssl_type(self, db_session):
        """execute_check routes SSL monitors to _execute_ssl_check_flow."""
        service = MonitorService()

        monitor = Monitor(
            name="SSL Dispatch",
            url="https://ssl.example.com",
            type=MonitorType.SSL,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        mock_check = MagicMock(spec=Check)
        with patch.object(service, "_execute_ssl_check_flow", return_value=mock_check) as mock_flow:
            result = await service.execute_check(db_session, monitor)

        mock_flow.assert_awaited_once_with(db_session, monitor)
        assert result is mock_check


@pytest.mark.asyncio
class TestHandleSSLIncident:
    """Tests for handle_ssl_incident: immediate incident creation without 3-failure wait."""

    async def test_ssl_down_creates_critical_incident(self, db_session):
        """DOWN status → creates CRITICAL incident immediately."""
        from app.models.monitor import Incident, IncidentSeverity, IncidentStatus

        service = MonitorService()

        monitor = Monitor(
            name="SSL Down Monitor",
            url="https://ssl.example.com",
            type=MonitorType.SSL,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        await service.handle_ssl_incident(db_session, monitor, MonitorStatus.DOWN, ssl_expiry_days=0)

        from sqlalchemy import select
        result = await db_session.execute(
            select(Incident).where(Incident.monitor_id == monitor.id)
        )
        incident = result.scalar_one_or_none()

        assert incident is not None
        assert incident.severity == IncidentSeverity.CRITICAL
        assert incident.status == IncidentStatus.INVESTIGATING

    async def test_ssl_degraded_creates_high_incident(self, db_session):
        """DEGRADED status → creates HIGH severity incident immediately."""
        from app.models.monitor import Incident, IncidentSeverity, IncidentStatus

        service = MonitorService()

        monitor = Monitor(
            name="SSL Degraded Monitor",
            url="https://ssl.example.com",
            type=MonitorType.SSL,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        await service.handle_ssl_incident(db_session, monitor, MonitorStatus.DEGRADED, ssl_expiry_days=15)

        from sqlalchemy import select
        result = await db_session.execute(
            select(Incident).where(Incident.monitor_id == monitor.id)
        )
        incident = result.scalar_one_or_none()

        assert incident is not None
        assert incident.severity == IncidentSeverity.HIGH
        assert incident.status == IncidentStatus.INVESTIGATING

    async def test_ssl_up_resolves_existing_incident(self, db_session):
        """UP status → auto-resolves an existing open incident."""
        from app.models.monitor import Incident, IncidentSeverity, IncidentStatus

        service = MonitorService()

        monitor = Monitor(
            name="SSL Recovered",
            url="https://ssl.example.com",
            type=MonitorType.SSL,
        )
        db_session.add(monitor)
        await db_session.commit()
        await db_session.refresh(monitor)

        # Create existing open incident
        existing = Incident(
            monitor_id=monitor.id,
            title="SSL cert expired",
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.INVESTIGATING,
        )
        db_session.add(existing)
        await db_session.commit()

        await service.handle_ssl_incident(db_session, monitor, MonitorStatus.UP, ssl_expiry_days=60)

        await db_session.refresh(existing)
        assert existing.status == IncidentStatus.RESOLVED
        assert existing.resolved_at is not None
