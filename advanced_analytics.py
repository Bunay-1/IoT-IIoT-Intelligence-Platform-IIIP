"""
Advanced Analytics Module for IoT Intelligence Platform.

This module provides predictive modeling, anomaly detection, dimensionality
reduction, clustering, and advanced analytics dashboard capabilities for
industrial IoT data analysis.
"""

from datetime import datetime, timedelta, timezone
import asyncio
from typing import Dict, List, Any, Optional, Union

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

from utils.logging_config import get_logger

class AnalyticsError(Exception):
    """Base exception for analytics module errors."""
    pass

class AdvancedAnalytics:
    """
    Advanced Analytics System for IoT data with stateful dataset management.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        self.datasets: Dict[str, pd.DataFrame] = {}
        self.analysis_results: Dict[str, Dict[str, Any]] = {}
        self.max_data_points = self.config.get('max_data_points', 10000)
        self.logger.info("AdvancedAnalytics module initialized.")

    def register_dataset(self, dataset_id: str, data: Union[pd.DataFrame, List[Dict[str, Any]]]):
        """Register a dataset for analysis."""
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("Data must be a pandas DataFrame or a list of dicts.")

        if len(df) > self.max_data_points:
            raise ValueError(f"Dataset exceeds max size of {self.max_data_points} rows.")

        # Ensure data is numeric for analysis, filling NaNs
        numeric_cols = df.select_dtypes(include=np.number).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

        self.datasets[dataset_id] = df
        self.logger.info(f"Registered dataset '{dataset_id}' with {len(df)} rows.")

    def get_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """Retrieve a registered dataset."""
        return self.datasets.get(dataset_id)

    def _get_numeric_data(self, dataset_id: str) -> pd.DataFrame:
        """Helper to get a scaled, numeric version of a dataset."""
        df = self.get_dataset(dataset_id)
        if df is None:
            raise ValueError(f"Dataset '{dataset_id}' not found.")

        numeric_df = df.select_dtypes(include=np.number)
        if numeric_df.empty:
            raise ValueError(f"Dataset '{dataset_id}' contains no numeric columns for analysis.")

        scaler = StandardScaler()
        return pd.DataFrame(scaler.fit_transform(numeric_df), columns=numeric_df.columns)

    def perform_pca(self, dataset_id: str, n_components: int = 2) -> Dict[str, Any]:
        """Perform Principal Component Analysis (PCA) for dimensionality reduction."""
        self.logger.info(f"Performing PCA on '{dataset_id}' with {n_components} components.")
        scaled_data = self._get_numeric_data(dataset_id)

        pca = PCA(n_components=n_components)
        principal_components = pca.fit_transform(scaled_data)

        result = {
            "principal_components": principal_components,
            "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
            "total_explained_variance": sum(pca.explained_variance_ratio_),
        }
        self.analysis_results[f"pca_{dataset_id}"] = result
        self.logger.info(f"PCA on '{dataset_id}' complete. Total variance explained: {result['total_explained_variance']:.2%}")
        return result

    def perform_kmeans_clustering(self, dataset_id: str, n_clusters: int = 4) -> Dict[str, Any]:
        """Perform K-Means clustering to segment data."""
        self.logger.info(f"Performing K-Means clustering on '{dataset_id}' with {n_clusters} clusters.")
        scaled_data = self._get_numeric_data(dataset_id)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        clusters = kmeans.fit_predict(scaled_data)

        # Add cluster labels back to the original dataframe
        original_df = self.get_dataset(dataset_id)
        original_df['cluster'] = clusters

        result = {
            "cluster_labels": clusters.tolist(),
            "cluster_centers": kmeans.cluster_centers_.tolist(),
            "inertia": kmeans.inertia_,
            "n_clusters": n_clusters,
        }
        self.analysis_results[f"kmeans_{dataset_id}"] = result
        self.logger.info(f"K-Means clustering on '{dataset_id}' complete.")
        return result

    def generate_cluster_visualization(self, dataset_id: str, output_path: str):
        """Generate and save a visualization of the clustering results using PCA."""
        self.logger.info(f"Generating cluster visualization for '{dataset_id}'.")

        # Ensure clustering and PCA have been run
        if f"kmeans_{dataset_id}" not in self.analysis_results:
            raise AnalyticsError("K-Means clustering must be performed before visualization.")
        pca_result = self.analysis_results.get(f"pca_{dataset_id}")
        if not pca_result or pca_result['principal_components'].shape[1] < 2:
             raise AnalyticsError("PCA with at least 2 components must be performed before visualization.")

        clusters = self.analysis_results[f"kmeans_{dataset_id}"]["cluster_labels"]
        pca_data = pca_result["principal_components"]

        plt.figure(figsize=(10, 8))
        sns.scatterplot(
            x=pca_data[:, 0],
            y=pca_data[:, 1],
            hue=clusters,
            palette=sns.color_palette("hsv", n_colors=len(set(clusters))),
            legend="full"
        )
        plt.title(f'Cluster Visualization for Dataset: {dataset_id}')
        plt.xlabel('Principal Component 1')
        plt.ylabel('Principal Component 2')

        plt.savefig(output_path)
        plt.close()
        self.logger.info(f"Cluster visualization saved to '{output_path}'.")

    def perform_anomaly_detection(self, dataset_id: str) -> Dict[str, Any]:
        """Perform anomaly detection using IsolationForest."""
        self.logger.info(f"Performing anomaly detection on '{dataset_id}'.")
        scaled_data = self._get_numeric_data(dataset_id)

        model = IsolationForest(contamination='auto', random_state=42)
        predictions = model.fit_predict(scaled_data)

        anomalies_indices = np.where(predictions == -1)[0]
        result = {
            "anomaly_count": len(anomalies_indices),
            "anomaly_indices": anomalies_indices.tolist()
        }
        self.analysis_results[f"anomaly_{dataset_id}"] = result
        return result

    def generate_summary_report(self) -> str:
        """Generate a summary report of all analyses performed."""
        report = f"Advanced Analytics Summary Report - {datetime.now(timezone.utc).isoformat()}\n"
        report += "="*50 + "\n"

        for name, result in self.analysis_results.items():
            report += f"\nAnalysis: {name}\n"
            report += "-"*20 + "\n"
            if "anomaly_count" in result:
                report += f"  Anomalies Found: {result['anomaly_count']}\n"
            if "total_explained_variance" in result:
                 report += f"  PCA Total Explained Variance: {result['total_explained_variance']:.2%}\n"
            if "n_clusters" in result:
                 report += f"  K-Means Clusters: {result['n_clusters']}\n"
                 report += f"  K-Means Inertia: {result['inertia']:.2f}\n"

        return report

if __name__ == "__main__":
    async def main():
        print("--- Advanced Analytics Module Demonstration ---")
        analytics = AdvancedAnalytics()

        # 1. Generate and register a sample dataset
        print("\n--- 1. Generating and registering dataset ---")
        np.random.seed(42)
        data = pd.DataFrame({
            'sensor_a': np.random.rand(100) * 100,
            'sensor_b': np.random.rand(100) * 50 + 20,
            'vibration': np.random.rand(100) * 5,
            'temperature': np.random.rand(100) * 30 + 50,
        })
        # Introduce some correlation for PCA
        data['sensor_c'] = data['sensor_a'] * 0.5 + np.random.normal(0, 5, 100)
        analytics.register_dataset("factory_sensors", data)

        # 2. Perform PCA for dimensionality reduction
        print("\n--- 2. Performing PCA ---")
        pca_result = analytics.perform_pca("factory_sensors", n_components=2)
        print(f"PCA complete. Total variance explained by 2 components: {pca_result['total_explained_variance']:.2%}")

        # 3. Perform K-Means Clustering
        print("\n--- 3. Performing K-Means Clustering ---")
        kmeans_result = analytics.perform_kmeans_clustering("factory_sensors", n_clusters=4)
        print(f"K-Means complete. {kmeans_result['n_clusters']} clusters found.")
        print("Dataset now contains a 'cluster' column.")
        print(analytics.get_dataset("factory_sensors").head())

        # 4. Generate Cluster Visualization
        print("\n--- 4. Generating Cluster Visualization ---")
        output_file = "cluster_visualization.png"
        try:
            analytics.generate_cluster_visualization("factory_sensors", output_file)
            print(f"Visualization saved to '{output_file}'. Please view the image.")
        except AnalyticsError as e:
            print(f"Could not generate visualization: {e}")

        # 5. Generate Final Report
        print("\n--- 5. Generating Summary Report ---")
        report = analytics.generate_summary_report()
        print(report)

    asyncio.run(main())