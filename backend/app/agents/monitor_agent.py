from app.agents.base_agent import BaseAgent
from typing import Dict, Any, List


class MonitorAgent(BaseAgent):
    """Agent for analyzing incidents and suggesting solutions"""

    def simulate_response(self, prompt: str) -> str:
        """Simulate incident analysis"""
        if "root cause" in prompt.lower():
            return """
**Root Cause Analysis**:

**Incident Summary**: Service "API Gateway" experienced downtime for 15 minutes

**Timeline**:
- 14:30 UTC: First failed health check detected
- 14:31 UTC: Incident created after 3 consecutive failures
- 14:32 UTC: Alert sent to on-call engineer
- 14:45 UTC: Service recovered, incident auto-resolved

**Probable Root Causes**:
1. **Database Connection Pool Exhaustion** (High Probability)
   - Response times increased before failure
   - Error logs show connection timeout errors
   - Pattern matches previous incidents on 2024-01-15

2. **Memory Leak in Application** (Medium Probability)
   - Memory usage trending upward over past 24 hours
   - Service became unresponsive before crashing

3. **External API Dependency Failure** (Low Probability)
   - Third-party service status shows no issues
   - Unlikely to be the primary cause

**Recommendations**:
1. Increase database connection pool size from 10 to 25
2. Implement connection pool monitoring alerts
3. Add memory profiling to identify leak source
4. Set up automated restarts when memory exceeds 80%
5. Implement circuit breaker for external API calls

**Prevention**:
- Deploy connection pool monitoring
- Set up memory usage alerts at 70% threshold
- Schedule weekly memory leak analysis
- Implement graceful degradation for dependencies
"""
        elif "pattern" in prompt.lower():
            return """
**Incident Pattern Analysis**:

**Detected Patterns**:

1. **Time-based Pattern**:
   - 60% of incidents occur between 14:00-16:00 UTC
   - Correlates with peak traffic hours
   - Suggests capacity issues

2. **Frequency Pattern**:
   - Incidents increased 200% in past week
   - Similar error signatures across incidents
   - Indicates systemic issue requiring attention

3. **Cascade Pattern**:
   - API Gateway failures often preceded by database slowdowns
   - 5-minute warning window detected
   - Opportunity for proactive intervention

**Recommendations**:
- Scale infrastructure before peak hours
- Implement predictive alerting
- Add circuit breakers to prevent cascading failures
"""
        else:
            return """
**Incident Analysis & Runbook**:

**Issue**: Monitor "Production API" is down

**Immediate Actions**:
1. Check service health dashboard
2. Review recent deployments (rollback if needed)
3. Check database connectivity
4. Verify external dependencies status
5. Review application logs for errors

**Escalation**:
- If not resolved in 15 minutes, escalate to senior engineer
- If customer-facing, notify customer success team
- Update status page with current information

**Recovery Steps**:
1. Restart application service
2. Clear cache if applicable
3. Verify database connections restored
4. Monitor for 10 minutes to confirm stability
5. Mark incident as resolved

**Post-Incident**:
- Document findings in incident update
- Schedule post-mortem within 48 hours
- Implement preventive measures
- Update runbook with lessons learned
"""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze incident and provide insights"""
        incident_data = input_data.get("incident", {})
        analysis_type = input_data.get("type", "general")  # general, root_cause, pattern

        system_prompt = """You are a monitoring and incident analysis agent. Analyze
        incidents to identify root causes, suggest solutions, and provide actionable
        runbooks. Use historical data to detect patterns."""

        prompt = f"""Analyze this incident and provide {analysis_type} analysis:

        Incident: {incident_data.get('title', 'Unknown')}
        Description: {incident_data.get('description', 'No description')}
        Monitor: {incident_data.get('monitor_name', 'Unknown')}
        Duration: {incident_data.get('duration', 'Unknown')}
        """

        result = await self.call_llm(prompt, system_prompt)

        return {
            "analysis": result,
            "analysis_type": analysis_type,
            "incident_id": incident_data.get("incident_id"),
            "confidence": 0.85  # Simulated confidence score
        }

    async def suggest_monitors(self, services: List[str]) -> Dict[str, Any]:
        """Suggest monitors for given services"""
        suggestions = []

        for service in services:
            suggestions.append({
                "service": service,
                "monitors": [
                    {
                        "type": "https",
                        "url": f"https://{service}/health",
                        "interval": 60,
                        "name": f"{service} - Health Check"
                    },
                    {
                        "type": "https",
                        "url": f"https://{service}/api/status",
                        "interval": 120,
                        "name": f"{service} - API Status"
                    }
                ],
                "thresholds": {
                    "response_time_warning": 500,
                    "response_time_critical": 1000,
                    "failure_threshold": 3
                }
            })

        return {
            "suggestions": suggestions,
            "total": len(suggestions)
        }
