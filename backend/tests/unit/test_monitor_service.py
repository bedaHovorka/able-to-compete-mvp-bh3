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
from app.models.monitor import Monitor, Check, MonitorStatus


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
