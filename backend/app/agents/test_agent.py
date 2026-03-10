from app.agents.base_agent import BaseAgent
from typing import Dict, Any


class TestAgent(BaseAgent):
    """Agent for generating test cases and test code"""

    def simulate_response(self, prompt: str) -> str:
        """Simulate test generation"""
        subject = prompt.split("for: ", 1)[-1] if "for: " in prompt else prompt
        resource = subject.replace(" ", "_").replace("-", "_").lower()[:30]
        prompt_prefix = prompt.split("for:")[0].lower() if "for:" in prompt else prompt.lower()
        if "integration" in prompt_prefix:
            return f"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.utils.database import get_db


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestIntegration_{subject.replace(" ", "_").replace("-", "_")[:40]}:
    @pytest.mark.asyncio
    async def test_create_returns_201(self, client):
        payload = {{"name": "test_{resource}", "description": "Integration test for {subject}"}}
        response = await client.post("/api/{resource}s/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_returns_200(self, client):
        response = await client.get("/api/{resource}s/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_by_id_returns_200(self, client):
        create_resp = await client.post("/api/{resource}s/", json={{"name": "item_for_get"}})
        item_id = create_resp.json()["id"]
        response = await client.get(f"/api/{resource}s/{{item_id}}")
        assert response.status_code == 200
        assert response.json()["id"] == item_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_404(self, client):
        response = await client.get("/api/{resource}s/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_returns_204(self, client):
        create_resp = await client.post("/api/{resource}s/", json={{"name": "item_to_delete"}})
        item_id = create_resp.json()["id"]
        response = await client.delete(f"/api/{resource}s/{{item_id}}")
        assert response.status_code == 204
"""
        elif "bdd" in prompt_prefix:
            return f"""
# BDD tests for: {subject}
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from httpx import AsyncClient
from app.main import app

scenarios("features/{resource}.feature")


@pytest.fixture
def context():
    return {{}}


@given("I am an authenticated user")
def authenticated_user(context):
    context["headers"] = {{"Authorization": "Bearer test-token"}}


@given(parsers.parse('a {resource} named "{{name}}" exists'), target_fixture="existing_item")
async def existing_item(name, db_session):
    from app.services.{resource}_service import {resource.title()}Service
    item = await {resource.title()}Service.create(db_session, name=name)
    return item


@when("I request to create a new item")
async def create_item(context):
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/{resource}s/",
            json={{"name": "new_{resource}", "description": "Created via BDD test"}},
            headers=context.get("headers", {{}})
        )
        context["response"] = resp


@when("I request the list of items")
async def list_items(context):
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/{resource}s/", headers=context.get("headers", {{}}))
        context["response"] = resp


@then("the response status should be 201")
def status_201(context):
    assert context["response"].status_code == 201


@then("the response status should be 200")
def status_200(context):
    assert context["response"].status_code == 200


@then("the response body should contain the created item")
def body_contains_item(context):
    data = context["response"].json()
    assert "id" in data
    assert data["name"] == "new_{resource}"


@then("the response body should be a list")
def body_is_list(context):
    assert isinstance(context["response"].json(), list)
"""
        else:
            return f"""
import pytest


class Test_{subject.replace(" ", "_").replace("-", "_")[:40]}:
    @pytest.mark.asyncio
    async def test_primary_operation_succeeds(self, db_session):
        # Arrange - set up for: {subject}
        input_data = {{"name": "test_item", "description": "Test for {subject}"}}

        # Act
        result = await service.create(db_session, **input_data)

        # Assert
        assert result is not None
        assert result.name == input_data["name"]
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_retrieve_existing_item(self, db_session, test_item):
        # Act
        result = await service.get(db_session, test_item.id)

        # Assert
        assert result is not None
        assert result.id == test_item.id

    @pytest.mark.asyncio
    async def test_update_item(self, db_session, test_item):
        # Arrange
        update_data = {{"name": "updated_name"}}

        # Act
        updated = await service.update(db_session, test_item.id, **update_data)

        # Assert
        assert updated.name == update_data["name"]

    @pytest.mark.asyncio
    async def test_delete_item(self, db_session, test_item):
        # Act
        success = await service.delete(db_session, test_item.id)

        # Assert
        assert success is True
        result = await service.get(db_session, test_item.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_input_raises_error(self, db_session):
        # Act & Assert
        with pytest.raises((ValueError, Exception)):
            await service.create(db_session, name=None)

    @pytest.mark.asyncio
    async def test_not_found_returns_none(self, db_session):
        # Act
        result = await service.get(db_session, id=9999999)

        # Assert
        assert result is None


# Fixtures
@pytest.fixture
async def test_item(db_session):
    item = await service.create(
        db_session,
        name="Test Item for {subject}"
    )
    return item
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
