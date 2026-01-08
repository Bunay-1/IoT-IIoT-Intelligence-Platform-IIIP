"""
Alerting System Module

This module implements comprehensive alerting system for monitoring and notifying
about system events, performance issues, and operational alerts.
"""

import asyncio
import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Any, Dict, List, Optional

import aiohttp

from utils.logging_config import get_logger

logger = get_logger(__name__)


class Alert:
    """Alert data structure."""
    
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


class AlertingSystem:
    """Comprehensive alerting system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.active_alerts = {}
        self.alert_history = []
        self.alert_rules = {}
        self.notification_channels = []
        self.running = False
        
    def _default_config(self) -> Dict[str, Any]:
        """Default alerting configuration."""
        return {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_address": "",
                "to_addresses": []
            },
            "slack": {
                "enabled": False,
                "webhook_url": "",
                "channel": "#alerts"
            },
            "webhook": {
                "enabled": False,
                "url": "",
                "headers": {}
            },
            "thresholds": {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "error_rate": 5.0,
                "response_time": 5.0
            }
        }
    
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
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop."""
        while self.running:
            try:
                # Check system metrics and generate alerts
                await self._check_system_metrics()
                
                # Clean up old alerts
                await self._cleanup_old_alerts()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Alerting monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _check_system_metrics(self):
        """Check system metrics and generate alerts."""
        try:
            import psutil
            
            # CPU usage check
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.config["thresholds"]["cpu_usage"]:
                await self.create_alert(
                    title="High CPU Usage",
                    message=f"CPU usage is {cpu_percent:.1f}%",
                    severity="warning" if cpu_percent < 90 else "critical",
                    source="system_monitor",
                    metadata={"cpu_percent": cpu_percent}
                )
            
            # Memory usage check
            memory = psutil.virtual_memory()
            if memory.percent > self.config["thresholds"]["memory_usage"]:
                await self.create_alert(
                    title="High Memory Usage",
                    message=f"Memory usage is {memory.percent:.1f}%",
                    severity="warning" if memory.percent < 95 else "critical",
                    source="system_monitor",
                    metadata={"memory_percent": memory.percent}
                )
                
        except ImportError:
            logger.warning("psutil not available for system monitoring")
        except Exception as e:
            logger.error(f"System metrics check failed: {e}")
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts."""
        cutoff = datetime.now() - timedelta(hours=24)
        
        # Move old alerts to history
        old_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.timestamp < cutoff
        ]
        
        for alert_id in old_alerts:
            alert = self.active_alerts.pop(alert_id)
            self.alert_history.append(alert)
    
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
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications through all configured channels."""
        tasks = []
        
        if self.config["email"]["enabled"]:
            tasks.append(self._send_email_alert(alert))
        
        if self.config["slack"]["enabled"]:
            tasks.append(self._send_slack_alert(alert))
        
        if self.config["webhook"]["enabled"]:
            tasks.append(self._send_webhook_alert(alert))
        
        # Always log the alert
        self._log_alert(alert)
        
        # Execute notifications in parallel
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_email_alert(self, alert: Alert):
        """Send alert via email."""
        if not self.config["email"]["enabled"]:
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.config["email"]["from_address"]
            msg['To'] = ', '.join(self.config["email"]["to_addresses"])
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
            
            server = smtplib.SMTP(
                self.config["email"]["smtp_server"],
                self.config["email"]["smtp_port"]
            )
            server.starttls()
            server.login(
                self.config["email"]["username"],
                self.config["email"]["password"]
            )
            
            text = msg.as_string()
            server.sendmail(
                self.config["email"]["from_address"],
                self.config["email"]["to_addresses"],
                text
            )
            
            server.quit()
            
            logger.info(f"Email alert sent for {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_slack_alert(self, alert: Alert):
        """Send alert via Slack webhook."""
        if not self.config["slack"]["enabled"]:
            return
        
        try:
            payload = {
                "channel": self.config["slack"]["channel"],
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
                async with session.post(
                    self.config["slack"]["webhook_url"],
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent for {alert.alert_id}")
                    else:
                        logger.error(f"Slack alert failed: {response.status}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    async def _send_webhook_alert(self, alert: Alert):
        """Send alert via webhook."""
        if not self.config["webhook"]["enabled"]:
            return
        
        try:
            payload = alert.to_dict()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config["webhook"]["url"],
                    json=payload,
                    headers=self.config["webhook"]["headers"]
                ) as response:
                    if response.status < 300:
                        logger.info(f"Webhook alert sent for {alert.alert_id}")
                    else:
                        logger.error(f"Webhook alert failed: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
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


# Global alerting system instance
alerting_system = AlertingSystem()


async def get_alerting_system(config: Optional[Dict[str, Any]] = None) -> AlertingSystem:
    """Get or create global alerting system instance."""
    global alerting_system
    if config:
        alerting_system = AlertingSystem(config)
    return alerting_system
