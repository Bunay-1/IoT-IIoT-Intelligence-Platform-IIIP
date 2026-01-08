"""
Predictive Quality Control Module

This module implements AI-driven quality control for manufacturing processes.
It uses machine learning models to predict product quality and detect defects in real-time.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from config import settings

logger = logging.getLogger(__name__)


class PredictiveQualityControl:
    def __init__(
        self, model_path: Optional[str] = None, threshold: Optional[float] = None
    ):
        """
        Initialize the predictive quality control system.

        Args:
            model_path: Path to pre-trained model file
            threshold: Quality threshold for defect detection (0-1)
        """
        self.model = None
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.threshold = threshold or settings.quality_threshold
        self.is_trained = False
        self.feature_names = []
        self.model_path = model_path or os.path.join(
            settings.models_dir, "quality_control_model.pkl"
        )

        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        # Load existing model if available
        if os.path.exists(self.model_path):
            self.load_model()

    def train_model(
        self,
        training_data: pd.DataFrame,
        target_column: str = "quality_score",
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """
        Train the quality control model.

        Args:
            training_data: DataFrame with features and target
            target_column: Name of the target column
            test_size: Fraction of data for testing
            random_state: Random state for reproducibility

        Returns:
            Training metrics and model performance
        """
        try:
            logger.info("Starting model training...")

            # Prepare data
            if target_column not in training_data.columns:
                raise ValueError(f"Target column '{target_column}' not found in data")

            X = training_data.drop(columns=[target_column])
            y = (training_data[target_column] >= self.threshold).astype(
                int
            )  # Binary classification

            self.feature_names = list(X.columns)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=random_state,
                class_weight="balanced",
            )
            self.model.fit(X_train_scaled, y_train)

            # Train anomaly detector
            self.anomaly_detector.fit(X_train_scaled)

            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

            report = classification_report(y_test, y_pred, output_dict=True)
            conf_matrix = confusion_matrix(y_test, y_pred).tolist()

            # Feature importance
            feature_importance = dict(
                zip(self.feature_names, self.model.feature_importances_)
            )

            self.is_trained = True
            self.save_model()

            results = {
                "accuracy": report["accuracy"],
                "precision": report["weighted avg"]["precision"],
                "recall": report["weighted avg"]["recall"],
                "f1_score": report["weighted avg"]["f1-score"],
                "confusion_matrix": conf_matrix,
                "feature_importance": feature_importance,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "trained_at": datetime.now().isoformat(),
            }

            logger.info(
                f"Model training completed. Accuracy: {results['accuracy']:.3f}"
            )
            return results

        except Exception as e:
            logger.error(f"Error during model training: {e}")
            raise

    def predict_quality(self, batch_data: pd.DataFrame) -> np.ndarray:
        """
        Predict quality scores for batch data.

        Args:
            batch_data: DataFrame with features

        Returns:
            Array of quality scores (0-1)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Please train the model first.")

        try:
            # Ensure all required features are present
            missing_features = set(self.feature_names) - set(batch_data.columns)
            if missing_features:
                raise ValueError(f"Missing features: {missing_features}")

            # Scale data
            X_scaled = self.scaler.transform(batch_data[self.feature_names])

            # Get predictions
            quality_scores = self.model.predict_proba(X_scaled)[:, 1]

            logger.info(f"Predicted quality for {len(batch_data)} samples")
            return quality_scores

        except Exception as e:
            logger.error(f"Error during quality prediction: {e}")
            raise

    def flag_defects(
        self, predictions: np.ndarray, batch_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Flag defects based on predictions.

        Args:
            predictions: Array of quality scores
            batch_ids: Optional list of batch identifiers

        Returns:
            Dictionary with defect information
        """
        try:
            defects_mask = predictions < self.threshold
            defect_indices = np.where(defects_mask)[0]

            defects = []
            for idx in defect_indices:
                defect_info = {
                    "index": int(idx),
                    "quality_score": float(predictions[idx]),
                    "is_defect": True,
                    "severity": "high" if predictions[idx] < 0.5 else "medium",
                }
                if batch_ids and idx < len(batch_ids):
                    defect_info["batch_id"] = batch_ids[idx]
                defects.append(defect_info)

            result = {
                "total_samples": len(predictions),
                "defect_count": len(defects),
                "defect_rate": len(defects) / len(predictions),
                "defects": defects,
                "quality_distribution": {
                    "excellent": np.sum(predictions >= 0.9),
                    "good": np.sum((predictions >= 0.8) & (predictions < 0.9)),
                    "poor": np.sum(predictions < 0.8),
                },
            }

            logger.info(
                f"Flagged {len(defects)} defects out of {len(predictions)} samples"
            )
            return result

        except Exception as e:
            logger.error(f"Error flagging defects: {e}")
            raise

    def detect_anomalies(self, data: pd.DataFrame) -> np.ndarray:
        """
        Detect anomalies in the data using isolation forest.

        Args:
            data: DataFrame with features

        Returns:
            Array of anomaly scores (-1 for anomalies, 1 for normal)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Please train the model first.")

        try:
            X_scaled = self.scaler.transform(data[self.feature_names])
            anomaly_scores = self.anomaly_detector.predict(X_scaled)

            logger.info(f"Detected {np.sum(anomaly_scores == -1)} anomalies")
            return anomaly_scores

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise

    def save_model(self):
        """Save the trained model to disk."""
        try:
            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "anomaly_detector": self.anomaly_detector,
                "feature_names": self.feature_names,
                "threshold": self.threshold,
                "is_trained": self.is_trained,
            }
            joblib.dump(model_data, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def load_model(self):
        """Load a trained model from disk."""
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.anomaly_detector = model_data["anomaly_detector"]
            self.feature_names = model_data["feature_names"]
            self.threshold = model_data["threshold"]
            self.is_trained = model_data["is_trained"]
            logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "is_trained": self.is_trained,
            "feature_names": self.feature_names,
            "threshold": self.threshold,
            "model_type": type(self.model).__name__ if self.model else None,
            "model_path": self.model_path,
        }
