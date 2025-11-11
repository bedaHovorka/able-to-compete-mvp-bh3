from app.models import Incident, Monitor
from app.utils.logger import logger
from app.config import settings
from typing import Dict, List
from datetime import datetime, timedelta
import asyncio
import httpx


class AlertService:
    def __init__(self):
        self.last_alert_times = {}
        self.cooldown_period = settings.ALERT_COOLDOWN

    async def send_alert(self, incident: Incident, monitor: Monitor, channels: List[str] = None):
        """Send alert through multiple channels"""
        if channels is None:
            channels = ["email", "webhook"]

        # Check cooldown
        incident_key = str(incident.id)
        last_alert_time = self.last_alert_times.get(incident_key)

        if last_alert_time:
            time_since_last_alert = (datetime.utcnow() - last_alert_time).total_seconds()
            if time_since_last_alert < self.cooldown_period:
                logger.info(f"Alert for incident {incident.id} is in cooldown period")
                return

        # Update last alert time
        self.last_alert_times[incident_key] = datetime.utcnow()

        # Send alerts
        for channel in channels:
            try:
                if channel == "email":
                    await self._send_email_alert(incident, monitor)
                elif channel == "webhook":
                    await self._send_webhook_alert(incident, monitor)
                elif channel == "sms":
                    await self._send_sms_alert(incident, monitor)
            except Exception as e:
                logger.error(f"Failed to send {channel} alert for incident {incident.id}: {e}")

    async def _send_email_alert(self, incident: Incident, monitor: Monitor):
        """Simulate sending email alert"""
        logger.info(f"[EMAIL] Alert for {incident.title}")
        logger.info(f"  Monitor: {monitor.name} ({monitor.url})")
        logger.info(f"  Severity: {incident.severity}")
        logger.info(f"  Description: {incident.description}")

    async def _send_webhook_alert(self, incident: Incident, monitor: Monitor):
        """Send webhook alert"""
        webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"  # Configure in production

        payload = {
            "text": f"INCIDENT: {incident.title}",
            "attachments": [
                {
                    "color": "danger" if incident.severity == "critical" else "warning",
                    "fields": [
                        {"title": "Monitor", "value": monitor.name, "short": True},
                        {"title": "URL", "value": monitor.url, "short": True},
                        {"title": "Severity", "value": incident.severity.value, "short": True},
                        {"title": "Status", "value": incident.status.value, "short": True},
                        {"title": "Description", "value": incident.description}
                    ],
                    "footer": "AbleToCompete Monitoring",
                    "ts": int(incident.started_at.timestamp())
                }
            ]
        }

        logger.info(f"[WEBHOOK] Alert sent for incident {incident.id}")
        # Uncomment to actually send webhook:
        # async with httpx.AsyncClient() as client:
        #     await client.post(webhook_url, json=payload)

    async def _send_sms_alert(self, incident: Incident, monitor: Monitor):
        """Simulate sending SMS alert"""
        logger.info(f"[SMS] Alert for {incident.title}")
        logger.info(f"  Monitor: {monitor.name}")
        logger.info(f"  Severity: {incident.severity}")

    def format_alert_message(self, incident: Incident, monitor: Monitor, template: str = "default") -> str:
        """Format alert message with template"""
        templates = {
            "default": f"""
🚨 INCIDENT ALERT

Monitor: {monitor.name}
URL: {monitor.url}
Status: {incident.status.value}
Severity: {incident.severity.value}

Description:
{incident.description}

Started: {incident.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
            """,
            "short": f"🚨 {monitor.name} is {incident.status.value} - {incident.severity.value} severity"
        }

        return templates.get(template, templates["default"])

    async def clear_cooldown(self, incident_id: str):
        """Clear cooldown for an incident"""
        if incident_id in self.last_alert_times:
            del self.last_alert_times[incident_id]
            logger.info(f"Cleared cooldown for incident {incident_id}")
