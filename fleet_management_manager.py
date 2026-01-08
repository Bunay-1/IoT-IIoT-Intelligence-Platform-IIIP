import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html


class FleetManagementManager:
    def __init__(self, fleet_data):
        """
        Initialize the fleet management system.
        Args:
            fleet_data (DataFrame): Data containing details about the fleet.
        """
        self.fleet_data = fleet_data
        self.app = Dash(__name__)
        self.app.layout = self._create_layout()

    def _create_layout(self):
        """
        Create the layout for the fleet management dashboard.
        Returns:
            Dash layout: Layout for the dashboard.
        """
        return html.Div(
            [
                html.H1("Fleet Management Dashboard"),
                dcc.Dropdown(
                    id="fleet-dropdown",
                    options=[
                        {"label": asset, "value": asset}
                        for asset in self.fleet_data["asset"].unique()
                    ],
                    value=self.fleet_data["asset"].iloc[0],
                    clearable=False,
                ),
                dcc.Graph(id="fleet-graph"),
            ]
        )

    def _update_fleet_graph(self, asset):
        """
        Update the fleet graph based on the selected asset.
        Args:
            asset (str): Selected asset.
        Returns:
            Figure: Plotly figure for fleet graph.
        """
        asset_data = self.fleet_data[self.fleet_data["asset"] == asset]
        fig = px.bar(asset_data, x="status", title=f"Status for {asset}")
        return fig

    def run(self):
        """
        Run the dashboard application.
        """
        self.app.callback(
            Output("fleet-graph", "figure"), Input("fleet-dropdown", "value")
        )(self._update_fleet_graph)

        self.app.run(debug=True)
