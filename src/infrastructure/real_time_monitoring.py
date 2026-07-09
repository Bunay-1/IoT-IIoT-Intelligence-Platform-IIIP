#!/usr/bin/env python3
"""
Real-time Monitoring and Alerting Service
Provides real-time updates and intelligent alerting for the central dashboard
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

@dataclass
class Alert:
    id: str
    title: str
    message: str
    level: AlertLevel
    status: AlertStatus
    module: str
    timestamp: datetime
    metadata: Dict[str, Any]
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None

class RealTimeMonitoringService:
    """Real-time monitoring and alerting service"""
    
    def __init__(self):
        self.active_connections: Set = set()
        self.alerts: Dict[str, Alert] = {}
        self.system_metrics = {}
        self.module_status = {}
        self.alert_counter = 0
        
    async def register_connection(self, websocket):
        """Register WebSocket connection for real-time updates"""
        self.active_connections.add(websocket)
        logger.info(f"New WebSocket connection registered. Total: {len(self.active_connections)}")
        
    async def unregister_connection(self, websocket):
        """Unregister WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket connection removed. Total: {len(self.active_connections)}")
        
    async def broadcast_update(self, message_type: str, data: Dict[str, Any]):
        """Broadcast update to all connected clients"""
        if not self.active_connections:
            return
            
        message = {
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Failed to send update to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.active_connections.discard(connection)
    
    async def create_alert(self, 
                          title: str,
                          message: str,
                          level: AlertLevel,
                          module: str,
                          metadata: Dict[str, Any] = None) -> Alert:
        """Create and broadcast new alert"""
        self.alert_counter += 1
        alert_id = f"alert_{self.alert_counter}_{int(datetime.now().timestamp())}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            level=level,
            status=AlertStatus.ACTIVE,
            module=module,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.alerts[alert_id] = alert
        
        # Broadcast alert
        await self.broadcast_update("new_alert", {
            "alert": {
                "id": alert.id,
                "title": alert.title,
                "message": alert.message,
                "level": alert.level.value,
                "status": alert.status.value,
                "module": alert.module,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
        })
        
        logger.warning(f"New alert created: {title} - {message}")
        return alert
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system"):
        """Acknowledge an alert"""
        if alert_id not in self.alerts:
            return False
            
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        
        await self.broadcast_update("alert_acknowledged", {
            "alert_id": alert_id,
            "acknowledged_by": acknowledged_by,
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        if alert_id not in self.alerts:
            return False
            
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        
        await self.broadcast_update("alert_resolved", {
            "alert_id": alert_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    async def update_system_metrics(self, metrics: Dict[str, Any]):
        """Update system metrics and broadcast"""
        self.system_metrics.update(metrics)
        
        await self.broadcast_update("system_metrics", {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        
        # Check for threshold alerts
        await self._check_metric_thresholds(metrics)
    
    async def update_module_status(self, module_name: str, status: Dict[str, Any]):
        """Update module status and broadcast"""
        self.module_status[module_name] = status
        
        await self.broadcast_update("module_status", {
            "module": module_name,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
        # Check for module alerts
        await self._check_module_alerts(module_name, status)
    
    async def _check_metric_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and create alerts"""
        thresholds = {
            "cpu_usage": {"warning": 70, "critical": 90},
            "memory_usage": {"warning": 75, "critical": 95},
            "disk_usage": {"warning": 80, "critical": 95},
            "error_rate": {"warning": 5, "critical": 10}
        }
        
        for metric, value in metrics.items():
            if metric in thresholds and isinstance(value, (int, float)):
                threshold = thresholds[metric]
                
                if value >= threshold["critical"]:
                    await self.create_alert(
                        title=f"Critical {metric.replace('_', ' ').title()}",
                        message=f"{metric.replace('_', ' ').title()} is at {value}%, exceeding critical threshold of {threshold['critical']}%",
                        level=AlertLevel.CRITICAL,
                        module="system_monitor",
                        metadata={"metric": metric, "value": value, "threshold": threshold["critical"]}
                    )
                elif value >= threshold["warning"]:
                    await self.create_alert(
                        title=f"High {metric.replace('_', ' ').title()}",
                        message=f"{metric.replace('_', ' ').title()} is at {value}%, exceeding warning threshold of {threshold['warning']}%",
                        level=AlertLevel.WARNING,
                        module="system_monitor",
                        metadata={"metric": metric, "value": value, "threshold": threshold["warning"]}
                    )
    
    async def _check_module_alerts(self, module_name: str, status: Dict[str, Any]):
        """Check module status for alerts"""
        if status.get("status") == "error":
            await self.create_alert(
                title=f"Module Error: {module_name}",
                message=f"Module {module_name} has encountered an error",
                level=AlertLevel.ERROR,
                module=module_name,
                metadata=status
            )
        elif status.get("status") == "offline":
            await self.create_alert(
                title=f"Module Offline: {module_name}",
                message=f"Module {module_name} is offline",
                level=AlertLevel.WARNING,
                module=module_name,
                metadata=status
            )
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        active_alerts = []
        
        for alert in self.alerts.values():
            if alert.status in [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]:
                active_alerts.append({
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "level": alert.level.value,
                    "status": alert.status.value,
                    "module": alert.module,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata,
                    "acknowledged_by": alert.acknowledged_by
                })
        
        # Sort by timestamp (newest first)
        active_alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        return active_alerts
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        active_alerts = await self.get_active_alerts()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": {
                "status": "healthy" if len([a for a in active_alerts if a["level"] == "critical"]) == 0 else "degraded",
                "active_alerts": len(active_alerts),
                "critical_alerts": len([a for a in active_alerts if a["level"] == "critical"]),
                "warning_alerts": len([a for a in active_alerts if a["level"] == "warning"]),
                "connected_clients": len(self.active_connections)
            },
            "metrics": self.system_metrics,
            "modules": self.module_status,
            "recent_alerts": active_alerts[:10]  # Last 10 alerts
        }
    
    async def start_monitoring_loop(self):
        """Start the monitoring loop for periodic updates"""
        while True:
            try:
                # Simulate metric updates
                await self.update_system_metrics({
                    "cpu_usage": 45 + (hash(datetime.now().isoformat()) % 20),
                    "memory_usage": 60 + (hash(datetime.now().isoformat()) % 15),
                    "disk_usage": 35 + (hash(datetime.now().isoformat()) % 10),
                    "active_connections": len(self.active_connections),
                    "uptime": "15d 7h 23m"
                })
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

# Global instance
real_time_monitor = RealTimeMonitoringService()
