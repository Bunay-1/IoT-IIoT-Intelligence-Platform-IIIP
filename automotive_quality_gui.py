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

from automotive_quality_control import automotive_quality, StatisticalProcessControl, ComponentType

logger = logging.getLogger(__name__)

class AutomotiveQualityGUI:
    """
    Interactive GUI for Automotive Quality Control Module
    Provides comprehensive quality management interface
    """

    def __init__(self):
        self.app = None
        self.layout_created = False

    def create_layout(self) -> html.Div:
        """Create the main layout for the automotive quality GUI"""
        return html.Div([
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

                # Update interval
                dcc.Interval(id="quality-update-interval", interval=10000, n_intervals=0),  # 10 second updates

            ], fluid=True)
        ])

    def get_dashboard_content(self) -> html.Div:
        """Get dashboard overview content"""
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Quality Overview"),
                        dbc.CardBody([
                            html.H4("Quality Score: 95.2%", className="card-title text-success"),
                            html.P("Overall system quality performance"),
                            dbc.Progress(value=95.2, color="success", className="mb-3"),
                            html.Div([
                                html.Span("Active Projects: ", className="fw-bold"),
                                html.Span("12", className="text-primary"),
                                html.Br(),
                                html.Span("Open NCs: ", className="fw-bold"),
                                html.Span("3", className="text-warning"),
                                html.Br(),
                                html.Span("SPC Charts: ", className="fw-bold"),
                                html.Span("45", className="text-info"),
                            ])
                        ])
                    ])
                ], width=4),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Recent Activity"),
                        dbc.CardBody([
                            dbc.ListGroup([
                                dbc.ListGroupItem("APQP Project 'Engine Block' completed phase 3", color="success"),
                                dbc.ListGroupItem("PPAP submitted for Transmission Unit", color="info"),
                                dbc.ListGroupItem("SPC violation detected on Line 2", color="warning"),
                                dbc.ListGroupItem("Quality audit scheduled for next week", color="primary"),
                            ], flush=True)
                        ])
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
                        dbc.Input(type="text", id="apqp-product-id", placeholder="Enter product ID"),
                        dbc.Label("Project Title", className="mt-2"),
                        dbc.Input(type="text", id="apqp-title", placeholder="Enter project title"),
                        dbc.Label("Customer", className="mt-2"),
                        dbc.Input(type="text", id="apqp-customer", placeholder="Enter customer name"),
                        dbc.Label("Target Completion", className="mt-2"),
                        dbc.Input(type="date", id="apqp-target-date"),
                    ])
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id="cancel-apqp-btn", className="ms-auto"),
                    dbc.Button("Create Project", id="submit-apqp-btn", color="primary"),
                ]),
            ], id="apqp-modal", is_open=False),
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
            elif tab == "spc":
                return self.get_spc_content()
            elif tab == "reports":
                return self.get_reports_content()
            elif tab == "nc":
                return self.get_nc_content()
            return html.Div("Select a tab")

        @app.callback(
            Output("quality-trends-chart", "figure"),
            Input("quality-update-interval", "n_intervals")
        )
        def update_quality_trends(n):
            """Update quality trends chart"""
            # Sample data - in real implementation, fetch from automotive_quality module
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
            df = pd.DataFrame({
                'date': dates,
                'quality_score': [95 + (i % 5) for i in range(30)],
                'defect_rate': [100 - (i % 20) for i in range(30)],
                'oee': [85 + (i % 10) for i in range(30)]
            })

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['quality_score'], mode='lines', name='Quality Score'))
            fig.add_trace(go.Scatter(x=df['date'], y=df['defect_rate'], mode='lines', name='Defect Rate (PPM)'))
            fig.add_trace(go.Scatter(x=df['date'], y=df['oee'], mode='lines', name='OEE %'))

            fig.update_layout(
                title="Quality Trends Over Time",
                xaxis_title="Date",
                yaxis_title="Value",
                height=400
            )

            return fig

        @app.callback(
            Output("apqp-modal", "is_open"),
            Output("apqp-projects-list", "children"),
            Input("create-apqp-btn", "n_clicks"),
            Input("cancel-apqp-btn", "n_clicks"),
            Input("submit-apqp-btn", "n_clicks"),
            State("apqp-modal", "is_open"),
            State("apqp-product-id", "value"),
            State("apqp-title", "value"),
            State("apqp-customer", "value"),
            State("apqp-target-date", "value"),
        )
        def handle_apqp_modal(create_clicks, cancel_clicks, submit_clicks, is_open,
                            product_id, title, customer, target_date):
            """Handle APQP modal interactions"""
            ctx = dash.callback_context

            if not ctx.triggered:
                return is_open, self.get_apqp_projects_list()

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "create-apqp-btn":
                return True, self.get_apqp_projects_list()
            elif button_id in ["cancel-apqp-btn", "submit-apqp-btn"]:
                if button_id == "submit-apqp-btn" and product_id and title:
                    # Create new APQP project
                    self.create_apqp_project(product_id, title, customer, target_date)
                return False, self.get_apqp_projects_list()

            return is_open, self.get_apqp_projects_list()

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

            if not ctx.triggered:
                return is_open, self.get_ppap_submissions_list()

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "create-ppap-btn":
                return True, self.get_ppap_submissions_list()
            elif button_id in ["cancel-ppap-btn", "submit-ppap-btn"]:
                if button_id == "submit-ppap-btn" and product_id:
                    # Submit new PPAP
                    self.submit_ppap(product_id, level, supplier_id)
                return False, self.get_ppap_submissions_list()

            return is_open, self.get_ppap_submissions_list()

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

            if not ctx.triggered:
                return is_open, self.get_nc_list()

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "create-nc-btn":
                return True, self.get_nc_list()
            elif button_id in ["cancel-nc-btn", "submit-nc-btn"]:
                if button_id == "submit-nc-btn" and description:
                    # Report new NC
                    self.report_non_conformance(description, severity, product_id, quantity)
                return False, self.get_nc_list()

            return is_open, self.get_nc_list()

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
            report = automotive_quality.generate_quality_report(
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

    def create_apqp_project(self, product_id: str, title: str, customer: str, target_date: str):
        """Create new APQP project"""
        project_config = {
            "product_id": product_id,
            "title": title,
            "customer": customer,
            "target_completion": target_date
        }
        automotive_quality.create_apqp_project(f"apqp_{int(datetime.now().timestamp())}", project_config)

    def submit_ppap(self, product_id: str, level: str, supplier_id: str):
        """Submit PPAP documentation"""
        submission_config = {
            "product_id": product_id,
            "submission_level": level,
            "supplier_id": supplier_id
        }
        automotive_quality.submit_ppap(f"ppap_{int(datetime.now().timestamp())}", submission_config)

    def report_non_conformance(self, description: str, severity: str, product_id: str, quantity: int):
        """Report non-conformance"""
        nc_config = {
            "description": description,
            "severity": severity,
            "product_id": product_id,
            "quantity_affected": quantity
        }
        automotive_quality.report_non_conformance(nc_config)

    def get_apqp_projects_list(self) -> html.Div:
        """Get list of APQP projects"""
        # Sample projects - in real implementation, fetch from automotive_quality
        projects = [
            {"id": "APQP_001", "title": "Engine Block Project", "status": "In Progress", "progress": 65},
            {"id": "APQP_002", "title": "Transmission Unit", "status": "Planning", "progress": 20},
            {"id": "APQP_003", "title": "Brake System", "status": "Completed", "progress": 100},
        ]

        return html.Div([
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong(f"{p['title']} ({p['id']})"),
                        html.Br(),
                        html.Small(f"Status: {p['status']} | Progress: {p['progress']}%"),
                        dbc.Progress(value=p['progress'], className="mt-1")
                    ])
                ]) for p in projects
            ], flush=True)
        ])

    def get_ppap_submissions_list(self) -> html.Div:
        """Get list of PPAP submissions"""
        # Sample submissions
        submissions = [
            {"id": "PPAP_001", "product": "Engine Block", "status": "Approved", "level": "Level 3"},
            {"id": "PPAP_002", "product": "Transmission", "status": "In Review", "level": "Level 3"},
            {"id": "PPAP_003", "product": "Brakes", "status": "Submitted", "level": "Level 2"},
        ]

        return html.Div([
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong(f"{s['product']} - {s['id']}"),
                        html.Br(),
                        html.Small(f"Status: {s['status']} | Level: {s['level']}")
                    ])
                ], color="success" if s['status'] == "Approved" else "warning")
                for s in submissions
            ], flush=True)
        ])

    def get_nc_list(self) -> html.Div:
        """Get list of non-conformances"""
        # Sample NCs
        ncs = [
            {"id": "NC_001", "description": "Dimensional deviation on shaft", "severity": "Major", "status": "Open"},
            {"id": "NC_002", "description": "Surface finish below spec", "severity": "Minor", "status": "Closed"},
            {"id": "NC_003", "description": "Material contamination", "severity": "Critical", "status": "Open"},
        ]

        return html.Div([
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Strong(f"NC-{s['id']}"),
                        html.Br(),
                        html.Span(s['description']),
                        html.Br(),
                        html.Small(f"Severity: {s['severity']} | Status: {s['status']}")
                    ])
                ], color="danger" if s['severity'] == "Critical" else "warning")
                for s in ncs
            ], flush=True)
        ])

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