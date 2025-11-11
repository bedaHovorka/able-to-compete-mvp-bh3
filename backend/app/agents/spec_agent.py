from app.agents.base_agent import BaseAgent
from typing import Dict, Any


class SpecAgent(BaseAgent):
    """Agent for generating specifications and user stories"""

    def simulate_response(self, prompt: str) -> str:
        """Simulate specification generation"""
        if "user story" in prompt.lower():
            return """
**User Story**: As a system administrator, I want to monitor website uptime so that I can quickly respond to outages.

**Acceptance Criteria**:
- Monitor should check URL every 60 seconds
- System creates incident after 3 consecutive failures
- Email and webhook alerts are sent when incident is created
- Incident is auto-resolved when service recovers
- Dashboard shows current status and uptime percentage

**BDD Scenarios**:

Scenario: Monitor detects service outage
  Given a monitor is configured for "https://example.com"
  And the monitor is enabled
  When the service fails health checks 3 times
  Then an incident should be created
  And alerts should be sent to configured channels

Scenario: Service recovery auto-resolves incident
  Given an active incident exists for a monitor
  When the service health check succeeds
  Then the incident should be marked as resolved
  And the resolution time should be recorded
"""
        elif "bdd" in prompt.lower():
            return """
Feature: Task Board Management

  Scenario: Create new task board
    Given I am an authenticated user
    When I create a board with name "Sprint Planning"
    Then the board should be created successfully
    And I should see the board in my dashboard

  Scenario: Add card to list
    Given I have a board with a list
    When I add a card titled "Implement login feature"
    Then the card should appear in the list
    And an activity log entry should be created

  Scenario: Move card between lists
    Given I have a card in "To Do" list
    When I move the card to "In Progress" list
    Then the card should be in the new list
    And the position should be updated
"""
        else:
            return """
**Generated Specification**:

**Overview**: Task and monitoring management system

**Features**:
1. Task Board Management
   - Create/edit/delete boards
   - Organize tasks in lists
   - Drag-and-drop cards
   - Label and categorize tasks

2. Monitoring System
   - Configure HTTP/HTTPS monitors
   - Automated health checks
   - Incident detection and management
   - Alert notifications

3. Audit & Compliance
   - Complete audit trail
   - User activity logging
   - Data change tracking

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
