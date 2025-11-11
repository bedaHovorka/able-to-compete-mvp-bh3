from app.agents.base_agent import BaseAgent
from typing import Dict, Any


class TestAgent(BaseAgent):
    """Agent for generating test cases and test code"""

    def simulate_response(self, prompt: str) -> str:
        """Simulate test generation"""
        return """
import pytest
from app.services import TaskService, MonitorService
from app.models import Board, Monitor, MonitorStatus

class TestTaskService:
    @pytest.mark.asyncio
    async def test_create_board(self, db_session):
        # Arrange
        board_name = "Test Board"
        board_description = "Test Description"

        # Act
        board = await TaskService.create_board(
            db_session,
            name=board_name,
            description=board_description
        )

        # Assert
        assert board is not None
        assert board.name == board_name
        assert board.description == board_description
        assert board.id is not None

    @pytest.mark.asyncio
    async def test_create_list_in_board(self, db_session, test_board):
        # Arrange
        list_name = "To Do"

        # Act
        list_obj = await TaskService.create_list(
            db_session,
            board_id=test_board.id,
            name=list_name
        )

        # Assert
        assert list_obj is not None
        assert list_obj.name == list_name
        assert list_obj.board_id == test_board.id

class TestMonitorService:
    @pytest.mark.asyncio
    async def test_create_monitor(self, db_session, monitor_service):
        # Arrange
        monitor_name = "Test API"
        monitor_url = "https://api.example.com/health"

        # Act
        monitor = await monitor_service.create_monitor(
            db_session,
            name=monitor_name,
            url=monitor_url
        )

        # Assert
        assert monitor is not None
        assert monitor.name == monitor_name
        assert monitor.url == monitor_url
        assert monitor.status == MonitorStatus.PAUSED

    @pytest.mark.asyncio
    async def test_execute_health_check(self, db_session, monitor_service, test_monitor):
        # Act
        check = await monitor_service.execute_check(db_session, test_monitor)

        # Assert
        assert check is not None
        assert check.monitor_id == test_monitor.id
        assert check.status in [MonitorStatus.UP, MonitorStatus.DOWN, MonitorStatus.DEGRADED]
        assert check.checked_at is not None

    @pytest.mark.asyncio
    async def test_incident_creation_on_failures(self, db_session, monitor_service):
        # Arrange
        monitor = await monitor_service.create_monitor(
            db_session,
            name="Failing Service",
            url="https://definitely-not-real-url-12345.com"
        )

        # Act - Simulate 3 failures
        for _ in range(3):
            await monitor_service.execute_check(db_session, monitor)

        # Assert - Incident should be created
        from sqlalchemy import select
        from app.models import Incident
        query = select(Incident).where(Incident.monitor_id == monitor.id)
        result = await db_session.execute(query)
        incident = result.scalar_one_or_none()

        assert incident is not None
        assert incident.monitor_id == monitor.id

# Fixtures
@pytest.fixture
async def test_board(db_session):
    board = await TaskService.create_board(
        db_session,
        name="Test Board"
    )
    return board

@pytest.fixture
async def test_monitor(db_session, monitor_service):
    monitor = await monitor_service.create_monitor(
        db_session,
        name="Test Monitor",
        url="https://example.com"
    )
    return monitor

@pytest.fixture
def monitor_service():
    from app.services import MonitorService
    return MonitorService()
"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test code from specification"""
        specification = input_data.get("specification", "")
        test_type = input_data.get("type", "unit")  # unit, integration, bdd

        system_prompt = """You are a test generation agent. Create comprehensive
        test cases and pytest code from specifications. Include fixtures, arrange-act-assert
        pattern, and edge cases."""

        prompt = f"Generate {test_type} tests for: {specification}"

        result = await self.call_llm(prompt, system_prompt)

        return {
            "test_code": result,
            "test_type": test_type,
            "specification": specification
        }
