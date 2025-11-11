# backend/tests/features/monitoring.feature
Feature: Service Monitoring
  As a DevOps engineer
  I want to monitor service health
  So that I can respond to incidents quickly

  Scenario: Add endpoint monitoring
    Given I am authenticated as an admin
    When I add monitoring for "https://api.example.com/health"
    Then health checks should start every 30 seconds
    And the status should be displayed on dashboard

  Scenario: Detect service downtime
    Given I have an active monitor
    When the endpoint returns status code 500
    Then an incident should be created
    And an alert should be sent
    And the status page should show "DOWN"

  Scenario: Auto-recovery detection
    Given a service is marked as DOWN
    When the service returns status 200 for 3 consecutive checks
    Then the incident should be auto-resolved
    And a recovery notification should be sent
