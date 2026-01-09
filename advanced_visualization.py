"""
Advanced Visualization Module

This module provides a comprehensive suite of tools for creating advanced, interactive,
and multi-dimensional data visualizations for the IoT IIoT Intelligence Platform.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any

class AdvancedVisualization:
    """
    A stateful manager for creating and managing complex data visualizations.
    """
    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initializes the visualization manager with an optional pandas DataFrame.

        Args:
            data: The initial dataset to work with.
        """
        self.data = data if data is not None else pd.DataFrame()
        self.fig: Optional[go.Figure] = None

    def load_data(self, data: pd.DataFrame):
        """Loads or replaces the dataset."""
        self.data = data

    def plot_3d_surface(self, x_col: str, y_col: str, z_col: str, title: str = "3D Surface Plot") -> go.Figure:
        """
        Generates an interactive 3D surface plot.

        Args:
            x_col: The column name for the X-axis.
            y_col: The column name for the Y-axis.
            z_col: The column name for the Z-axis.
            title: The title of the plot.

        Returns:
            A Plotly Figure object.
        """
        if self.data.empty or not all(c in self.data.columns for c in [x_col, y_col, z_col]):
            raise ValueError("Data is not loaded or columns are missing for 3D plot.")

        fig = go.Figure(data=[go.Mesh3d(
            x=self.data[x_col],
            y=self.data[y_col],
            z=self.data[z_col],
            opacity=0.5,
            intensity=self.data[z_col],
            colorscale='Viridis'
        )])

        fig.update_layout(
            title_text=title,
            scene=dict(xaxis_title=x_col, yaxis_title=y_col, zaxis_title=z_col)
        )
        self.fig = fig
        return fig

    def plot_geospatial_heatmap(self, lat_col: str, lon_col: str, z_col: str, title: str = "Geospatial Heatmap") -> go.Figure:
        """
        Generates an interactive geospatial heatmap on a world map.

        Args:
            lat_col: The column name for latitude.
            lon_col: The column name for longitude.
            z_col: The column name for the intensity/value at each coordinate.
            title: The title of the plot.

        Returns:
            A Plotly Figure object.
        """
        if self.data.empty or not all(c in self.data.columns for c in [lat_col, lon_col, z_col]):
            raise ValueError("Data is not loaded or columns are missing for geospatial plot.")

        fig = go.Figure(data=go.Densitymap(
            lat=self.data[lat_col],
            lon=self.data[lon_col],
            z=self.data[z_col],
            radius=10
        ))

        fig.update_layout(
            map_style="stamen-terrain",
            map_center_lon=0,
            map_center_lat=0,
            map_zoom=1,
            title_text=title
        )
        self.fig = fig
        return fig

    def save_visualization(self, filepath: str):
        """
        Saves the current visualization to an HTML file.

        Args:
            filepath: The path to save the HTML file.
        """
        if self.fig:
            self.fig.write_html(filepath)
            print(f"Visualization saved to {filepath}")
        else:
            print("No visualization to save.")


if __name__ == '__main__':
    # --- Demo of Advanced Visualization ---

    # 1. Create sample data for 3D plot
    sample_data_3d = {
        'x': [1, 2, 3, 1, 2, 3, 1, 2, 3],
        'y': [1, 1, 1, 2, 2, 2, 3, 3, 3],
        'z': [1, 4, 9, 2, 5, 8, 3, 6, 7]
    }
    df_3d = pd.DataFrame(sample_data_3d)

    # 2. Create and show 3D Surface Plot
    viz_manager = AdvancedVisualization(df_3d)
    fig_3d = viz_manager.plot_3d_surface('x', 'y', 'z', title="Machine Performance Surface")
    print("Generated 3D Surface Plot. A browser window may open.")
    # fig_3d.show() # This would open a browser window. Commented out for automated environments.
    viz_manager.save_visualization("3d_surface_plot.html")

    # 3. Create sample data for Geospatial Heatmap
    sample_geo_data = {
        'latitude': [34.05, 40.71, 39.95, 48.85, 51.50, 35.67],
        'longitude': [-118.24, -74.00, -75.16, 2.35, -0.12, 139.65],
        'intensity': [10, 50, 25, 80, 60, 40] # e.g., sensor readings or error rates
    }
    df_geo = pd.DataFrame(sample_geo_data)

    # 4. Create and show Geospatial Heatmap
    viz_manager.load_data(df_geo)
    fig_geo = viz_manager.plot_geospatial_heatmap(
        lat_col='latitude', lon_col='longitude', z_col='intensity',
        title="Global Sensor Activity Heatmap"
    )
    print("Generated Geospatial Heatmap. A browser window may open.")
    # fig_geo.show()
    viz_manager.save_visualization("geospatial_heatmap.html")
