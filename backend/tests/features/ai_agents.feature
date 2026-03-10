Feature: AI-Powered Incident Analysis
  As an on-call engineer
  I want AI to analyze incidents automatically
  So that I can resolve issues faster

  Scenario: Analyze incident with simulated AI response
    Given I have an open incident for a failing monitor
    When I request a general incident analysis
    Then I should receive an analysis with actionable recommendations
    And the analysis should reference the incident

  @real_llm
  Scenario: Analyze incident with real Anthropic API
    Given I have an open incident for a failing monitor
    When I request a root cause analysis using the real LLM
    Then the response should contain a structured root cause analysis
