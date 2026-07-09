"""
Energy Optimization AI Module

This module implements AI-driven energy optimization for manufacturing processes.
It analyzes energy consumption patterns and provides optimization recommendations
to reduce energy costs while maintaining production efficiency.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.core.config import settings
from src.utils.logging_config import LoggerMixin
from src.utils.performance_monitor import monitor_operation
from src.utils.security import SecurityError, input_validator, validate_input


class EnergyOptimizationError(Exception):
    """Base exception for energy optimization errors."""

    pass


class DataValidationError(EnergyOptimizationError):
    """Raised when input data validation fails."""

    pass


class ModelTrainingError(EnergyOptimizationError):
    """Raised when model training fails."""

    pass


class EnergyOptimizationAI:
    """
    AI-powered energy optimization system for manufacturing processes.

    This class provides comprehensive energy consumption analysis and optimization
    recommendations using machine learning models and real-time monitoring.
    """

    def __init__(
        self, config: Optional[Dict[str, Any]] = None, model_path: Optional[str] = None
    ) -> None:
        """
        Initialize the Energy Optimization AI system.

        Args:
            config: Configuration dictionary with optimization parameters
            model_path: Path to pre-trained model file
        """
        self.config = config or self._get_default_config()
        self.logger = get_logger(__name__)

        # Model components
        self.model: Optional[RandomForestRegressor] = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names: List[str] = []
        self.target_name = "energy_consumption"

        # Model persistence
        self.model_path = model_path or self.config.get(
            "model_path", f"{settings.models_dir}/energy_optimization_model.pkl"
        )

        # Optimization parameters
        self.baseline_consumption = self.config.get("baseline_consumption", 100.0)
        self.optimization_threshold = self.config.get("optimization_threshold", 0.05)
        self.monitoring_interval = self.config.get(
            "monitoring_interval", 300
        )  # 5 minutes

        # Load existing model if available
        self._load_model_if_exists()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration parameters."""
        return {
            "baseline_consumption": 100.0,
            "optimization_threshold": 0.05,
            "monitoring_interval": 300,
            "model_path": f"{settings.models_dir}/energy_optimization_model.pkl",
            "max_training_samples": 10000,
            "test_size": 0.2,
            "random_state": 42,
        }

    def _load_model_if_exists(self) -> None:
        """Load existing model if available."""
        try:
            import os

            if os.path.exists(self.model_path):
                self.load_model()
                self.logger.info(
                    f"Loaded existing energy optimization model from {self.model_path}"
                )
        except Exception as e:
            self.logger.warning(f"Could not load existing model: {e}")

    async def train_model(
        self,
        training_data: pd.DataFrame,
        target_column: str = "energy_consumption",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Train the energy optimization model asynchronously.

        Args:
            training_data: DataFrame with features and energy consumption data
            target_column: Name of the target column
            **kwargs: Additional training parameters

        Returns:
            Training results and metrics

        Raises:
            ModelTrainingError: If training fails
            DataValidationError: If data validation fails
        """
        try:
            self.logger.info("Starting energy optimization model training...")

            # Validate input data
            await self._validate_training_data(training_data, target_column)

            # Prepare features and target
            X = training_data.drop(columns=[target_column])
            y = training_data[target_column]

            self.feature_names = list(X.columns)

            # Split data
            test_size = kwargs.get("test_size", self.config["test_size"])
            random_state = kwargs.get("random_state", self.config["random_state"])

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train model
            self.model = RandomForestRegressor(
                n_estimators=kwargs.get("n_estimators", 100),
                max_depth=kwargs.get("max_depth", 10),
                random_state=random_state,
                n_jobs=-1,
            )

            await asyncio.get_event_loop().run_in_executor(
                None, self.model.fit, X_train_scaled, y_train
            )

            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)

            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)

            # Feature importance
            feature_importance = dict(
                zip(self.feature_names, self.model.feature_importances_)
            )

            self.is_trained = True
            self._save_model()

            results = {
                "mae": float(mae),
                "mse": float(mse),
                "rmse": float(rmse),
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "feature_importance": feature_importance,
                "trained_at": datetime.now().isoformat(),
                "model_params": {
                    "n_estimators": self.model.n_estimators,
                    "max_depth": self.model.max_depth,
                },
            }

            self.logger.info(
                f"Energy optimization model training completed. MAE: {mae:.3f}"
            )
            return results

        except Exception as e:
            self.logger.error(f"Error during model training: {e}")
            raise ModelTrainingError(
                f"Failed to train energy optimization model: {e}"
            ) from e

    async def _validate_training_data(
        self, data: pd.DataFrame, target_column: str
    ) -> None:
        """Validate training data."""
        if data.empty:
            raise DataValidationError("Training data cannot be empty")

        if target_column not in data.columns:
            raise DataValidationError(
                f"Target column '{target_column}' not found in data"
            )

        # Check for minimum samples
        min_samples = 100
        if len(data) < min_samples:
            raise DataValidationError(
                f"Need at least {min_samples} samples for training"
            )

        # Check for missing values
        if data.isnull().any().any():
            self.logger.warning(
                "Training data contains missing values, they will be filled"
            )
            data = data.fillna(data.mean())

    async def predict_consumption(
        self, features: Union[pd.DataFrame, Dict[str, Any]]
    ) -> Union[float, np.ndarray]:
        """
        Predict energy consumption for given features.

        Args:
            features: Input features for prediction

        Returns:
            Predicted energy consumption

        Raises:
            EnergyOptimizationError: If prediction fails
        """
        if not self.is_trained:
            raise EnergyOptimizationError(
                "Model not trained. Please train the model first."
            )

        try:
            # Convert to DataFrame if needed
            if isinstance(features, dict):
                features = pd.DataFrame([features])

            # Validate features
            await self._validate_prediction_features(features)

            # Scale features
            X_scaled = self.scaler.transform(features[self.feature_names])

            # Make prediction
            prediction = self.model.predict(X_scaled)

            # Return single value for single input, array for multiple
            result = prediction[0] if len(prediction) == 1 else prediction

            self.logger.debug(f"Predicted energy consumption: {result}")
            return result

        except Exception as e:
            self.logger.error(f"Error during consumption prediction: {e}")
            raise EnergyOptimizationError(
                f"Failed to predict energy consumption: {e}"
            ) from e

    async def _validate_prediction_features(self, features: pd.DataFrame) -> None:
        """Validate prediction features."""
        missing_features = set(self.feature_names) - set(features.columns)
        if missing_features:
            raise DataValidationError(f"Missing required features: {missing_features}")

    async def optimize_energy(
        self,
        current_parameters: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate energy optimization recommendations.

        Args:
            current_parameters: Current machine/process parameters
            constraints: Optimization constraints

        Returns:
            Optimization recommendations
        """
        try:
            self.logger.info("Generating energy optimization recommendations...")

            # Predict current consumption
            current_consumption = await self.predict_consumption(current_parameters)

            # Generate optimization scenarios
            scenarios = await self._generate_optimization_scenarios(
                current_parameters, constraints or {}
            )

            # Evaluate scenarios
            scenario_results = []
            for scenario in scenarios:
                consumption = await self.predict_consumption(scenario["parameters"])
                savings = current_consumption - consumption
                savings_percent = (savings / current_consumption) * 100

                scenario_result = {
                    "scenario": scenario["name"],
                    "parameters": scenario["parameters"],
                    "predicted_consumption": float(consumption),
                    "energy_savings": float(savings),
                    "savings_percent": float(savings_percent),
                    "feasibility_score": scenario["feasibility_score"],
                }
                scenario_results.append(scenario_result)

            # Sort by savings
            scenario_results.sort(key=lambda x: x["energy_savings"], reverse=True)

            # Filter significant savings
            significant_savings = [
                s
                for s in scenario_results
                if s["savings_percent"] >= self.optimization_threshold * 100
            ]

            result = {
                "current_consumption": float(current_consumption),
                "optimization_scenarios": scenario_results[:5],  # Top 5 scenarios
                "significant_savings": significant_savings,
                "recommended_scenario": scenario_results[0]
                if scenario_results
                else None,
                "generated_at": datetime.now().isoformat(),
            }

            self.logger.info(
                f"Generated {len(scenario_results)} optimization scenarios"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error during energy optimization: {e}")
            raise EnergyOptimizationError(f"Failed to optimize energy: {e}") from e

    async def _generate_optimization_scenarios(
        self, current_params: Dict[str, Any], constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimization scenarios."""
        scenarios = []

        # Speed optimization scenario
        if "speed" in current_params:
            speed = current_params["speed"]
            # Reduce speed by 10% if above minimum
            min_speed = constraints.get("min_speed", speed * 0.8)
            if speed > min_speed:
                new_speed = max(min_speed, speed * 0.9)
                scenarios.append(
                    {
                        "name": "Reduce Speed",
                        "parameters": {**current_params, "speed": new_speed},
                        "feasibility_score": 0.9,
                    }
                )

        # Temperature optimization
        if "temperature" in current_params:
            temp = current_params["temperature"]
            # Optimize temperature to ideal range
            ideal_temp = constraints.get("ideal_temperature", temp)
            if abs(temp - ideal_temp) > 5:
                scenarios.append(
                    {
                        "name": "Optimize Temperature",
                        "parameters": {**current_params, "temperature": ideal_temp},
                        "feasibility_score": 0.8,
                    }
                )

        # Load optimization
        if "load" in current_params:
            load = current_params["load"]
            # Reduce load during off-peak hours
            if load > 0.7:  # High load
                scenarios.append(
                    {
                        "name": "Reduce Load",
                        "parameters": {**current_params, "load": load * 0.8},
                        "feasibility_score": 0.7,
                    }
                )

        # Default scenario if no specific optimizations
        if not scenarios:
            scenarios.append(
                {
                    "name": "Baseline Optimization",
                    "parameters": current_params,
                    "feasibility_score": 0.5,
                }
            )

        return scenarios

    async def monitor_consumption(
        self, real_time_data: pd.DataFrame, alert_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Monitor real-time energy consumption and detect anomalies.

        Args:
            real_time_data: Real-time sensor data
            alert_threshold: Threshold for consumption alerts

        Returns:
            Monitoring results with alerts and insights
        """
        try:
            self.logger.info("Monitoring real-time energy consumption...")

            # Predict expected consumption
            predictions = await self.predict_consumption(real_time_data)

            # Calculate deviations
            if hasattr(real_time_data, self.target_name):
                actual_consumption = real_time_data[self.target_name].values
                deviations = actual_consumption - predictions
                deviation_percent = (deviations / predictions) * 100
            else:
                deviations = np.zeros(len(predictions))
                deviation_percent = np.zeros(len(predictions))

            # Generate alerts
            threshold = alert_threshold or (self.baseline_consumption * 0.1)
            alerts = []

            for i, (dev, dev_pct) in enumerate(zip(deviations, deviation_percent)):
                if abs(dev) > threshold:
                    alert = {
                        "timestamp": datetime.now().isoformat(),
                        "index": i,
                        "actual_consumption": float(actual_consumption[i])
                        if len(actual_consumption) > i
                        else None,
                        "predicted_consumption": float(predictions[i]),
                        "deviation": float(dev),
                        "deviation_percent": float(dev_pct),
                        "severity": "high" if abs(dev_pct) > 20 else "medium",
                    }
                    alerts.append(alert)

            # Calculate statistics
            stats = {
                "total_samples": len(real_time_data),
                "alerts_count": len(alerts),
                "avg_predicted_consumption": float(np.mean(predictions)),
                "max_predicted_consumption": float(np.max(predictions)),
                "min_predicted_consumption": float(np.min(predictions)),
                "monitoring_timestamp": datetime.now().isoformat(),
            }

            result = {
                "statistics": stats,
                "alerts": alerts,
                "predictions": predictions.tolist()
                if isinstance(predictions, np.ndarray)
                else [predictions],
                "insights": self._generate_monitoring_insights(stats, alerts),
            }

            self.logger.info(f"Monitoring completed. Generated {len(alerts)} alerts")
            return result

        except Exception as e:
            self.logger.error(f"Error during consumption monitoring: {e}")
            raise EnergyOptimizationError(f"Failed to monitor consumption: {e}") from e

    def _generate_monitoring_insights(
        self, stats: Dict[str, Any], alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate insights from monitoring data."""
        insights = []

        if stats["alerts_count"] > 0:
            insights.append(f"Detected {stats['alerts_count']} consumption anomalies")

        avg_consumption = stats["avg_predicted_consumption"]
        if avg_consumption > self.baseline_consumption * 1.2:
            insights.append("High energy consumption detected - consider optimization")
        elif avg_consumption < self.baseline_consumption * 0.8:
            insights.append("Energy consumption is below baseline - good efficiency")

        return insights

    def _save_model(self) -> None:
        """Save the trained model to disk."""
        try:
            import os

            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "config": self.config,
                "is_trained": self.is_trained,
                "trained_at": datetime.now().isoformat(),
            }
            joblib.dump(model_data, self.model_path)
            self.logger.info(f"Energy optimization model saved to {self.model_path}")
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")

    def load_model(self) -> None:
        """Load a trained model from disk."""
        try:
            model_data = joblib.load(self.model_path)
            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.feature_names = model_data["feature_names"]
            self.config.update(model_data.get("config", {}))
            self.is_trained = model_data["is_trained"]
            self.logger.info(f"Energy optimization model loaded from {self.model_path}")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "is_trained": self.is_trained,
            "feature_names": self.feature_names,
            "model_type": type(self.model).__name__ if self.model else None,
            "model_path": self.model_path,
            "config": self.config,
        }
