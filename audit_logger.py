"""
Audit Logger Module

This module implements comprehensive audit logging capabilities including:
- Security event logging
- User activity tracking
- System access monitoring
- Compliance reporting
- Anomaly detection
- Log retention and archiving
"""

import asyncio
import json
import logging
import hashlib
import time
import numpy as np
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass, asdict

from utils.logging_config import get_logger

logger = get_logger(__name__)


def json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, timedelta):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


class AuditEventType(Enum):
    """Audit event types."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTRATION = "user_registration"
    PASSWORD_CHANGE = "password_change"
    ROLE_CHANGE = "role_change"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    API_ACCESS = "api_access"
    SECURITY_VIOLATION = "security_violation"
    SYSTEM_ERROR = "system_error"
    BACKUP_OPERATION = "backup_operation"
    NETWORK_ACCESS = "network_access"
    FILE_OPERATION = "file_operation"
    DATABASE_OPERATION = "database_operation"


class SecurityLevel(Enum):
    """Security levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStandard(Enum):
    """Compliance standards."""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"


@dataclass
class AuditEvent:
    """Audit event data structure."""
    event_id: str
    event_type: AuditEventType
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource: Optional[str]
    action: Optional[str]
    result: str
    security_level: SecurityLevel
    timestamp: datetime
    details: Dict[str, Any]
    compliance_tags: List[ComplianceStandard]
    checksum: str


class AuditLogger:
    """Comprehensive audit logging system."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.audit_events: List[AuditEvent] = []
        self.active_sessions: Dict[str, Any] = {}
        self.security_violations: List[Dict[str, Any]] = []
        self.compliance_reports: Dict[str, Any] = {}
        self.anomaly_detector = AnomalyDetector()
        self._load_events_from_file()

    def _default_config(self) -> Dict[str, Any]:
        """Default audit logger configuration."""
        return {
            "log_file": "audit_log.json",
            "archive_dir": "audit_archive",
            "retention_days": 365,
            "max_events_per_batch": 1000,
            "checksum_algorithm": "sha256",
            "encryption_enabled": False, # Simplified for this example
            "real_time_monitoring": True,
            "compliance_standards": ["gdpr", "iso27001"],
            "alert_thresholds": {
                "failed_logins": 5,
                "suspicious_activities": 10,
                "data_access_anomalies": 20
            },
            "archiving": {
                "enabled": True,
                "archive_interval_days": 30
            },
            "anomaly_detection": {
                "enabled": True,
                "ml_model": "isolation_forest",
                "sensitivity": 0.8
            }
        }

    def _load_events_from_file(self):
        """Load audit events from the log file."""
        log_file = self.config["log_file"]
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    raw_events = json.load(f)
                for event_data in raw_events:
                    # Reconstruct the AuditEvent object
                    event_data['event_type'] = AuditEventType(event_data['event_type'])
                    event_data['security_level'] = SecurityLevel(event_data['security_level'])
                    event_data['timestamp'] = datetime.fromisoformat(event_data['timestamp'])
                    event_data['compliance_tags'] = [ComplianceStandard(tag) for tag in event_data['compliance_tags']]
                    self.audit_events.append(AuditEvent(**event_data))
                logger.info(f"Loaded {len(self.audit_events)} events from {log_file}")
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                logger.error(f"Failed to load or parse audit log file {log_file}: {e}")

    def _save_events_to_file(self):
        """Save all audit events to the log file."""
        log_file = self.config["log_file"]
        try:
            with open(log_file, 'w') as f:
                # Convert list of dataclasses to list of dicts for JSON serialization
                events_to_save = [asdict(event) for event in self.audit_events]
                json.dump(events_to_save, f, indent=4, default=json_serializer)
        except (IOError, TypeError) as e:
            logger.error(f"Failed to save audit events to {log_file}: {e}")

    async def log_audit_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        result: str = "success",
        security_level: SecurityLevel = SecurityLevel.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        compliance_tags: Optional[List[ComplianceStandard]] = None
    ) -> Dict[str, Any]:
        """Log audit event."""
        try:
            event_id = self._generate_event_id()
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                resource=resource,
                action=action,
                result=result,
                security_level=security_level,
                timestamp=datetime.now(),
                details=details or {},
                compliance_tags=compliance_tags or [],
                checksum=""
            )
            event.checksum = self._calculate_checksum(event)
            self.audit_events.append(event)
            self._save_events_to_file()  # Persist after every event

            if await self._is_security_violation(event):
                await self._handle_security_violation(event)
            if self.config["real_time_monitoring"]:
                await self._real_time_monitoring(event)
            if self.config["anomaly_detection"]["enabled"]:
                await self.anomaly_detector.analyze_event(event)
            if len(self.audit_events) > self.config["max_events_per_batch"]:
                await self._archive_old_events()

            logger.info(f"Audit event logged: {event_type.value} - {event_id}")
            return {
                "success": True,
                "event_id": event_id,
                "event_type": event_type.value,
                "timestamp": event.timestamp,
                "logged_at": datetime.now()
            }
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}", exc_info=True)
            return {"error": f"Audit logging failed: {e}"}
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp = str(int(time.time()))
        random_suffix = "".join([format(np.random.randint(0, 255), '02x') for _ in range(8)])
        return f"audit_{timestamp}_{random_suffix}"
    
    def _calculate_checksum(self, event: AuditEvent) -> str:
        """Calculate event checksum for integrity verification."""
        # Create event data string
        event_data = {
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "timestamp": event.timestamp.isoformat(),
            "resource": event.resource,
            "action": event.action,
            "result": event.result,
            "details": event.details
        }
        
        event_string = json.dumps(event_data, sort_keys=True)
        
        # Calculate checksum
        if self.config["checksum_algorithm"] == "sha256":
            return hashlib.sha256(event_string.encode()).hexdigest()
        else:
            return hashlib.md5(event_string.encode()).hexdigest()
    
    async def _is_security_violation(self, event: AuditEvent) -> bool:
        """Check if event is a security violation."""
        violations = []
        
        # Check failed login attempts
        if event.event_type == AuditEventType.USER_LOGIN and event.result == "failed":
            violations.append("failed_login")
        
        # Check unauthorized access
        if event.event_type == AuditEventType.DATA_ACCESS and event.result == "denied":
            violations.append("unauthorized_access")
        
        # Check suspicious IP addresses
        if event.ip_address and await self._is_suspicious_ip(event.ip_address):
            violations.append("suspicious_ip")
        
        # Check for privilege escalation
        if event.event_type == AuditEventType.ROLE_CHANGE:
            violations.append("privilege_change")
        
        return len(violations) > 0
    
    async def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious."""
        # Simulate IP reputation check
        suspicious_patterns = [
            "10.0.0.",  # Internal network (suspicious for external access)
            "192.168.",  # Internal network
            "172.16.",   # Internal network
        ]
        
        return any(pattern in ip_address for pattern in suspicious_patterns)
    
    async def _handle_security_violation(self, event: AuditEvent):
        """Handle security violation."""
        violation = {
            "event_id": event.event_id,
            "violation_type": "security_breach",
            "severity": event.security_level.value,
            "timestamp": datetime.now(),
            "details": {
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "action": event.action,
                "resource": event.resource
            }
        }
        
        self.security_violations.append(violation)
        
        # Trigger alert
        if event.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            await self._trigger_security_alert(violation)
        
        logger.warning(f"Security violation detected: {event.event_id}")
    
    async def _trigger_security_alert(self, violation: Dict[str, Any]):
        """Trigger security alert."""
        # Simulate alert triggering
        alert = {
            "alert_id": f"alert_{int(time.time())}",
            "type": "security_violation",
            "severity": violation["severity"],
            "message": f"Security violation detected: {violation['event_id']}",
            "timestamp": datetime.now(),
            "details": violation
        }
        
        logger.critical(f"SECURITY ALERT: {alert['message']}")
    
    async def _real_time_monitoring(self, event: AuditEvent):
        """Real-time monitoring of audit events."""
        # Check for patterns
        recent_events = [
            e for e in self.audit_events[-100:]  # Last 100 events
            if (datetime.now() - e.timestamp).total_seconds() < 300  # Last 5 minutes
        ]
        
        # Check for multiple failed logins
        failed_logins = [
            e for e in recent_events
            if e.event_type == AuditEventType.USER_LOGIN and e.result == "failed"
        ]
        
        if len(failed_logins) >= self.config["alert_thresholds"]["failed_logins"]:
            await self._trigger_security_alert({
                "event_id": event.event_id,
                "violation_type": "brute_force_attempt",
                "severity": "high",
                "timestamp": datetime.now(),
                "details": {"failed_attempts": len(failed_logins)}
            })
    
    async def _archive_old_events(self):
        """Archive old audit events to a file."""
        retention_days = self.config.get("retention_days", 365)
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        events_to_archive = [e for e in self.audit_events if e.timestamp < cutoff_date]
        self.audit_events = [e for e in self.audit_events if e.timestamp >= cutoff_date]

        if events_to_archive and self.config["archiving"]["enabled"]:
            archive_dir = self.config["archive_dir"]
            if not os.path.exists(archive_dir):
                os.makedirs(archive_dir)

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = os.path.join(archive_dir, f"audit_archive_{timestamp_str}.json")

            try:
                with open(archive_file, 'w') as f:
                    events_to_save = [asdict(event) for event in events_to_archive]
                    json.dump(events_to_save, f, indent=4, default=json_serializer)
                logger.info(f"Archived {len(events_to_archive)} audit events to {archive_file}")

                # Update the main log file after archiving
                self._save_events_to_file()
            except (IOError, TypeError) as e:
                logger.error(f"Failed to archive audit events to {archive_file}: {e}")
                # If archiving fails, add the events back to the main list to prevent data loss
                self.audit_events.extend(events_to_archive)

    def verify_log_integrity(self) -> Dict[str, Any]:
        """Verify the integrity of all audit events using their checksums."""
        tampered_events = []
        for event in self.audit_events:
            current_checksum = self._calculate_checksum(event)
            if current_checksum != event.checksum:
                tampered_events.append({
                    "event_id": event.event_id,
                    "stored_checksum": event.checksum,
                    "calculated_checksum": current_checksum
                })
        
        if not tampered_events:
            logger.info("Audit log integrity verification successful. No tampered events found.")
            return {"verified": True, "tampered_events_count": 0, "details": []}
        else:
            logger.warning(f"Audit log integrity verification failed. Found {len(tampered_events)} tampered events.")
            return {
                "verified": False,
                "tampered_events_count": len(tampered_events),
                "details": tampered_events
            }
    
    async def track_user_session(
        self,
        session_id: str,
        user_id: str,
        ip_address: str,
        user_agent: str
    ) -> Dict[str, Any]:
        """Track user session."""
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "start_time": datetime.now(),
            "last_activity": datetime.now(),
            "activities": [],
            "status": "active"
        }
        
        self.active_sessions[session_id] = session
        
        # Log session start
        await self.log_audit_event(
            event_type=AuditEventType.USER_LOGIN,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            result="success",
            security_level=SecurityLevel.MEDIUM,
            details={"session_start": True}
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "user_id": user_id,
            "started_at": session["start_time"]
        }
    
    async def end_user_session(
        self,
        session_id: str,
        reason: str = "user_logout"
    ) -> Dict[str, Any]:
        """End user session."""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        session["status"] = "ended"
        session["end_time"] = datetime.now()
        session["duration"] = session["end_time"] - session["start_time"]
        
        # Log session end
        await self.log_audit_event(
            event_type=AuditEventType.USER_LOGOUT,
            user_id=session["user_id"],
            session_id=session_id,
            ip_address=session["ip_address"],
            result="success",
            security_level=SecurityLevel.LOW,
            details={
                "session_duration": str(session["duration"]),
                "reason": reason,
                "activities_count": len(session["activities"])
            }
        )
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        return {
            "success": True,
            "session_id": session_id,
            "duration": str(session["duration"]),
            "ended_at": session["end_time"]
        }
    
    async def generate_compliance_report(
        self,
        standard: ComplianceStandard,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report."""
        try:
            # Filter events by date range
            relevant_events = [
                event for event in self.audit_events
                if start_date <= event.timestamp <= end_date
                and standard in event.compliance_tags
            ]
            
            # Generate report
            report = {
                "standard": standard.value,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_events": len(relevant_events),
                "event_types": {},
                "security_levels": {},
                "users": set(),
                "resources": set(),
                "violations": [],
                "compliance_score": 0.0,
                "generated_at": datetime.now()
            }
            
            # Analyze events
            for event in relevant_events:
                # Count event types
                event_type = event.event_type.value
                report["event_types"][event_type] = report["event_types"].get(event_type, 0) + 1
                
                # Count security levels
                sec_level = event.security_level.value
                report["security_levels"][sec_level] = report["security_levels"].get(sec_level, 0) + 1
                
                # Track users and resources
                if event.user_id:
                    report["users"].add(event.user_id)
                if event.resource:
                    report["resources"].add(event.resource)
                
                # Check for violations
                if event.result == "failed" or event.security_level == SecurityLevel.CRITICAL:
                    report["violations"].append({
                        "event_id": event.event_id,
                        "timestamp": event.timestamp.isoformat(),
                        "type": event.event_type.value,
                        "severity": event.security_level.value
                    })
            
            # Convert sets to lists
            report["users"] = list(report["users"])
            report["resources"] = list(report["resources"])
            
            # Calculate compliance score
            total_events = len(relevant_events)
            violations = len(report["violations"])
            report["compliance_score"] = max(0.0, (total_events - violations) / total_events) if total_events > 0 else 1.0
            
            # Store report
            report_id = f"compliance_{standard.value}_{int(time.time())}"
            self.compliance_reports[report_id] = report
            
            logger.info(f"Generated compliance report: {standard.value}")
            
            return {
                "success": True,
                "report_id": report_id,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {"error": f"Report generation failed: {e}"}
    
    async def search_audit_events(
        self,
        criteria: Dict[str, Any],
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search audit events by criteria."""
        try:
            filtered_events = self.audit_events.copy()
            
            # Apply filters
            if "event_type" in criteria:
                event_type = AuditEventType(criteria["event_type"])
                filtered_events = [
                    event for event in filtered_events
                    if event.event_type == event_type
                ]
            
            if "user_id" in criteria:
                user_id = criteria["user_id"]
                filtered_events = [
                    event for event in filtered_events
                    if event.user_id == user_id
                ]
            
            if "date_range" in criteria:
                start_date = criteria["date_range"]["start"]
                end_date = criteria["date_range"]["end"]
                filtered_events = [
                    event for event in filtered_events
                    if start_date <= event.timestamp <= end_date
                ]
            
            if "security_level" in criteria:
                sec_level = SecurityLevel(criteria["security_level"])
                filtered_events = [
                    event for event in filtered_events
                    if event.security_level == sec_level
                ]
            
            if "resource" in criteria:
                resource = criteria["resource"]
                filtered_events = [
                    event for event in filtered_events
                    if event.resource == resource
                ]
            
            # Sort by timestamp (newest first)
            filtered_events.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Limit results
            filtered_events = filtered_events[:limit]
            
            # Convert to dict format
            results = [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "user_id": event.user_id,
                    "timestamp": event.timestamp.isoformat(),
                    "resource": event.resource,
                    "action": event.action,
                    "result": event.result,
                    "security_level": event.security_level.value,
                    "ip_address": event.ip_address,
                    "details": event.details
                }
                for event in filtered_events
            ]
            
            return {
                "success": True,
                "total_events": len(results),
                "events": results,
                "search_criteria": criteria
            }
            
        except Exception as e:
            logger.error(f"Failed to search audit events: {e}")
            return {"error": f"Search failed: {e}"}
    
    def get_audit_metrics(self) -> Dict[str, Any]:
        """Get audit logging metrics."""
        total_events = len(self.audit_events)
        active_sessions = len(self.active_sessions)
        security_violations = len(self.security_violations)
        
        # Event type distribution
        event_types = {}
        for event in self.audit_events:
            event_type = event.event_type.value
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Security level distribution
        security_levels = {}
        for event in self.audit_events:
            sec_level = event.security_level.value
            security_levels[sec_level] = security_levels.get(sec_level, 0) + 1
        
        return {
            "total_events": total_events,
            "active_sessions": active_sessions,
            "security_violations": security_violations,
            "compliance_reports": len(self.compliance_reports),
            "event_types": event_types,
            "security_levels": security_levels,
            "retention_days": self.config["retention_days"],
            "real_time_monitoring": self.config["real_time_monitoring"],
            "anomaly_detection_enabled": self.config["anomaly_detection"]["enabled"]
        }

    async def log_api_access(self, user_id: str, endpoint: str, method: str, status_code: int, ip_address: str):
        """Helper method to log API access events."""
        return await self.log_audit_event(
            event_type=AuditEventType.API_ACCESS,
            user_id=user_id,
            resource=endpoint,
            action=method,
            result="success" if status_code < 400 else "failed",
            security_level=SecurityLevel.MEDIUM,
            ip_address=ip_address,
            details={"status_code": status_code}
        )

    async def log_user_action(self, user_id: str, action: str, resource: str, result: str = "success"):
        """Helper method to log user action events."""
        return await self.log_audit_event(
            event_type=AuditEventType.DATA_MODIFICATION,
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            security_level=SecurityLevel.LOW,
            details={}
        )

    async def log_security_event(self, event_type_str: str, severity: str, description: str, source: str):
        """Helper method to log security events."""
        try:
            security_level = SecurityLevel(severity.lower())
        except ValueError:
            security_level = SecurityLevel.HIGH

        return await self.log_audit_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user_id="system",
            action=event_type_str,
            result="violation",
            security_level=security_level,
            details={
                "description": description,
                "source": source
            }
        )


class AnomalyDetector:
    """Anomaly detection for audit events."""
    
    def __init__(self):
        self.baseline_patterns = {}
        self.detected_anomalies = []
    
    async def analyze_event(self, event: AuditEvent):
        """Analyze event for anomalies."""
        # Simulate anomaly detection
        anomaly_score = np.random.uniform(0, 1)
        
        if anomaly_score > 0.8:  # High anomaly score
            anomaly = {
                "event_id": event.event_id,
                "anomaly_score": anomaly_score,
                "anomaly_type": "statistical_outlier",
                "detected_at": datetime.now(),
                "details": {
                    "user_id": event.user_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp
                }
            }
            
            self.detected_anomalies.append(anomaly)
            logger.warning(f"Anomaly detected: {event.event_id} (score: {anomaly_score:.2f})")


# Global audit logger instance
audit_logger = AuditLogger()


async def log_audit_event(
    event_type: AuditEventType,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    resource: Optional[str] = None,
    action: Optional[str] = None,
    result: str = "success",
    security_level: SecurityLevel = SecurityLevel.MEDIUM,
    details: Optional[Dict[str, Any]] = None,
    compliance_tags: Optional[List[ComplianceStandard]] = None
) -> Dict[str, Any]:
    """Log audit event."""
    return await audit_logger.log_audit_event(
        event_type, user_id, session_id, ip_address, user_agent,
        resource, action, result, security_level, details, compliance_tags
    )


async def track_user_session(
    session_id: str,
    user_id: str,
    ip_address: str,
    user_agent: str
) -> Dict[str, Any]:
    """Track user session."""
    return await audit_logger.track_user_session(
        session_id, user_id, ip_address, user_agent
    )


async def end_user_session(
    session_id: str,
    reason: str = "user_logout"
) -> Dict[str, Any]:
    """End user session."""
    return await audit_logger.end_user_session(session_id, reason)


async def generate_compliance_report(
    standard: ComplianceStandard,
    start_date: datetime,
    end_date: datetime
) -> Dict[str, Any]:
    """Generate compliance report."""
    return await audit_logger.generate_compliance_report(standard, start_date, end_date)


async def search_audit_events(
    criteria: Dict[str, Any],
    limit: int = 100
) -> Dict[str, Any]:
    """Search audit events."""
    return await audit_logger.search_audit_events(criteria, limit)


def get_audit_logger_metrics() -> Dict[str, Any]:
    """Get audit logger metrics."""
    return audit_logger.get_audit_metrics()


async def log_api_access(user_id: str, endpoint: str, method: str, status_code: int, ip_address: str):
    """Log API access event."""
    return await audit_logger.log_api_access(user_id, endpoint, method, status_code, ip_address)


async def log_user_action(user_id: str, action: str, resource: str, result: str):
    """Log user action event."""
    return await audit_logger.log_user_action(user_id, action, resource, result)


async def log_security_event(event_type: str, severity: str, description: str, source: str):
    """Log security event."""
    return await audit_logger.log_security_event(event_type, severity, description, source)


async def run_simulation():
    """Run a full simulation of the AuditLogger's capabilities."""
    print("--- Running AuditLogger Simulation ---")

    # We are re-initializing the global logger, so we must declare it global at the start.
    global audit_logger

    # Clean up previous run's files for a fresh start
    config = audit_logger.config
    log_file = config['log_file']
    archive_dir = config['archive_dir']
    if os.path.exists(log_file):
        os.remove(log_file)
    if os.path.exists(archive_dir):
        import shutil
        shutil.rmtree(archive_dir)

    # Re-initialize logger to start with a clean state
    audit_logger = AuditLogger()

    print("\n[1] Logging various types of audit events...")
    await log_user_action("admin", "update_config", "system.settings", result="success")
    await log_api_access("user123", "/api/data", "GET", 200, "192.168.1.10")
    await log_security_event("firewall_block", "high", "Blocked suspicious inbound traffic", "firewall_service")
    await log_audit_event(
        AuditEventType.DATA_ACCESS, "user456", resource="/db/customer_records",
        action="read", security_level=SecurityLevel.HIGH,
        compliance_tags=[ComplianceStandard.GDPR, ComplianceStandard.PCI_DSS]
    )

    print("\n[2] Simulating a brute-force attack to trigger alerts...")
    for i in range(config['alert_thresholds']['failed_logins']):
        await log_audit_event(
            AuditEventType.USER_LOGIN, "attacker", result="failed",
            ip_address="10.0.0.99", security_level=SecurityLevel.CRITICAL
        )

    print("\n[3] Tracking a full user session...")
    session_id = "session_xyz_789"
    await track_user_session(session_id, "jane.doe", "203.0.113.50", "Chrome/98.0")
    await log_user_action("jane.doe", "create_report", "/reports/quarterly", result="success")
    await end_user_session(session_id)

    print("\n[4] Searching for specific audit events...")
    search_results = await search_audit_events({"user_id": "attacker"})
    print(f"Found {search_results.get('total_events')} events for user 'attacker'.")

    print("\n[5] Generating a compliance report...")
    report_result = await generate_compliance_report(
        ComplianceStandard.GDPR,
        datetime.now() - timedelta(days=1),
        datetime.now() + timedelta(days=1)
    )
    if report_result.get("success"):
        print(f"Successfully generated GDPR compliance report (ID: {report_result.get('report_id')}).")
        print(f"Compliance Score: {report_result['report']['compliance_score']:.2%}")

    print("\n[6] Verifying log integrity...")
    integrity_report = audit_logger.verify_log_integrity()
    print(f"Initial integrity verification successful: {integrity_report['verified']}")

    print("\n[7] Simulating log tampering and re-verifying...")

    # Tamper with the log file directly
    try:
        with open(log_file, 'r+') as f:
            events = json.load(f)
            if events:
                events[0]['details']['tampered'] = True # Change a detail
                f.seek(0)
                f.truncate()
                json.dump(events, f, indent=4, default=json_serializer)

        # Re-load the logger to read the tampered file
        tampered_logger = AuditLogger()
        integrity_report_after_tamper = tampered_logger.verify_log_integrity()
        print(f"Verification after tampering successful: {integrity_report_after_tamper['verified']}")
        if not integrity_report_after_tamper['verified']:
            print(f"Detected {integrity_report_after_tamper['tampered_events_count']} tampered event(s).")

    except (IOError, json.JSONDecodeError) as e:
        print(f"Could not simulate tampering: {e}")


    print("\n[8] Displaying final audit metrics...")
    metrics = get_audit_logger_metrics()
    print(json.dumps(metrics, indent=2, default=str))

    print("\n--- Simulation Complete ---")


if __name__ == "__main__":
    asyncio.run(run_simulation())
