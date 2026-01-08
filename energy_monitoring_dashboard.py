import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html


class EnergyMonitoringDashboard:
    def __init__(self, data):
        self.data = data
        self.app = Dash(__name__)
        self.app.layout = self._create_layout()

    def _create_layout(self):
        fig = px.line(
            self.data,
            x="timestamp",
            y="energy_consumption",
            title="Energy Consumption Over Time",
        )
        return html.Div(
            [
                html.H1("Energy Monitoring Dashboard"),
                dcc.Graph(figure=fig),
            ]
        )

    def run(self):
        self.app.run(debug=True)


# Пример данни за демонстрация
data = pd.DataFrame(
    {
        "timestamp": pd.date_range(start="2023-01-01", periods=100, freq="H"),
        "energy_consumption": pd.Series(range(100)),
    }
)

# Създаване и стартиране на дashboard-а
dashboard = EnergyMonitoringDashboard(data)
dashboard.run()
