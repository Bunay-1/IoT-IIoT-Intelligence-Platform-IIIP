"""
Fleet Management Manager Module

This module implements comprehensive fleet management for industrial vehicles (AGVs, forklifts, drones).
It monitors real-time telemetry, tracks battery and state-of-health, computes optimized routes,
and provides interactive, non-blocking Plotly visualizations for Dash integrations.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class FleetManagementManager:
    """
    Stateful manager for industrial fleet telemetry, routing, and operational dashboards.

    Manages AGVs, automated forklifts, and utility drones. Recommends heuristic routing
    and generates Plotly figures of fleet statistics, with support for hosting a Dash dashboard.
    """

    def __init__(self, fleet_data: Optional[pd.DataFrame] = None):
        """
        Initialize the fleet management manager.

        Args:
            fleet_data: Optional pre-loaded vehicle DataFrame.
        """
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.vehicles: Dict[str, Dict[str, Any]] = {}

        if fleet_data is not None and not fleet_data.empty:
            self._load_from_df(fleet_data)
        else:
            # Register a few default AGVs
            self.register_vehicle("AGV-01", "autonomous_tugger", 0.95, (42.6977, 23.3219))
            self.register_vehicle("AGV-02", "automated_forklift", 0.88, (42.6980, 23.3225))
            self.register_vehicle("Drone-01", "delivery_quadcopter", 1.00, (42.6950, 23.3200))

        # Setup Dash app (lazy initialization)
        self.app: Optional[Dash] = None
        self.logger.info("Fleet Management Manager initialized.")

    def _load_from_df(self, df: pd.DataFrame):
        """Internal helper to load vehicles from a Pandas DataFrame."""
        for _, row in df.iterrows():
            vid = str(row.get("asset", f"Asset-{len(self.vehicles) + 1}"))
            self.vehicles[vid] = {
                "vehicle_id": vid,
                "vehicle_type": str(row.get("type", "AGV")),
                "status": str(row.get("status", "idle")),
                "battery_level": float(row.get("battery_level", 1.0)),
                "location": (float(row.get("latitude", 42.6977)), float(row.get("longitude", 23.3219))),
                "speed_mps": float(row.get("speed_mps", 0.0)),
                "cargo_loaded": bool(row.get("cargo_loaded", False)),
                "last_update": datetime.now(timezone.utc).isoformat()
            }

    def register_vehicle(
        self,
        vehicle_id: str,
        vehicle_type: str,
        battery_level: float = 1.0,
        current_location: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Register a new industrial vehicle in the fleet.

        Args:
            vehicle_id: Unique ID of the vehicle (e.g. 'AGV-05').
            vehicle_type: Category ('automated_forklift', 'delivery_quadcopter', etc.).
            battery_level: Initial battery charge (0.0 to 1.0).
            current_location: Initial GPS or coordinate tuple (lat, lon).

        Returns:
            The registered vehicle metadata.
        """
        if vehicle_id in self.vehicles:
            self.logger.warning(f"Vehicle '{vehicle_id}' already registered.")
            return self.vehicles[vehicle_id]

        vehicle = {
            "vehicle_id": vehicle_id,
            "vehicle_type": vehicle_type,
            "status": "idle",
            "battery_level": max(0.0, min(1.0, battery_level)),
            "location": current_location or (42.6977 + np.random.normal(0, 0.005), 23.3219 + np.random.normal(0, 0.005)),
            "speed_mps": 0.0,
            "cargo_loaded": False,
            "last_update": datetime.now(timezone.utc).isoformat()
        }

        self.vehicles[vehicle_id] = vehicle
        self.logger.info(f"Registered industrial vehicle '{vehicle_id}' ({vehicle_type}).")
        return vehicle

    def update_telemetry(
        self,
        vehicle_id: str,
        location: Tuple[float, float],
        battery_level: float,
        speed_mps: float,
        cargo_loaded: bool,
        status: str = "active"
    ) -> bool:
        """
        Update the real-time telemetry state of a vehicle.

        Args:
            vehicle_id: Unique ID of the vehicle.
            location: New (lat, lon) coordinates.
            battery_level: Current battery charge (0.0 to 1.0).
            speed_mps: Instantaneous speed in meters per second.
            cargo_loaded: Whether cargo is currently loaded.
            status: General operational status ('active', 'idle', 'charging', 'critical').

        Returns:
            True if updated successfully, False otherwise.
        """
        if vehicle_id not in self.vehicles:
            self.logger.warning(f"Vehicle '{vehicle_id}' not found.")
            return False

        vehicle = self.vehicles[vehicle_id]
        vehicle.update({
            "location": location,
            "battery_level": max(0.0, min(1.0, battery_level)),
            "speed_mps": max(0.0, speed_mps),
            "cargo_loaded": cargo_loaded,
            "status": status,
            "last_update": datetime.now(timezone.utc).isoformat()
        })
        self.logger.debug(f"Telemetry updated for '{vehicle_id}': status='{status}', battery={battery_level:.2%}")
        return True

    def recommend_route(self, vehicle_id: str, destination: Tuple[float, float]) -> Dict[str, Any]:
        """
        Compute an optimized route recommendation based on distance heuristics.

        Args:
            vehicle_id: ID of the routing vehicle.
            destination: Target coordinates (lat, lon).

        Returns:
            A route recommendation payload with route paths, distance, and estimated time.
        """
        if vehicle_id not in self.vehicles:
            raise ValueError(f"Vehicle '{vehicle_id}' is not registered.")

        vehicle = self.vehicles[vehicle_id]
        start_loc = vehicle["location"]

        # Simple Euclidean distance estimate (approx. 111km per degree)
        lat_diff = destination[0] - start_loc[0]
        lon_diff = destination[1] - start_loc[1]
        distance_km = np.sqrt(lat_diff**2 + lon_diff**2) * 111.0

        # Estimate duration based on speed
        speed_kmh = (vehicle["speed_mps"] * 3.6) if vehicle["speed_mps"] > 0 else 10.0  # fallback 10km/h
        duration_hours = distance_km / speed_kmh

        # Generate linear waypoint sequence
        waypoints = [
            start_loc,
            (start_loc[0] + lat_diff * 0.5, start_loc[1] + lon_diff * 0.5),
            destination
        ]

        route_plan = {
            "vehicle_id": vehicle_id,
            "start_point": start_loc,
            "destination": destination,
            "estimated_distance_km": float(distance_km),
            "estimated_duration_minutes": float(duration_hours * 60.0),
            "waypoints": waypoints,
            "safety_assessment": "clear" if vehicle["battery_level"] > 0.2 else "recharge_warning"
        }

        self.logger.info(f"Recommended route for '{vehicle_id}' to {destination}: {distance_km:.2f} km.")
        return route_plan

    def to_pandas(self) -> pd.DataFrame:
        """Convert fleet state to a Pandas DataFrame."""
        records = []
        for vid, data in self.vehicles.items():
            records.append({
                "asset": vid,
                "type": data["vehicle_type"],
                "status": data["status"],
                "battery_level": data["battery_level"],
                "latitude": data["location"][0],
                "longitude": data["location"][1],
                "speed_mps": data["speed_mps"],
                "cargo_loaded": data["cargo_loaded"]
            })
        return pd.DataFrame(records)

    def generate_status_figure(self) -> Any:
        """
        Generate a Plotly Express bar figure representing fleet status distribution.

        Returns:
            Plotly Express Figure.
        """
        df = self.to_pandas()
        fig = px.bar(
            df,
            x="status",
            color="type",
            title="Индустриален флот: Статус по видове активи",
            labels={"status": "Работен Статус", "count": "Брой Активи"},
            barmode="group"
        )
        return fig

    def generate_battery_figure(self) -> Any:
        """
        Generate a Plotly Express scatter figure representing battery level vs. speed.

        Returns:
            Plotly Express Figure.
        """
        df = self.to_pandas()
        fig = px.scatter(
            df,
            x="battery_level",
            y="speed_mps",
            color="status",
            size="speed_mps",
            hover_name="asset",
            title="Телеметрия: Заряд на батерията спрямо скорост",
            labels={"battery_level": "Ниво на батерията (0-1)", "speed_mps": "Скорост (m/s)"}
        )
        return fig

    def _create_layout(self) -> html.Div:
        """Create Dash layout."""
        df = self.to_pandas()
        return html.Div([
            html.H1("Fleet Management Dashboard - Industry 5.0", style={"textAlign": "center"}),
            html.Div([
                html.Label("Изберете актив за подробна статистика:"),
                dcc.Dropdown(
                    id="fleet-dropdown",
                    options=[{"label": asset, "value": asset} for asset in df["asset"].unique()],
                    value=df["asset"].iloc[0] if not df.empty else None,
                    clearable=False
                )
            ], style={"width": "50%", "margin": "0 auto"}),
            dcc.Graph(id="fleet-graph")
        ])

    def run(self, host: str = "127.0.0.1", port: int = 8051, debug: bool = False):
        """
        Build and start the local Dash dashboard application.

        Args:
            host: Dashboard host address.
            port: Dashboard port.
            debug: Debug mode boolean.
        """
        self.app = Dash(__name__)
        self.app.layout = self._create_layout()

        @self.app.callback(
            Output("fleet-graph", "figure"),
            Input("fleet-dropdown", "value")
        )
        def update_graph(asset):
            df = self.to_pandas()
            asset_data = df[df["asset"] == asset]
            return px.bar(asset_data, x="status", title=f"Текущ Статус за {asset}")

        self.logger.info(f"Starting Fleet Management Dashboard on http://{host}:{port}")
        self.app.run_server(host=host, port=port, debug=debug)
