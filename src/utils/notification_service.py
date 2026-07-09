"""
Advanced notification service with multiple channels
"""

import asyncio
import json
import logging
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class NotificationMessage:
    """Notification message structure."""

    title: str
    message: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    recipients: List[str]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class NotificationChannel:
    """Base class for notification channels."""

    async def send(self, message: NotificationMessage) -> bool:
        """Send notification through this channel."""
        raise NotImplementedError


class EmailChannel(NotificationChannel):
    """Email notification channel."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send(self, message: NotificationMessage) -> bool:
        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = ", ".join(message.recipients)
            msg["Subject"] = f"[{message.severity.upper()}] {message.title}"

            body = f"""
{message.message}

Severity: {message.severity}
Timestamp: {message.timestamp.isoformat()}

{f"Metadata: {json.dumps(message.metadata, indent=2)}" if message.metadata else ""}
            """
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent to {len(message.recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


class WebhookChannel(NotificationChannel):
    """Webhook notification channel."""

    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}

    async def send(self, message: NotificationMessage) -> bool:
        try:
            payload = {
                "title": message.title,
                "message": message.message,
                "severity": message.severity,
                "recipients": message.recipients,
                "metadata": message.metadata,
                "timestamp": message.timestamp.isoformat(),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={**self.headers, "Content-Type": "application/json"},
                ) as response:
                    if response.status in (200, 201, 202):
                        logger.info(f"Webhook sent successfully to {self.webhook_url}")
                        return True
                    else:
                        logger.error(f"Webhook failed with status {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False


class SlackChannel(NotificationChannel):
    """Slack notification channel."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, message: NotificationMessage) -> bool:
        try:
            # Map severity to Slack colors
            color_map = {
                "low": "good",
                "medium": "warning",
                "high": "danger",
                "critical": "danger",
            }

            payload = {
                "attachments": [
                    {
                        "title": message.title,
                        "text": message.message,
                        "color": color_map.get(message.severity, "warning"),
                        "fields": [
                            {
                                "title": "Severity",
                                "value": message.severity,
                                "short": True,
                            },
                            {
                                "title": "Timestamp",
                                "value": message.timestamp.isoformat(),
                                "short": True,
                            },
                        ],
                    }
                ]
            }

            if message.metadata:
                payload["attachments"][0]["fields"].extend(
                    [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in message.metadata.items()
                    ]
                )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 200:
                        logger.info("Slack notification sent successfully")
                        return True
                    else:
                        logger.error(
                            f"Slack notification failed with status {response.status}"
                        )
                        return False

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class NotificationService:
    """Main notification service with multiple channels."""

    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.templates: Dict[str, str] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None

    def add_channel(self, name: str, channel: NotificationChannel):
        """Add a notification channel."""
        self.channels[name] = channel
        logger.info(f"Added notification channel: {name}")

    def add_template(self, name: str, template: str):
        """Add a notification template."""
        self.templates[name] = template

    def format_template(self, template_name: str, **kwargs) -> str:
        """Format a notification template."""
        if template_name not in self.templates:
            return kwargs.get("message", "No template found")

        try:
            return self.templates[template_name].format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return self.templates[template_name]

    async def send_notification(
        self, message: NotificationMessage, channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """Send notification through specified channels."""
        results = {}

        channels_to_use = channels or list(self.channels.keys())

        for channel_name in channels_to_use:
            if channel_name in self.channels:
                success = await self.channels[channel_name].send(message)
                results[channel_name] = success
            else:
                logger.warning(f"Unknown channel: {channel_name}")
                results[channel_name] = False

        return results

    async def queue_notification(
        self, message: NotificationMessage, channels: Optional[List[str]] = None
    ):
        """Queue notification for async processing."""
        await self._queue.put((message, channels))

    async def start_processing(self):
        """Start the notification processing task."""
        if self._processing_task is None:
            self._processing_task = asyncio.create_task(self._process_queue())

    async def stop_processing(self):
        """Stop the notification processing task."""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

    async def _process_queue(self):
        """Process queued notifications."""
        while True:
            try:
                message, channels = await self._queue.get()
                await self.send_notification(message, channels)
                self._queue.task_done()
            except Exception as e:
                logger.error(f"Error processing notification: {e}")

    async def send_alert(
        self,
        machine_id: str,
        alert_type: str,
        severity: str,
        details: Dict[str, Any],
        recipients: List[str],
    ):
        """Send a machine alert notification."""
        title = f"Machine Alert: {machine_id}"
        message = f"""
Alert Type: {alert_type}
Machine: {machine_id}
Severity: {severity}

Details:
{json.dumps(details, indent=2)}
        """

        notification = NotificationMessage(
            title=title,
            message=message.strip(),
            severity=severity,
            recipients=recipients,
            metadata={"machine_id": machine_id, "alert_type": alert_type, **details},
        )

        # Send through all channels
        await self.send_notification(notification)

    def get_channel_status(self) -> Dict[str, bool]:
        """Get status of all channels."""
        # Simple implementation - in real world, test actual connectivity
        return {name: True for name in self.channels.keys()}


# Global notification service instance
notification_service = NotificationService()

# Add default templates
notification_service.add_template(
    "machine_alert",
    "🚨 Machine {machine_id} Alert\nType: {alert_type}\nSeverity: {severity}\nDetails: {details}",
)

notification_service.add_template(
    "maintenance_due",
    "🔧 Maintenance Due for {machine_id}\nNext maintenance: {next_date}\nPriority: {priority}",
)
