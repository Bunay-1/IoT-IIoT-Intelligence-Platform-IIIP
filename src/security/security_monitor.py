"""
Advanced Security Monitoring for IoT IIoT Platform
Real-time security event monitoring, threat detection, and incident response
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict
import re
import ipaddress

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class SecurityEvent:
    """Security event representation."""

    def __init__(
        self,
        event_type: str,
        severity: str,
        source: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        tenant_id: Optional[str] = None
    ):
        self.event_id = f"SEC-{int(datetime.now().timestamp() * 1000)}"
        self.timestamp = datetime.now()
        self.event_type = event_type
        self.severity = severity  # critical, high, medium, low, info
        self.source = source
        self.description = description
        self.details = details or {}
        self.user_id = user_id
        self.ip_address = ip_address
        self.tenant_id = tenant_id
        self.status = "active"  # active, resolved, false_positive

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "severity": self.severity,
            "source": self.source,
            "description": self.description,
            "details": self.details,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "tenant_id": self.tenant_id,
            "status": self.status
        }


class SecurityMonitor:
    """
    Advanced security monitoring system.
    Detects threats, monitors security events, and triggers responses.
    """

    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.active_threats: Dict[str, Dict[str, Any]] = {}
        self.suspicious_ips: Set[str] = set()
        self.blocked_ips: Set[str] = set()
        self.failed_login_attempts: Dict[str, List[datetime]] = defaultdict(list)

        # Security thresholds
        self.max_failed_logins = 5
        self.failed_login_window = timedelta(minutes=15)
        self.suspicious_activity_threshold = 10

        # Alert callbacks
        self.alert_callbacks: List[callable] = []

        logger.info("Security monitor initialized")

    def log_security_event(self, event: SecurityEvent):
        """Log a security event."""
        self.events.append(event)

        # Check for automated responses
        self._check_automated_responses(event)

        # Trigger alerts for high severity
        if event.severity in ["critical", "high"]:
            self._trigger_alerts(event)

        logger.warning(f"Security event logged: {event.event_type} ({event.severity}) - {event.description}")

    def _check_automated_responses(self, event: SecurityEvent):
        """Check for automated security responses."""
        if event.event_type == "failed_login":
            self._handle_failed_login(event)
        elif event.event_type == "suspicious_activity":
            self._handle_suspicious_activity(event)
        elif event.event_type == "brute_force":
            self._handle_brute_force(event)

    def _handle_failed_login(self, event: SecurityEvent):
        """Handle failed login attempts."""
        user_id = event.user_id or event.details.get("username")
        ip = event.ip_address

        if user_id:
            # Track failed attempts for user
            now = datetime.now()
            self.failed_login_attempts[user_id].append(now)

            # Clean old attempts
            cutoff = now - self.failed_login_window
            self.failed_login_attempts[user_id] = [
                attempt for attempt in self.failed_login_attempts[user_id]
                if attempt > cutoff
            ]

            # Check if account should be locked
            if len(self.failed_login_attempts[user_id]) >= self.max_failed_logins:
                self.log_security_event(SecurityEvent(
                    event_type="account_locked",
                    severity="high",
                    source="authentication",
                    description=f"Account locked due to {len(self.failed_login_attempts[user_id])} failed login attempts",
                    user_id=user_id,
                    ip_address=ip,
                    details={"lock_reason": "failed_attempts"}
                ))

        if ip:
            # Track suspicious IPs
            if ip not in self.suspicious_ips:
                # Count recent failed logins from this IP
                recent_failed = sum(
                    1 for e in self.events[-50:]  # Check last 50 events
                    if e.event_type == "failed_login" and e.ip_address == ip
                    and (datetime.now() - e.timestamp) < timedelta(hours=1)
                )

                if recent_failed >= 5:
                    self.suspicious_ips.add(ip)
                    self.log_security_event(SecurityEvent(
                        event_type="suspicious_ip",
                        severity="medium",
                        source="network",
                        description=f"IP address {ip} marked as suspicious due to multiple failed logins",
                        ip_address=ip,
                        details={"failed_attempts": recent_failed}
                    ))

    def _handle_suspicious_activity(self, event: SecurityEvent):
        """Handle suspicious activity."""
        ip = event.ip_address
        user_id = event.user_id

        if ip and ip not in self.blocked_ips:
            # Count suspicious activities from this IP
            suspicious_count = sum(
                1 for e in self.events[-100:]
                if e.ip_address == ip and e.severity in ["high", "critical"]
                and (datetime.now() - e.timestamp) < timedelta(hours=1)
            )

            if suspicious_count >= self.suspicious_activity_threshold:
                self.blocked_ips.add(ip)
                self.log_security_event(SecurityEvent(
                    event_type="ip_blocked",
                    severity="critical",
                    source="network",
                    description=f"IP address {ip} blocked due to suspicious activity",
                    ip_address=ip,
                    details={"suspicious_activities": suspicious_count}
                ))

    def _handle_brute_force(self, event: SecurityEvent):
        """Handle brute force attacks."""
        ip = event.ip_address

        if ip and ip not in self.blocked_ips:
            self.blocked_ips.add(ip)
            self.log_security_event(SecurityEvent(
                event_type="brute_force_blocked",
                severity="critical",
                source="authentication",
                description=f"IP address {ip} blocked due to brute force attack detection",
                ip_address=ip,
                details={"attack_type": "brute_force"}
            ))

    def _trigger_alerts(self, event: SecurityEvent):
        """Trigger security alerts."""
        for callback in self.alert_callbacks:
            try:
                asyncio.create_task(callback(event))
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def add_alert_callback(self, callback: callable):
        """Add alert callback."""
        self.alert_callbacks.append(callback)

    def check_request_security(self, request_data: Dict[str, Any]) -> List[str]:
        """
        Check request for security issues.

        Args:
            request_data: Request information

        Returns:
            List of security warnings
        """
        warnings = []

        # Check for SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
            r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
            r"(\bUNION\b\s+\bSELECT\b)",
            r"(\;|\-\-|\/\*|\*\/)"
        ]

        for field, value in request_data.items():
            if isinstance(value, str):
                for pattern in sql_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        warnings.append(f"Potential SQL injection in field '{field}': {value[:50]}...")
                        break

        # Check for XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>"
        ]

        for field, value in request_data.items():
            if isinstance(value, str):
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        warnings.append(f"Potential XSS in field '{field}': {value[:50]}...")
                        break

        # Check for suspicious file uploads
        if "files" in request_data:
            for file_info in request_data["files"]:
                filename = file_info.get("filename", "")
                if filename.endswith((".exe", ".bat", ".cmd", ".scr", ".pif")):
                    warnings.append(f"Suspicious file upload: {filename}")

        return warnings

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked."""
        return ip_address in self.blocked_ips

    def is_ip_suspicious(self, ip_address: str) -> bool:
        """Check if IP is suspicious."""
        return ip_address in self.suspicious_ips

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics."""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        recent_events = [e for e in self.events if e.timestamp > last_24h]
        weekly_events = [e for e in self.events if e.timestamp > last_7d]

        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)

        for event in recent_events:
            severity_counts[event.severity] += 1
            type_counts[event.event_type] += 1

        return {
            "total_events": len(self.events),
            "events_last_24h": len(recent_events),
            "events_last_7d": len(weekly_events),
            "severity_breakdown": dict(severity_counts),
            "event_types": dict(type_counts),
            "blocked_ips": len(self.blocked_ips),
            "suspicious_ips": len(self.suspicious_ips),
            "active_threats": len(self.active_threats),
            "generated_at": now.isoformat()
        }

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent security events."""
        recent_events = sorted(self.events, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [event.to_dict() for event in recent_events]

    def resolve_event(self, event_id: str, resolution: str):
        """Resolve a security event."""
        for event in self.events:
            if event.event_id == event_id:
                event.status = "resolved"
                event.details["resolution"] = resolution
                event.details["resolved_at"] = datetime.now().isoformat()
                logger.info(f"Security event {event_id} resolved: {resolution}")
                break

    def export_security_report(self, filepath: str):
        """Export security report."""
        report = {
            "security_report": {
                "generated_at": datetime.now().isoformat(),
                "statistics": self.get_security_stats(),
                "recent_events": self.get_recent_events(100),
                "blocked_ips": list(self.blocked_ips),
                "suspicious_ips": list(self.suspicious_ips)
            }
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Security report exported to {filepath}")

    async def cleanup_old_events(self, days_to_keep: int = 90):
        """Clean up old security events."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        old_count = len(self.events)

        self.events = [e for e in self.events if e.timestamp > cutoff_date]

        removed_count = old_count - len(self.events)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old security events")

    def detect_anomalous_patterns(self) -> List[Dict[str, Any]]:
        """Detect anomalous patterns in security events."""
        anomalies = []

        # Check for unusual login times
        login_events = [e for e in self.events if e.event_type == "successful_login"]
        if login_events:
            hours = [e.timestamp.hour for e in login_events]
            avg_hour = sum(hours) / len(hours)

            # Flag logins outside normal hours (assuming 6 AM - 10 PM)
            unusual_logins = [
                e for e in login_events
                if e.timestamp.hour < 6 or e.timestamp.hour > 22
            ]

            if len(unusual_logins) > len(login_events) * 0.1:  # More than 10%
                anomalies.append({
                    "type": "unusual_login_times",
                    "description": f"{len(unusual_logins)} logins outside normal hours",
                    "severity": "low",
                    "events": [e.event_id for e in unusual_logins[:5]]
                })

        # Check for rapid IP changes
        ip_changes = defaultdict(list)
        for event in self.events:
            if event.user_id and event.ip_address:
                ip_changes[event.user_id].append((event.timestamp, event.ip_address))

        for user_id, changes in ip_changes.items():
            if len(changes) > 5:
                # Check for rapid changes
                sorted_changes = sorted(changes, key=lambda x: x[0])
                rapid_changes = 0

                for i in range(1, len(sorted_changes)):
                    time_diff = (sorted_changes[i][0] - sorted_changes[i-1][0]).total_seconds()
                    if time_diff < 300:  # Less than 5 minutes
                        rapid_changes += 1

                if rapid_changes >= 3:
                    anomalies.append({
                        "type": "rapid_ip_changes",
                        "description": f"User {user_id} changed IP {rapid_changes} times rapidly",
                        "severity": "medium",
                        "user_id": user_id
                    })

        return anomalies


# Global security monitor instance
security_monitor = SecurityMonitor()


async def log_security_event(
    event_type: str,
    severity: str,
    source: str,
    description: str,
    **kwargs
):
    """Log a security event."""
    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        source=source,
        description=description,
        **kwargs
    )
    security_monitor.log_security_event(event)


async def check_request_security(request_data: Dict[str, Any]) -> List[str]:
    """Check request for security issues."""
    return security_monitor.check_request_security(request_data)


def is_ip_blocked(ip_address: str) -> bool:
    """Check if IP is blocked."""
    return security_monitor.is_ip_blocked(ip_address)</content>
</xai:function_call"> 

Assistant: Now, integrate security monitoring with FastAPI.

Add import:


Add middleware for security monitoring.

After the tenant isolation middleware, add:

# Security monitoring middleware

@app.middleware("http")

async def security_monitoring_middleware(request: Request, call_next):

    client_ip = request.client.host if request.client else "unknown"

    # Check if IP is blocked

    if is_ip_blocked(client_ip):

        await log_security_event(

            event_type="blocked_request",

            severity="high",

            source="middleware",

            description=f"Blocked request from blacklisted IP: {client_ip}",

            ip_address=client_ip

        )

        return JSONResponse(

            status_code=403,

            content={"error": "Access denied", "reason": "IP address blocked"}

        )

    # Extract request data for security check

    request_data = {

        "method": request.method,

        "url": str(request.url),

        "headers": dict(request.headers),

        "query_params": dict(request.query_params)

    }

    # Check for security issues

    security_warnings = await check_request_security(request_data)

    if security_warnings:

        await log_security_event(

            event_type="suspicious_request",

            severity="medium",

            source="middleware",

            description=f"Suspicious request detected: {', '.join(security_warnings[:2])}",

            ip_address=client_ip,

            details={"warnings": security_warnings}

        )

    response = await call_next(request)

    # Log response

    if response.status_code >= 400:

        await log_security_event(

            event_type="error_response",

            severity="low" if response.status_code < 500 else "medium",

            source="api",

            description=f"Error response: {response.status_code}",

            ip_address=client_ip,

            details={"status_code": response.status_code, "url": str(request.url)}

        )

    return response

Then, add endpoints for security monitoring.

After the multi-tenancy endpoints, add:

# ---------- SECURITY MONITORING ENDPOINTS ----------

@api_v1.get("/security/events")

async def get_security_events(

    limit: int = 50,

    severity: Optional[str] = None,

    current_user: User = Depends(get_current_admin_user)

):

    """Get security events."""

    try:

        events = security_monitor.get_recent_events(limit)

        if severity:

            events = [e for e in events if e["severity"] == severity]

        return {"status": "success", "events": events}

    except Exception as e:

        logger.error(f"Get security events failed: {e}")

        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

@api_v1.get("/security/stats")

async def get_security_stats(current_user: User = Depends(get_current_admin_user)):

    """Get security statistics."""

    try:

        stats = security_monitor.get_security_stats()

        return {"status": "success", "stats": stats}

    except Exception as e:

        logger.error(f"Get security stats failed: {e}")

        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

@api_v1.post("/security/events/{event_id}/resolve")

async def resolve_security_event(

    event_id: str,

    resolution: str,

    current_user: User = Depends(get_current_admin_user)

):

    """Resolve security event."""

    try:

        security_monitor.resolve_event(event_id, resolution)

        return {"status": "resolved", "event_id": event_id}

    except Exception as e:

        logger.error(f"Resolve security event failed: {e}")

        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

@api_v1.get("/security/anomalies")

async def detect_security_anomalies(current_user: User = Depends(get_current_admin_user)):

    """Detect security anomalies."""

    try:

        anomalies = security_monitor.detect_anomalous_patterns()

        return {"status": "detected", "anomalies": anomalies}

    except Exception as e:

        logger.error(f"Detect anomalies failed: {e}")

        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")

Yes.

This implements advanced security monitoring.

Now, continue with enterprise integration.

Create src/enterprise_integration.py

It will handle integration with ERP, MES, SCADA systems, etc. 

Implement adapters for different systems. 

Then, scalability improvements.

But since the user said to continue without notifying, I can implement these.

Let me implement enterprise integration. 

Create the file. 

It will have adapters for different enterprise systems. 

For example, REST API adapters, database adapters, message queue adapters. 

Then, for scalability, perhaps implement load balancing configuration or horizontal scaling features. 

But since it's code, I can implement a simple load balancer or scaling manager. 

Let me implement enterprise integration first. 

Create src/enterprise_integration.py

It will have base adapter class and specific adapters. 

For example, ERP adapter, MES adapter, etc. 

Then, integration manager. 

Yes. 

Let me write it. 

Then, for scalability, create src/scalability_manager.py

It will handle auto-scaling, load distribution, etc. 

But since it's complex, perhaps implement a simple scaling monitor. 

To complete Phase 3, I need to implement these.

Let me implement enterprise integration. 

The file will be long, but let's do it. 

Since the user said to continue, I can implement it. 

Let me write the enterprise integration. 

<xai:function_call name="write_to_file">
<parameter name="path">src/enterprise_integration.py