from app.agents.base_agent import BaseAgent
from typing import Dict, Any


class SpecAgent(BaseAgent):
    """Agent for generating specifications and user stories"""

    def simulate_response(self, prompt: str) -> str:
        """Simulate specification generation"""
        requirements = prompt.split("for: ", 1)[-1] if "for: " in prompt else prompt
        if "user story" in prompt.lower():
            return f"""
**User Story**: As a user, I want to {requirements} so that I can achieve my goals efficiently.

**Acceptance Criteria**:
- System should implement core functionality for: {requirements}
- All primary use cases are covered and accessible
- Error states are handled gracefully with clear messaging
- Performance meets expected standards under normal load
- Changes are persisted and reflected immediately in the UI

**BDD Scenarios**:

Scenario: Successfully complete primary action
  Given I am an authenticated user
  And the system is configured for "{requirements}"
  When I perform the main action
  Then the operation should complete successfully
  And the result should be visible in the interface

Scenario: Handle failure gracefully
  Given I am using the system for "{requirements}"
  When an error occurs during the operation
  Then a clear error message should be displayed
  And the system should remain in a consistent state
"""
        elif "bdd" in prompt.lower():
            return f"""
Feature: {requirements}

  Scenario: Complete primary workflow
    Given I am an authenticated user
    When I initiate the main workflow for "{requirements}"
    Then the system should process my request successfully
    And I should see the updated state in the interface

  Scenario: Validate input and constraints
    Given I am working with "{requirements}"
    When I provide invalid or missing input
    Then the system should show a validation error
    And no data should be modified

  Scenario: Handle concurrent operations
    Given multiple users are working with "{requirements}"
    When they perform actions simultaneously
    Then each operation should complete correctly
    And data integrity should be maintained
"""
        else:
            return f"""
**Generated Specification**:

**Overview**: {requirements}

**Features**:
1. Core Functionality
   - Implement primary operations for the described system
   - Support standard CRUD operations
   - Real-time updates and notifications
   - Data validation and error handling

2. User Interface
   - Intuitive and responsive design
   - Clear feedback for all user actions
   - Accessible to all users

3. Integration & API
   - RESTful API endpoints
   - Authentication and authorization
   - Audit logging for all changes

**Technical Requirements**:
- RESTful API design
- WebSocket for real-time updates
- PostgreSQL for data persistence
- JWT authentication
- Rate limiting and security
"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specification from requirements"""
        requirements = input_data.get("requirements", "")
        spec_type = input_data.get("type", "general")  # general, user_story, bdd

        system_prompt = """You are a technical specification agent. Generate clear,
        actionable specifications from user requirements. Include acceptance criteria
        and BDD scenarios where applicable."""

        prompt = f"Generate a {spec_type} specification for: {requirements}"

        result = await self.call_llm(prompt, system_prompt)

        return {
            "specification": result,
            "type": spec_type,
            "requirements": requirements
        }
