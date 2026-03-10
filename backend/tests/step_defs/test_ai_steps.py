"""BDD steps for ai_agents.feature — all step functions are sync (TestClient)."""
from unittest.mock import AsyncMock, patch
from pytest_bdd import scenarios, given, when, then

scenarios("../features/ai_agents.feature")


# ── Shared Given ─────────────────────────────────────────────────────────────

@given("I have an open incident for a failing monitor", target_fixture="incident_ctx")
def open_incident_for_failing_monitor(client, headers):
    # 1. Create a monitor
    r = client.post(
        "/api/monitors",
        json={
            "name": "AI Test Monitor",
            "url": "https://failing.example.com/health",
            "interval": 60,
            "type": "https",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    monitor = r.json()
    monitor_id = monitor["id"]

    # 2. Drive the monitor DOWN via 3 consecutive failing checks
    with patch(
        "httpx.AsyncClient.get",
        new_callable=AsyncMock,
        side_effect=Exception("Connection refused"),
    ):
        for _ in range(3):
            r = client.post(f"/api/monitors/{monitor_id}/check", headers=headers)
            assert r.status_code == 200, r.text

    # 3. Retrieve the created incident
    r = client.get(f"/api/incidents?monitor_id={monitor_id}", headers=headers)
    assert r.status_code == 200, r.text
    incidents = r.json()
    assert len(incidents) >= 1, f"Expected at least 1 incident, got: {incidents}"

    return {"monitor": monitor, "incident": incidents[0], "headers": headers}


# ── Scenario 1: Simulated AI response ────────────────────────────────────────

@when("I request a general incident analysis", target_fixture="analysis_result")
def request_general_analysis(client, headers, incident_ctx):
    incident_id = incident_ctx["incident"]["id"]
    r = client.post(
        "/api/agents/monitor",
        json={
            "incident_id": incident_id,
            "description": "Service is returning errors",
            "analysis_type": "general",
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


@then("I should receive an analysis with actionable recommendations")
def analysis_has_actionable_recommendations(analysis_result):
    analysis_text = analysis_result["result"]["analysis"]
    assert len(analysis_text) > 50, (
        f"Analysis too short ({len(analysis_text)} chars): {analysis_text}"
    )
    action_keywords = ["action", "check", "restart", "review", "monitor", "step"]
    assert any(kw in analysis_text.lower() for kw in action_keywords), (
        f"No actionable keywords found in analysis: {analysis_text}"
    )


@then("the analysis should reference the incident")
def analysis_references_incident(analysis_result, incident_ctx):
    assert str(analysis_result["incident_id"]) == str(incident_ctx["incident"]["id"]), (
        f"incident_id mismatch: {analysis_result['incident_id']} != {incident_ctx['incident']['id']}"
    )


# ── Scenario 2: Real LLM (skipped when ANTHROPIC_API_KEY not set) ─────────────

@when("I request a root cause analysis using the real LLM", target_fixture="analysis_result")
def request_root_cause_analysis(client, headers, incident_ctx):
    incident_id = incident_ctx["incident"]["id"]
    r = client.post(
        "/api/agents/monitor",
        json={
            "incident_id": incident_id,
            "description": "Service is returning errors",
            "analysis_type": "root_cause",
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


@then("the response should contain a structured root cause analysis")
def response_has_structured_root_cause(analysis_result):
    analysis_text = analysis_result["result"]["analysis"]
    assert len(analysis_text) >= 100, (
        f"Analysis too short ({len(analysis_text)} chars): {analysis_text}"
    )
    assert any(kw in analysis_text.lower() for kw in ["root cause", "analysis"]), (
        f"Expected 'root cause' or 'analysis' in response: {analysis_text}"
    )
