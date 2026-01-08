"""
Module: Sensor Health Monitor

This module monitors the health and performance of IoT sensors in the IIoT platform.
It analyzes sensor data for anomalies, calibration issues, and overall health status.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from config import settings
from utils.logging_config import LoggerMixin
from utils.performance_monitor import monitor_operation
from utils.security import SecurityError, input_validator, validate_input

# Import core ML engines for integration
try:
    from automl_engine import automl_engine
    from reinforcement_learning import rl_engine

    AUTOML_AVAILABLE = True
    RL_AVAILABLE = True
except ImportError:
    AUTOML_AVAILABLE = False
    RL_AVAILABLE = False
    # Logger will be available after class definition


class SensorStatus(Enum):
    """Enumeration of possible sensor health statuses."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"
    MAINTENANCE_REQUIRED = "maintenance_required"


@dataclass
class SensorMetrics:
    """Data structure for sensor health metrics."""

    sensor_id: str
    timestamp: datetime
    status: SensorStatus
    signal_strength: Optional[float] = None
    battery_level: Optional[float] = None
    temperature: Optional[float] = None
    calibration_offset: Optional[float] = None
    data_quality_score: Optional[float] = None
    anomaly_score: Optional[float] = None
    last_reading: Optional[datetime] = None
    readings_count: int = 0
    error_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


class SensorHealthMonitorError(Exception):
    """Base exception for SensorHealthMonitor module."""

    pass


class InvalidSensorDataError(SensorHealthMonitorError):
    """Raised when sensor data is invalid or corrupted."""

    pass


class SensorNotFoundError(SensorHealthMonitorError):
    """Raised when requested sensor is not found."""

    pass


class SensorHealthMonitor(LoggerMixin):
    """
    Advanced sensor health monitoring system with anomaly detection and predictive maintenance.

    This class monitors IoT sensor health by analyzing data patterns, detecting anomalies,
    and providing maintenance recommendations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SensorHealthMonitor.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

        # Sensor registry and metrics
        self.sensors: Dict[str, SensorMetrics] = {}
        self.historical_data: Dict[str, List[SensorMetrics]] = {}

        # Health thresholds
        self.thresholds = {
            "signal_strength_min": 0.3,
            "battery_level_min": 0.15,
            "temperature_max": 80.0,
            "calibration_offset_max": 0.05,
            "data_quality_min": 0.7,
            "anomaly_score_max": 0.8,
            "max_offline_hours": 2,
            "error_rate_max": 0.1,
        }

        # Update with config
        self.thresholds.update(self.config.get("thresholds", {}))

        # Monitoring settings
        self.monitoring_interval = self.config.get("monitoring_interval", 60)  # seconds
        self.history_retention_days = self.config.get("history_retention_days", 30)

        self.logger.info("SensorHealthMonitor initialized")

    @validate_input(
        {
            "sensor_id": {
                "type": "string",
                "max_length": 50,
                "required": True,
                "pattern": "^[a-zA-Z0-9_-]{1,50}$",
            }
        }
    )
    def register_sensor(
        self, sensor_id: str, initial_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a new sensor for monitoring.

        Args:
            sensor_id: Unique identifier for the sensor
            initial_data: Optional initial sensor data

        Raises:
            ValueError: If sensor_id is invalid
            SecurityError: If input validation fails
        """
        # Security checks
        if input_validator.check_sql_injection(sensor_id):
            raise SecurityError("Invalid sensor ID: potential SQL injection detected")

        if input_validator.check_xss(sensor_id):
            raise SecurityError("Invalid sensor ID: potential XSS detected")

        if not input_validator.validate_sensor_id(sensor_id):
            raise SecurityError("Invalid sensor ID format")

        if sensor_id in self.sensors:
            self.logger.warning(f"Sensor {sensor_id} already registered, updating")
        else:
            self.logger.info(f"Registering new sensor: {sensor_id}")

        # Validate initial data if provided
        if initial_data:
            for key, value in initial_data.items():
                if isinstance(value, (int, float)):
                    input_validator.validate_numeric_range(
                        value, -1000, 1000
                    )  # Reasonable bounds

        metrics = SensorMetrics(
            sensor_id=sensor_id,
            timestamp=datetime.now(),
            status=SensorStatus.OFFLINE,
            **(initial_data or {}),
        )

        self.sensors[sensor_id] = metrics
        self.historical_data[sensor_id] = []

    @monitor_operation("sensor_health_monitor.update_sensor_data")
    @validate_input(
        {
            "sensor_id": {
                "type": "string",
                "max_length": 50,
                "required": True,
                "pattern": "^[a-zA-Z0-9_-]{1,50}$",
            }
        }
    )
    def update_sensor_data(
        self, sensor_id: str, data: Dict[str, Any], timestamp: Optional[datetime] = None
    ) -> SensorMetrics:
        """
        Update sensor data and recalculate health metrics.

        Args:
            sensor_id: ID of the sensor to update
            data: New sensor data
            timestamp: Optional timestamp for the data

        Returns:
            Updated sensor metrics

        Raises:
            SensorNotFoundError: If sensor is not registered
            InvalidSensorDataError: If data is invalid
        """
        if sensor_id not in self.sensors:
            raise SensorNotFoundError(f"Sensor {sensor_id} not registered")

        try:
            current_metrics = self.sensors[sensor_id]
            update_time = timestamp or datetime.now()

            # Validate data
            self._validate_sensor_data(data)

            # Update metrics
            for key, value in data.items():
                if hasattr(current_metrics, key):
                    setattr(current_metrics, key, value)

            current_metrics.timestamp = update_time
            current_metrics.last_reading = update_time
            current_metrics.readings_count += 1

            # Recalculate health status
            current_metrics.status = self._calculate_health_status(sensor_id)

            # Store historical data
            self._store_historical_data(sensor_id, current_metrics)

            self.logger.debug(
                f"Updated sensor {sensor_id} data, status: {current_metrics.status.value}"
            )
            return current_metrics

        except Exception as e:
            self.logger.error(f"Error updating sensor {sensor_id} data: {e}")
            # Increment error count
            self.sensors[sensor_id].error_count += 1
            raise SensorHealthMonitorError(f"Failed to update sensor data: {e}") from e

    def monitor_sensor_health(
        self, sensor_id: Optional[str] = None
    ) -> Union[SensorMetrics, Dict[str, SensorMetrics]]:
        """
        Monitor health of a specific sensor or all sensors.

        Args:
            sensor_id: Optional specific sensor ID to monitor

        Returns:
            SensorMetrics for single sensor or dict of all sensors

        Raises:
            SensorNotFoundError: If specific sensor not found
        """
        if sensor_id:
            if sensor_id not in self.sensors:
                raise SensorNotFoundError(f"Sensor {sensor_id} not found")
            return self.sensors[sensor_id]
        else:
            # Monitor all sensors
            results = {}
            for sid, metrics in self.sensors.items():
                # Update status if needed (check for timeouts, etc.)
                metrics.status = self._calculate_health_status(sid)
                results[sid] = metrics

            self.logger.info(f"Monitored {len(results)} sensors")
            return results

    @monitor_operation("sensor_health_monitor.analyze_sensor_data")
    def analyze_sensor_data(
        self, sensor_id: str, data_window: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Perform detailed analysis of sensor data for health assessment.

        Args:
            sensor_id: ID of the sensor to analyze
            data_window: Optional DataFrame with historical data

        Returns:
            Dictionary with analysis results

        Raises:
            SensorNotFoundError: If sensor not found
        """
        if sensor_id not in self.sensors:
            raise SensorNotFoundError(f"Sensor {sensor_id} not found")

        try:
            metrics = self.sensors[sensor_id]
            analysis = {
                "sensor_id": sensor_id,
                "timestamp": datetime.now(),
                "overall_health": metrics.status.value,
                "metrics": asdict(metrics),
                "recommendations": [],
            }

            # Get historical data if not provided
            if data_window is None:
                data_window = self._get_historical_dataframe(sensor_id, hours=24)

            if not data_window.empty:
                # Perform advanced analysis
                analysis.update(self._perform_advanced_analysis(sensor_id, data_window))

            # Generate recommendations
            analysis["recommendations"] = self._generate_recommendations(
                sensor_id, analysis
            )

            self.logger.info(f"Completed analysis for sensor {sensor_id}")
            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing sensor {sensor_id} data: {e}")
            raise SensorHealthMonitorError(f"Failed to analyze sensor data: {e}") from e

    def _validate_sensor_data(self, data: Dict[str, Any]) -> None:
        """Validate incoming sensor data."""
        required_fields = []  # No required fields for flexibility

        # Check data types
        numeric_fields = [
            "signal_strength",
            "battery_level",
            "temperature",
            "calibration_offset",
            "data_quality_score",
            "anomaly_score",
        ]

        for field in numeric_fields:
            if field in data:
                try:
                    data[field] = float(data[field])
                except (ValueError, TypeError):
                    raise InvalidSensorDataError(
                        f"Invalid numeric value for {field}: {data[field]}"
                    )

    def _calculate_health_status(self, sensor_id: str) -> SensorStatus:
        """Calculate overall health status for a sensor."""
        metrics = self.sensors[sensor_id]

        # Check if sensor is offline
        if metrics.last_reading:
            offline_hours = (
                datetime.now() - metrics.last_reading
            ).total_seconds() / 3600
            if offline_hours > self.thresholds["max_offline_hours"]:
                return SensorStatus.OFFLINE

        # Check error rate
        if metrics.readings_count > 0:
            error_rate = metrics.error_count / metrics.readings_count
            if error_rate > self.thresholds["error_rate_max"]:
                return SensorStatus.CRITICAL

        # Check individual metrics
        critical_checks = [
            (
                metrics.signal_strength,
                self.thresholds["signal_strength_min"],
                lambda x, t: x is not None and x < t,
            ),
            (
                metrics.battery_level,
                self.thresholds["battery_level_min"],
                lambda x, t: x is not None and x < t,
            ),
            (
                metrics.temperature,
                self.thresholds["temperature_max"],
                lambda x, t: x is not None and x > t,
            ),
            (
                metrics.calibration_offset,
                self.thresholds["calibration_offset_max"],
                lambda x, t: x is not None and abs(x) > t,
            ),
            (
                metrics.data_quality_score,
                self.thresholds["data_quality_min"],
                lambda x, t: x is not None and x < t,
            ),
            (
                metrics.anomaly_score,
                self.thresholds["anomaly_score_max"],
                lambda x, t: x is not None and x > t,
            ),
        ]

        for value, threshold, check_func in critical_checks:
            if check_func(value, threshold):
                return SensorStatus.CRITICAL

        # Warning checks (less strict)
        warning_checks = [
            (
                metrics.signal_strength,
                self.thresholds["signal_strength_min"] * 1.2,
                lambda x, t: x is not None and x < t,
            ),
            (
                metrics.battery_level,
                self.thresholds["battery_level_min"] * 1.5,
                lambda x, t: x is not None and x < t,
            ),
            (
                metrics.anomaly_score,
                self.thresholds["anomaly_score_max"] * 0.8,
                lambda x, t: x is not None and x > t,
            ),
        ]

        for value, threshold, check_func in warning_checks:
            if check_func(value, threshold):
                return SensorStatus.WARNING

        return SensorStatus.HEALTHY

    def _perform_advanced_analysis(
        self, sensor_id: str, data_window: pd.DataFrame
    ) -> Dict[str, Any]:
        """Perform advanced statistical analysis on sensor data."""
        analysis = {
            "trend_analysis": {},
            "volatility": {},
            "correlation_insights": {},
            "predictive_insights": {},
        }

        try:
            # Basic statistical analysis
            numeric_columns = data_window.select_dtypes(include=[np.number]).columns

            for col in numeric_columns:
                if col in data_window.columns:
                    series = data_window[col].dropna()
                    if len(series) > 1:
                        # Trend analysis
                        analysis["trend_analysis"][col] = {
                            "slope": np.polyfit(range(len(series)), series, 1)[0],
                            "volatility": series.std(),
                            "min": series.min(),
                            "max": series.max(),
                            "mean": series.mean(),
                        }

                        # Volatility analysis
                        if len(series) > 10:
                            rolling_std = series.rolling(
                                window=min(10, len(series))
                            ).std()
                            analysis["volatility"][col] = {
                                "current_volatility": rolling_std.iloc[-1]
                                if not rolling_std.empty
                                else 0,
                                "avg_volatility": rolling_std.mean()
                                if not rolling_std.empty
                                else 0,
                            }

            # Correlation analysis if multiple numeric columns
            if len(numeric_columns) > 1:
                corr_matrix = data_window[numeric_columns].corr()
                # Find highly correlated pairs
                high_corr = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i + 1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            high_corr.append(
                                {
                                    "pair": [
                                        corr_matrix.columns[i],
                                        corr_matrix.columns[j],
                                    ],
                                    "correlation": corr_val,
                                }
                            )
                analysis["correlation_insights"] = high_corr

        except Exception as e:
            self.logger.warning(f"Advanced analysis failed for sensor {sensor_id}: {e}")

        return analysis

    def _generate_recommendations(
        self, sensor_id: str, analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate maintenance and improvement recommendations."""
        recommendations = []
        metrics = self.sensors[sensor_id]

        # Status-based recommendations
        if metrics.status == SensorStatus.CRITICAL:
            recommendations.append(
                "Immediate maintenance required - sensor showing critical issues"
            )
        elif metrics.status == SensorStatus.WARNING:
            recommendations.append(
                "Schedule maintenance soon - sensor showing warning signs"
            )
        elif metrics.status == SensorStatus.OFFLINE:
            recommendations.append(
                "Sensor is offline - check connectivity and power supply"
            )

        # Specific metric recommendations
        if (
            metrics.battery_level
            and metrics.battery_level < self.thresholds["battery_level_min"]
        ):
            recommendations.append("Replace battery immediately")

        if (
            metrics.calibration_offset
            and abs(metrics.calibration_offset)
            > self.thresholds["calibration_offset_max"]
        ):
            recommendations.append(
                "Recalibrate sensor - offset exceeds acceptable range"
            )

        if (
            metrics.temperature
            and metrics.temperature > self.thresholds["temperature_max"]
        ):
            recommendations.append("Check cooling system - sensor temperature too high")

        # Trend-based recommendations
        trend_analysis = analysis.get("trend_analysis", {})
        for metric, trend in trend_analysis.items():
            if trend.get("slope", 0) < -0.01:  # Deteriorating trend
                recommendations.append(
                    f"Monitor {metric} - showing deteriorating trend"
                )

        return recommendations

    def _store_historical_data(self, sensor_id: str, metrics: SensorMetrics) -> None:
        """Store metrics in historical data with retention policy."""
        if sensor_id not in self.historical_data:
            self.historical_data[sensor_id] = []

        self.historical_data[sensor_id].append(metrics)

        # Apply retention policy
        cutoff_date = datetime.now() - timedelta(days=self.history_retention_days)
        self.historical_data[sensor_id] = [
            m for m in self.historical_data[sensor_id] if m.timestamp > cutoff_date
        ]

    def _get_historical_dataframe(
        self, sensor_id: str, hours: int = 24
    ) -> pd.DataFrame:
        """Get historical data as DataFrame for analysis."""
        if sensor_id not in self.historical_data:
            return pd.DataFrame()

        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_data = [
            m for m in self.historical_data[sensor_id] if m.timestamp > cutoff_time
        ]

        if not recent_data:
            return pd.DataFrame()

        # Convert to DataFrame
        data_dict = {}
        for metric in asdict(recent_data[0]).keys():
            data_dict[metric] = [getattr(m, metric) for m in recent_data]

        df = pd.DataFrame(data_dict)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        return df

    def get_sensor_stats(self, sensor_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for sensor(s).

        Args:
            sensor_id: Optional specific sensor ID

        Returns:
            Dictionary with sensor statistics
        """
        if sensor_id:
            if sensor_id not in self.sensors:
                raise SensorNotFoundError(f"Sensor {sensor_id} not found")

            metrics = self.sensors[sensor_id]
            history = self.historical_data.get(sensor_id, [])

            return {
                "sensor_id": sensor_id,
                "current_status": metrics.status.value,
                "total_readings": metrics.readings_count,
                "error_count": metrics.error_count,
                "error_rate": metrics.error_count / max(metrics.readings_count, 1),
                "last_reading": metrics.last_reading.isoformat()
                if metrics.last_reading
                else None,
                "historical_records": len(history),
                "health_score": self._calculate_health_score(metrics),
            }
        else:
            # Stats for all sensors
            stats = {}
            status_counts = {}

            for sid, metrics in self.sensors.items():
                stats[sid] = self.get_sensor_stats(sid)
                status = metrics.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            return {
                "total_sensors": len(self.sensors),
                "status_distribution": status_counts,
                "individual_stats": stats,
            }

    def _calculate_health_score(self, metrics: SensorMetrics) -> float:
        """Calculate a numerical health score (0-100)."""
        score = 100.0

        # Deduct points for various issues
        if metrics.status == SensorStatus.CRITICAL:
            score -= 50
        elif metrics.status == SensorStatus.WARNING:
            score -= 25
        elif metrics.status == SensorStatus.OFFLINE:
            score -= 40

        # Deduct for low signal strength
        if (
            metrics.signal_strength
            and metrics.signal_strength < self.thresholds["signal_strength_min"]
        ):
            score -= (
                self.thresholds["signal_strength_min"] - metrics.signal_strength
            ) * 100

        # Deduct for low battery
        if (
            metrics.battery_level
            and metrics.battery_level < self.thresholds["battery_level_min"]
        ):
            score -= (
                self.thresholds["battery_level_min"] - metrics.battery_level
            ) * 200

        # Deduct for high error rate
        if metrics.readings_count > 0:
            error_rate = metrics.error_count / metrics.readings_count
            score -= error_rate * 50

        return max(0.0, min(100.0, score))

    async def detect_anomalies_automl(
        self, sensor_id: str, data_window: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Detect anomalies using integrated AutoML engine.

        Args:
            sensor_id: ID of the sensor to analyze
            data_window: Optional DataFrame with historical data

        Returns:
            Dictionary with anomaly detection results
        """
        if not AUTOML_AVAILABLE or not automl_engine.best_model:
            self.logger.warning("AutoML engine not available for anomaly detection")
            return {
                "sensor_id": sensor_id,
                "anomaly_detection_available": False,
                "anomalies_detected": [],
                "message": "AutoML not available",
            }

        try:
            # Get historical data if not provided
            if data_window is None:
                data_window = self._get_historical_dataframe(sensor_id, hours=24)

            if data_window.empty:
                return {
                    "sensor_id": sensor_id,
                    "anomaly_detection_available": True,
                    "anomalies_detected": [],
                    "message": "No historical data available",
                }

            # Prepare data for AutoML (use recent data points)
            recent_data = data_window.tail(
                min(100, len(data_window))
            )  # Last 100 readings

            # Select numeric columns for anomaly detection
            numeric_cols = recent_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return {
                    "sensor_id": sensor_id,
                    "anomaly_detection_available": True,
                    "anomalies_detected": [],
                    "message": "No numeric data available for anomaly detection",
                }

            # Use AutoML to predict expected values
            predictions = automl_engine.predict(recent_data[numeric_cols])

            # Calculate anomaly scores (deviation from predictions)
            anomalies = []
            for i, (idx, row) in enumerate(recent_data.iterrows()):
                if i < len(predictions):
                    # Simple anomaly score based on prediction error
                    actual_values = row[numeric_cols].values
                    predicted_values = (
                        predictions[i]
                        if hasattr(predictions[i], "__len__")
                        else [predictions[i]]
                    )

                    # Calculate mean absolute error
                    if len(actual_values) == len(predicted_values):
                        error = np.mean(np.abs(actual_values - predicted_values))
                        anomaly_score = min(
                            error / np.mean(np.abs(actual_values) + 1e-6), 1.0
                        )  # Normalize

                        if anomaly_score > self.thresholds.get(
                            "anomaly_score_max", 0.8
                        ):
                            anomalies.append(
                                {
                                    "timestamp": idx,
                                    "anomaly_score": anomaly_score,
                                    "actual_values": dict(
                                        zip(numeric_cols, actual_values)
                                    ),
                                    "predicted_values": dict(
                                        zip(numeric_cols, predicted_values)
                                    ),
                                    "error": error,
                                }
                            )

            result = {
                "sensor_id": sensor_id,
                "anomaly_detection_available": True,
                "anomalies_detected": anomalies,
                "total_anomalies": len(anomalies),
                "model_used": automl_engine.best_model_name,
                "data_points_analyzed": len(recent_data),
                "analysis_timestamp": datetime.now(),
            }

            self.logger.info(
                f"AutoML anomaly detection completed for {sensor_id}: {len(anomalies)} anomalies detected"
            )
            return result

        except Exception as e:
            self.logger.error(f"AutoML anomaly detection failed for {sensor_id}: {e}")
            return {
                "sensor_id": sensor_id,
                "anomaly_detection_available": True,
                "anomalies_detected": [],
                "error": str(e),
            }

    async def optimize_sensor_parameters(
        self, sensor_id: str
    ) -> Optional[Dict[str, float]]:
        """
        Optimize sensor parameters using integrated RL engine.

        Args:
            sensor_id: ID of the sensor to optimize

        Returns:
            Optimized parameters if available, None otherwise
        """
        if not RL_AVAILABLE or sensor_id not in self.sensors:
            return None

        try:
            current_metrics = self.sensors[sensor_id]

            # Prepare current parameters for RL optimization
            current_params = {}
            if current_metrics.signal_strength is not None:
                current_params["signal_strength"] = current_metrics.signal_strength
            if current_metrics.battery_level is not None:
                current_params["battery_level"] = current_metrics.battery_level
            if current_metrics.temperature is not None:
                current_params["temperature"] = current_metrics.temperature

            if not current_params:
                return None

            # Use RL to optimize parameters
            optimized = rl_engine.optimize_parameters(current_params)

            self.logger.info(f"RL optimization completed for sensor {sensor_id}")
            return optimized

        except Exception as e:
            self.logger.error(f"RL optimization failed for sensor {sensor_id}: {e}")
            return None
