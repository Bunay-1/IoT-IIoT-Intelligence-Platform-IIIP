"""
Mixed Reality Dashboard Module for IoT IIoT Intelligence Platform

This module provides mixed reality dashboards for real-time monitoring and control
of industrial processes, combining virtual and physical environments.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class DashboardWidget:
    """Represents a dashboard widget."""
    widget_id: str
    widget_type: str  # 'gauge', 'chart', 'alert', 'control', '3d_model'
    title: str
    data_source: str
    position: Dict[str, float]  # x, y, z coordinates in MR space
    size: Dict[str, float]  # width, height, depth
    properties: Dict[str, Any] = field(default_factory=dict)
    update_interval: int = 5  # seconds
    last_update: Optional[float] = None

@dataclass
class MRDashboard:
    """Mixed reality dashboard configuration."""
    dashboard_id: str
    title: str
    workspace: str  # physical or virtual workspace
    widgets: List[DashboardWidget] = field(default_factory=list)
    user_permissions: List[str] = field(default_factory=list)
    layout_preset: str = "default"
    theme: str = "industrial"

class MixedRealityDashboard:
    """
    Mixed Reality Dashboard for real-time industrial monitoring.
    Provides immersive, interactive dashboards combining VR and physical spaces.
    """

    def __init__(self, dashboards_path: str = "data/mr_dashboards.json",
                 data_connectors_path: str = "data/data_connectors.json"):
        """
        Initialize mixed reality dashboard system.

        Args:
            dashboards_path: Path to dashboard configurations
            data_connectors_path: Path to data connector configurations
        """
        self.dashboards_path = Path(dashboards_path)
        self.data_connectors_path = Path(data_connectors_path)

        self.dashboards_path.parent.mkdir(parents=True, exist_ok=True)
        self.data_connectors_path.parent.mkdir(parents=True, exist_ok=True)

        self.dashboards: Dict[str, MRDashboard] = {}
        self.data_connectors: Dict[str, Dict] = {}
        self.active_sessions: Dict[str, Dict] = {}

        # Load configurations
        self._load_dashboards()
        self._load_data_connectors()

        # Initialize default dashboard if none exist
        if not self.dashboards:
            self._create_default_dashboard()

    def _load_dashboards(self):
        """Load dashboard configurations."""
        try:
            if self.dashboards_path.exists():
                with open(self.dashboards_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for dashboard_data in data.get('dashboards', []):
                        dashboard = self._deserialize_dashboard(dashboard_data)
                        self.dashboards[dashboard.dashboard_id] = dashboard
                logger.info(f"Loaded {len(self.dashboards)} MR dashboards")
        except Exception as e:
            logger.error(f"Failed to load dashboards: {e}")

    def _load_data_connectors(self):
        """Load data connector configurations."""
        try:
            if self.data_connectors_path.exists():
                with open(self.data_connectors_path, 'r', encoding='utf-8') as f:
                    self.data_connectors = json.load(f)
                logger.info(f"Loaded {len(self.data_connectors)} data connectors")
            else:
                # Create default connectors
                self._create_default_connectors()
        except Exception as e:
            logger.error(f"Failed to load data connectors: {e}")

    def _create_default_dashboard(self):
        """Create a default production monitoring dashboard."""
        dashboard = MRDashboard(
            dashboard_id="production_monitoring_001",
            title="Production Line MR Dashboard",
            workspace="assembly_line",
            widgets=[
                DashboardWidget(
                    widget_id="machine_status_gauge",
                    widget_type="gauge",
                    title="Machine Status",
                    data_source="machine_status",
                    position={"x": 0.0, "y": 1.5, "z": -2.0},
                    size={"width": 0.5, "height": 0.5, "depth": 0.1},
                    properties={
                        "min_value": 0,
                        "max_value": 100,
                        "units": "%",
                        "color_scheme": "traffic_light"
                    }
                ),
                DashboardWidget(
                    widget_id="production_chart",
                    widget_type="chart",
                    title="Production Rate",
                    data_source="production_metrics",
                    position={"x": 1.0, "y": 1.2, "z": -2.0},
                    size={"width": 1.0, "height": 0.6, "depth": 0.1},
                    properties={
                        "chart_type": "line",
                        "time_window": 3600,  # 1 hour
                        "metrics": ["units_per_hour", "efficiency"]
                    }
                ),
                DashboardWidget(
                    widget_id="alert_panel",
                    widget_type="alert",
                    title="Active Alerts",
                    data_source="alert_system",
                    position={"x": -1.0, "y": 1.8, "z": -2.0},
                    size={"width": 0.8, "height": 0.4, "depth": 0.1},
                    properties={
                        "max_alerts": 5,
                        "severity_filter": ["critical", "warning"],
                        "auto_dismiss": False
                    }
                ),
                DashboardWidget(
                    widget_id="control_panel",
                    widget_type="control",
                    title="Process Controls",
                    data_source="process_controls",
                    position={"x": 0.5, "y": 0.8, "z": -1.5},
                    size={"width": 0.6, "height": 0.8, "depth": 0.1},
                    properties={
                        "controls": ["start_stop", "speed_adjust", "emergency_stop"],
                        "permissions_required": ["operator", "supervisor"]
                    }
                ),
                DashboardWidget(
                    widget_id="equipment_model",
                    widget_type="3d_model",
                    title="Equipment 3D Model",
                    data_source="equipment_model",
                    position={"x": -1.5, "y": 0.0, "z": -3.0},
                    size={"width": 2.0, "height": 2.0, "depth": 2.0},
                    properties={
                        "model_source": "digital_twin",
                        "interactive": True,
                        "show_measurements": True,
                        "highlight_anomalies": True
                    }
                )
            ],
            user_permissions=["operator", "supervisor", "maintenance"],
            layout_preset="production_line",
            theme="industrial_dark"
        )

        self.dashboards[dashboard.dashboard_id] = dashboard
        self._save_dashboards()

    def _create_default_connectors(self):
        """Create default data connectors."""
        self.data_connectors = {
            "machine_status": {
                "type": "mqtt",
                "topic": "factory/machines/+/status",
                "fields": ["power", "temperature", "vibration", "efficiency"]
            },
            "production_metrics": {
                "type": "timescaledb",
                "table": "production_metrics",
                "query": "SELECT * FROM production_metrics WHERE timestamp > NOW() - INTERVAL '1 hour'",
                "fields": ["units_produced", "cycle_time", "efficiency", "downtime"]
            },
            "alert_system": {
                "type": "redis",
                "key_pattern": "alerts:*",
                "fields": ["severity", "message", "timestamp", "equipment_id"]
            },
            "process_controls": {
                "type": "rest_api",
                "endpoint": "/api/process/controls",
                "methods": ["GET", "POST"],
                "authentication": "jwt"
            },
            "equipment_model": {
                "type": "digital_twin",
                "model_id": "assembly_line_001",
                "update_frequency": 1,  # Hz
                "include_sensors": True
            }
        }
        self._save_data_connectors()

    def _deserialize_dashboard(self, data: Dict) -> MRDashboard:
        """Deserialize dashboard from JSON data."""
        widgets = [DashboardWidget(**w) for w in data.get('widgets', [])]
        return MRDashboard(
            dashboard_id=data['dashboard_id'],
            title=data['title'],
            workspace=data['workspace'],
            widgets=widgets,
            user_permissions=data.get('user_permissions', []),
            layout_preset=data.get('layout_preset', 'default'),
            theme=data.get('theme', 'industrial')
        )

    def _save_dashboards(self):
        """Save dashboards to storage."""
        try:
            data = {
                'dashboards': [
                    {
                        'dashboard_id': d.dashboard_id,
                        'title': d.title,
                        'workspace': d.workspace,
                        'widgets': [vars(w) for w in d.widgets],
                        'user_permissions': d.user_permissions,
                        'layout_preset': d.layout_preset,
                        'theme': d.theme
                    }
                    for d in self.dashboards.values()
                ]
            }

            with open(self.dashboards_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("Dashboards saved successfully")
        except Exception as e:
            logger.error(f"Failed to save dashboards: {e}")

    def _save_data_connectors(self):
        """Save data connectors to storage."""
        try:
            with open(self.data_connectors_path, 'w', encoding='utf-8') as f:
                json.dump(self.data_connectors, f, indent=2, ensure_ascii=False)

            logger.info("Data connectors saved successfully")
        except Exception as e:
            logger.error(f"Failed to save data connectors: {e}")

    def start_dashboard_session(self, dashboard_id: str, user_id: str,
                               workspace_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a mixed reality dashboard session.

        Args:
            dashboard_id: Dashboard ID
            user_id: User ID
            workspace_context: Physical workspace context

        Returns:
            Session configuration and initial data
        """
        if dashboard_id not in self.dashboards:
            raise ValueError(f"Dashboard {dashboard_id} not found")

        dashboard = self.dashboards[dashboard_id]

        # Check permissions
        if not self._check_permissions(user_id, dashboard.user_permissions):
            raise PermissionError(f"User {user_id} does not have permission to access dashboard {dashboard_id}")

        session_id = f"{dashboard_id}_{user_id}_{int(time.time())}"

        session = {
            'session_id': session_id,
            'dashboard_id': dashboard_id,
            'user_id': user_id,
            'start_time': time.time(),
            'workspace_context': workspace_context,
            'active_widgets': {},
            'user_interactions': []
        }

        self.active_sessions[session_id] = session

        # Generate MR environment
        mr_environment = self._generate_mr_environment(dashboard, workspace_context)

        # Initialize widget data
        initial_data = self._get_initial_widget_data(dashboard)

        logger.info(f"Started MR dashboard session {session_id}")

        return {
            'session_id': session_id,
            'dashboard': vars(dashboard),
            'mr_environment': mr_environment,
            'initial_widget_data': initial_data,
            'status': 'active'
        }

    def _check_permissions(self, user_id: str, required_permissions: List[str]) -> bool:
        """Check if user has required permissions."""
        # Simplified permission check - in real implementation, check against user database
        user_permissions = ["operator", "supervisor"]  # Mock user permissions
        return any(perm in user_permissions for perm in required_permissions)

    def _generate_mr_environment(self, dashboard: MRDashboard,
                                workspace_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mixed reality environment configuration."""
        return {
            'workspace': dashboard.workspace,
            'physical_anchor_points': workspace_context.get('anchor_points', []),
            'virtual_overlays': [
                {
                    'type': 'spatial_grid',
                    'opacity': 0.3,
                    'color': 'blue'
                },
                {
                    'type': 'safety_zones',
                    'zones': workspace_context.get('safety_zones', [])
                }
            ],
            'interaction_modes': {
                'gesture_recognition': True,
                'voice_commands': True,
                'hand_tracking': True,
                'eye_tracking': False
            },
            'rendering_settings': {
                'resolution': '4K',
                'frame_rate': 60,
                'anti_aliasing': True,
                'real_time_reflections': True
            },
            'audio_settings': {
                'spatial_audio': True,
                'alert_sounds': True,
                'voice_feedback': True
            }
        }

    def _get_initial_widget_data(self, dashboard: MRDashboard) -> Dict[str, Any]:
        """Get initial data for all dashboard widgets."""
        widget_data = {}

        for widget in dashboard.widgets:
            try:
                data = self._fetch_widget_data(widget)
                widget_data[widget.widget_id] = {
                    'data': data,
                    'timestamp': time.time(),
                    'status': 'active'
                }
            except Exception as e:
                logger.warning(f"Failed to get initial data for widget {widget.widget_id}: {e}")
                widget_data[widget.widget_id] = {
                    'data': None,
                    'timestamp': time.time(),
                    'status': 'error',
                    'error': str(e)
                }

        return widget_data

    def _fetch_widget_data(self, widget: DashboardWidget) -> Any:
        """Fetch data for a specific widget."""
        connector = self.data_connectors.get(widget.data_source)
        if not connector:
            raise ValueError(f"No connector found for data source {widget.data_source}")

        # Simulate data fetching based on connector type
        if connector['type'] == 'mqtt':
            return self._simulate_mqtt_data(widget)
        elif connector['type'] == 'timescaledb':
            return self._simulate_db_data(widget)
        elif connector['type'] == 'redis':
            return self._simulate_redis_data(widget)
        elif connector['type'] == 'rest_api':
            return self._simulate_api_data(widget)
        elif connector['type'] == 'digital_twin':
            return self._simulate_digital_twin_data(widget)
        else:
            return {"value": np.random.random(), "timestamp": time.time()}

    def _simulate_mqtt_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Simulate MQTT sensor data."""
        return {
            "power": np.random.uniform(80, 100),
            "temperature": np.random.uniform(60, 80),
            "vibration": np.random.uniform(0.1, 2.0),
            "efficiency": np.random.uniform(85, 95),
            "timestamp": time.time()
        }

    def _simulate_db_data(self, widget: DashboardWidget) -> List[Dict[str, Any]]:
        """Simulate time-series database data."""
        timestamps = [time.time() - i * 60 for i in range(60)]  # Last hour, 1-minute intervals
        return [
            {
                "timestamp": ts,
                "units_produced": np.random.randint(50, 100),
                "cycle_time": np.random.uniform(45, 55),
                "efficiency": np.random.uniform(85, 95),
                "downtime": np.random.uniform(0, 5)
            }
            for ts in timestamps
        ]

    def _simulate_redis_data(self, widget: DashboardWidget) -> List[Dict[str, Any]]:
        """Simulate alert data from Redis."""
        alerts = []
        if np.random.random() < 0.3:  # 30% chance of alerts
            severities = ['warning', 'critical']
            messages = [
                'High temperature detected',
                'Vibration exceeds threshold',
                'Maintenance required',
                'Process deviation detected'
            ]

            alerts.append({
                'severity': np.random.choice(severities),
                'message': np.random.choice(messages),
                'timestamp': time.time(),
                'equipment_id': f'eq_{np.random.randint(1, 10)}'
            })

        return alerts

    def _simulate_api_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Simulate control system API data."""
        return {
            "current_speed": np.random.uniform(50, 100),
            "target_speed": 75,
            "status": np.random.choice(['running', 'stopped', 'maintenance']),
            "last_command": "set_speed",
            "timestamp": time.time()
        }

    def _simulate_digital_twin_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Simulate digital twin model data."""
        return {
            "model_url": "/models/assembly_line_001.glb",
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "sensor_data": {
                "temperature_sensors": [np.random.uniform(60, 80) for _ in range(5)],
                "vibration_sensors": [np.random.uniform(0.1, 2.0) for _ in range(3)],
                "pressure_sensors": [np.random.uniform(1, 5) for _ in range(2)]
            },
            "anomalies": [] if np.random.random() > 0.2 else [
                {"component": "motor_1", "type": "overheating", "severity": "warning"}
            ],
            "timestamp": time.time()
        }

    def update_widget_data(self, session_id: str, widget_id: str) -> Dict[str, Any]:
        """
        Update data for a specific widget.

        Args:
            session_id: Session ID
            widget_id: Widget ID

        Returns:
            Updated widget data
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        dashboard = self.dashboards[session['dashboard_id']]

        widget = next((w for w in dashboard.widgets if w.widget_id == widget_id), None)
        if not widget:
            raise ValueError(f"Widget {widget_id} not found")

        try:
            data = self._fetch_widget_data(widget)
            update_data = {
                'widget_id': widget_id,
                'data': data,
                'timestamp': time.time(),
                'status': 'active'
            }

            # Store in session
            session['active_widgets'][widget_id] = update_data

            return update_data

        except Exception as e:
            logger.error(f"Failed to update widget {widget_id}: {e}")
            return {
                'widget_id': widget_id,
                'data': None,
                'timestamp': time.time(),
                'status': 'error',
                'error': str(e)
            }

    def handle_user_interaction(self, session_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle user interaction with the MR dashboard.

        Args:
            session_id: Session ID
            interaction_data: Interaction details

        Returns:
            Interaction response
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]

        # Record interaction
        interaction_record = {
            'timestamp': time.time(),
            'type': interaction_data.get('type'),
            'target': interaction_data.get('target'),
            'action': interaction_data.get('action'),
            'parameters': interaction_data.get('parameters', {})
        }

        session['user_interactions'].append(interaction_record)

        # Process interaction
        response = self._process_interaction(session, interaction_data)

        return {
            'interaction_id': f"int_{int(time.time())}_{len(session['user_interactions'])}",
            'response': response,
            'timestamp': time.time()
        }

    def _process_interaction(self, session: Dict, interaction_data: Dict) -> Dict[str, Any]:
        """Process user interaction."""
        interaction_type = interaction_data.get('type')
        target = interaction_data.get('target')

        if interaction_type == 'gesture':
            return self._handle_gesture_interaction(session, interaction_data)
        elif interaction_type == 'voice_command':
            return self._handle_voice_interaction(session, interaction_data)
        elif interaction_type == 'widget_control':
            return self._handle_widget_control(session, interaction_data)
        else:
            return {'status': 'unknown_interaction_type'}

    def _handle_gesture_interaction(self, session: Dict, interaction_data: Dict) -> Dict[str, Any]:
        """Handle gesture-based interactions."""
        gesture = interaction_data.get('gesture')

        if gesture == 'point':
            # Highlight pointed object
            return {
                'action': 'highlight',
                'target': interaction_data.get('target'),
                'effect': 'glow'
            }
        elif gesture == 'pinch':
            # Zoom or scale
            return {
                'action': 'scale',
                'target': interaction_data.get('target'),
                'scale_factor': interaction_data.get('scale', 1.2)
            }

        return {'status': 'gesture_processed'}

    def _handle_voice_interaction(self, session: Dict, interaction_data: Dict) -> Dict[str, Any]:
        """Handle voice command interactions."""
        command = interaction_data.get('command', '').lower()

        if 'status' in command:
            return {
                'action': 'report_status',
                'message': 'All systems operating within normal parameters'
            }
        elif 'alert' in command:
            return {
                'action': 'show_alerts',
                'filter': 'active'
            }
        elif 'shutdown' in command:
            return {
                'action': 'emergency_shutdown',
                'confirmation_required': True
            }

        return {'status': 'command_processed'}

    def _handle_widget_control(self, session: Dict, interaction_data: Dict) -> Dict[str, Any]:
        """Handle widget control interactions."""
        widget_id = interaction_data.get('widget_id')
        action = interaction_data.get('action')

        if action == 'adjust_value':
            # Send control command to process system
            return {
                'action': 'control_command_sent',
                'widget_id': widget_id,
                'new_value': interaction_data.get('value'),
                'confirmation_pending': True
            }
        elif action == 'acknowledge_alert':
            return {
                'action': 'alert_acknowledged',
                'alert_id': interaction_data.get('alert_id')
            }

        return {'status': 'control_processed'}

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a dashboard session.

        Args:
            session_id: Session ID

        Returns:
            Session summary
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        end_time = time.time()
        duration = end_time - session['start_time']

        summary = {
            'session_id': session_id,
            'duration_seconds': duration,
            'interactions_count': len(session['user_interactions']),
            'widgets_accessed': list(session['active_widgets'].keys()),
            'end_time': datetime.fromtimestamp(end_time).isoformat()
        }

        # Clean up session
        del self.active_sessions[session_id]

        logger.info(f"Ended MR dashboard session {session_id}")

        return {
            'status': 'ended',
            'summary': summary
        }

    def get_available_dashboards(self, user_id: str) -> List[Dict]:
        """
        Get dashboards available to a user.

        Args:
            user_id: User ID

        Returns:
            List of available dashboards
        """
        available_dashboards = []

        for dashboard in self.dashboards.values():
            if self._check_permissions(user_id, dashboard.user_permissions):
                available_dashboards.append({
                    'dashboard_id': dashboard.dashboard_id,
                    'title': dashboard.title,
                    'workspace': dashboard.workspace,
                    'widget_count': len(dashboard.widgets),
                    'theme': dashboard.theme
                })

        return available_dashboards

    def create_custom_dashboard(self, dashboard_config: Dict, user_id: str) -> str:
        """
        Create a custom dashboard.

        Args:
            dashboard_config: Dashboard configuration
            user_id: Creator user ID

        Returns:
            Dashboard ID
        """
        dashboard_id = f"custom_{user_id}_{int(time.time())}"

        widgets = [DashboardWidget(**w) for w in dashboard_config.get('widgets', [])]

        dashboard = MRDashboard(
            dashboard_id=dashboard_id,
            title=dashboard_config['title'],
            workspace=dashboard_config['workspace'],
            widgets=widgets,
            user_permissions=dashboard_config.get('user_permissions', [user_id]),
            layout_preset=dashboard_config.get('layout_preset', 'custom'),
            theme=dashboard_config.get('theme', 'industrial')
        )

        self.dashboards[dashboard_id] = dashboard
        self._save_dashboards()

        logger.info(f"Created custom dashboard {dashboard_id}")

        return dashboard_id


# Example usage
if __name__ == "__main__":
    # Initialize MR dashboard system
    mr_dashboard = MixedRealityDashboard()

    # Get available dashboards
    dashboards = mr_dashboard.get_available_dashboards("user_001")
    print("Available dashboards:", [d['title'] for d in dashboards])

    # Start a dashboard session
    if dashboards:
        session = mr_dashboard.start_dashboard_session(
            dashboard_id=dashboards[0]['dashboard_id'],
            user_id="user_001",
            workspace_context={
                'anchor_points': [{'x': 0, 'y': 0, 'z': 0}],
                'safety_zones': [{'type': 'restricted', 'bounds': {'x': 5, 'y': 2, 'z': 3}}]
            }
        )
        print("Started session:", session['session_id'])

        # Update widget data
        widget_update = mr_dashboard.update_widget_data(
            session_id=session['session_id'],
            widget_id=session['dashboard']['widgets'][0]['widget_id']
        )
        print("Widget update:", widget_update['status'])

        # Handle user interaction
        interaction = mr_dashboard.handle_user_interaction(
            session_id=session['session_id'],
            interaction_data={
                'type': 'voice_command',
                'command': 'show status'
            }
        )
        print("Interaction response:", interaction['response'])

        # End session
        summary = mr_dashboard.end_session(session['session_id'])
        print("Session ended:", summary['summary']['duration_seconds'], "seconds")