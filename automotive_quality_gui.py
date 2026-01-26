"""
Automotive Quality Control GUI Module
Interactive Dash-based interface for automotive quality management
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

import dash
import numpy as np

# Load environment variables
load_dotenv()
from dash import Input, Output, State, dcc, html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate

from automotive_quality_control import AutomotiveQualityManager, StatisticalProcessControl

logger = logging.getLogger(__name__)

class AutomotiveQualityGUI:
    """
    Interactive GUI for Automotive Quality Control Module
    Provides comprehensive quality management interface
    """

    def __init__(self, state_file="gui_state.json"):
        self.app = None
        self.layout_created = False
        self.quality_manager = AutomotiveQualityManager()
        self.state_file = state_file
        self.apqp_projects = []
        self.ppap_submissions = []
        self.non_conformances = []
        self.fmeas = []
        self.events = []
        self._load_state()

    def _load_state(self):
        """Load state from a JSON file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.apqp_projects = state.get('apqp_projects', [])
                    self.ppap_submissions = state.get('ppap_submissions', [])
                    self.non_conformances = state.get('non_conformances', [])
                    self.fmeas = state.get('fmeas', [])
                    self.events = state.get('events', [])
                    logger.info("GUI state loaded successfully from %s", self.state_file)
            except (json.JSONDecodeError, IOError) as e:
                logger.error("Error loading state from %s: %s", self.state_file, e)
                self._initialize_default_state()
        else:
            logger.info("No state file found. Initializing default state.")
            self._initialize_default_state()

    def _save_state(self):
        """Save the current state to a JSON file."""
        state = {
            'apqp_projects': self.apqp_projects,
            'ppap_submissions': self.ppap_submissions,
            'non_conformances': self.non_conformances,
            'fmeas': self.fmeas,
            'events': self.events
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=4)
            logger.info("GUI state saved successfully to %s", self.state_file)
        except IOError as e:
            logger.error("Error saving state to %s: %s", self.state_file, e)

    def _initialize_default_state(self):
        """Initialize with some default data if state is empty."""
        self.apqp_projects = [
            {"id": "APQP_001", "title": "Engine Block Project", "status": "In Progress", "progress": 65, "customer": "OEM Inc.", "target_date": "2024-12-31"},
        ]
        self.ppap_submissions = [
            {"id": "PPAP_001", "product": "Engine Block", "status": "Approved", "level": "Level 3", "supplier_id": "SUP-123"},
        ]
        self.non_conformances = [
            {"id": "NC_001", "description": "Dimensional deviation on shaft", "severity": "Major", "status": "Open", "product_id": "PROD-542", "quantity": 10},
        ]
        self.fmeas = []
        self.events = [
             {"timestamp": datetime.now().isoformat(), "message": "System Initialized"},
        ]
        self._save_state()

    def _add_event(self, message: str):
        """Add a new event to the activity log."""
        event = {"timestamp": datetime.now().isoformat(), "message": message}
        self.events.insert(0, event)
        # Keep only the last 20 events
        self.events = self.events[:20]
        self._save_state()

    def create_layout(self) -> html.Div:
        """Create the main layout for the automotive quality GUI"""
        return html.Div([
            dcc.Store(id='active-project-store'),
            dcc.Location(id='url', refresh=False),
            dbc.Container([
                # Header
                dbc.Row([
                    dbc.Col([
                        html.H1("Automotive Quality Control System", className="text-center my-4"),
                        html.P("APQP, PPAP, FMEA, and SPC Management", className="text-center text-muted")
                    ])
                ]),

                # Navigation Tabs
                dbc.Row([
                    dbc.Col([
                        dbc.Tabs([
                            dbc.Tab(label="Dashboard", tab_id="dashboard"),
                            dbc.Tab(label="APQP Projects", tab_id="apqp"),
                            dbc.Tab(label="PPAP Submissions", tab_id="ppap"),
                            dbc.Tab(label="FMEA", tab_id="fmea"),
                            dbc.Tab(label="SPC Charts", tab_id="spc"),
                            dbc.Tab(label="Quality Reports", tab_id="reports"),
                            dbc.Tab(label="Non-Conformances", tab_id="nc"),
                        ], id="quality-tabs", active_tab="dashboard"),
                    ], width=12)
                ]),

                # Content Area
                dbc.Row([
                    dbc.Col([
                        html.Div(id="quality-tab-content", children=html.Div("Loading quality dashboard..."))
                    ], width=12)
                ]),

                 dcc.Interval(id="quality-update-interval", interval=30000, n_intervals=0),

            ], fluid=True)
        ])

    def get_dashboard_content(self) -> html.Div:
        """Get dashboard overview content"""
        # --- Dynamic Metrics Calculation ---
        total_ncs = len(self.non_conformances)
        open_ncs = len([nc for nc in self.non_conformances if nc.get('status', 'Open') == 'Open'])
        # Simple quality score calculation (can be much more complex)
        quality_score = max(0, 100 - (open_ncs * 5))
        active_projects = len([p for p in self.apqp_projects if p.get('status') != 'Completed'])
        total_fmeas = len(self.fmeas)
        high_risk_fmeas = len([f for f in self.fmeas if f.get('rpn', 0) > 100])

        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Quality Overview"),
                        dbc.CardBody([
                            html.H4(f"Quality Score: {quality_score:.1f}%", className=f"card-title text-{'success' if quality_score > 90 else 'warning'}"),
                            html.P("Overall system quality performance"),
                            dbc.Progress(value=quality_score, color="success" if quality_score > 90 else "warning", className="mb-3"),
                            html.Div([
                                html.Span("Active APQP Projects: ", className="fw-bold"),
                                html.Span(f"{active_projects}", className="text-primary"),
                                html.Br(),
                                html.Span("Open Non-Conformances: ", className="fw-bold"),
                                html.Span(f"{open_ncs}", className="text-warning"),
                                html.Br(),
                                html.Span("High-Risk FMEAs (>100 RPN): ", className="fw-bold"),
                                html.Span(f"{high_risk_fmeas}", className="text-danger"),
                            ])
                        ])
                    ])
                ], width=4),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Recent Activity"),
                        dbc.CardBody(
                            dbc.ListGroup([
                                dbc.ListGroupItem(f"{e['message']} ({datetime.fromisoformat(e['timestamp']).strftime('%Y-%m-%d %H:%M')})")
                                for e in self.events[:5] # Show top 5 recent events
                            ], flush=True) if self.events else html.P("No recent activity.")
                        )
                    ])
                ], width=4),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Key Metrics"),
                        dbc.CardBody([
                            html.Div([
                                html.H5("PPM: 85", className="text-success"),
                                html.H5("Cpk Avg: 1.45", className="text-primary"),
                                html.H5("On-Time Delivery: 97%", className="text-info"),
                            ])
                        ])
                    ])
                ], width=4)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Quality Trends"),
                        dbc.CardBody([
                            dcc.Graph(id="quality-trends-chart")
                        ])
                    ])
                ], width=12)
            ])
        ])

    def get_apqp_content(self) -> html.Div:
        """Get APQP projects management content"""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H3("APQP Project Management"),
                    dbc.Button("Create New Project", color="primary", className="mb-3", id="create-apqp-btn"),
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Active Projects"),
                        dbc.CardBody([
                            html.Div(id="apqp-projects-list")
                        ])
                    ])
                ], width=8),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Project Details"),
                        dbc.CardBody([
                            html.Div(id="apqp-project-details")
                        ])
                    ])
                ], width=4)
            ]),

            # Modal for creating new APQP project
            dbc.Modal([
                dbc.ModalHeader("Create New APQP Project"),
                dbc.ModalBody([
                    dbc.Form([
                        dbc.Label("Product ID"),
                        dbc.Input(type="text", id="apqp-product-id-input", placeholder="Enter product ID"),
                        dbc.Label("Project Title", className="mt-2"),
                        dbc.Input(type="text", id="apqp-title-input", placeholder="Enter project title"),
                        dbc.Label("Customer", className="mt-2"),
                        dbc.Input(type="text", id="apqp-customer-input", placeholder="Enter customer name"),
                        dbc.Label("Target Completion", className="mt-2"),
                        dbc.Input(type="date", id="apqp-target-date-input"),
                    ]),
                    html.Div(id="apqp-modal-feedback", className="mt-2")
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id="cancel-apqp-btn", className="ms-auto"),
                    dbc.Button("Create Project", id="submit-apqp-btn", color="primary"),
                ]),
            ], id="apqp-modal", is_open=False),
        ])

    def get_fmea_content(self) -> html.Div:
        """Get FMEA management content."""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H3("Failure Mode and Effects Analysis (FMEA)"),
                    dbc.Button("Create New FMEA", color="primary", className="mb-3", id="create-fmea-btn"),
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Active FMEAs"),
                    dbc.CardBody(html.Div(id="fmea-list"))
                ]), width=12)
            ]),
            # FMEA Modal
            dbc.Modal([
                dbc.ModalHeader("Create New FMEA"),
                dbc.ModalBody([
                    dbc.Form([
                        dbc.Label("Product/Process Name"),
                        dbc.Input(type="text", id="fmea-name", placeholder="e.g., Engine Assembly Line"),
                        dbc.Label("Potential Failure Mode", className="mt-2"),
                        dbc.Input(type="text", id="fmea-failure-mode", placeholder="e.g., Bolt over-torqued"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Severity (1-10)", className="mt-2"),
                                dbc.Input(type="number", id="fmea-severity", min=1, max=10, value=5),
                            ]),
                            dbc.Col([
                                dbc.Label("Occurrence (1-10)", className="mt-2"),
                                dbc.Input(type="number", id="fmea-occurrence", min=1, max=10, value=5),
                            ]),
                            dbc.Col([
                                dbc.Label("Detection (1-10)", className="mt-2"),
                                dbc.Input(type="number", id="fmea-detection", min=1, max=10, value=5),
                            ]),
                        ]),
                        html.H4("RPN: -", id="fmea-rpn-display", className="mt-3 text-center")
                    ])
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id="cancel-fmea-btn", className="ms-auto"),
                    dbc.Button("Create FMEA", id="submit-fmea-btn", color="primary"),
                ]),
            ], id="fmea-modal", is_open=False),
        ])

    def get_ppap_content(self) -> html.Div:
        """Get PPAP submissions content"""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H3("PPAP Submission Management"),
                    dbc.Button("Submit New PPAP", color="success", className="mb-3", id="create-ppap-btn"),
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Submission Status"),
                        dbc.CardBody([
                            html.Div(id="ppap-submissions-list")
                        ])
                    ])
                ], width=12)
            ]),

            # PPAP Modal
            dbc.Modal([
                dbc.ModalHeader("Submit PPAP Documentation"),
                dbc.ModalBody([
                    dbc.Form([
                        dbc.Label("Product ID"),
                        dbc.Input(type="text", id="ppap-product-id", placeholder="Enter product ID"),
                        dbc.Label("Submission Level", className="mt-2"),
                        dbc.Select(
                            id="ppap-level",
                            options=[
                                {"label": "Level 1", "value": "Level 1"},
                                {"label": "Level 2", "value": "Level 2"},
                                {"label": "Level 3", "value": "Level 3"},
                                {"label": "Level 4", "value": "Level 4"},
                                {"label": "Level 5", "value": "Level 5"},
                            ],
                            value="Level 3"
                        ),
                        dbc.Label("Supplier ID (optional)", className="mt-2"),
                        dbc.Input(type="text", id="ppap-supplier-id", placeholder="Enter supplier ID"),
                    ])
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id="cancel-ppap-btn", className="ms-auto"),
                    dbc.Button("Submit PPAP", id="submit-ppap-btn", color="success"),
                ]),
            ], id="ppap-modal", is_open=False),
        ])

    def get_spc_content(self) -> html.Div:
        """Get SPC charts content"""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H3("Statistical Process Control (SPC) Simulation"),
                    html.P("Натиснете бутона, за да стартирате нова симулация на производствен процес и да генерирате контролни карти."),
                    dbc.Button("Стартирай SPC симулация", color="primary", className="mb-3", id="run-spc-sim-btn", n_clicks=0),
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col(dcc.Loading(id="loading-spc", children=html.Div(id="spc-simulation-output")), width=12)
            ])
        ])

    def get_reports_content(self) -> html.Div:
        """Get quality reports content"""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H3("Quality Reports & Analytics"),
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Generate Report"),
                        dbc.CardBody([
                            dbc.Form([
                                dbc.Label("Report Type"),
                                dbc.Select(
                                    id="report-type",
                                    options=[
                                        {"label": "Quality Metrics", "value": "quality_metrics"},
                                        {"label": "Non-Conformance Summary", "value": "non_conformance_summary"},
                                        {"label": "Supplier Performance", "value": "supplier_performance"},
                                    ]
                                ),
                                dbc.Label("Start Date", className="mt-2"),
                                dbc.Input(type="date", id="report-start-date"),
                                dbc.Label("End Date", className="mt-2"),
                                dbc.Input(type="date", id="report-end-date"),
                                dbc.Button("Generate Report", color="primary", className="mt-3", id="generate-report-btn"),
                            ])
                        ])
                    ])
                ], width=4),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Report Results"),
                        dbc.CardBody([
                            html.Div(id="report-results")
                        ])
                    ])
                ], width=8)
            ]),
        ])

    def get_nc_content(self) -> html.Div:
        """Get non-conformances content"""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H3("Non-Conformance Management"),
                    dbc.Button("Report New NC", color="danger", className="mb-3", id="create-nc-btn"),
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Open Non-Conformances"),
                        dbc.CardBody([
                            html.Div(id="nc-list")
                        ])
                    ])
                ], width=12)
            ]),

            # NC Modal
            dbc.Modal([
                dbc.ModalHeader("Report Non-Conformance"),
                dbc.ModalBody([
                    dbc.Form([
                        dbc.Label("Description"),
                        dbc.Textarea(id="nc-description", placeholder="Describe the non-conformance"),
                        dbc.Label("Severity", className="mt-2"),
                        dbc.Select(
                            id="nc-severity",
                            options=[
                                {"label": "Minor", "value": "minor"},
                                {"label": "Major", "value": "major"},
                                {"label": "Critical", "value": "critical"},
                            ],
                            value="minor"
                        ),
                        dbc.Label("Product ID (optional)", className="mt-2"),
                        dbc.Input(type="text", id="nc-product-id", placeholder="Enter product ID"),
                        dbc.Label("Quantity Affected", className="mt-2"),
                        dbc.Input(type="number", id="nc-quantity", value=1),
                    ])
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id="cancel-nc-btn", className="ms-auto"),
                    dbc.Button("Report NC", id="submit-nc-btn", color="danger"),
                ]),
            ], id="nc-modal", is_open=False),
        ])

    def setup_callbacks(self, app):
        """Setup Dash callbacks"""

        @app.callback(
            Output("quality-tab-content", "children"),
            Input("quality-tabs", "active_tab")
        )
        def render_tab_content(tab):
            if tab == "dashboard":
                return self.get_dashboard_content()
            elif tab == "apqp":
                return self.get_apqp_content()
            elif tab == "ppap":
                return self.get_ppap_content()
            elif tab == "fmea":
                return self.get_fmea_content()
            elif tab == "spc":
                return self.get_spc_content()
            elif tab == "reports":
                return self.get_reports_content()
            elif tab == "nc":
                return self.get_nc_content()
            return html.Div("Select a tab")

        @app.callback(
            Output("fmea-modal", "is_open"),
            Output("fmea-list", "children"),
            Input("create-fmea-btn", "n_clicks"),
            Input("cancel-fmea-btn", "n_clicks"),
            Input("submit-fmea-btn", "n_clicks"),
            State("fmea-modal", "is_open"),
            State("fmea-name", "value"),
            State("fmea-failure-mode", "value"),
            State("fmea-severity", "value"),
            State("fmea-occurrence", "value"),
            State("fmea-detection", "value"),
        )
        def handle_fmea_modal(create_clicks, cancel_clicks, submit_clicks, is_open,
                             name, failure_mode, severity, occurrence, detection):
            ctx = dash.callback_context
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if triggered_id == "create-fmea-btn":
                return True, self.get_fmea_list()

            if triggered_id == "submit-fmea-btn":
                if not all([name, failure_mode, severity, occurrence, detection]):
                    raise PreventUpdate

                rpn = severity * occurrence * detection
                new_fmea = {
                    "id": f"FMEA_{int(datetime.now().timestamp())}",
                    "name": name,
                    "failure_mode": failure_mode,
                    "severity": severity,
                    "occurrence": occurrence,
                    "detection": detection,
                    "rpn": rpn
                }
                self.fmeas.append(new_fmea)
                self.fmeas.sort(key=lambda x: x['rpn'], reverse=True)
                self._add_event(f"New FMEA created for {name} (RPN: {rpn})")
                self._save_state()
                return False, self.get_fmea_list()

            if triggered_id == "cancel-fmea-btn":
                return False, self.get_fmea_list()

            if not is_open:
                return False, self.get_fmea_list()

            raise PreventUpdate

        @app.callback(
            Output("fmea-rpn-display", "children"),
            Input("fmea-severity", "value"),
            Input("fmea-occurrence", "value"),
            Input("fmea-detection", "value"),
        )
        def update_rpn_display(severity, occurrence, detection):
            if not all([severity, occurrence, detection]):
                return "RPN: -"
            rpn = severity * occurrence * detection
            return f"RPN: {rpn}"

        @app.callback(
            Output("quality-trends-chart", "figure"),
            [Input("quality-update-interval", "n_intervals"), Input("url", "pathname")]
        )
        def update_quality_trends(n, pathname):
            """Update quality trends chart"""
            # This is still sample data, but regeneration is triggered dynamically
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')

            # Simulate dynamic data
            quality_scores = 95 + np.random.randn(30).cumsum() * 0.1
            quality_scores = np.clip(quality_scores, 90, 100)

            defect_rates = 50 + np.random.randn(30).cumsum() * 0.2
            defect_rates = np.clip(defect_rates, 20, 80)

            oee = 85 + np.random.randn(30).cumsum() * 0.15
            oee = np.clip(oee, 80, 95)

            df = pd.DataFrame({
                'date': dates,
                'quality_score': quality_scores,
                'defect_rate_ppm': defect_rates,
                'oee_percentage': oee
            })

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['quality_score'], mode='lines+markers', name='Quality Score'))
            fig.add_trace(go.Scatter(x=df['date'], y=df['defect_rate_ppm'], mode='lines+markers', name='Defect Rate (PPM)'))
            fig.add_trace(go.Scatter(x=df['date'], y=df['oee_percentage'], mode='lines+markers', name='OEE %'))

            fig.update_layout(
                title="Quality Trends Over Time (Simulated)",
                xaxis_title="Date",
                yaxis_title="Value",
                height=400,
                legend=dict(x=0.01, y=0.99)
            )

            return fig

        @app.callback(
            [Output("apqp-modal", "is_open"),
             Output("apqp-projects-list", "children"),
             Output("apqp-modal-feedback", "children")],
            [Input("create-apqp-btn", "n_clicks"),
             Input("cancel-apqp-btn", "n_clicks"),
             Input("submit-apqp-btn", "n_clicks")],
            [State("apqp-modal", "is_open"),
             State("apqp-product-id-input", "value"),
             State("apqp-title-input", "value"),
             State("apqp-customer-input", "value"),
             State("apqp-target-date-input", "value")]
        )
        def handle_apqp_modal(create_clicks, cancel_clicks, submit_clicks, is_open,
                            product_id, title, customer, target_date):
            """Handle APQP modal interactions"""
            ctx = dash.callback_context
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if triggered_id == "create-apqp-btn":
                return True, self.get_apqp_projects_list(), ""

            if triggered_id == "submit-apqp-btn":
                if not all([product_id, title, customer, target_date]):
                    return True, self.get_apqp_projects_list(), dbc.Alert("All fields are required!", color="danger")

                new_project = {
                    "id": f"APQP_{int(datetime.now().timestamp())}",
                    "product_id": product_id,
                    "title": title,
                    "customer": customer,
                    "target_date": target_date,
                    "status": "Planning",
                    "progress": 5
                }
                self.apqp_projects.append(new_project)
                self._add_event(f"New APQP project created: {title}")
                self._save_state()
                return False, self.get_apqp_projects_list(), ""

            if triggered_id == "cancel-apqp-btn":
                return False, self.get_apqp_projects_list(), ""

            if not is_open:
                 return False, self.get_apqp_projects_list(), ""

            raise PreventUpdate

        @app.callback(
            Output("ppap-modal", "is_open"),
            Output("ppap-submissions-list", "children"),
            Input("create-ppap-btn", "n_clicks"),
            Input("cancel-ppap-btn", "n_clicks"),
            Input("submit-ppap-btn", "n_clicks"),
            State("ppap-modal", "is_open"),
            State("ppap-product-id", "value"),
            State("ppap-level", "value"),
            State("ppap-supplier-id", "value"),
        )
        def handle_ppap_modal(create_clicks, cancel_clicks, submit_clicks, is_open,
                            product_id, level, supplier_id):
            """Handle PPAP modal interactions"""
            ctx = dash.callback_context
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if triggered_id == "create-ppap-btn":
                return True, self.get_ppap_submissions_list()

            if triggered_id == "submit-ppap-btn":
                if not product_id:
                     raise PreventUpdate

                new_submission = {
                    "id": f"PPAP_{int(datetime.now().timestamp())}",
                    "product": product_id,
                    "level": level,
                    "supplier_id": supplier_id,
                    "status": "Submitted"
                }
                self.ppap_submissions.append(new_submission)
                self._add_event(f"New PPAP submitted for product {product_id}")
                self._save_state()
                return False, self.get_ppap_submissions_list()

            if triggered_id == "cancel-ppap-btn":
                return False, self.get_ppap_submissions_list()

            if not is_open:
                return False, self.get_ppap_submissions_list()

            raise PreventUpdate

        @app.callback(
            Output("nc-modal", "is_open"),
            Output("nc-list", "children"),
            Input("create-nc-btn", "n_clicks"),
            Input("cancel-nc-btn", "n_clicks"),
            Input("submit-nc-btn", "n_clicks"),
            State("nc-modal", "is_open"),
            State("nc-description", "value"),
            State("nc-severity", "value"),
            State("nc-product-id", "value"),
            State("nc-quantity", "value"),
        )
        def handle_nc_modal(create_clicks, cancel_clicks, submit_clicks, is_open,
                          description, severity, product_id, quantity):
            """Handle NC modal interactions"""
            ctx = dash.callback_context
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if triggered_id == "create-nc-btn":
                return True, self.get_nc_list()

            if triggered_id == "submit-nc-btn":
                if not description:
                    raise PreventUpdate

                new_nc = {
                    "id": f"NC_{int(datetime.now().timestamp())}",
                    "description": description,
                    "severity": severity,
                    "product_id": product_id,
                    "quantity": quantity,
                    "status": "Open"
                }
                self.non_conformances.append(new_nc)
                self._add_event(f"New Non-Conformance reported: {description[:30]}...")
                self._save_state()
                return False, self.get_nc_list()

            if triggered_id == "cancel-nc-btn":
                return False, self.get_nc_list()

            if not is_open:
                 return False, self.get_nc_list()

            raise PreventUpdate

        @app.callback(
            Output("report-results", "children"),
            Input("generate-report-btn", "n_clicks"),
            State("report-type", "value"),
            State("report-start-date", "value"),
            State("report-end-date", "value"),
        )
        def generate_report(n_clicks, report_type, start_date, end_date):
            """Generate quality report"""
            if not n_clicks or not report_type or not start_date or not end_date:
                raise PreventUpdate

            # Generate report using automotive_quality module
            report = self.quality_manager.generate_quality_report(
                report_type, start_date, end_date
            )

            return html.Div([
                html.H4("Report Generated"),
                html.Pre(json.dumps(report, indent=2))
            ])

        @app.callback(
            Output("spc-simulation-output", "children"),
            Input("run-spc-sim-btn", "n_clicks")
        )
        def run_spc_simulation(n_clicks):
            """Run SPC simulation and display charts"""
            if n_clicks == 0:
                return html.Div("Натиснете бутона, за да стартирате симулацията.")

            # Generate sample data for simulation
            np.random.seed(int(datetime.now().timestamp()))
            data = pd.DataFrame({
                'measurement': np.concatenate([
                    np.random.normal(loc=10.0, scale=0.1, size=100),
                    np.random.normal(loc=10.15, scale=0.12, size=50)  # Simulate a process shift
                ])
            })

            spc = StatisticalProcessControl(data, 'measurement', subgroup_size=5)
            spc.calculate_control_limits()
            analysis_df = spc.analyze()

            x_bar_chart = dcc.Graph(figure=spc.plot_x_bar_chart())
            r_chart = dcc.Graph(figure=spc.plot_r_chart())

            results_table = dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in analysis_df.columns],
                data=analysis_df.to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                }
            )

            return html.Div([
                dbc.Row([
                    dbc.Col(x_bar_chart, width=6),
                    dbc.Col(r_chart, width=6)
                ]),
                dbc.Row([
                    dbc.Col([
                        html.H4("Резултати от анализа", className="mt-4"),
                        results_table
                    ], width=12)
                ])
            ])

    def get_apqp_projects_list(self) -> html.Div:
        """Get list of APQP projects"""
        if not self.apqp_projects:
            return html.Div("No APQP projects found.")

        return html.Div([
            dbc.ListGroup([
                dbc.ListGroupItem(
                    [
                        html.Div([
                            html.Strong(f"{p['title']} ({p['id']})"),
                            html.Br(),
                            html.Small(f"Status: {p['status']} | Progress: {p['progress']}%"),
                            dbc.Progress(value=p['progress'], className="mt-1")
                        ])
                    ],
                    id={'type': 'apqp-project-item', 'index': p['id']},
                    action=True,
                    n_clicks=0
                ) for p in self.apqp_projects
            ], flush=True),
            dbc.Offcanvas(
                html.Div(id="apqp-offcanvas-content"),
                id="apqp-offcanvas",
                title="Project Details",
                is_open=False,
                placement="end"
            )
        ])

    def get_ppap_submissions_list(self) -> html.Div:
        """Get list of PPAP submissions"""
        if not self.ppap_submissions:
            return html.Div("No PPAP submissions found.")

        status_color = {"Approved": "success", "Submitted": "info", "In Review": "warning", "Rejected": "danger"}
        return html.Div([
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong(f"{s['product']} - {s['id']}"),
                        html.Br(),
                        html.Small(f"Status: {s['status']} | Level: {s['level']}")
                    ])
                ], color=status_color.get(s['status'], 'secondary'))
                for s in self.ppap_submissions
            ], flush=True)
        ])

    def get_nc_list(self) -> html.Div:
        """Get list of non-conformances"""
        if not self.non_conformances:
            return html.Div("No open non-conformances found.")

        severity_color = {"Critical": "danger", "Major": "warning", "Minor": "info"}
        return html.Div([
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong(f"{s['id']}"),
                        html.Br(),
                        html.Span(s['description']),
                        html.Br(),
                        html.Small(f"Severity: {s['severity']} | Status: {s['status']}")
                    ])
                ], color=severity_color.get(s['severity'], 'secondary'))
                for s in self.non_conformances
            ], flush=True)
        ])

    def get_fmea_list(self) -> html.Div:
        """Get list of FMEAs as a table."""
        if not self.fmeas:
            return html.Div("No FMEA records found.")

        fmea_df = pd.DataFrame(self.fmeas)

        def get_rpn_color(rpn):
            if rpn > 100: return 'red'
            if rpn > 50: return 'orange'
            return 'inherit'

        table_header = [
            html.Thead(html.Tr([
                html.Th("Process/Product"),
                html.Th("Failure Mode"),
                html.Th("Severity"),
                html.Th("Occurrence"),
                html.Th("Detection"),
                html.Th("RPN"),
            ]))
        ]
        table_body = [
            html.Tbody([
                html.Tr([
                    html.Td(row['name']),
                    html.Td(row['failure_mode']),
                    html.Td(row['severity']),
                    html.Td(row['occurrence']),
                    html.Td(row['detection']),
                    html.Td(row['rpn'], style={'fontWeight': 'bold', 'color': get_rpn_color(row['rpn'])}),
                ]) for idx, row in fmea_df.iterrows()
            ])
        ]

        return dbc.Table(table_header + table_body, bordered=True, striped=True, hover=True, responsive=True)

        @app.callback(
            [Output("apqp-offcanvas", "is_open"),
             Output("apqp-offcanvas-content", "children"),
             Output('active-project-store', 'data')],
            [Input({'type': 'apqp-project-item', 'index': dash.dependencies.ALL}, 'n_clicks'),
             Input("save-apqp-changes-btn", "n_clicks")],
            [State({'type': 'apqp-project-item', 'index': dash.dependencies.ALL}, 'id'),
             State("apqp-offcanvas", "is_open"),
             State('active-project-store', 'data'),
             State("apqp-status-dropdown", "value"),
             State("apqp-progress-slider", "value")]
        )
        def handle_apqp_offcanvas(n_clicks_list, save_clicks, item_ids, is_open, project_id_data, status, progress):
            ctx = dash.callback_context
            if not ctx.triggered or not any(n_clicks_list):
                raise PreventUpdate

            triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]

            if 'save-apqp-changes-btn' in triggered_input and project_id_data:
                project_id = project_id_data.get('project_id')
                project = next((p for p in self.apqp_projects if p['id'] == project_id), None)
                if project and status and progress is not None:
                    project['status'] = status
                    project['progress'] = progress
                    self._add_event(f"Updated APQP project: {project['title']}")
                    self._save_state()
                return False, dash.no_update, None

            if 'apqp-project-item' in triggered_input:
                clicked_item_index = next(i for i, n_clicks in enumerate(n_clicks_list) if n_clicks > 0)
                clicked_item_id = item_ids[clicked_item_index]['index']

                project = next((p for p in self.apqp_projects if p['id'] == clicked_item_id), None)
                if not project:
                    raise PreventUpdate

                content = html.Div([
                    html.H5(project['title']), html.Hr(),
                    html.P(f"ID: {project['id']}"),
                    html.P(f"Customer: {project['customer']}"),
                    html.P(f"Target Date: {project['target_date']}"),
                    html.Hr(),
                    dbc.Label("Status"),
                    dcc.Dropdown(id="apqp-status-dropdown",
                                 options=[{'label': s, 'value': s} for s in ['Planning', 'In Progress', 'Completed', 'On Hold']],
                                 value=project['status']),
                    dbc.Label("Progress (%)", className="mt-3"),
                    dcc.Slider(id="apqp-progress-slider", min=0, max=100, step=5, value=project['progress'],
                               marks={i: str(i) for i in range(0, 101, 20)}),
                    dbc.Button("Save Changes", id="save-apqp-changes-btn", color="primary", className="mt-4 w-100")
                ])
                return True, content, {'project_id': clicked_item_id}

            return False, dash.no_update, None

# Global GUI instance
automotive_quality_gui = AutomotiveQualityGUI()

def create_app():
    """Create and configure the Dash app"""
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        title="Automotive Quality Control",
        update_title="Loading..."
    )

    app.layout = automotive_quality_gui.create_layout()
    automotive_quality_gui.setup_callbacks(app)

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv('AUTOMOTIVE_QUALITY_GUI_PORT', 8051))
    app.run(debug=False, host='0.0.0.0', port=port)