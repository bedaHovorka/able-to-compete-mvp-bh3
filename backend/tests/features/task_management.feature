# backend/tests/features/task_management.feature
Feature: Task Management System
  As a project manager
  I want to manage tasks on boards
  So that my team can collaborate effectively

  Scenario: Create a new board
    Given I am an authenticated user
    When I create a board named "MVP Development"
    Then the board should be created with default lists
    And an audit log entry should be created

  Scenario: Add a card to a list
    Given I have a board with a "To Do" list
    When I add a card titled "Setup monitoring" to the list
    Then the card should appear in the list
    And the card should have a unique position

  Scenario: Move card between lists
    Given I have a card in the "To Do" list
    When I move the card to "In Progress" list
    Then the card should be in the new list
    And the position should be updated
    And an activity log should be recorded
