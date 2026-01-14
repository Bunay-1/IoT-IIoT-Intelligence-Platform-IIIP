"""
AI/ML Dashboard for IoT IIoT Intelligence Platform
Comprehensive interface for AI model management, monitoring, and optimization
"""

import asyncio
import json
import logging
import os
import random
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DashboardState:
    """
    Manages the simulated state of the AI/ML platform.
    This acts as a mock backend for the dashboard.
    """

    def __init__(self):
        self.models = {
            'AnomalyDetector': {'accuracy': 94.2, 'f1_score': 92.1, 'drift_score': 0.02, 'drift_threshold': 0.1},
            'PredictiveMaint': {'accuracy': 91.8, 'f1_score': 89.7, 'drift_score': 0.08, 'drift_threshold': 0.1},
            'QualityControl': {'accuracy': 96.1, 'f1_score': 94.8, 'drift_score': 0.05, 'drift_threshold': 0.1},
            'EnergyForecast': {'accuracy': 89.3, 'f1_score': 87.2, 'drift_score': 0.15, 'drift_threshold': 0.1},
        }
        self.resources = {'CPU': 65, 'GPU': 80, 'Memory': 72, 'Storage': 45}
        self.training_jobs = [
            {"name": "AnomalyDetector_v3", "status": "Running", "progress": 10, "eta": "2h 30m"},
            {"name": "QualityModel_v2", "status": "Queued", "progress": 0, "eta": "Pending"},
            {"name": "EnergyPredictor_v1", "status": "Completed", "progress": 100, "eta": "Done"},
        ]
        self.recent_activities = deque(
            [
                ("Model 'AnomalyDetector_v2' deployed successfully", "success", datetime.now()),
                ("Federated learning round completed", "info", datetime.now() - timedelta(minutes=5)),
                ("Drift detected in predictive maintenance model", "warning", datetime.now() - timedelta(minutes=10)),
                ("New training data labeled and validated", "primary", datetime.now() - timedelta(minutes=15)),
            ],
            maxlen=5
        )
        self.federated_learning_progress = [85, 87, 89, 91, 92, 93, 94, 94.5, 95, 95.2]

    def update_state(self):
        """Simulate real-time updates to the platform state."""
        # Update model metrics slightly
        for model in self.models.values():
            model['accuracy'] += random.uniform(-0.1, 0.1)
            model['f1_score'] += random.uniform(-0.1, 0.1)
            model['drift_score'] += random.uniform(-0.01, 0.01)
            model['accuracy'] = max(80, min(99, model['accuracy']))
            model['f1_score'] = max(80, min(99, model['f1_score']))
            model['drift_score'] = max(0, min(1, model['drift_score']))

        # Update resource utilization
        for resource in self.resources:
            self.resources[resource] += random.randint(-2, 2)
            self.resources[resource] = max(10, min(100, self.resources[resource]))

        # Update training jobs
        for job in self.training_jobs:
            if job['status'] == 'Running' and job['progress'] < 100:
                job['progress'] += random.randint(1, 5)
                if job['progress'] >= 100:
                    job['progress'] = 100
                    job['status'] = 'Completed'
                    self.recent_activities.appendleft((f"Training job '{job['name']}' completed", "success", datetime.now()))


class AIMLDashboard:
    """
    Comprehensive AI/ML Dashboard
    Provides unified interface for all AI and ML operations
    """

    def __init__(self, state: DashboardState):
        self.state = state

    def create_layout(self) -> html.Div:
        """Create the main layout for the AI/ML dashboard"""
        return html.Div([
            dbc.Container([
                dbc.Row([dbc.Col([
                    html.H1("AI/ML Intelligence Center", className="text-center my-4"),
                    html.P("Live Simulation of Model Management, Monitoring, and Optimization", className="text-center text-muted")
                ])]),
                dbc.Row([dbc.Col(dbc.Tabs([
                    dbc.Tab(label="Dashboard", tab_id="ai-dashboard"),
                    dbc.Tab(label="Model Monitoring", tab_id="model-monitoring"),
                    dbc.Tab(label="Explainable AI (Static)", tab_id="xai"),
                    dbc.Tab(label="Federated Learning", tab_id="federated"),
                    # Add more tabs as needed
                ], id="ai-tabs", active_tab="ai-dashboard"), width=12)]),
                dbc.Row([dbc.Col(html.Div(id="ai-tab-content"), width=12)]),
                dcc.Interval(id="ai-update-interval", interval=5000, n_intervals=0), # 5-second updates
            ], fluid=True)
        ])

    def get_dashboard_content(self) -> html.Div:
        """Get AI/ML dashboard overview content"""
        return html.Div([
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("AI System Overview"),
                    dbc.CardBody(id="system-overview-content")
                ]), width=4),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Model Performance"),
                    dbc.CardBody(id="model-performance-summary")
                ]), width=4),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Recent Activity"),
                    dbc.CardBody(id="recent-activity-log")
                ]), width=4)
            ], className="mb-4"),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Model Performance Trends"),
                    dbc.CardBody(dcc.Graph(id="ai-performance-chart"))
                ]), width=6),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Resource Utilization"),
                    dbc.CardBody(dcc.Graph(id="ai-resources-chart"))
                ]), width=6)
            ], className="mb-4"),
            dbc.Row([dbc.Col(dbc.Card([
                dbc.CardHeader("Active Training Jobs"),
                dbc.CardBody(id="training-jobs-list")
            ]), width=12)])
        ])

    def get_model_monitoring_content(self) -> html.Div:
        return html.Div([
            dbc.Row([
                dbc.Col(html.H3("Model Performance & Drift Monitoring"), width=12)
            ]),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Model Health Overview"),
                    dbc.CardBody(id="model-health-table")
                ]), width=8),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Drift Detection"),
                    dbc.CardBody(dcc.Graph(id="drift-detection-chart"))
                ]), width=4)
            ]),
        ])

    def get_xai_content(self) -> html.Div:
        """Get Explainable AI content (static for now)"""
        features = ['Temperature', 'Vibration', 'Pressure', 'Current', 'Voltage', 'Speed']
        importance = [0.35, 0.28, 0.18, 0.12, 0.05, 0.02]
        fig_importance = px.bar(x=features, y=importance, title="Global Feature Importance")

        return html.Div([
            html.H3("Explainable AI Engine"),
            dbc.Row([
                dbc.Col(dcc.Graph(figure=fig_importance), width=6),
                dbc.Col(html.Div("SHAP values and other local explanations would appear here."), width=6)
            ])
        ])

    def get_federated_content(self) -> html.Div:
        return html.Div([
            html.H3("Federated Learning Orchestrator"),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Training Progress"),
                    dbc.CardBody(dcc.Graph(id="federated-progress-chart"))
                ]), width=12)
            ])
        ])


    def setup_callbacks(self, app):
        @app.callback(Output("ai-tab-content", "children"), Input("ai-tabs", "active_tab"))
        def render_tab_content(tab):
            if tab == "ai-dashboard": return self.get_dashboard_content()
            if tab == "model-monitoring": return self.get_model_monitoring_content()
            if tab == "xai": return self.get_xai_content()
            if tab == "federated": return self.get_federated_content()
            return html.Div("Select a tab")

        # Callbacks for the main dashboard tab
        @app.callback(
            Output("system-overview-content", "children"),
            Input("ai-update-interval", "n_intervals")
        )
        def update_system_overview(n):
            active_models = len(self.state.models)
            running_jobs = sum(1 for job in self.state.training_jobs if job['status'] == 'Running')
            return html.Div([
                html.H4("System Status: Operational", className="card-title text-success"),
                html.P("All services are running"),
                html.Div([
                    html.Span("Active Models: ", className="fw-bold"), html.Span(active_models, className="text-primary"), html.Br(),
                    html.Span("Training Jobs: ", className="fw-bold"), html.Span(running_jobs, className="text-warning"),
                ])
            ])

        @app.callback(
            Output("model-performance-summary", "children"),
            Input("ai-update-interval", "n_intervals")
        )
        def update_model_performance_summary(n):
            avg_accuracy = np.mean([m['accuracy'] for m in self.state.models.values()])
            avg_f1 = np.mean([m['f1_score'] for m in self.state.models.values()])
            drift_alerts = sum(1 for m in self.state.models.values() if m['drift_score'] > m['drift_threshold'])
            return html.Div([
                html.H5(f"Avg Accuracy: {avg_accuracy:.2f}%", className="text-success"),
                html.H5(f"Avg F1-Score: {avg_f1:.2f}%", className="text-primary"),
                html.H5(f"Drift Alerts: {drift_alerts}", className="text-warning" if drift_alerts > 0 else "text-muted"),
            ])

        @app.callback(
            Output("recent-activity-log", "children"),
            Input("ai-update-interval", "n_intervals")
        )
        def update_recent_activity(n):
            return dbc.ListGroup(
                [dbc.ListGroupItem(f"[{ts.strftime('%H:%M:%S')}] {msg}", color=color) for msg, color, ts in self.state.recent_activities],
                flush=True, style={"fontSize": "0.8rem"}
            )

        @app.callback(Output("ai-performance-chart", "figure"), Input("ai-update-interval", "n_intervals"))
        def update_ai_performance(n):
            model_names = list(self.state.models.keys())
            accuracies = [self.state.models[m]['accuracy'] for m in model_names]
            f1_scores = [self.state.models[m]['f1_score'] for m in model_names]

            fig = go.Figure()
            fig.add_trace(go.Bar(name='Accuracy', x=model_names, y=accuracies))
            fig.add_trace(go.Bar(name='F1-Score', x=model_names, y=f1_scores))
            fig.update_layout(title="Live Model Performance", barmode='group', height=400, yaxis_range=[80,100])
            return fig

        @app.callback(Output("ai-resources-chart", "figure"), Input("ai-update-interval", "n_intervals"))
        def update_ai_resources(n):
            return px.pie(values=list(self.state.resources.values()), names=list(self.state.resources.keys()), title="Resource Utilization", hole=0.3)

        @app.callback(Output("training-jobs-list", "children"), Input("ai-update-interval", "n_intervals"))
        def update_training_jobs(n):
            return dbc.ListGroup(
                [dbc.ListGroupItem([
                    html.Div([
                        html.Strong(job['name']), html.Br(),
                        html.Small(f"Status: {job['status']} | Progress: {job['progress']}%"),
                        dbc.Progress(value=job['progress'], className="mt-1")
                    ])
                ]) for job in self.state.training_jobs],
                flush=True
            )

        # Callbacks for the model monitoring tab
        @app.callback(Output("drift-detection-chart", "figure"), Input("ai-update-interval", "n_intervals"))
        def update_drift_chart(n):
            model_names = list(self.state.models.keys())
            drift_scores = [self.state.models[m]['drift_score'] for m in model_names]
            thresholds = [self.state.models[m]['drift_threshold'] for m in model_names]

            fig = go.Figure()
            fig.add_trace(go.Bar(x=model_names, y=drift_scores, name='Drift Score'))
            fig.add_trace(go.Scatter(x=model_names, y=thresholds, mode='lines', name='Threshold', line=dict(color='red', dash='dash')))
            fig.update_layout(title="Model Drift", height=300, yaxis_range=[0,0.2])
            return fig

        @app.callback(Output("federated-progress-chart", "figure"), Input("ai-update-interval", "n_intervals"))
        def update_federated_progress(n):
            rounds = list(range(1, len(self.state.federated_learning_progress) + 1))
            fig = go.Figure(go.Scatter(x=rounds, y=self.state.federated_learning_progress, mode='lines+markers'))
            fig.update_layout(title="Federated Learning Global Accuracy", xaxis_title="Round", yaxis_title="Accuracy (%)", height=400)
            return fig

# Global state management
dashboard_state = DashboardState()

def create_app(state: DashboardState):
    """Create and configure the Dash app"""
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
    dashboard_ui = AIMLDashboard(state)
    app.layout = dashboard_ui.create_layout()
    dashboard_ui.setup_callbacks(app)
    return app

def run_simulation_loop(state: DashboardState, interval_seconds: int = 2):
    """The background thread function to update the state."""
    logger.info("Starting background simulation loop...")
    while True:
        try:
            state.update_state()
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    app = create_app(dashboard_state)
    port = int(os.getenv('AI_ML_DASHBOARD_PORT', 8052))

    # Run the simulation in a separate thread
    simulation_thread = threading.Thread(target=run_simulation_loop, args=(dashboard_state,), daemon=True)
    simulation_thread.start()

    logger.info(f"Starting Dash server on http://0.0.0.0:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)