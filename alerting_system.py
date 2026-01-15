"""
Alerting System Module

This module implements comprehensive alerting system for monitoring and notifying
about system events, performance issues, and operational alerts.
"""

import asyncio
import json
import logging
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional

import aiohttp
from abc import ABC, abstractmethod

from utils.logging_config import get_logger

from dataclasses import dataclass, field

logger = get_logger(__name__)


@dataclass
class Event:
    """Represents a single raw event in the system."""
    event_type: str  # e.g., "cpu.load", "app.error_rate"
    value: Any
    source: str = "default"
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


class Alert:
    """Alert data structure, generated when a Rule is triggered."""
    
    def __init__(
        self,
        alert_id: str,
        title: str,
        message: str,
        severity: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.alert_id = alert_id
        self.title = title
        self.message = message
        self.severity = severity  # info, warning, critical
        self.source = source
        self.timestamp = datetime.now()
        self.acknowledged = False
        self.acknowledged_by = None
        self.acknowledged_at = None
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "metadata": self.metadata
        }


# --- Notification Channels (Strategy Pattern) ---

class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_enabled = config.get("enabled", False)

    @abstractmethod
    async def send(self, alert: Alert):
        """Send a notification for the given alert."""
        pass

class EmailChannel(NotificationChannel):
    """Sends alerts via email."""
    async def send(self, alert: Alert):
        if not self.is_enabled:
            return

        try:
            msg = MimeMultipart()
            msg['From'] = self.config["from_address"]
            msg['To'] = ', '.join(self.config["to_addresses"])
            msg['Subject'] = f"[{alert.severity.upper()}] {alert.title}"

            body = f"""
Alert Details:
- ID: {alert.alert_id}
- Title: {alert.title}
- Message: {alert.message}
- Severity: {alert.severity}
- Source: {alert.source}
- Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Metadata: {json.dumps(alert.metadata, indent=2)}
            """
            msg.attach(MimeText(body, 'plain'))

            # Note: smtplib is blocking. In a real-world high-performance
            # system, this would be run in a thread pool executor.
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, self._send_smtp_email, msg
            )
            logger.info(f"Email alert sent for {alert.alert_id}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def _send_smtp_email(self, msg: MIMEMultipart):
        """Synchronous part of sending email."""
        server = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
        server.starttls()
        server.login(self.config["username"], self.config["password"])
        text = msg.as_string()
        server.sendmail(self.config["from_address"], self.config["to_addresses"], text)
        server.quit()

class SlackChannel(NotificationChannel):
    """Sends alerts via Slack webhook."""
    async def send(self, alert: Alert):
        if not self.is_enabled:
            return

        try:
            payload = {
                "channel": self.config["channel"],
                "username": "IoT Platform Alert",
                "icon_emoji": ":warning:" if alert.severity == "warning" else ":rotating_light:",
                "attachments": [{
                    "color": "danger" if alert.severity == "critical" else "warning",
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {"title": "Severity", "value": alert.severity, "short": True},
                        {"title": "Source", "value": alert.source, "short": True},
                        {"title": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                    ]
                }]
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config["webhook_url"], json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent for {alert.alert_id}")
                    else:
                        logger.error(f"Slack alert failed: {response.status} - {await response.text()}")

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

class WebhookChannel(NotificationChannel):
    """Sends alerts via a generic webhook."""
    async def send(self, alert: Alert):
        if not self.is_enabled:
            return

        try:
            payload = alert.to_dict()
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config["url"],
                    json=payload,
                    headers=self.config.get("headers", {})
                ) as response:
                    if response.status < 300:
                        logger.info(f"Webhook alert sent for {alert.alert_id}")
                    else:
                        logger.error(f"Webhook alert failed: {response.status} - {await response.text()}")

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")


class Rule:
    """Defines a condition for triggering an alert."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        condition: str, # e.g., "event.value > 90 and event.tags.get('env') == 'prod'"
        for_duration: timedelta,
        cooldown: timedelta,
        severity: str,
        message_template: str
    ):
        self.rule_id = rule_id
        self.name = name
        self.condition = condition
        self.for_duration = for_duration
        self.cooldown = cooldown
        self.severity = severity
        self.message_template = message_template
        self.escalation_policy: Optional[EscalationPolicy] = None # Added for escalation

        # State
        self.is_breached = False
        self.breach_start_time: Optional[datetime] = None
        self.last_triggered_time: Optional[datetime] = None
        self.snoozed_until: Optional[datetime] = None

    def evaluate(self, event: Event) -> bool:
        """Evaluate the rule condition against an event."""
        try:
            # Provide event in the local scope for eval
            return eval(self.condition, {"__builtins__": {}}, {"event": event})
        except Exception as e:
            logger.error(f"Error evaluating rule '{self.rule_id}': {e}")
            return False

    def update_state(self, is_condition_met: bool):
        """Update the breach state of the rule."""
        now = datetime.now()

        if is_condition_met:
            if not self.is_breached:
                self.is_breached = True
                self.breach_start_time = now
        else:
            self.is_breached = False
            self.breach_start_time = None

    def should_trigger(self) -> bool:
        """Check if the rule should trigger an alert."""
        now = datetime.now()

        # Check if snoozed
        if self.snoozed_until and now < self.snoozed_until:
            return False

        # Check cooldown
        if self.last_triggered_time and (now - self.last_triggered_time) < self.cooldown:
            return False

        # Check if breach duration is met
        if self.is_breached and self.breach_start_time:
            if (now - self.breach_start_time) >= self.for_duration:
                return True

        return False

    def reset_after_trigger(self):
        """Reset state after an alert has been triggered."""
        self.last_triggered_time = datetime.now()
        self.is_breached = False
        self.breach_start_time = None


@dataclass
class EscalationStep:
    """A single step in an escalation policy."""
    delay: timedelta
    channels: List[str] # Names of channels to notify

@dataclass
class EscalationPolicy:
    """Defines a sequence of escalation steps."""
    policy_id: str
    steps: List[EscalationStep]


class AlertingSystem:
    """Comprehensive alerting system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.rules: Dict[str, Rule] = {}
        self.escalation_policies: Dict[str, EscalationPolicy] = {}
        self.notification_channels: Dict[str, NotificationChannel] = self._setup_channels()
        self.running = False
        self.history_file_path = self.config.get("history_file_path", "alert_history.json")
        self._load_history()
        
    def _default_config(self) -> Dict[str, Any]:
        """Default alerting configuration."""
        return {
            "history_file_path": "alert_history.json",
            "channels": {
                "email": {"enabled": False},
                "slack": {"enabled": False},
                "webhook": {"enabled": False}
            },
            "thresholds": {
                "cpu_usage": 80.0,
                "memory_usage": 85.0
            }
        }

    def _setup_channels(self) -> Dict[str, NotificationChannel]:
        """Initialize notification channels based on config."""
        channels = {}
        channel_configs = self.config.get("channels", {})

        if "email" in channel_configs:
            channels["email"] = EmailChannel(channel_configs["email"])
        if "slack" in channel_configs:
            channels["slack"] = SlackChannel(channel_configs["slack"])
        if "webhook" in channel_configs:
            channels["webhook"] = WebhookChannel(channel_configs["webhook"])

        logger.info(f"Initialized {len(channels)} notification channels.")
        return channels
    
    async def start(self):
        """Start alerting system."""
        self.running = True
        logger.info("Alerting system started")
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop(self):
        """Stop alerting system."""
        self.running = False
        logger.info("Alerting system stopped")
    
    def add_rule(self, rule: Rule):
        """Add a new rule to the system."""
        self.rules[rule.rule_id] = rule
        logger.info(f"Rule '{rule.name}' added.")

    async def process_event(self, event: Event):
        """Process an incoming event and evaluate rules."""
        logger.debug(f"Processing event: {event.event_type} = {event.value}")
        for rule in self.rules.values():
            # Check if the rule is relevant for this event type
            # (simple optimization to avoid string evaluation for all events)
            if event.event_type not in rule.condition:
                continue

            is_condition_met = rule.evaluate(event)
            rule.update_state(is_condition_met)
            
            if rule.should_trigger():
                logger.info(f"Rule '{rule.name}' triggered for event {event.event_type}.")

                # Format the message
                message = rule.message_template.format(
                    value=event.value,
                    source=event.source,
                    tags=event.tags
                )

                await self.create_alert(
                    title=rule.name,
                    message=message,
                    severity=rule.severity,
                    source=event.source,
                    metadata={
                        "rule_id": rule.rule_id,
                        "triggering_event": event.__dict__
                    }
                )
                rule.reset_after_trigger()

    async def _monitoring_loop(self):
        """Continuous monitoring loop for internal metrics and alert cleanup."""
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not installed. System metric monitoring is disabled.")
            psutil = None

        while self.running:
            if psutil:
                # Generate system metric events
                await self.process_event(Event(
                    event_type="cpu.usage",
                    value=psutil.cpu_percent(interval=1),
                    source="system_monitor"
                ))
                await self.process_event(Event(
                    event_type="memory.usage",
                    value=psutil.virtual_memory().percent,
                    source="system_monitor"
                ))

            await self._cleanup_old_alerts()
            await self._process_escalations()
            await asyncio.sleep(30) # Check more frequently for escalations
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts and persist history."""
        cutoff = datetime.now() - timedelta(hours=24)
        
        # Move old alerts to history
        old_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.timestamp < cutoff
        ]
        
        moved_count = 0
        for alert_id in old_alerts:
            alert = self.active_alerts.pop(alert_id)
            self.alert_history.append(alert)
            moved_count += 1

        if moved_count > 0:
            logger.info(f"Moved {moved_count} old alerts to history.")
            self._save_history()
    
    async def create_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create and process a new alert."""
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_alerts)}"
        
        alert = Alert(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=severity,
            source=source,
            metadata=metadata
        )
        
        # Check for duplicate alerts
        if self._is_duplicate_alert(alert):
            logger.debug(f"Duplicate alert suppressed: {alert_id}")
            return alert_id
        
        # Add to active alerts
        self.active_alerts[alert_id] = alert
        
        # Send notifications
        await self._send_notifications(alert)
        
        logger.info(f"Alert created: {alert_id} - {title}")
        return alert_id
    
    def _is_duplicate_alert(self, new_alert: Alert) -> bool:
        """Check if alert is duplicate of existing active alert."""
        for alert in self.active_alerts.values():
            if (alert.title == new_alert.title and 
                alert.source == new_alert.source and
                alert.severity == new_alert.severity and
                (datetime.now() - alert.timestamp).total_seconds() < 300):  # 5 minutes
                return True
        return False
    
    def _save_history(self):
        """Save the alert history to a JSON file."""
        try:
            with open(self.history_file_path, 'w') as f:
                history_dicts = [alert.to_dict() for alert in self.alert_history]
                json.dump(history_dicts, f, indent=2)
            logger.info(f"Alert history saved to {self.history_file_path}")
        except IOError as e:
            logger.error(f"Failed to save alert history: {e}")

    def _load_history(self):
        """Load alert history from a JSON file."""
        try:
            if not os.path.exists(self.history_file_path):
                logger.info("No alert history file found. Starting fresh.")
                return

            with open(self.history_file_path, 'r') as f:
                history_dicts = json.load(f)
                for alert_dict in history_dicts:
                    # Reconstruct Alert object
                    alert = Alert(
                        alert_id=alert_dict["alert_id"],
                        title=alert_dict["title"],
                        message=alert_dict["message"],
                        severity=alert_dict["severity"],
                        source=alert_dict["source"],
                        metadata=alert_dict["metadata"]
                    )
                    alert.timestamp = datetime.fromisoformat(alert_dict["timestamp"])
                    alert.acknowledged = alert_dict["acknowledged"]
                    alert.acknowledged_by = alert_dict["acknowledged_by"]
                    if alert_dict["acknowledged_at"]:
                        alert.acknowledged_at = datetime.fromisoformat(alert_dict["acknowledged_at"])
                    self.alert_history.append(alert)
            logger.info(f"Loaded {len(self.alert_history)} alerts from history.")
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load alert history: {e}")

    async def _send_notifications(self, alert: Alert, channel_names: Optional[List[str]] = None):
        """
        Send alert notifications.
        If channel_names is provided, sends only to those channels.
        Otherwise, sends to all enabled channels.
        """
        if channel_names:
            channels_to_notify = [
                self.notification_channels[name]
                for name in channel_names
                if name in self.notification_channels and self.notification_channels[name].is_enabled
            ]
        else:
            channels_to_notify = [ch for ch in self.notification_channels.values() if ch.is_enabled]

        tasks = [channel.send(alert) for channel in channels_to_notify]
        
        # Always log the alert as a fallback
        self._log_alert(alert)
        
        # Execute notifications in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Notification task failed: {result}")

    def add_escalation_policy(self, policy: EscalationPolicy):
        """Add a new escalation policy."""
        self.escalation_policies[policy.policy_id] = policy
        logger.info(f"Escalation policy '{policy.policy_id}' added.")

    async def _process_escalations(self):
        """Check for unacknowledged alerts and trigger escalation steps."""
        now = datetime.now()
        for alert in list(self.active_alerts.values()):
            if alert.acknowledged:
                continue

            rule_id = alert.metadata.get("rule_id")
            if not rule_id or rule_id not in self.rules:
                continue
            
            rule = self.rules[rule_id]
            if not rule.escalation_policy:
                continue

            time_since_alert = now - alert.timestamp
            
            # Find the next step to execute
            next_step_to_execute = None
            last_executed_step_index = alert.metadata.get("last_escalation_step", -1)

            if last_executed_step_index < len(rule.escalation_policy.steps) - 1:
                next_step = rule.escalation_policy.steps[last_executed_step_index + 1]
                if time_since_alert >= next_step.delay:
                    next_step_to_execute = next_step
            
            if next_step_to_execute:
                logger.info(f"Escalating alert {alert.alert_id} for rule '{rule.name}'.")
                escalation_alert = Alert(
                    alert_id=f"esc_{alert.alert_id}",
                    title=f"[ESCALATION] {alert.title}",
                    message=alert.message,
                    severity=alert.severity,
                    source=alert.source,
                    metadata=alert.metadata
                )
                await self._send_notifications(escalation_alert, channel_names=next_step_to_execute.channels)
                alert.metadata["last_escalation_step"] = last_executed_step_index + 1

    def snooze_rule(self, rule_id: str, duration: timedelta):
        """Temporarily disable a rule from triggering."""
        if rule_id in self.rules:
            self.rules[rule_id].snoozed_until = datetime.now() + duration
            logger.info(f"Rule '{self.rules[rule_id].name}' snoozed for {duration}.")
        else:
            logger.warning(f"Cannot snooze unknown rule_id: {rule_id}")
    
    def _log_alert(self, alert: Alert):
        """Log alert (fallback notification)."""
        log_level = logging.WARNING if alert.severity in ["warning", "critical"] else logging.INFO
        logger.log(log_level, f"ALERT [{alert.severity}]: {alert.title} - {alert.message}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = acknowledged_by
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        return [alert.to_dict() for alert in self.active_alerts.values()]
    
    def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get alert history with optional filtering."""
        alerts = self.alert_history.copy()
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if source:
            alerts = [a for a in alerts if a.source == source]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [alert.to_dict() for alert in alerts[:limit]]
    
    def clear_resolved_alerts(self):
        """Clear alerts that are no longer active."""
        cutoff = datetime.now() - timedelta(hours=24)
        to_remove = []
        
        for alert_id, alert in self.active_alerts.items():
            if alert.timestamp < cutoff:
                to_remove.append(alert_id)
        
        for alert_id in to_remove:
            del self.active_alerts[alert_id]
        
        if to_remove:
            logger.info(f"Cleared {len(to_remove)} resolved alerts")


if __name__ == "__main__":

    async def event_simulator(alert_system: AlertingSystem):
        """Simulates various system events."""
        logger.info("[SIM] Starting event simulation...")

        # 1. Simulate a CPU spike that resolves itself
        logger.info("[SIM] Simulating temporary CPU spike...")
        await alert_system.process_event(Event(event_type="cpu.usage", value=95, source="server-1", tags={"env": "prod"}))
        await asyncio.sleep(2)
        await alert_system.process_event(Event(event_type="cpu.usage", value=70, source="server-1", tags={"env": "prod"}))

        # 2. Simulate a persistent high memory usage to trigger an alert
        logger.info("[SIM] Simulating persistent memory issue...")
        await alert_system.process_event(Event(event_type="memory.usage", value=96, source="db-5", tags={"env": "prod"}))
        await asyncio.sleep(11) # Wait for the 'for_duration' to pass

        # 3. Acknowledge the alert
        active_alerts = alert_system.get_active_alerts()
        if active_alerts:
            alert_to_ack = active_alerts[0]
            logger.info(f"[SIM] Acknowledging alert {alert_to_ack['alert_id']}")
            alert_system.acknowledge_alert(alert_to_ack['alert_id'], "auto-sim")

        # 4. Simulate a custom application error to trigger escalation
        logger.info("[SIM] Simulating critical application error for escalation test...")
        await alert_system.process_event(Event(event_type="app.errors", value=55, source="payment-gateway", tags={"tier": "1"}))
        await asyncio.sleep(11) # Trigger the initial alert
        logger.info("[SIM] Waiting for escalation... (will take ~20 seconds)")
        await asyncio.sleep(22)

        # 5. Snooze a rule and simulate events that should be ignored
        logger.info("[SIM] Snoozing the CPU rule and simulating another spike...")
        alert_system.snooze_rule("cpu-prod-critical", timedelta(seconds=30))
        await alert_system.process_event(Event(event_type="cpu.usage", value=99, source="server-1", tags={"env": "prod"}))
        await asyncio.sleep(11) # No alert should be created

        logger.info("[SIM] Event simulation finished.")

    async def main():
        """Main function to run the alerting system simulation."""

        # Define a more complete configuration
        config = {
            "history_file_path": "alert_history_demo.json",
            "channels": {
                # In a real scenario, these would be fully configured
                "email": {"enabled": False, "to_addresses": ["devops@example.com"]},
                "slack": {"enabled": False, "webhook_url": "https://hooks.slack.com/services/..."}
            }
        }

        # Initialize the alerting system
        alert_system = AlertingSystem(config)

        # --- Define Rules and Policies ---
        # 1. Escalation Policy for critical errors
        critical_escalation = EscalationPolicy(
            policy_id="critical-policy",
            steps=[
                EscalationStep(delay=timedelta(seconds=20), channels=["email", "slack"]) # Escalate after 20s
            ]
        )
        alert_system.add_escalation_policy(critical_escalation)

        # 2. CPU Rule
        cpu_rule = Rule(
            rule_id="cpu-prod-critical",
            name="Critical CPU Load on Production",
            condition="event.event_type == 'cpu.usage' and event.value > 90 and event.tags.get('env') == 'prod'",
            for_duration=timedelta(seconds=5),
            cooldown=timedelta(minutes=5),
            severity="critical",
            message_template="CPU usage is at {value}% on {source}."
        )
        alert_system.add_rule(cpu_rule)

        # 3. Memory Rule
        mem_rule = Rule(
            rule_id="mem-prod-warning",
            name="High Memory Usage on Production",
            condition="event.event_type == 'memory.usage' and event.value > 95",
            for_duration=timedelta(seconds=10),
            cooldown=timedelta(minutes=10),
            severity="warning",
            message_template="Memory usage is at {value}% on {source}."
        )
        alert_system.add_rule(mem_rule)

        # 4. Custom App Error Rule with Escalation
        app_error_rule = Rule(
            rule_id="app-error-critical",
            name="High Application Error Rate",
            condition="event.event_type == 'app.errors' and event.value > 50",
            for_duration=timedelta(seconds=10),
            cooldown=timedelta(minutes=2),
            severity="critical",
            message_template="Application error rate is {value} errors/min on {source}."
        )
        app_error_rule.escalation_policy = critical_escalation
        alert_system.add_rule(app_error_rule)

        # --- Run Simulation ---
        await alert_system.start()

        try:
            # Run the system for a while to allow monitoring and escalations
            await event_simulator(alert_system)
            logger.info("Main simulation finished. Giving system time for final cleanup...")
            await asyncio.sleep(5)
        finally:
            await alert_system.stop()
            # Clean up the demo history file
            if os.path.exists(config["history_file_path"]):
                os.remove(config["history_file_path"])
                logger.info(f"Cleaned up demo history file: {config['history_file_path']}")


    # Run the main async function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")
