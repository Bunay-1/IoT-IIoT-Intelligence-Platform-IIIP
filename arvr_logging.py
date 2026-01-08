"""
AR/VR Logging Module

This module implements comprehensive logging for AR/VR systems including:
- Session logging and tracking
- Performance metrics logging
- Error and exception handling
- User interaction logging
- System event logging
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from utils.logging_config import get_logger

logger = get_logger(__name__)


class ARVRLogging:
    """AR/VR specific logging system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.session_logs = {}
        self.performance_logs = []
        self.error_logs = []
        self.interaction_logs = []
        self.system_logs = []
        
    def _default_config(self) -> Dict[str, Any]:
        """Default AR/VR logging configuration."""
        return {
            "log_levels": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "retention_days": 30,
            "max_log_size": 1000,
            "log_to_file": True,
            "log_to_database": True,
            "real_time_monitoring": True
        }
    
    def log_session_event(
        self,
        session_id: str,
        event_type: str,
        details: Dict[str, Any],
        severity: str = "INFO"
    ) -> bool:
        """Log AR/VR session event."""
        if session_id not in self.session_logs:
            self.session_logs[session_id] = {
                "session_id": session_id,
                "events": [],
                "created_at": datetime.now(),
                "last_updated": datetime.now()
            }
        
        event = {
            "timestamp": datetime.now(),
            "event_type": event_type,
            "severity": severity,
            "details": details
        }
        
        self.session_logs[session_id]["events"].append(event)
        self.session_logs[session_id]["last_updated"] = datetime.now()
        
        # Limit event history
        if len(self.session_logs[session_id]["events"]) > self.config["max_log_size"]:
            self.session_logs[session_id]["events"] = self.session_logs[session_id]["events"][-self.config["max_log_size"]:]
        
        logger.info(f"AR/VR Session Event: {session_id} - {event_type}")
        return True
    
    def log_performance_metrics(
        self,
        session_id: str,
        metrics: Dict[str, Any]
    ) -> bool:
        """Log performance metrics."""
        performance_entry = {
            "timestamp": datetime.now(),
            "session_id": session_id,
            "metrics": metrics
        }
        
        self.performance_logs.append(performance_entry)
        
        # Limit performance logs
        if len(self.performance_logs) > self.config["max_log_size"]:
            self.performance_logs = self.performance_logs[-self.config["max_log_size"]:]
        
        logger.debug(f"AR/VR Performance: {session_id} - FPS: {metrics.get('fps', 'N/A')}")
        return True
    
    def log_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log AR/VR error."""
        error_entry = {
            "timestamp": datetime.now(),
            "session_id": session_id,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "context": context or {}
        }
        
        self.error_logs.append(error_entry)
        
        # Limit error logs
        if len(self.error_logs) > self.config["max_log_size"]:
            self.error_logs = self.error_logs[-self.config["max_log_size"]:]
        
        logger.error(f"AR/VR Error: {session_id} - {error_type}: {error_message}")
        return True
    
    def log_user_interaction(
        self,
        session_id: str,
        user_id: str,
        interaction_type: str,
        interaction_data: Dict[str, Any]
    ) -> bool:
        """Log user interaction."""
        interaction_entry = {
            "timestamp": datetime.now(),
            "session_id": session_id,
            "user_id": user_id,
            "interaction_type": interaction_type,
            "interaction_data": interaction_data
        }
        
        self.interaction_logs.append(interaction_entry)
        
        # Limit interaction logs
        if len(self.interaction_logs) > self.config["max_log_size"]:
            self.interaction_logs = self.interaction_logs[-self.config["max_log_size"]:]
        
        logger.debug(f"AR/VR Interaction: {user_id} - {interaction_type}")
        return True
    
    def log_system_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        severity: str = "INFO"
    ) -> bool:
        """Log system event."""
        system_entry = {
            "timestamp": datetime.now(),
            "event_type": event_type,
            "severity": severity,
            "event_data": event_data
        }
        
        self.system_logs.append(system_entry)
        
        # Limit system logs
        if len(self.system_logs) > self.config["max_log_size"]:
            self.system_logs = self.system_logs[-self.config["max_log_size"]:]
        
        logger.info(f"AR/VR System Event: {event_type}")
        return True
    
    def get_session_logs(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get logs for specific session."""
        return self.session_logs.get(session_id)
    
    def get_performance_logs(
        self,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get performance logs."""
        logs = self.performance_logs
        
        if session_id:
            logs = [log for log in logs if log["session_id"] == session_id]
        
        return logs[-limit:]
    
    def get_error_logs(
        self,
        session_id: Optional[str] = None,
        error_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get error logs."""
        logs = self.error_logs
        
        if session_id:
            logs = [log for log in logs if log["session_id"] == session_id]
        
        if error_type:
            logs = [log for log in logs if log["error_type"] == error_type]
        
        return logs[-limit:]
    
    def get_interaction_logs(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        interaction_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get interaction logs."""
        logs = self.interaction_logs
        
        if session_id:
            logs = [log for log in logs if log["session_id"] == session_id]
        
        if user_id:
            logs = [log for log in logs if log["user_id"] == user_id]
        
        if interaction_type:
            logs = [log for log in logs if log["interaction_type"] == interaction_type]
        
        return logs[-limit:]
    
    def get_system_logs(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get system logs."""
        logs = self.system_logs
        
        if event_type:
            logs = [log for log in logs if log["event_type"] == event_type]
        
        if severity:
            logs = [log for log in logs if log["severity"] == severity]
        
        return logs[-limit:]
    
    def get_logging_metrics(self) -> Dict[str, Any]:
        """Get logging system metrics."""
        return {
            "total_sessions": len(self.session_logs),
            "total_performance_logs": len(self.performance_logs),
            "total_error_logs": len(self.error_logs),
            "total_interaction_logs": len(self.interaction_logs),
            "total_system_logs": len(self.system_logs),
            "average_events_per_session": sum(
                len(session["events"]) 
                for session in self.session_logs.values()
            ) / len(self.session_logs) if self.session_logs else 0,
            "recent_errors": len([
                error for error in self.error_logs
                if (datetime.now() - error["timestamp"]).total_seconds() < 3600
            ]),
            "logging_uptime": str(datetime.now() - datetime.now().replace(hour=0, minute=0, second=0))
        }
    
    def cleanup_old_logs(self) -> bool:
        """Clean up old logs based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.config["retention_days"])
        
        # Clean session logs
        old_sessions = [
            session_id for session_id, session in self.session_logs.items()
            if session["last_updated"] < cutoff_date
        ]
        
        for session_id in old_sessions:
            del self.session_logs[session_id]
        
        # Clean performance logs
        self.performance_logs = [
            log for log in self.performance_logs
            if log["timestamp"] >= cutoff_date
        ]
        
        # Clean error logs
        self.error_logs = [
            log for log in self.error_logs
            if log["timestamp"] >= cutoff_date
        ]
        
        # Clean interaction logs
        self.interaction_logs = [
            log for log in self.interaction_logs
            if log["timestamp"] >= cutoff_date
        ]
        
        # Clean system logs
        self.system_logs = [
            log for log in self.system_logs
            if log["timestamp"] >= cutoff_date
        ]
        
        logger.info(f"AR/VR Log cleanup completed. Removed {len(old_sessions)} old sessions.")
        return True


# Global AR/VR logging instance
arvr_logging = ARVRLogging()


def log_arvr_session_event(
    session_id: str,
    event_type: str,
    details: Dict[str, Any],
    severity: str = "INFO"
) -> bool:
    """Log AR/VR session event."""
    return arvr_logging.log_session_event(session_id, event_type, details, severity)


def log_arvr_performance_metrics(
    session_id: str,
    metrics: Dict[str, Any]
) -> bool:
    """Log performance metrics."""
    return arvr_logging.log_performance_metrics(session_id, metrics)


def log_arvr_error(
    session_id: str,
    error_type: str,
    error_message: str,
    stack_trace: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> bool:
    """Log AR/VR error."""
    return arvr_logging.log_error(session_id, error_type, error_message, stack_trace, context)


def log_arvr_user_interaction(
    session_id: str,
    user_id: str,
    interaction_type: str,
    interaction_data: Dict[str, Any]
) -> bool:
    """Log user interaction."""
    return arvr_logging.log_user_interaction(session_id, user_id, interaction_type, interaction_data)


def log_arvr_system_event(
    event_type: str,
    event_data: Dict[str, Any],
    severity: str = "INFO"
) -> bool:
    """Log system event."""
    return arvr_logging.log_system_event(event_type, event_data, severity)


def get_arvr_logging_metrics() -> Dict[str, Any]:
    """Get logging system metrics."""
    return arvr_logging.get_logging_metrics()
