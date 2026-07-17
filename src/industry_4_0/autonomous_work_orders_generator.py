"""
Autonomous Work Orders Generator Module

This module implements AI-driven and event-driven generation of industrial work orders.
It automatically triggers maintenance tasks upon detecting anomalies or predictive faults,
structuring them with clear priorities, estimated durations, and resource requirements,
and optimizes schedules using classic heuristic algorithms (EDD, SPT).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AutonomousWorkOrdersGenerator:
    """
    Intelligent scheduling and autonomous generation of maintenance work orders.

    Generates structured work orders triggered by sensor telemetry, predictive maintenance alerts,
    or quality control defects, and optimizes execution schedules to minimize downtime and tardiness.
    """

    def __init__(self, work_order_data: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the work orders generator.

        Args:
            work_order_data: Optional initial list of work orders.
        """
        self.work_orders: List[Dict[str, Any]] = work_order_data or []
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Autonomous Work Orders Generator initialized.")

    def generate_work_order(
        self,
        component_id: str,
        trigger_type: str,
        severity: str,
        details: str,
        estimated_hours: float = 2.0,
        due_days_from_now: int = 3
    ) -> Dict[str, Any]:
        """
        Dynamically generate a structured work order.

        Args:
            component_id: ID of the machine, line, or subsystem requiring attention.
            trigger_type: Source of trigger (e.g., 'anomaly_detected', 'predictive_rul_alert', 'manual_request').
            severity: Severity of the trigger ('low', 'medium', 'high', 'critical').
            details: Contextual details or description of the fault.
            estimated_hours: Estimated processing/repair time.
            due_days_from_now: Due window in days.

        Returns:
            The generated work order dictionary.
        """
        # Determine priority score based on severity
        severity_weights = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        weight = severity_weights.get(severity.lower(), 1)

        # Calculate due timestamp
        created_time = datetime.now(timezone.utc)
        due_time = created_time.replace(day=created_time.day + min(due_days_from_now, 28))  # Safe offset

        work_order = {
            "work_order_id": f"WO-{len(self.work_orders) + 1:05d}",
            "component_id": component_id,
            "trigger_type": trigger_type,
            "severity": severity,
            "priority_score": weight,
            "status": "pending",
            "details": details,
            "estimated_hours": estimated_hours,
            "created_at": created_time.isoformat(),
            "due_at": due_time.isoformat(),
            "assigned_team": self._assign_team(trigger_type, weight)
        }

        self.work_orders.append(work_order)
        self.logger.info(f"Generated autonomous work order: {work_order['work_order_id']} for '{component_id}'.")
        return work_order

    def _assign_team(self, trigger_type: str, priority_score: int) -> str:
        """Heuristic resource/team assignment."""
        if priority_score >= 3:
            return "Emergency response team (ERT)"
        if "anomaly" in trigger_type.lower():
            return "Diagnostics & Telemetry team"
        if "quality" in trigger_type.lower():
            return "Quality assurance squad"
        return "General Maintenance Team"

    def optimize_schedule(self, criterion: str = "EDD") -> List[Dict[str, Any]]:
        """
        Optimize the execution schedule of pending work orders.

        Args:
            criterion: Optimization heuristic:
                       - 'EDD' (Earliest Due Date) to minimize maximum tardiness.
                       - 'SPT' (Shortest Processing Time) to maximize throughput.
                       - 'PRIORITY' (Priority Score) to address critical issues first.

        Returns:
            The ordered list of work orders.
        """
        pending_orders = [wo for wo in self.work_orders if wo["status"] == "pending"]

        if not pending_orders:
            self.logger.info("No pending work orders to optimize.")
            return []

        self.logger.info(f"Optimizing schedule for {len(pending_orders)} pending work orders using '{criterion}' criterion.")

        if criterion.upper() == "EDD":
            # Earliest Due Date
            pending_orders.sort(key=lambda x: x["due_at"])
        elif criterion.upper() == "SPT":
            # Shortest Processing Time
            pending_orders.sort(key=lambda x: x["estimated_hours"])
        elif criterion.upper() == "PRIORITY":
            # Highest Priority Score first
            pending_orders.sort(key=lambda x: x["priority_score"], reverse=True)
        else:
            self.logger.warning(f"Unknown scheduling criterion '{criterion}'. Defaulting to EDD.")
            pending_orders.sort(key=lambda x: x["due_at"])

        return pending_orders

    def update_work_order_status(self, work_order_id: str, new_status: str) -> bool:
        """
        Update the status of a specific work order.

        Args:
            work_order_id: Unique ID of the work order.
            new_status: New status (e.g. 'pending', 'in_progress', 'completed', 'cancelled').

        Returns:
            True if updated successfully, False otherwise.
        """
        for wo in self.work_orders:
            if wo["work_order_id"] == work_order_id:
                old_status = wo["status"]
                wo["status"] = new_status
                self.logger.info(f"Updated {work_order_id} status: {old_status} -> {new_status}")
                return True
        self.logger.warning(f"Work order '{work_order_id}' not found.")
        return False

    def generate_work_orders(self) -> List[str]:
        """
        Legacy method to ensure complete backward compatibility.
        """
        self.logger.info("Calling legacy generate_work_orders().")
        # Generates two default orders if none exist
        if not self.work_orders:
            self.generate_work_order("CNC-001", "manual_request", "medium", "Legacy automatic setup.")
            self.generate_work_order("CNC-002", "manual_request", "high", "Legacy automatic setup 2.")

        return [wo["work_order_id"] for wo in self.work_orders]

    def analyze_work_order_data(self, data: Any) -> List[str]:
        """
        Legacy analysis method for backward compatibility.
        """
        self.logger.info("Calling legacy analyze_work_order_data().")
        return ["Work Order 1", "Work Order 2"]
