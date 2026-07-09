"""
Advanced Visualization Module for Manufacturing Analytics

This module generates a sophisticated, multi-panel interactive dashboard for
analyzing simulated sensor data from a global network of factories. It showcases
advanced visualizations like geospatial maps, 3D scatter plots, time series,
and correlation heatmaps.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def generate_factory_sensor_data(num_factories: int = 5, num_data_points: int = 200) -> pd.DataFrame:
    """
    Generates a realistic, correlated dataset simulating sensor readings from multiple factories.

    Args:
        num_factories: The number of distinct factories to simulate.
        num_data_points: The number of sensor readings per factory.

    Returns:
        A pandas DataFrame with the simulated data.
    """
    logger.info(f"Generating simulated sensor data for {num_factories} factories...")

    factory_locations = {
        'Factory_A': (40.7128, -74.0060),  # New York
        'Factory_B': (34.0522, -118.2437), # Los Angeles
        'Factory_C': (51.5074, -0.1278),   # London
        'Factory_D': (35.6895, 139.6917),  # Tokyo
        'Factory_E': (48.8566, 2.3522),    # Paris
    }
    factory_ids = list(factory_locations.keys())[:num_factories]

    data_frames = []

    for i, factory_id in enumerate(factory_ids):
        lat, lon = factory_locations[factory_id]

        # Base operational parameters for each factory
        base_temp = 20 + (i * 5) + np.random.randn(num_data_points).cumsum() * 0.1
        base_pressure = 1010 + (i * 2) + np.random.randn(num_data_points).cumsum() * 0.05

        # Create correlated data
        timestamps = pd.to_datetime(np.arange(num_data_points), unit='h', origin=pd.Timestamp('2023-01-01'))
        temperature = base_temp + np.sin(np.arange(num_data_points) / 24 * 2 * np.pi) * 2 # Daily cycle
        pressure = base_pressure + np.random.normal(0, 0.5, num_data_points)

        # Vibration correlated with temperature and pressure
        vibration = 0.1 * temperature + 0.05 * (pressure - 1010) + np.random.normal(0, 0.1, num_data_points)

        # Energy consumption is a function of all three
        energy_consumption = 500 + (temperature - 20) * 10 + (pressure - 1010) * 5 + vibration * 20 + np.random.normal(0, 20, num_data_points)

        # Production output is optimal at a certain temp/pressure range
        temp_efficiency = 1 - (abs(temperature - 25) / 10)
        pressure_efficiency = 1 - (abs(pressure - 1015) / 10)
        production_output = 100 * temp_efficiency * pressure_efficiency + np.random.normal(0, 5, num_data_points)

        df = pd.DataFrame({
            'timestamp': timestamps,
            'factory_id': factory_id,
            'latitude': lat,
            'longitude': lon,
            'temperature': np.clip(temperature, 15, 40),
            'pressure': np.clip(pressure, 1000, 1030),
            'vibration': np.clip(vibration, 0, 10),
            'energy_consumption': np.clip(energy_consumption, 400, 700),
            'production_output': np.clip(production_output, 50, 120)
        })
        data_frames.append(df)

    return pd.concat(data_frames, ignore_index=True)


class ManufacturingDashboard:
    """
    Creates a multi-faceted dashboard for analyzing manufacturing data.
    """
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.fig = make_subplots(
            rows=2, cols=2,
            specs=[[{'type': 'scattergeo'}, {'type': 'heatmap'}],
                   [{'type': 'scatter3d'}, {'type': 'xy'}]],
            subplot_titles=(
                "Global Factory Operations Overview",
                "Sensor Correlation Matrix",
                "Production Output Drivers (3D)",
                "Energy vs. Temperature (Factory A)"
            )
        )
        logger.info("Initialized dashboard structure.")

    def _add_geospatial_map(self):
        """Adds a geospatial map of factory locations to the dashboard."""
        summary = self.data.groupby('factory_id').agg({
            'latitude': 'first', 'longitude': 'first',
            'production_output': 'mean', 'temperature': 'mean'
        }).reset_index()

        self.fig.add_trace(go.Scattergeo(
            lon=summary['longitude'],
            lat=summary['latitude'],
            text=summary['factory_id'],
            mode='markers',
            marker=dict(
                size=summary['production_output'] / 5, # Size by output
                color=summary['temperature'], # Color by temp
                colorscale='Bluered',
                showscale=True,
                colorbar_title="Avg Temp (°C)"
            )
        ), row=1, col=1)
        logger.debug("Added geospatial map to dashboard.")

    def _add_correlation_heatmap(self):
        """Adds a correlation matrix of sensor data."""
        corr_data = self.data[['temperature', 'pressure', 'vibration', 'energy_consumption', 'production_output']].corr()
        self.fig.add_trace(go.Heatmap(
            z=corr_data.values,
            x=corr_data.columns,
            y=corr_data.columns,
            colorscale='Blues'
        ), row=1, col=2)
        logger.debug("Added correlation heatmap to dashboard.")

    def _add_3d_scatter(self):
        """Adds a 3D scatter plot to explore production drivers."""
        sample = self.data.sample(n=min(500, len(self.data))) # Sample for performance
        self.fig.add_trace(go.Scatter3d(
            x=sample['temperature'],
            y=sample['pressure'],
            z=sample['production_output'],
            mode='markers',
            marker=dict(
                size=5,
                color=sample['energy_consumption'], # Color by energy
                colorscale='Viridis',
                colorbar_title="Energy (kWh)",
                opacity=0.8
            )
        ), row=2, col=1)

        # Update 3D scene layout
        self.fig.update_layout(
            scene=dict(
                xaxis_title='Temperature (°C)',
                yaxis_title='Pressure (hPa)',
                zaxis_title='Production Output'
            )
        )
        logger.debug("Added 3D scatter plot to dashboard.")

    def _add_time_series(self):
        """Adds a time series plot for a specific factory."""
        factory_a_data = self.data[self.data['factory_id'] == 'Factory_A']
        self.fig.add_trace(go.Scatter(
            x=factory_a_data['timestamp'],
            y=factory_a_data['energy_consumption'],
            name='Energy Consumption',
            mode='lines',
            line=dict(color='red')
        ), row=2, col=2)

        # Create a secondary y-axis for temperature
        self.fig.add_trace(go.Scatter(
            x=factory_a_data['timestamp'],
            y=factory_a_data['temperature'],
            name='Temperature',
            mode='lines',
            line=dict(color='blue', dash='dash'),
            yaxis='y2'
        ), row=2, col=2)
        logger.debug("Added time series plot to dashboard.")

    def create_dashboard(self) -> go.Figure:
        """Assembles all components into the final dashboard figure."""
        logger.info("Assembling dashboard...")
        self._add_geospatial_map()
        self._add_correlation_heatmap()
        self._add_3d_scatter()
        self._add_time_series()

        # Update overall layout
        self.fig.update_layout(
            height=800,
            width=1200,
            title_text="Global Manufacturing Intelligence Dashboard",
            showlegend=False
        )

        # Update time series subplot layout
        self.fig.update_layout(
            yaxis2=dict(
                title="Temperature (°C)",
                overlaying='y',
                side='right'
            ),
            xaxis4=dict(title="Timestamp"),
            yaxis4=dict(title="Energy (kWh)")
        )
        logger.info("Dashboard assembly complete.")
        return self.fig

    def save_dashboard(self, filepath: str):
        """Saves the dashboard to an interactive HTML file."""
        if self.fig:
            self.fig.write_html(filepath)
            logger.info(f"Dashboard saved to {filepath}")
        else:
            logger.warning("No dashboard figure to save. Call create_dashboard() first.")

async def main():
    """Main function to generate data and create the dashboard."""
    # Generate a rich, correlated dataset
    sensor_data = generate_factory_sensor_data(num_factories=5, num_data_points=500)

    # Create and assemble the dashboard
    dashboard = ManufacturingDashboard(sensor_data)
    dashboard.create_dashboard()

    # Save the interactive dashboard to an HTML file
    output_path = "manufacturing_dashboard.html"
    dashboard.save_dashboard(output_path)

    print(f"\nInteractive manufacturing dashboard has been saved to: {output_path}")

if __name__ == '__main__':
    asyncio.run(main())
