"""
Advanced Analytics Module

Този модул предоставя високо ниво на аналитични възможности чрез машинно обучение:
- Намаляване на размерността с PCA
- Клъстеризация с KMeans и GMM (Gaussian Mixture Models)
- Прогнозиране на времеви редове
- Детекция на аномалии чрез Isolation Forest
"""

import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Any, Dict, List, Optional, Tuple, Union
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.mixture import GaussianMixture

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AdvancedAnalytics:
    """Енджин за разширени анализи и машинно обучение."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = None
        self.clustering_model = None
        self.anomaly_detector = IsolationForest(contamination=0.05, random_state=42)
        logger.info("Advanced Analytics Engine initialized.")

    def preprocess_data(self, data: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Нормализиране на данните."""
        return self.scaler.fit_transform(data)

    def reduce_dimensions(self, data: np.ndarray, n_components: int = 2) -> np.ndarray:
        """Намаляване на размерността чрез PCA."""
        self.pca = PCA(n_components=n_components)
        reduced_data = self.pca.fit_transform(data)
        logger.info(f"Dimensions reduced to {n_components}. Explained variance: {sum(self.pca.explained_variance_ratio_):.2%}")
        return reduced_data

    def perform_clustering(self, data: np.ndarray, n_clusters: int = 3, method: str = 'kmeans') -> np.ndarray:
        """Групиране на данни (клъстеризация)."""
        if method == 'kmeans':
            self.clustering_model = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        elif method == 'gmm':
            self.clustering_model = GaussianMixture(n_components=n_clusters, random_state=42)
        else:
            raise ValueError(f"Unknown clustering method: {method}")

        labels = self.clustering_model.fit_predict(data)
        logger.info(f"Clustering completed using {method}. Clusters: {n_clusters}")
        return labels

    def detect_anomalies(self, data: np.ndarray) -> np.ndarray:
        """Откриване на аномалии (Outlier detection)."""
        # -1 за аномалия, 1 за нормална стойност
        predictions = self.anomaly_detector.fit_predict(data)
        anomalies_count = np.sum(predictions == -1)
        logger.info(f"Anomaly detection completed. Found {anomalies_count} anomalies.")
        return predictions

    def generate_analytics_report(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Генерира подробен статистически отчет."""
        scaled_data = self.preprocess_data(data.values)

        # 1. Dimensions
        reduced = self.reduce_dimensions(scaled_data, n_components=min(2, data.shape[1]))

        # 2. Clusters
        clusters = self.perform_clustering(scaled_data, n_clusters=min(3, data.shape[0]))

        # 3. Anomalies
        anomalies = self.detect_anomalies(scaled_data)

        return {
            "statistics": data.describe().to_dict(),
            "anomalies_found": int(np.sum(anomalies == -1)),
            "cluster_distribution": pd.Series(clusters).value_counts().to_dict(),
            "pca_explained_variance": self.pca.explained_variance_ratio_.tolist()
        }


def run_demo():
    """Демонстрация на модула."""
    print("--- Advanced Analytics Demo ---")

    # Генериране на синтетични данни
    np.random.seed(42)
    data = pd.DataFrame({
        "temperature": np.random.normal(70, 5, 100),
        "vibration": np.random.normal(1.2, 0.3, 100),
        "pressure": np.random.normal(1013, 20, 100),
        "power_draw": np.random.normal(15, 2, 100)
    })

    # Добавяне на аномалии
    data.iloc[0] = [120, 5.0, 1500, 50]

    analytics = AdvancedAnalytics()
    report = analytics.generate_analytics_report(data)

    print(f"\nОткрити аномалии: {report['anomalies_found']}")
    print(f"Разпределение по клъстери: {report['cluster_distribution']}")
    print(f"Обяснена вариация (PCA): {report['pca_explained_variance']}")


if __name__ == "__main__":
    run_demo()
