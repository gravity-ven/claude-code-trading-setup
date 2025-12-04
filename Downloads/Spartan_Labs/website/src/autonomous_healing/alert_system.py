#!/usr/bin/env python3
"""
SPARTAN LABS - ALERT & NOTIFICATION SYSTEM
===========================================

Multi-channel alert system that only triggers when autonomous healing fails.

Alert Channels:
1. Visual indicators on website (real-time health bars)
2. Browser notifications (degraded mode)
3. Email alerts (critical failures)
4. SMS alerts (system-wide outages)
5. Dashboard health status

Alert Levels:
- INFO: Autonomous fix successful (no user notification)
- WARNING: Degraded mode (visual indicator only)
- ERROR: Autonomous fix failed (email notification)
- CRITICAL: System failure (email + SMS)

Author: Spartan Labs
Version: 1.0.0
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from error_monitor import ErrorEvent, DataSource, HealthStatus, EndpointHealth
from healing_engine import HealingResult

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"           # No user notification
    WARNING = "warning"     # Visual indicator
    ERROR = "error"         # Email notification
    CRITICAL = "critical"   # Email + SMS


class AlertChannel(Enum):
    """Alert delivery channels."""
    WEB_UI = "web_ui"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"


@dataclass
class Alert:
    """Alert message structure."""
    id: str
    timestamp: datetime
    level: AlertLevel
    title: str
    message: str
    source: DataSource
    endpoint: str
    health_status: HealthStatus
    error_rate: float
    affected_endpoints: List[str]
    healing_attempted: bool
    healing_successful: bool
    recommended_actions: List[str]
    auto_resolve: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'source': self.source.value,
            'endpoint': self.endpoint,
            'health_status': self.health_status.value,
            'error_rate': round(self.error_rate, 2),
            'affected_endpoints': self.affected_endpoints,
            'healing_attempted': self.healing_attempted,
            'healing_successful': self.healing_successful,
            'recommended_actions': self.recommended_actions,
            'auto_resolve': self.auto_resolve,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class WebUINotifier:
    """
    Real-time web UI notifications via WebSocket.

    Displays:
    - Color-coded health bars for each data source
    - Degraded mode banners
    - Autonomous healing status
    - Recovery notifications
    """

    def __init__(self, websocket_url: str = "ws://localhost:8888/ws/health"):
        self.websocket_url = websocket_url
        self.active_alerts: Dict[str, Alert] = {}

    async def send_health_update(self, health_data: List[EndpointHealth]):
        """Send real-time health update to web UI."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.websocket_url) as ws:
                    payload = {
                        'type': 'health_update',
                        'timestamp': datetime.now().isoformat(),
                        'endpoints': [h.to_dict() for h in health_data]
                    }

                    await ws.send_json(payload)
                    logger.debug("📊 Health update sent to web UI")
        except Exception as e:
            logger.warning(f"Failed to send web UI update: {e}")

    async def send_alert(self, alert: Alert):
        """Send alert to web UI."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.websocket_url) as ws:
                    payload = {
                        'type': 'alert',
                        'alert': alert.to_dict()
                    }

                    await ws.send_json(payload)

                    # Track active alert
                    self.active_alerts[alert.id] = alert

                    logger.info(f"🔔 Alert sent to web UI: {alert.title}")
        except Exception as e:
            logger.warning(f"Failed to send web UI alert: {e}")

    async def resolve_alert(self, alert_id: str):
        """Mark alert as resolved in web UI."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved_at = datetime.now()

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(self.websocket_url) as ws:
                        payload = {
                            'type': 'alert_resolved',
                            'alert_id': alert_id,
                            'resolved_at': alert.resolved_at.isoformat()
                        }

                        await ws.send_json(payload)
                        del self.active_alerts[alert_id]

                        logger.info(f"✅ Alert resolved in web UI: {alert.title}")
            except Exception as e:
                logger.warning(f"Failed to resolve web UI alert: {e}")

    def generate_health_bar_html(self, health: EndpointHealth) -> str:
        """Generate HTML for health status bar."""
        color_map = {
            HealthStatus.HEALTHY: "#00ff00",    # Green
            HealthStatus.DEGRADED: "#ffff00",   # Yellow
            HealthStatus.CRITICAL: "#ff9900",   # Orange
            HealthStatus.FAILED: "#ff0000",     # Red
        }

        color = color_map[health.status]
        uptime = health.uptime_percentage

        html = f"""
        <div class="health-bar" data-source="{health.source.value}" data-endpoint="{health.endpoint}">
            <div class="health-bar-header">
                <span class="source-name">{health.source.value}</span>
                <span class="endpoint-name">{health.endpoint}</span>
                <span class="status-badge" style="background-color: {color};">
                    {health.status.value.upper()}
                </span>
            </div>
            <div class="health-bar-meter">
                <div class="meter-fill" style="width: {uptime}%; background-color: {color};"></div>
            </div>
            <div class="health-bar-stats">
                <span>Uptime: {uptime:.1f}%</span>
                <span>Error Rate: {health.error_rate*100:.1f}%</span>
                <span>Avg Response: {health.avg_response_time:.2f}s</span>
            </div>
        </div>
        """
        return html


class EmailNotifier:
    """
    Email notification system for errors and critical alerts.

    Only sends emails when:
    - Autonomous healing fails
    - Error persists for > 5 minutes
    - Critical system failure
    """

    def __init__(self, smtp_config: Dict[str, str], recipients: List[str]):
        self.smtp_config = smtp_config
        self.recipients = recipients
        self.sent_alerts: Dict[str, datetime] = {}  # Prevent spam

    async def send_alert(self, alert: Alert):
        """Send email alert."""
        # Rate limiting: Don't send same alert more than once per hour
        if alert.id in self.sent_alerts:
            last_sent = self.sent_alerts[alert.id]
            if datetime.now() - last_sent < timedelta(hours=1):
                logger.debug(f"Skipping duplicate email alert: {alert.id}")
                return

        try:
            # Compose email
            subject = f"[{alert.level.value.upper()}] {alert.title}"
            body = self._compose_email_body(alert)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(self.recipients)

            # Plain text and HTML versions
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(self._compose_email_html(alert), 'html')

            msg.attach(text_part)
            msg.attach(html_part)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)

            self.sent_alerts[alert.id] = datetime.now()
            logger.info(f"📧 Email alert sent: {alert.title}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def _compose_email_body(self, alert: Alert) -> str:
        """Compose plain text email body."""
        body = f"""
SPARTAN LABS - AUTONOMOUS HEALING SYSTEM ALERT

Level: {alert.level.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

{alert.title}

{alert.message}

Data Source: {alert.source.value}
Endpoint: {alert.endpoint}
Health Status: {alert.health_status.value}
Error Rate: {alert.error_rate*100:.1f}%

Affected Endpoints: {len(alert.affected_endpoints)}
{chr(10).join(f"  - {ep}" for ep in alert.affected_endpoints)}

Autonomous Healing:
- Attempted: {'Yes' if alert.healing_attempted else 'No'}
- Successful: {'Yes' if alert.healing_successful else 'No'}

Recommended Actions:
{chr(10).join(f"{i+1}. {action}" for i, action in enumerate(alert.recommended_actions))}

Dashboard: http://localhost:8888/health-dashboard
        """
        return body

    def _compose_email_html(self, alert: Alert) -> str:
        """Compose HTML email body."""
        color_map = {
            AlertLevel.INFO: "#3498db",
            AlertLevel.WARNING: "#f39c12",
            AlertLevel.ERROR: "#e74c3c",
            AlertLevel.CRITICAL: "#c0392b",
        }

        color = color_map[alert.level]

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .alert-box {{ border: 3px solid {color}; padding: 20px; border-radius: 8px; }}
                .alert-header {{ background-color: {color}; color: white; padding: 10px; margin: -20px -20px 20px -20px; }}
                .alert-level {{ font-size: 24px; font-weight: bold; }}
                .section {{ margin: 15px 0; }}
                .section-title {{ font-weight: bold; color: #333; }}
                .metric {{ background-color: #f8f9fa; padding: 8px; margin: 5px 0; border-radius: 4px; }}
                .actions {{ background-color: #e8f5e9; padding: 15px; border-left: 4px solid #4caf50; }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <div class="alert-header">
                    <div class="alert-level">{alert.level.value.upper()} ALERT</div>
                    <div>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
                </div>

                <h2>{alert.title}</h2>
                <p>{alert.message}</p>

                <div class="section">
                    <div class="section-title">Data Source Details</div>
                    <div class="metric">Source: {alert.source.value}</div>
                    <div class="metric">Endpoint: {alert.endpoint}</div>
                    <div class="metric">Health Status: {alert.health_status.value}</div>
                    <div class="metric">Error Rate: {alert.error_rate*100:.1f}%</div>
                </div>

                <div class="section">
                    <div class="section-title">Affected Endpoints ({len(alert.affected_endpoints)})</div>
                    {"".join(f'<div class="metric">{ep}</div>' for ep in alert.affected_endpoints)}
                </div>

                <div class="section">
                    <div class="section-title">Autonomous Healing Status</div>
                    <div class="metric">Healing Attempted: {'✅ Yes' if alert.healing_attempted else '❌ No'}</div>
                    <div class="metric">Healing Successful: {'✅ Yes' if alert.healing_successful else '❌ No'}</div>
                </div>

                <div class="actions">
                    <div class="section-title">Recommended Actions</div>
                    {"".join(f'<div>{i+1}. {action}</div>' for i, action in enumerate(alert.recommended_actions))}
                </div>

                <p style="margin-top: 20px;">
                    <a href="http://localhost:8888/health-dashboard" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                        View Health Dashboard
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        return html


class SMSNotifier:
    """
    SMS notification system for critical failures.

    Only sends SMS for CRITICAL level alerts (system-wide outages).
    """

    def __init__(self, twilio_config: Dict[str, str], recipients: List[str]):
        self.twilio_config = twilio_config
        self.recipients = recipients
        self.sent_alerts: Dict[str, datetime] = {}

    async def send_alert(self, alert: Alert):
        """Send SMS alert (CRITICAL only)."""
        if alert.level != AlertLevel.CRITICAL:
            return  # SMS only for critical

        # Rate limiting: Max 1 SMS per hour
        if alert.id in self.sent_alerts:
            last_sent = self.sent_alerts[alert.id]
            if datetime.now() - last_sent < timedelta(hours=1):
                return

        try:
            # SMS message (160 chars max)
            message = f"SPARTAN CRITICAL: {alert.title}. {alert.source.value} {alert.health_status.value}. Check dashboard."

            # Twilio API call would go here
            # For now, just log
            logger.info(f"📱 SMS alert would be sent: {message}")

            self.sent_alerts[alert.id] = datetime.now()

        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")


class AlertManager:
    """
    Central alert management system.

    Responsibilities:
    - Create alerts from error events
    - Route alerts to appropriate channels
    - Track alert lifecycle
    - Auto-resolve alerts when healing succeeds
    """

    def __init__(
        self,
        smtp_config: Optional[Dict[str, str]] = None,
        twilio_config: Optional[Dict[str, str]] = None,
        email_recipients: List[str] = None,
        sms_recipients: List[str] = None
    ):
        self.web_notifier = WebUINotifier()

        self.email_notifier = None
        if smtp_config and email_recipients:
            self.email_notifier = EmailNotifier(smtp_config, email_recipients)

        self.sms_notifier = None
        if twilio_config and sms_recipients:
            self.sms_notifier = SMSNotifier(twilio_config, sms_recipients)

        self.active_alerts: Dict[str, Alert] = {}
        self.alert_counter = 0

    async def create_alert_from_error(
        self,
        error: ErrorEvent,
        health: EndpointHealth,
        healing_result: Optional[HealingResult] = None
    ) -> Alert:
        """Create alert from error event."""
        self.alert_counter += 1

        # Determine alert level
        if healing_result and healing_result.success:
            level = AlertLevel.INFO  # Healed - no user notification
        elif health.status == HealthStatus.FAILED:
            level = AlertLevel.CRITICAL
        elif health.status == HealthStatus.CRITICAL:
            level = AlertLevel.ERROR
        elif health.status == HealthStatus.DEGRADED:
            level = AlertLevel.WARNING
        else:
            level = AlertLevel.INFO

        # Generate title
        title = f"{error.source.value} - {health.status.value.title()}"

        # Generate message
        if healing_result and healing_result.success:
            message = f"Error detected and automatically healed using {healing_result.strategy_used}."
        else:
            message = f"Error persisting on {error.endpoint}. {error.error_message}"

        # Recommended actions
        actions = []
        if error.error_type.name == "RATE_LIMIT":
            actions = [
                "System automatically switched to fallback data source",
                "Monitoring rate limit recovery",
                "Manual action: Consider upgrading API plan"
            ]
        elif error.error_type.name == "TIMEOUT":
            actions = [
                "System using cached data",
                "Retrying with reduced request size",
                "Manual action: Check upstream API status"
            ]
        elif error.error_type.name == "AUTH_ERROR":
            actions = [
                "System attempting API key rotation",
                "Manual action required: Verify API credentials",
                "Check API key expiration date"
            ]

        alert = Alert(
            id=f"alert_{self.alert_counter}_{int(datetime.now().timestamp())}",
            timestamp=datetime.now(),
            level=level,
            title=title,
            message=message,
            source=error.source,
            endpoint=error.endpoint,
            health_status=health.status,
            error_rate=health.error_rate,
            affected_endpoints=[error.endpoint],
            healing_attempted=healing_result is not None,
            healing_successful=healing_result.success if healing_result else False,
            recommended_actions=actions,
            auto_resolve=healing_result and healing_result.success
        )

        return alert

    async def dispatch_alert(self, alert: Alert):
        """Dispatch alert to appropriate channels."""
        logger.info(f"🚨 Dispatching {alert.level.value} alert: {alert.title}")

        # Always update web UI
        await self.web_notifier.send_alert(alert)

        # Email for ERROR and CRITICAL
        if alert.level in (AlertLevel.ERROR, AlertLevel.CRITICAL):
            if self.email_notifier:
                await self.email_notifier.send_alert(alert)

        # SMS for CRITICAL only
        if alert.level == AlertLevel.CRITICAL:
            if self.sms_notifier:
                await self.sms_notifier.send_alert(alert)

        # Track alert
        self.active_alerts[alert.id] = alert

        # Auto-resolve if healing successful
        if alert.auto_resolve:
            await asyncio.sleep(5)  # Wait 5 seconds
            await self.resolve_alert(alert.id)

    async def resolve_alert(self, alert_id: str):
        """Resolve alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]

            # Notify web UI
            await self.web_notifier.resolve_alert(alert_id)

            # Remove from active alerts
            del self.active_alerts[alert_id]

            logger.info(f"✅ Alert resolved: {alert.title}")

    async def send_health_update(self, health_data: List[EndpointHealth]):
        """Send periodic health update to web UI."""
        await self.web_notifier.send_health_update(health_data)

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())


if __name__ == "__main__":
    # Test alert system
    async def test():
        # SMTP configuration (example)
        smtp_config = {
            'host': 'smtp.gmail.com',
            'port': 587,
            'username': 'alerts@spartanlabs.com',
            'password': 'secure_password',
            'from_email': 'alerts@spartanlabs.com'
        }

        alert_manager = AlertManager(
            smtp_config=smtp_config,
            email_recipients=['admin@spartanlabs.com']
        )

        # Simulate error
        from error_monitor import ErrorEvent, ErrorType
        error = ErrorEvent(
            timestamp=datetime.now(),
            source=DataSource.YAHOO_FINANCE,
            endpoint='/quote/AAPL',
            error_type=ErrorType.RATE_LIMIT,
            error_message="Rate limit exceeded",
            response_time=2.5,
            http_status_code=429,
            request_params={},
            retry_count=0,
            fixed_automatically=False,
            fix_method=None
        )

        health = EndpointHealth(
            source=DataSource.YAHOO_FINANCE,
            endpoint='/quote/AAPL',
            status=HealthStatus.DEGRADED,
            total_requests=100,
            failed_requests=10,
            error_rate=0.10,
            avg_response_time=2.5,
            last_success=datetime.now() - timedelta(minutes=5),
            last_failure=datetime.now(),
            consecutive_failures=3,
            uptime_percentage=90.0
        )

        alert = await alert_manager.create_alert_from_error(error, health)
        await alert_manager.dispatch_alert(alert)

        print(f"Alert dispatched: {alert.title}")

    asyncio.run(test())
