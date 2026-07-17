"""
Contextual Anomaly Detection Engine for IoT Predictive Maintenance
Implements unsupervised learning algorithms for real-time anomaly detection
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import mean_squared_error
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler, StandardScaler

logger = logging.getLogger(__name__)


class ContextualAnomalyClassifier:
    """
    Advanced anomaly detection engine using multiple unsupervised algorithms.
    Supports Isolation Forest and Autoencoder-based detection with real-time scoring.
    """

    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        Initialize the anomaly detection engine.

        Args:
            contamination: Expected proportion of anomalies in the data
            random_state: Random seed for reproducibility
        """
        self.contamination = contamination
        self.random_state = random_state
        self.models_dir = Path("models/anomaly_detection")
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Initialize models
        self.isolation_forest = None
        self.autoencoder = None
        self.scaler = StandardScaler()
        self.feature_scaler = MinMaxScaler()

        # Training metadata
        self.is_trained = False
        self.feature_names = []
        self.training_stats = {}

    def preprocess_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame]:
        """
        Preprocess data for anomaly detection.

        Args:
            data: Input dataframe with sensor data

        Returns:
            Tuple of (processed_data, original_data)
        """
        # Handle missing values
        processed_data = data.fillna(data.mean(numeric_only=True))

        # Store feature names
        self.feature_names = processed_data.columns.tolist()

        # Scale features
        scaled_data = self.scaler.fit_transform(processed_data)

        return scaled_data, processed_data

    def train_isolation_forest(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Train Isolation Forest model.

        Args:
            X: Training data

        Returns:
            Training statistics
        """
        logger.info("Training Isolation Forest model...")

        self.isolation_forest = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100,
        )

        # Fit the model
        self.isolation_forest.fit(X)

        # Calculate training anomaly scores
        anomaly_scores = self.isolation_forest.decision_function(X)
        predictions = self.isolation_forest.predict(X)

        # Convert predictions (-1 for anomaly, 1 for normal) to scores (0-1)
        scores = (anomaly_scores - anomaly_scores.min()) / (
            anomaly_scores.max() - anomaly_scores.min()
        )

        stats = {
            "algorithm": "isolation_forest",
            "n_estimators": 100,
            "contamination": self.contamination,
            "anomaly_score_range": (
                float(anomaly_scores.min()),
                float(anomaly_scores.max()),
            ),
            "predicted_anomalies": int((predictions == -1).sum()),
            "training_samples": len(X),
        }

        logger.info(
            f"Isolation Forest trained. Detected {stats['predicted_anomalies']} anomalies in training data"
        )
        return stats

    def train_autoencoder(
        self, X: np.ndarray, encoding_dim: int = 32, epochs: int = 100
    ) -> Dict[str, Any]:
        """
        Train Autoencoder model for anomaly detection.

        Args:
            X: Training data
            encoding_dim: Dimension of the encoding layer
            epochs: Number of training epochs

        Returns:
            Training statistics
        """
        logger.info("Training Autoencoder model...")

        input_dim = X.shape[1]

        # Create autoencoder architecture
        # Encoder: input -> hidden -> encoding
        # Decoder: encoding -> hidden -> output
        hidden_dim = max(encoding_dim * 2, input_dim // 2)

        self.autoencoder = MLPRegressor(
            hidden_layer_sizes=(hidden_dim, encoding_dim, hidden_dim),
            activation="relu",
            solver="adam",
            alpha=0.001,
            batch_size=min(32, len(X)),
            learning_rate="adaptive",
            max_iter=epochs,
            random_state=self.random_state,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=10,
        )

        # Train autoencoder (reconstruct input)
        self.autoencoder.fit(X, X)

        # Calculate reconstruction errors per sample
        reconstructed = self.autoencoder.predict(X)
        reconstruction_errors = np.mean((X - reconstructed) ** 2, axis=1)

        # Normalize reconstruction errors to anomaly scores (0-1)
        # Higher error = more anomalous
        err_min = reconstruction_errors.min()
        err_max = reconstruction_errors.max()
        if err_max > err_min:
            normalized_errors = (reconstruction_errors - err_min) / (err_max - err_min)
        else:
            normalized_errors = np.zeros_like(reconstruction_errors)

        # Determine threshold based on contamination
        threshold = np.percentile(normalized_errors, (1 - self.contamination) * 100)

        stats = {
            "algorithm": "autoencoder",
            "input_dim": input_dim,
            "encoding_dim": encoding_dim,
            "hidden_dim": hidden_dim,
            "epochs": epochs,
            "final_loss": self.autoencoder.best_loss_,
            "reconstruction_error_mean": float(np.mean(reconstruction_errors)),
            "reconstruction_error_std": float(np.std(reconstruction_errors)),
            "anomaly_threshold": float(threshold),
            "predicted_anomalies": int((normalized_errors > threshold).sum()),
            "training_samples": len(X),
        }

        logger.info(
            f"Autoencoder trained. Reconstruction error: {stats['reconstruction_error_mean']:.4f}"
        )
        return stats

    def train(
        self,
        data: pd.DataFrame,
        algorithms: List[str] = ["isolation_forest", "autoencoder"],
    ) -> Dict[str, Any]:
        """
        Train anomaly detection models.

        Args:
            data: Training data
            algorithms: List of algorithms to train

        Returns:
            Training results
        """
        logger.info(f"Starting anomaly detection training with {len(data)} samples")

        # Preprocess data
        X_processed, X_original = self.preprocess_data(data)

        training_results = {
            "training_timestamp": pd.Timestamp.now().isoformat(),
            "algorithms_trained": algorithms,
            "data_shape": X_processed.shape,
            "feature_names": self.feature_names,
        }

        # Train selected algorithms
        if "isolation_forest" in algorithms:
            if_stats = self.train_isolation_forest(X_processed)
            training_results["isolation_forest"] = if_stats

        if "autoencoder" in algorithms:
            ae_stats = self.train_autoencoder(X_processed)
            training_results["autoencoder"] = ae_stats

        self.is_trained = True
        self.training_stats = training_results

        # Save models
        self.save_models()

        logger.info("Anomaly detection training completed")
        return training_results

    def score_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Score new data for anomalies using trained models.

        Args:
            data: New data to score

        Returns:
            Anomaly scores and predictions
        """
        if not self.is_trained:
            raise ValueError("Models must be trained before scoring")

        # Preprocess data (using fitted scaler)
        data_processed = data.fillna(data.mean(numeric_only=True))
        data_processed = data_processed[self.feature_names]  # Ensure same features
        X_scaled = self.scaler.transform(data_processed)

        results = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "samples_scored": len(data),
            "scores": {},
        }

        # Isolation Forest scoring
        if self.isolation_forest:
            if_scores = self.isolation_forest.decision_function(X_scaled)
            # Normalize to 0-1 scale (higher = more anomalous)
            if_scores_norm = (if_scores - if_scores.min()) / (
                if_scores.max() - if_scores.min()
            )
            if_predictions = self.isolation_forest.predict(X_scaled)
            # Convert to 0-1 (1 = anomaly)
            if_predictions_binary = (if_predictions == -1).astype(int)

            results["scores"]["isolation_forest"] = {
                "anomaly_scores": if_scores_norm.tolist(),
                "predictions": if_predictions_binary.tolist(),
                "mean_score": float(np.mean(if_scores_norm)),
                "anomalies_detected": int(np.sum(if_predictions_binary)),
            }

        # Autoencoder scoring
        if self.autoencoder:
            reconstructed = self.autoencoder.predict(X_scaled)
            reconstruction_errors = np.mean((X_scaled - reconstructed) ** 2, axis=1)

            # Normalize reconstruction errors
            err_min = reconstruction_errors.min()
            err_max = reconstruction_errors.max()
            if err_max > err_min:
                errors_norm = (reconstruction_errors - err_min) / (err_max - err_min)
            else:
                errors_norm = np.zeros_like(reconstruction_errors)

            # Use training threshold
            threshold = self.training_stats.get("autoencoder", {}).get(
                "anomaly_threshold", 0.5
            )
            ae_predictions = (errors_norm > threshold).astype(int)

            results["scores"]["autoencoder"] = {
                "anomaly_scores": errors_norm.tolist(),
                "predictions": ae_predictions.tolist(),
                "mean_score": float(np.mean(errors_norm)),
                "anomalies_detected": int(np.sum(ae_predictions)),
                "threshold": threshold,
            }

        # Ensemble score (average of available models)
        available_scores = [
            model_scores["anomaly_scores"]
            for model_scores in results["scores"].values()
        ]
        if available_scores:
            ensemble_scores = np.mean(available_scores, axis=0)
            ensemble_predictions = (ensemble_scores > 0.5).astype(int)

            results["scores"]["ensemble"] = {
                "anomaly_scores": ensemble_scores.tolist(),
                "predictions": ensemble_predictions.tolist(),
                "mean_score": float(np.mean(ensemble_scores)),
                "anomalies_detected": int(np.sum(ensemble_predictions)),
            }

        return results

    def classify_anomalies(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Main method to classify anomalies in data.

        Args:
            data: Input data to analyze

        Returns:
            Classification results
        """
        logger.info(f"Classifying anomalies in {len(data)} samples")

        # Score anomalies
        scores = self.score_anomalies(data)

        # Create detailed results
        results = {
            "classification_results": scores,
            "anomaly_summary": {
                "total_samples": len(data),
                "algorithms_used": list(scores["scores"].keys()),
                "anomalies_by_algorithm": {
                    alg: scores["scores"][alg]["anomalies_detected"]
                    for alg in scores["scores"]
                },
            },
        }

        # Add contextual information
        if "ensemble" in scores["scores"]:
            ensemble = scores["scores"]["ensemble"]
            results["anomaly_summary"]["ensemble_anomalies"] = ensemble[
                "anomalies_detected"
            ]
            results["anomaly_summary"]["ensemble_anomaly_rate"] = ensemble[
                "anomalies_detected"
            ] / len(data)

        logger.info(
            f"Anomaly classification completed. Found anomalies: {results['anomaly_summary']}"
        )
        return results

    def analyze_data(self, data: Union[pd.DataFrame, Dict]) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.

        Args:
            data: Input data

        Returns:
            Analysis results
        """
        if isinstance(data, dict):
            data = pd.DataFrame([data])
        elif not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be DataFrame or dict")

        return self.classify_anomalies(data)

    def save_models(self, filepath: Optional[str] = None):
        """Save trained models to disk."""
        if not self.is_trained:
            return

        if filepath is None:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.models_dir / f"anomaly_detector_{timestamp}.pkl"

        model_data = {
            "isolation_forest": self.isolation_forest,
            "autoencoder": self.autoencoder,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "training_stats": self.training_stats,
            "contamination": self.contamination,
            "random_state": self.random_state,
            "is_trained": self.is_trained,
        }

        joblib.dump(model_data, filepath)
        logger.info(f"Models saved to {filepath}")

    def load_models(self, filepath: str):
        """Load trained models from disk."""
        model_data = joblib.load(filepath)

        self.isolation_forest = model_data["isolation_forest"]
        self.autoencoder = model_data["autoencoder"]
        self.scaler = model_data["scaler"]
        self.feature_names = model_data["feature_names"]
        self.training_stats = model_data["training_stats"]
        self.contamination = model_data["contamination"]
        self.random_state = model_data["random_state"]
        self.is_trained = model_data["is_trained"]

        logger.info(f"Models loaded from {filepath}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about trained models."""
        return {
            "is_trained": self.is_trained,
            "algorithms": ["isolation_forest"]
            if self.isolation_forest
            else [] + ["autoencoder"]
            if self.autoencoder
            else [],
            "feature_names": self.feature_names,
            "contamination": self.contamination,
            "training_stats": self.training_stats,
        }


# Global anomaly detector instance
anomaly_detector = ContextualAnomalyClassifier()
