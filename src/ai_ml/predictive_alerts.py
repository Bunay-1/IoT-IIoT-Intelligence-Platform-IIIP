"""
Module: Predictive Alerts

This module generates predictive alerts based on data analysis and machine learning models.
It identifies potential issues or opportunities and notifies users proactively.
"""

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from src.core.config import settings
from src.utils.logging_config import LoggerMixin, get_logger
from src.utils.performance_monitor import monitor_operation
from src.utils.security import SecurityError, input_validator, validate_input

# Import core ML engines for integration
try:
    from src.ai_ml.automl_engine import src.ai_ml.automl_engine
    from src.ai_ml.reinforcement_learning import rl_engine

    AUTOML_AVAILABLE = True
    RL_AVAILABLE = True
except ImportError:
    AUTOML_AVAILABLE = False
    RL_AVAILABLE = False
    # Logger will be available after class definition


@dataclass
class Alert:
    """Alert data structure."""

    id: str
    machine_id: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    alert_type: str  # 'anomaly', 'failure_prediction', 'maintenance_due', 'performance_drop'
    message: str
    prediction_value: float
    threshold: float
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PredictiveAlertsError(Exception):
    """Base exception for PredictiveAlerts module."""

    pass


class ModelNotFoundError(PredictiveAlertsError):
    """Raised when requested model is not found."""

    pass


class InvalidDataError(PredictiveAlertsError):
    """Raised when input data is invalid."""

    pass


class PredictiveAlerts(LoggerMixin):
    """
    Enhanced predictive alerts system with async support and ML integration.

    This class manages machine learning models for predictive analysis and generates
    alerts based on predictions and configurable thresholds.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PredictiveAlerts system.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.models: Dict[str, Any] = {}
        self.alerts: List[Alert] = []
        self._alert_counter = 0
        self._lock = asyncio.Lock()

        # Default thresholds
        self.default_thresholds = {
            "anomaly_score": 0.8,
            "failure_probability": 0.7,
            "performance_drop": 0.15,  # 15% drop
            "maintenance_days": 30,
        }

        # Update with config
        self.default_thresholds.update(self.config.get("thresholds", {}))

        self.logger.info("PredictiveAlerts initialized")

    @monitor_operation("predictive_alerts.add_model")
    @validate_input(
        {"model_name": {"type": "string", "max_length": 100, "required": True}}
    )
    def add_model(self, model_name: str, model: Any) -> None:
        """
        Add a machine learning model for predictive analysis.

        Args:
            model_name: Name identifier for the model
            model: Trained ML model with predict method

        Raises:
            ValueError: If model_name is empty or model is invalid
            SecurityError: If input validation fails
        """
        # Additional security checks
        if input_validator.check_sql_injection(model_name):
            raise SecurityError("Invalid model name: potential SQL injection detected")

        if input_validator.check_xss(model_name):
            raise SecurityError("Invalid model name: potential XSS detected")

        if not hasattr(model, "predict"):
            raise ValueError("Model must have a 'predict' method")

        self.models[model_name] = model
        self.logger.info(f"Model '{model_name}' added for predictive alerts")

    @monitor_operation("predictive_alerts.analyze_data")
    @validate_input(
        {"model_name": {"type": "string", "max_length": 100, "required": True}}
    )
    async def analyze_data_async(
        self, data: Union[pd.DataFrame, np.ndarray, List], model_name: str
    ) -> Dict[str, Any]:
        """
        Asynchronously analyze data using a specific model to predict outcomes.

        Args:
            data: Input data for prediction
            model_name: Name of the model to use

        Returns:
            Dictionary containing prediction results

        Raises:
            ModelNotFoundError: If model is not found
            InvalidDataError: If data is invalid
        """
        async with self._lock:
            try:
                if model_name not in self.models:
                    raise ModelNotFoundError(f"Model '{model_name}' not found")

                # Validate data
                if isinstance(data, pd.DataFrame) and data.empty:
                    raise InvalidDataError("Input DataFrame cannot be empty")
                elif isinstance(data, (list, np.ndarray)) and len(data) == 0:
                    raise InvalidDataError("Input data cannot be empty")

                model = self.models[model_name]

                # Run prediction in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                prediction = await loop.run_in_executor(None, model.predict, data)

                result = {
                    "model_name": model_name,
                    "prediction": prediction.tolist()
                    if hasattr(prediction, "tolist")
                    else prediction,
                    "timestamp": datetime.now(),
                    "data_shape": getattr(data, "shape", len(data))
                    if hasattr(data, "shape")
                    else len(data),
                }

                self.logger.info(
                    f"Data analyzed using model '{model_name}', prediction shape: {len(result['prediction'])}"
                )
                return result

            except Exception as e:
                self.logger.error(
                    f"Error analyzing data with model '{model_name}': {e}"
                )
                raise PredictiveAlertsError(f"Failed to analyze data: {e}") from e

    def analyze_data(
        self, data: Union[pd.DataFrame, np.ndarray, List], model_name: str
    ) -> Dict[str, Any]:
        """
        Synchronously analyze data using a specific model.

        Args:
            data: Input data for prediction
            model_name: Name of the model to use

        Returns:
            Dictionary containing prediction results
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If event loop is running, we need to handle differently
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.analyze_data_async(data, model_name)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.analyze_data_async(data, model_name)
                )
        except Exception as e:
            self.logger.error(f"Synchronous analysis failed: {e}")
            raise

    @monitor_operation("predictive_alerts.generate_alert")
    async def generate_alert_async(
        self,
        prediction_result: Dict[str, Any],
        alert_type: str,
        machine_id: str,
        custom_threshold: Optional[float] = None,
    ) -> Optional[Alert]:
        """
        Generate an alert based on prediction results.

        Args:
            prediction_result: Result from analyze_data
            alert_type: Type of alert ('anomaly', 'failure_prediction', etc.)
            machine_id: ID of the machine
            custom_threshold: Optional custom threshold

        Returns:
            Alert object if threshold exceeded, None otherwise
        """
        async with self._lock:
            try:
                threshold = custom_threshold or self.default_thresholds.get(
                    alert_type, 0.8
                )

                # Extract prediction value
                prediction = prediction_result["prediction"]
                if isinstance(prediction, list) and len(prediction) > 0:
                    prediction_value = float(np.mean(prediction))
                else:
                    prediction_value = float(prediction)

                # Check if alert should be generated
                should_alert = self._should_generate_alert(
                    prediction_value, threshold, alert_type
                )

                if should_alert:
                    self._alert_counter += 1
                    alert = Alert(
                        id=f"alert_{self._alert_counter}",
                        machine_id=machine_id,
                        severity=self._calculate_severity(
                            prediction_value, threshold, alert_type
                        ),
                        alert_type=alert_type,
                        message=self._generate_alert_message(
                            alert_type, prediction_value, threshold
                        ),
                        prediction_value=prediction_value,
                        threshold=threshold,
                        timestamp=datetime.now(),
                        metadata={
                            "model_name": prediction_result.get("model_name"),
                            "data_shape": prediction_result.get("data_shape"),
                        },
                    )

                    self.alerts.append(alert)
                    self.logger.warning(
                        f"Alert generated: {alert.message} (severity: {alert.severity})"
                    )
                    return alert
                else:
                    self.logger.debug(
                        f"No alert generated for {alert_type}, prediction: {prediction_value}, threshold: {threshold}"
                    )
                    return None

            except Exception as e:
                self.logger.error(f"Error generating alert: {e}")
                raise PredictiveAlertsError(f"Failed to generate alert: {e}") from e

    def generate_alert(
        self,
        prediction: Union[float, List, np.ndarray],
        alert_threshold: float,
        machine_id: str = "unknown",
        alert_type: str = "custom",
    ) -> Optional[Alert]:
        """
        Synchronous method to generate an alert (legacy compatibility).

        Args:
            prediction: Prediction value(s)
            alert_threshold: Threshold for alert generation
            machine_id: Machine identifier
            alert_type: Type of alert

        Returns:
            Alert object if threshold exceeded, None otherwise
        """
        try:
            # Convert to prediction result format
            if isinstance(prediction, list):
                prediction_value = float(np.mean(prediction))
            elif isinstance(prediction, np.ndarray):
                prediction_value = float(np.mean(prediction))
            else:
                prediction_value = float(prediction)

            prediction_result = {
                "prediction": prediction_value,
                "timestamp": datetime.now(),
            }

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.generate_alert_async(
                            prediction_result, alert_type, machine_id, alert_threshold
                        ),
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.generate_alert_async(
                        prediction_result, alert_type, machine_id, alert_threshold
                    )
                )
        except Exception as e:
            self.logger.error(f"Synchronous alert generation failed: {e}")
            raise

    def _should_generate_alert(
        self, prediction_value: float, threshold: float, alert_type: str
    ) -> bool:
        """Determine if an alert should be generated based on prediction and threshold."""
        if alert_type in ["anomaly_score", "failure_probability", "performance_drop"]:
            return prediction_value > threshold
        elif alert_type == "maintenance_days":
            return (
                prediction_value < threshold
            )  # Less than threshold means maintenance due soon
        return prediction_value > threshold

    def _calculate_severity(
        self, prediction_value: float, threshold: float, alert_type: str
    ) -> str:
        """Calculate alert severity based on prediction value."""
        ratio = prediction_value / threshold if threshold > 0 else 1.0

        if ratio > 2.0:
            return "critical"
        elif ratio > 1.5:
            return "high"
        elif ratio > 1.2:
            return "medium"
        else:
            return "low"

    def _generate_alert_message(
        self, alert_type: str, prediction_value: float, threshold: float
    ) -> str:
        """Generate human-readable alert message."""
        messages = {
            "anomaly_score": f"Anomaly detected with score {prediction_value:.3f} (threshold: {threshold})",
            "failure_probability": f"High failure probability: {prediction_value:.1%} (threshold: {threshold:.1%})",
            "performance_drop": f"Performance drop detected: {prediction_value:.1%} (threshold: {threshold:.1%})",
            "maintenance_due": f"Maintenance due in {prediction_value:.0f} days (threshold: {threshold} days)",
        }
        return messages.get(
            alert_type, f"Alert triggered: {prediction_value:.3f} > {threshold}"
        )

    async def get_alerts_async(
        self,
        machine_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """
        Asynchronously retrieve alerts with filtering.

        Args:
            machine_id: Filter by machine ID
            acknowledged: Filter by acknowledgment status
            severity: Filter by severity
            limit: Maximum number of alerts to return

        Returns:
            List of matching alerts
        """
        async with self._lock:
            alerts = self.alerts.copy()

            # Apply filters
            if machine_id:
                alerts = [a for a in alerts if a.machine_id == machine_id]
            if acknowledged is not None:
                alerts = [a for a in alerts if a.acknowledged == acknowledged]
            if severity:
                alerts = [a for a in alerts if a.severity == severity]

            # Sort by timestamp (newest first) and limit
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            alerts = alerts[:limit]

            self.logger.debug(f"Retrieved {len(alerts)} alerts with filters")
            return alerts

    def get_alerts(
        self,
        machine_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """
        Synchronously retrieve alerts with filtering.

        Args:
            machine_id: Filter by machine ID
            acknowledged: Filter by acknowledgment status
            severity: Filter by severity
            limit: Maximum number of alerts to return

        Returns:
            List of matching alerts
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.get_alerts_async(
                            machine_id, acknowledged, severity, limit
                        ),
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.get_alerts_async(machine_id, acknowledged, severity, limit)
                )
        except Exception as e:
            self.logger.error(f"Error retrieving alerts: {e}")
            return []

    async def acknowledge_alert_async(
        self, alert_id: str, acknowledged_by: str
    ) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: ID of the alert to acknowledge
            acknowledged_by: User who acknowledged the alert

        Returns:
            True if alert was acknowledged, False if not found
        """
        async with self._lock:
            for alert in self.alerts:
                if alert.id == alert_id and not alert.acknowledged:
                    alert.acknowledged = True
                    alert.acknowledged_at = datetime.now()
                    alert.acknowledged_by = acknowledged_by
                    self.logger.info(
                        f"Alert {alert_id} acknowledged by {acknowledged_by}"
                    )
                    return True
            return False

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Synchronously acknowledge an alert.

        Args:
            alert_id: ID of the alert to acknowledge
            acknowledged_by: User who acknowledged the alert

        Returns:
            True if alert was acknowledged, False if not found
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.acknowledge_alert_async(alert_id, acknowledged_by),
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.acknowledge_alert_async(alert_id, acknowledged_by)
                )
        except Exception as e:
            self.logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False

    async def clear_alerts_async(self, machine_id: Optional[str] = None) -> int:
        """
        Clear alerts (optionally for specific machine).

        Args:
            machine_id: Optional machine ID to clear alerts for

        Returns:
            Number of alerts cleared
        """
        async with self._lock:
            if machine_id:
                initial_count = len(self.alerts)
                self.alerts = [a for a in self.alerts if a.machine_id != machine_id]
                cleared = initial_count - len(self.alerts)
            else:
                cleared = len(self.alerts)
                self.alerts.clear()

            self.logger.info(f"Cleared {cleared} alerts")
            return cleared

    def clear_alerts(self, machine_id: Optional[str] = None) -> int:
        """
        Synchronously clear alerts.

        Args:
            machine_id: Optional machine ID to clear alerts for

        Returns:
            Number of alerts cleared
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.clear_alerts_async(machine_id)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(self.clear_alerts_async(machine_id))
        except Exception as e:
            self.logger.error(f"Error clearing alerts: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about alerts.

        Returns:
            Dictionary with alert statistics
        """
        total_alerts = len(self.alerts)
        acknowledged = len([a for a in self.alerts if a.acknowledged])
        unacknowledged = total_alerts - acknowledged

        severity_counts = {}
        for alert in self.alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1

        return {
            "total_alerts": total_alerts,
            "acknowledged": acknowledged,
            "unacknowledged": unacknowledged,
            "severity_breakdown": severity_counts,
            "models_loaded": list(self.models.keys()),
        }

    async def predict_with_automl(
        self, data: Union[pd.DataFrame, np.ndarray, List]
    ) -> Optional[Dict[str, Any]]:
        """
        Make predictions using integrated AutoML engine.

        Args:
            data: Input data for prediction

        Returns:
            Prediction results if AutoML is available, None otherwise
        """
        if not AUTOML_AVAILABLE or not automl_engine.best_model:
            self.logger.warning("AutoML engine not available or not trained")
            return None

        try:
            # Convert data to DataFrame if needed
            if isinstance(data, (list, np.ndarray)):
                if isinstance(data[0], dict):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame(data)
            else:
                df = data

            # Make prediction
            predictions = automl_engine.predict(df)

            result = {
                "predictions": predictions.tolist()
                if hasattr(predictions, "tolist")
                else predictions,
                "model_name": automl_engine.best_model_name,
                "confidence": automl_engine.best_score,
                "timestamp": datetime.now(),
                "data_shape": df.shape,
            }

            self.logger.info(
                f"AutoML prediction completed using {automl_engine.best_model_name}"
            )
            return result

        except Exception as e:
            self.logger.error(f"AutoML prediction failed: {e}")
            return None

    async def generate_alert_from_automl(
        self,
        data: Union[pd.DataFrame, np.ndarray, List],
        machine_id: str,
        alert_type: str = "automl_prediction",
    ) -> Optional[Alert]:
        """
        Generate alerts based on AutoML predictions.

        Args:
            data: Input data for AutoML prediction
            machine_id: Machine identifier
            alert_type: Type of alert to generate

        Returns:
            Alert if prediction exceeds thresholds, None otherwise
        """
        prediction_result = await self.predict_with_automl(data)
        if not prediction_result:
            return None

        # Use prediction values to determine if alert should be generated
        predictions = prediction_result["predictions"]
        if isinstance(predictions, list) and len(predictions) > 0:
            prediction_value = float(np.mean(predictions))
        else:
            prediction_value = float(predictions)

        # For anomaly detection, high prediction values indicate anomalies
        threshold = self.default_thresholds.get("anomaly_score", 0.8)

        if prediction_value > threshold:
            alert = Alert(
                id=f"automl_alert_{int(datetime.now().timestamp())}",
                machine_id=machine_id,
                severity="high" if prediction_value > threshold * 1.5 else "medium",
                alert_type=alert_type,
                message=f"AutoML detected anomaly with score {prediction_value:.3f} (threshold: {threshold})",
                prediction_value=prediction_value,
                threshold=threshold,
                timestamp=datetime.now(),
                metadata={
                    "model_name": prediction_result.get("model_name"),
                    "automl_confidence": prediction_result.get("confidence"),
                    "data_shape": prediction_result.get("data_shape"),
                },
            )

            self.alerts.append(alert)
            self.logger.warning(f"AutoML alert generated: {alert.message}")
            return alert

        return None

    def optimize_with_rl(
        self, current_parameters: Dict[str, float]
    ) -> Optional[Dict[str, float]]:
        """
        Optimize parameters using integrated RL engine.

        Args:
            current_parameters: Current parameter values

        Returns:
            Optimized parameters if RL is available, None otherwise
        """
        if not RL_AVAILABLE:
            self.logger.warning("RL engine not available for optimization")
            return None

        try:
            optimized = rl_engine.optimize_parameters(current_parameters)
            self.logger.info("RL optimization completed")
            return optimized

        except Exception as e:
            self.logger.error(f"RL optimization failed: {e}")
            return None
