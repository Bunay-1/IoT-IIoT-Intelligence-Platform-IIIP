"""
Cross-Factory Intelligence Network Module

This module implements a collaborative intelligence system connecting multiple industrial sites (factories).
It facilitates secure sharing of operational insights, federated KPI benchmarking,
cross-site anomaly propagation, and predictive resource routing.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CrossFactoryIntelligenceNetwork:
    """
    Stateful cross-factory intelligence network for collaborative Industry 5.0 operations.

    Allows registering multiple factories, sharing telemetry/operational insights,
    performing collaborative Overall Equipment Effectiveness (OEE) and KPI analysis,
    and propagating proactive anomaly advisories to prevent chain failures.
    """

    def __init__(self, network_id: str = "global-net-01"):
        """
        Initialize the intelligence network.

        Args:
            network_id: Unique identifier for this network.
        """
        self.network_id = network_id
        self.factories: Dict[str, Dict[str, Any]] = {}
        self.shared_insights_log: List[Dict[str, Any]] = []
        self.anomaly_advisories: List[Dict[str, Any]] = []
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Cross-Factory Intelligence Network '{self.network_id}' initialized.")

    def register_factory(
        self,
        factory_id: str,
        location: str,
        production_lines: List[str],
        base_kpis: Optional[Dict[str, float]] = None
    ) -> bool:
        """
        Register a factory in the collaborative network.

        Args:
            factory_id: Unique ID of the factory.
            location: Geolocation or descriptive name of the site.
            production_lines: List of production line identifiers.
            base_kpis: Optional dictionary of base KPIs.

        Returns:
            True if registration succeeded, False otherwise.
        """
        try:
            if factory_id in self.factories:
                self.logger.warning(f"Factory '{factory_id}' is already registered.")
                return False

            self.factories[factory_id] = {
                "factory_id": factory_id,
                "location": location,
                "production_lines": production_lines,
                "registered_at": datetime.now(timezone.utc).isoformat(),
                "current_kpis": base_kpis or {
                    "availability": 0.95,
                    "performance": 0.90,
                    "quality_rate": 0.98,
                    "oee": 0.8379,
                    "energy_efficiency_score": 85.0
                },
                "status": "nominal"
            }
            self.logger.info(f"Successfully registered factory '{factory_id}' in '{location}'.")
            return True
        except Exception as e:
            self.logger.error(f"Error registering factory '{factory_id}': {e}")
            return False

    def share_insights(self, factory_id: str, insight_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Share an operational insight or ML telemetry summary from a specific factory.

        Args:
            factory_id: ID of the sharing factory.
            insight_type: Type of insight (e.g., 'predictive_maintenance', 'tool_wear_model', 'quality_alert').
            data: Key-value data of the insight.

        Returns:
            The recorded insight log metadata.
        """
        if factory_id not in self.factories:
            raise ValueError(f"Factory '{factory_id}' is not registered in this network.")

        insight_log = {
            "insight_id": f"ins-{len(self.shared_insights_log) + 1:04d}",
            "sender_factory_id": factory_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "insight_type": insight_type,
            "payload": data,
            "security_seal": f"sha256-sim-{hash(factory_id) + len(self.shared_insights_log)}"
        }

        self.shared_insights_log.append(insight_log)
        self.logger.info(f"Recorded shared insight '{insight_log['insight_id']}' from factory '{factory_id}'.")
        return insight_log

    def perform_network_kpi_benchmarking(self) -> Dict[str, Any]:
        """
        Benchmark Overall Equipment Effectiveness (OEE) and other key metrics across all registered sites.

        Returns:
            A dictionary containing comparative KPIs, averages, and the best-performing site (Leader).
        """
        if not self.factories:
            return {"error": "No factories registered in the network."}

        records = []
        for fid, f_data in self.factories.items():
            kpis = f_data["current_kpis"]
            records.append({
                "factory_id": fid,
                "location": f_data["location"],
                "oee": kpis.get("oee", 0.0),
                "availability": kpis.get("availability", 0.0),
                "performance": kpis.get("performance", 0.0),
                "quality_rate": kpis.get("quality_rate", 0.0),
                "energy_efficiency": kpis.get("energy_efficiency_score", 0.0)
            })

        df = pd.DataFrame(records)
        avg_oee = float(df["oee"].mean())
        avg_energy = float(df["energy_efficiency"].mean())

        leader_row = df.loc[df["oee"].idxmax()] if not df.empty else None
        leader_id = leader_row["factory_id"] if leader_row is not None else "N/A"

        result = {
            "benchmark_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_network_sites": len(self.factories),
            "averages": {
                "oee": avg_oee,
                "availability": float(df["availability"].mean()),
                "performance": float(df["performance"].mean()),
                "quality_rate": float(df["quality_rate"].mean()),
                "energy_efficiency_score": avg_energy
            },
            "factory_leaderboard": df.sort_values(by="oee", ascending=False).to_dict(orient="records"),
            "network_leader_site": leader_id
        }
        self.logger.info(f"Cross-factory KPI benchmarking complete. Leader site: {leader_id}")
        return result

    def propagate_anomaly_advisory(
        self,
        origin_factory_id: str,
        severity: str,
        critical_component: str,
        root_cause_analysis: str
    ) -> Dict[str, Any]:
        """
        Propagate an anomaly warning/advisory to all other factories in the network
        to trigger proactive/self-healing configurations.

        Args:
            origin_factory_id: Factory where the anomaly occurred.
            severity: Severity level ('low', 'medium', 'high', 'critical').
            critical_component: Component or subsystem affected.
            root_cause_analysis: Causal findings or warning details.

        Returns:
            Advisory details and propagation receipts.
        """
        if origin_factory_id not in self.factories:
            raise ValueError(f"Origin factory '{origin_factory_id}' is not registered.")

        advisory_id = f"adv-{len(self.anomaly_advisories) + 1:04d}"
        recipients = [fid for fid in self.factories if fid != origin_factory_id]

        advisory = {
            "advisory_id": advisory_id,
            "origin_factory_id": origin_factory_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": severity,
            "critical_component": critical_component,
            "details": root_cause_analysis,
            "propagated_to": recipients
        }

        self.anomaly_advisories.append(advisory)

        # Simulating advisory delivery
        for recipient in recipients:
            self.factories[recipient]["status"] = "advisory_active"
            self.logger.info(f"Delivered advisory '{advisory_id}' to factory '{recipient}'. Status updated to 'advisory_active'.")

        self.logger.warning(f"Propagated critical anomaly advisory '{advisory_id}' from '{origin_factory_id}' to {len(recipients)} sites.")
        return advisory

    def get_factory_status(self, factory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current operational status and recorded details of a factory.

        Args:
            factory_id: Unique ID of the factory.

        Returns:
            The factory details dictionary, or None if not found.
        """
        return self.factories.get(factory_id)

    def analyze_factory_data(self, factory_id: str) -> str:
        """
        Legacy mock analytical method to ensure complete backward compatibility.
        """
        if factory_id in self.factories:
            return f"Factory insights analyzed for {factory_id}"
        return "Factory insights analyzed"
