"""
Frontend integration utilities for dashboard and UI
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DashboardDataProvider:
    """Provide data for frontend dashboards."""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def get_machine_dashboard_data(self, machine_id: str) -> Dict[str, Any]:
        """Get dashboard data for a specific machine."""
        # This would integrate with the database
        return {
            "machine_id": machine_id,
            "status": "active",
            "current_metrics": {
                "temperature": 75.5,
                "vibration": 2.1,
                "power_consumption": 15.2,
            },
            "alerts": [
                {
                    "id": 1,
                    "severity": "warning",
                    "message": "High temperature detected",
                    "timestamp": datetime.now().isoformat(),
                }
            ],
            "charts": {
                "temperature_trend": self._generate_trend_data("temperature"),
                "performance_metrics": self._generate_performance_data(),
            },
        }

    async def get_overview_dashboard_data(self) -> Dict[str, Any]:
        """Get overview dashboard data."""
        return {
            "summary": {
                "total_machines": 25,
                "active_machines": 23,
                "alerts_today": 5,
                "efficiency_score": 87.5,
            },
            "charts": {
                "machine_status_distribution": {
                    "active": 23,
                    "maintenance": 1,
                    "offline": 1,
                },
                "alerts_over_time": self._generate_alerts_chart(),
                "efficiency_trend": self._generate_efficiency_trend(),
            },
            "recent_alerts": [
                {
                    "machine_id": "CNC-001",
                    "severity": "high",
                    "message": "Critical vibration levels",
                    "timestamp": datetime.now().isoformat(),
                }
            ],
        }

    async def get_analytics_dashboard_data(
        self, time_range: str = "24h"
    ) -> Dict[str, Any]:
        """Get analytics dashboard data."""
        return {
            "time_range": time_range,
            "kpis": {
                "mean_time_between_failures": 125.5,
                "overall_equipment_effectiveness": 85.2,
                "predictive_accuracy": 92.1,
                "cost_savings": 45000,
            },
            "charts": {
                "failure_prediction_accuracy": self._generate_accuracy_chart(),
                "maintenance_cost_trend": self._generate_cost_trend(),
                "downtime_analysis": self._generate_downtime_chart(),
            },
            "insights": [
                {
                    "type": "improvement",
                    "title": "Maintenance Optimization",
                    "description": "Preventive maintenance reduced downtime by 15%",
                    "impact": "high",
                }
            ],
        }

    def _generate_trend_data(self, metric: str) -> List[Dict[str, Any]]:
        """Generate sample trend data."""
        data = []
        base_time = datetime.now() - timedelta(hours=24)

        for i in range(24):
            data.append(
                {
                    "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                    "value": 70 + (i % 10) + (5 if metric == "temperature" else 0),
                }
            )

        return data

    def _generate_performance_data(self) -> List[Dict[str, Any]]:
        """Generate performance metrics data."""
        return [
            {"metric": "Availability", "value": 95.2, "target": 98.0},
            {"metric": "Performance", "value": 87.5, "target": 90.0},
            {"metric": "Quality", "value": 92.1, "target": 95.0},
            {"metric": "OEE", "value": 83.4, "target": 85.0},
        ]

    def _generate_alerts_chart(self) -> List[Dict[str, Any]]:
        """Generate alerts over time chart data."""
        data = []
        base_time = datetime.now() - timedelta(days=7)

        for i in range(7):
            data.append(
                {
                    "date": (base_time + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "critical": 2 + (i % 3),
                    "warning": 5 + (i % 5),
                    "info": 10 + (i % 8),
                }
            )

        return data

    def _generate_efficiency_trend(self) -> List[Dict[str, Any]]:
        """Generate efficiency trend data."""
        data = []
        base_time = datetime.now() - timedelta(days=30)

        for i in range(30):
            data.append(
                {
                    "date": (base_time + timedelta(days=i)).strftime("%Y-%m-%d"),
                    "efficiency": 80 + (i % 15) + (5 if i > 20 else 0),
                }
            )

        return data

    def _generate_accuracy_chart(self) -> List[Dict[str, Any]]:
        """Generate prediction accuracy chart."""
        return [
            {"model": "Temperature", "accuracy": 94.2},
            {"model": "Vibration", "accuracy": 89.7},
            {"model": "Power", "accuracy": 96.1},
            {"model": "Overall", "accuracy": 92.1},
        ]

    def _generate_cost_trend(self) -> List[Dict[str, Any]]:
        """Generate maintenance cost trend."""
        data = []
        base_time = datetime.now() - timedelta(months=6)

        for i in range(6):
            data.append(
                {
                    "month": (base_time + timedelta(days=30 * i)).strftime("%Y-%m"),
                    "preventive_cost": 5000 + (i * 200),
                    "corrective_cost": 15000 - (i * 800),
                    "total_savings": i * 3000,
                }
            )

        return data

    def _generate_downtime_chart(self) -> List[Dict[str, Any]]:
        """Generate downtime analysis chart."""
        return [
            {"category": "Planned Maintenance", "hours": 24, "percentage": 15.2},
            {"category": "Unplanned Failures", "hours": 45, "percentage": 28.3},
            {"category": "Setup/Changeover", "hours": 32, "percentage": 20.1},
            {"category": "Other", "hours": 58, "percentage": 36.4},
        ]


class APIResponseFormatter:
    """Format API responses for frontend consumption."""

    @staticmethod
    def format_success_response(
        data: Any, meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format successful API response."""
        response = {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        if meta:
            response["meta"] = meta

        return response

    @staticmethod
    def format_error_response(
        error: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Format error API response."""
        response = {
            "success": False,
            "error": {
                "message": error,
                "code": error_code,
                "timestamp": datetime.now().isoformat(),
            },
        }

        if details:
            response["error"]["details"] = details

        return response

    @staticmethod
    def format_paginated_response(
        data: List[Any], page: int, page_size: int, total: int
    ) -> Dict[str, Any]:
        """Format paginated API response."""
        return {
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
            "timestamp": datetime.now().isoformat(),
        }


class WebSocketMessageHandler:
    """Handle WebSocket messages for real-time updates."""

    def __init__(self):
        self.subscriptions: Dict[str, set] = {}

    async def handle_subscription(self, client_id: str, machine_ids: List[str]):
        """Handle client subscription to machine updates."""
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()

        self.subscriptions[client_id].update(machine_ids)
        logger.info(f"Client {client_id} subscribed to machines: {machine_ids}")

    async def handle_unsubscription(
        self, client_id: str, machine_ids: Optional[List[str]] = None
    ):
        """Handle client unsubscription."""
        if client_id in self.subscriptions:
            if machine_ids:
                self.subscriptions[client_id].difference_update(machine_ids)
            else:
                del self.subscriptions[client_id]
            logger.info(
                f"Client {client_id} unsubscribed from machines: {machine_ids or 'all'}"
            )

    async def broadcast_machine_update(self, machine_id: str, data: Dict[str, Any]):
        """Broadcast machine update to subscribed clients."""
        message = {
            "type": "machine_update",
            "machine_id": machine_id,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        # In a real implementation, this would send to WebSocket connections
        # For now, just log the broadcast
        subscribed_clients = [
            client_id
            for client_id, machines in self.subscriptions.items()
            if machine_id in machines
        ]

        if subscribed_clients:
            logger.info(
                f"Broadcasting update for {machine_id} to {len(subscribed_clients)} clients"
            )
        else:
            logger.debug(f"No clients subscribed to {machine_id}")

        return message

    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription statistics."""
        total_subscriptions = sum(
            len(machines) for machines in self.subscriptions.values()
        )
        return {
            "active_clients": len(self.subscriptions),
            "total_subscriptions": total_subscriptions,
            "subscriptions_per_client": {
                client_id: len(machines)
                for client_id, machines in self.subscriptions.items()
            },
        }


# Global instances
dashboard_provider = DashboardDataProvider()
response_formatter = APIResponseFormatter()
websocket_handler = WebSocketMessageHandler()
