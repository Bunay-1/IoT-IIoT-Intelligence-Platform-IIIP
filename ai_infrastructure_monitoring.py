"""
AI Infrastructure Monitoring Module

This module implements AI infrastructure monitoring for the IoT IIoT platform,
providing model performance tracking, infrastructure monitoring, anomaly detection, and automated optimization.
"""

import asyncio
import json
import time
import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum

import numpy as np
from scipy.stats import ks_2samp, linregress

from utils.logging_config import get_logger

logger = get_logger(__name__)


class MonitoringMetric(Enum):
    """Monitoring metrics."""
    MODEL_ACCURACY = "model_accuracy"
    MODEL_LATENCY = "model_latency"
    MODEL_THROUGHPUT = "model_throughput"
    MODEL_MEMORY_USAGE = "model_memory_usage"
    MODEL_CPU_USAGE = "model_cpu_usage"
    PREDICTION_DRIFT = "prediction_drift"
    DATA_DRIFT = "data_drift"
    INFRASTRUCTURE_HEALTH = "infrastructure_health"
    RESOURCE_UTILIZATION = "resource_utilization"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class OptimizationAction(Enum):
    """Optimization actions."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RETRAIN_MODEL = "retrain_model"
    UPDATE_MODEL = "update_model"
    RESTART_SERVICE = "restart_service"
    LOAD_BALANCE = "load_balance"


class AIInfrastructureMonitoring:
    """
    AI Infrastructure Monitoring system.

    Features:
    - Model performance monitoring
    - Infrastructure health tracking
    - Anomaly detection
    - Automated optimization
    - Drift detection
    - Predictive maintenance
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # Model monitoring
        self.model_metrics: Dict[str, Dict] = defaultdict(dict)

        # Infrastructure monitoring
        self.infrastructure_metrics: Dict[str, Dict] = defaultdict(dict)

        # Active alerts
        self.active_alerts: Dict[str, Dict] = {}

        # Optimization rules
        self.optimization_rules: Dict[str, List[Dict]] = defaultdict(list)
        self.cooldown_timestamps: Dict[str, datetime] = {}

        # Historical data
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))

        # Drift detection
        self.drift_detectors: Dict[str, Dict] = {}

        # Performance baselines
        self.performance_baselines: Dict[str, Dict] = {}

        self.logger = get_logger(__name__)
        self.logger.info("AI Infrastructure Monitoring initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "monitoring_interval": 60,  # seconds
            "metrics_retention_hours": 24,
            "alert_cooldown_minutes": 5,
            "drift_detection_enabled": True,
            "auto_optimization_enabled": True,
            "anomaly_detection_sensitivity": 3.0,  # 3-sigma sensitivity
            "anomaly_min_samples": 20, # Min samples for std dev calc
            "performance_baseline_window": 168,  # 7 days in hours
            "max_alerts_per_hour": 10,
            "enable_predictive_maintenance": True,
        }

    def register_model_monitoring(
        self,
        model_id: str,
        model_config: Dict,
        monitoring_config: Optional[Dict] = None
    ) -> bool:
        """
        Register model for monitoring.

        Args:
            model_id: Model identifier
            model_config: Model configuration
            monitoring_config: Monitoring configuration for drift, etc.

        Returns:
            Registration success
        """
        try:
            monitoring = {
                "model_id": model_id,
                "config": model_config,
                "monitoring_config": monitoring_config or {},
                "registered_at": datetime.now(),
                "last_updated": None,
                "status": "active",
                "metrics": {
                    "accuracy": [],
                    "latency": [],
                    "throughput": [],
                    "memory_usage": [],
                    "cpu_usage": [],
                    "prediction_count": 0
                },
                "alerts": [],
                "drift_score": 0.0,
                "drift_detected": False,
                "performance_score": 1.0
            }

            self.model_metrics[model_id] = monitoring

            # Initialize drift detection
            if self.config["drift_detection_enabled"]:
                self._initialize_drift_detection(model_id, monitoring_config)

            self.logger.info(f"Registered model monitoring: {model_id}")
            return True

        except Exception as e:
            self.logger.error(f"Model monitoring registration failed: {e}")
            return False

    def _initialize_drift_detection(self, model_id: str, monitoring_config: Optional[Dict]):
        """Initialize drift detection for model."""
        drift_config = monitoring_config.get("drift_detection", {}) if monitoring_config else {}

        detector = {
            "model_id": model_id,
            "reference_data": [],
            "current_data": deque(maxlen=1000),
            "drift_threshold": drift_config.get("threshold", 0.1),
            "window_size": drift_config.get("window_size", 100),
            "last_drift_check": None,
            "drift_detected": False,
            "drift_score": 0.0
        }

        self.drift_detectors[model_id] = detector

    def register_infrastructure_monitoring(
        self,
        component_id: str,
        component_type: str,
        monitoring_config: Optional[Dict] = None
    ) -> bool:
        """
        Register infrastructure component for monitoring.

        Args:
            component_id: Component identifier
            component_type: Type of component
            monitoring_config: Monitoring configuration

        Returns:
            Registration success
        """
        try:
            monitoring = {
                "component_id": component_id,
                "component_type": component_type,
                "monitoring_config": monitoring_config or {},
                "registered_at": datetime.now(),
                "last_updated": None,
                "status": "active",
                "metrics": {
                    "cpu_usage": [],
                    "memory_usage": [],
                    "disk_usage": [],
                    "network_io": [],
                    "response_time": [],
                    "error_rate": [],
                    "uptime": 0
                },
                "health_score": 1.0,
                "alerts": []
            }

            self.infrastructure_metrics[component_id] = monitoring

            self.logger.info(f"Registered infrastructure monitoring: {component_id}")
            return True

        except Exception as e:
            self.logger.error(f"Infrastructure monitoring registration failed: {e}")
            return False

    async def record_model_metrics(
        self,
        model_id: str,
        metrics: Dict[str, Union[float, int]],
        prediction_data: Optional[Dict] = None
    ):
        """
        Record model performance metrics.

        Args:
            model_id: Model identifier
            metrics: Performance metrics
            prediction_data: Prediction data for drift detection
        """
        try:
            if model_id not in self.model_metrics:
                self.logger.warning(f"Model {model_id} not registered for monitoring")
                return

            monitoring = self.model_metrics[model_id]
            monitoring["last_updated"] = datetime.now()

            # Record metrics
            for metric_name, value in metrics.items():
                if metric_name in monitoring["metrics"]:
                    monitoring["metrics"][metric_name].append({
                        "value": value,
                        "timestamp": datetime.now()
                    })

                    # Keep only recent metrics
                    if len(monitoring["metrics"][metric_name]) > 1000:
                        monitoring["metrics"][metric_name] = monitoring["metrics"][metric_name][-1000:]

            monitoring["metrics"]["prediction_count"] += 1

            # Store in global history
            timestamp = datetime.now()
            for metric_name, value in metrics.items():
                self.metrics_history[f"model_{model_id}_{metric_name}"].append({
                    "value": value,
                    "timestamp": timestamp
                })

            # Check for drift if prediction data provided
            if prediction_data and self.config["drift_detection_enabled"]:
                await self._check_model_drift(model_id, prediction_data)

            # Check for anomalies
            await self._check_for_anomalies(model_id, "model", metrics)

            # Update performance score
            self._update_model_performance_score(model_id)

        except Exception as e:
            self.logger.error(f"Model metrics recording failed: {e}")

    async def record_infrastructure_metrics(
        self,
        component_id: str,
        metrics: Dict[str, Union[float, int]]
    ):
        """
        Record infrastructure metrics.

        Args:
            component_id: Component identifier
            metrics: Infrastructure metrics
        """
        try:
            if component_id not in self.infrastructure_metrics:
                self.logger.warning(f"Component {component_id} not registered for monitoring")
                return

            monitoring = self.infrastructure_metrics[component_id]
            monitoring["last_updated"] = datetime.now()

            # Record metrics
            for metric_name, value in metrics.items():
                if metric_name in monitoring["metrics"]:
                    monitoring["metrics"][metric_name].append({
                        "value": value,
                        "timestamp": datetime.now()
                    })

                    # Keep only recent metrics
                    if len(monitoring["metrics"][metric_name]) > 1000:
                        monitoring["metrics"][metric_name] = monitoring["metrics"][metric_name][-1000:]

            # Store in global history
            timestamp = datetime.now()
            for metric_name, value in metrics.items():
                self.metrics_history[f"infra_{component_id}_{metric_name}"].append({
                    "value": value,
                    "timestamp": timestamp
                })

            # Update health score
            self._update_infrastructure_health_score(component_id)

            # Check for anomalies
            await self._check_for_anomalies(component_id, "infrastructure", metrics)

        except Exception as e:
            self.logger.error(f"Infrastructure metrics recording failed: {e}")

    async def _check_model_drift(self, model_id: str, prediction_data: Dict):
        """Check for model drift."""
        try:
            detector = self.drift_detectors.get(model_id)
            if not detector:
                return

            # Add current data point
            detector["current_data"].append(prediction_data)

            # Check if we have enough data for drift detection
            if len(detector["current_data"]) < detector["window_size"]:
                return

            # Calculate drift score (simplified - in real implementation would use statistical tests)
            current_window = list(detector["current_data"])[-detector["window_size"]:]

            # Simple drift detection based on prediction distribution change
            if detector["reference_data"]:
                drift_score = self._calculate_drift_score(detector["reference_data"], current_window)
                detector["drift_score"] = drift_score
                detector["last_drift_check"] = datetime.now()
                self.model_metrics[model_id]["drift_score"] = drift_score

                if drift_score > detector["drift_threshold"]:
                    detector["drift_detected"] = True
                    self.model_metrics[model_id]["drift_detected"] = True
                    await self._trigger_drift_alert(model_id, drift_score)
                else:
                    detector["drift_detected"] = False
                    self.model_metrics[model_id]["drift_detected"] = False

            # Update reference data periodically
            if len(detector["current_data"]) % (detector["window_size"] * 10) == 0:
                detector["reference_data"] = current_window.copy()

        except Exception as e:
            self.logger.error(f"Drift detection failed for {model_id}: {e}")

    def _calculate_drift_score(self, reference_data: List[Dict], current_data: List[Dict]) -> float:
        """
        Calculate drift score using the Kolmogorov-Smirnov (K-S) test.
        This compares the distributions of two samples.
        The returned drift score is 1 - p-value, where a small p-value indicates
        a significant difference between distributions.
        """
        try:
            # We assume the prediction data is a dictionary of features
            # For this example, we'll check drift on each feature individually
            # and return the maximum drift score found.

            if not reference_data or not current_data:
                return 0.0

            # Get all feature keys from the reference data
            if not isinstance(reference_data[0], dict):
                 # Handle simple list of values case
                ref_values = reference_data
                curr_values = current_data
                stat, p_value = ks_2samp(ref_values, curr_values)
                return 1 - p_value

            all_keys = set(reference_data[0].keys())

            max_drift_score = 0.0

            for key in all_keys:
                ref_values = [d.get(key, 0) for d in reference_data]
                curr_values = [d.get(key, 0) for d in current_data]

                if len(ref_values) < 2 or len(curr_values) < 2:
                    continue

                # Perform the K-S test
                try:
                    stat, p_value = ks_2samp(ref_values, curr_values)
                    drift_score = 1 - p_value
                    if drift_score > max_drift_score:
                        max_drift_score = drift_score
                except Exception as e:
                    self.logger.debug(f"Could not perform K-S test for feature '{key}': {e}")

            return max_drift_score

        except Exception as e:
            self.logger.error(f"Error during K-S drift calculation: {e}")
            return 0.0

    async def _trigger_drift_alert(self, model_id: str, drift_score: float):
        """Trigger drift alert."""
        alert = {
            "alert_id": f"drift_{model_id}_{int(time.time())}",
            "type": "model_drift",
            "model_id": model_id,
            "severity": AlertSeverity.WARNING.value,
            "message": f"Model drift detected for {model_id} (score: {drift_score:.3f})",
            "timestamp": datetime.now(),
            "data": {"drift_score": drift_score}
        }

        await self._process_alert(alert)

    async def _check_for_anomalies(self, entity_id: str, entity_type: str, metrics: Dict[str, Union[float, int]]):
        """
        Check for anomalies in metrics using the 3-sigma rule.

        Args:
            entity_id: ID of the model or infrastructure component.
            entity_type: 'model' or 'infrastructure'.
            metrics: The latest metrics recorded.
        """
        history_key_prefix = f"model_{entity_id}" if entity_type == "model" else f"infra_{entity_id}"

        for metric_name, current_value in metrics.items():
            history_key = f"{history_key_prefix}_{metric_name}"
            metric_history = self.metrics_history.get(history_key, [])

            if len(metric_history) < self.config["anomaly_min_samples"]:
                continue

            values = [m["value"] for m in metric_history]

            try:
                mean = statistics.mean(values)
                std_dev = statistics.stdev(values)
            except statistics.StatisticsError:
                continue # Not enough data to calculate stdev

            if std_dev == 0:
                continue # Avoid division by zero if all values are the same

            sensitivity = self.config["anomaly_detection_sensitivity"]
            upper_bound = mean + sensitivity * std_dev
            lower_bound = mean - sensitivity * std_dev

            if not (lower_bound <= current_value <= upper_bound):
                # Anomaly detected
                alert_name = f"{entity_id}_{metric_name}_anomaly"

                # Check cooldown
                last_alert_time = self.cooldown_timestamps.get(alert_name)
                if last_alert_time:
                    cooldown_minutes = self.config["alert_cooldown_minutes"]
                    if (datetime.now() - last_alert_time).total_seconds() < cooldown_minutes * 60:
                        continue
                self.cooldown_timestamps[alert_name] = datetime.now()

                message = (
                    f"Anomaly detected for {entity_type} {entity_id}: "
                    f"{metric_name} is {current_value:.2f}, which is outside the "
                    f"expected range [{lower_bound:.2f}, {upper_bound:.2f}]"
                )

                alert = {
                    "alert_id": f"{alert_name}_{int(time.time())}",
                    "type": f"{entity_type}_anomaly",
                    "entity_id": entity_id,
                    "metric": metric_name,
                    "severity": AlertSeverity.WARNING.value,
                    "message": message,
                    "timestamp": datetime.now(),
                    "data": {
                        "metric": metric_name,
                        "current_value": current_value,
                        "mean": mean,
                        "std_dev": std_dev,
                        "lower_bound": lower_bound,
                        "upper_bound": upper_bound
                    }
                }
                await self._process_alert(alert)

    async def _process_alert(self, alert: Dict):
        """Process and dispatch alert."""
        alert_id = alert["alert_id"]

        # Store active alert
        self.active_alerts[alert_id] = alert

        # Log alert
        self.logger.warning(f"Alert triggered: {alert['message']}")

        # In real implementation, would send to notification system
        # For now, just log

        # Auto-resolve after some time (simplified)
        asyncio.create_task(self._auto_resolve_alert(alert_id, 3600))  # 1 hour

    async def _run_predictive_maintenance_check(self, component_id: str):
        """
        Runs predictive maintenance checks for an infrastructure component.
        Uses linear regression to predict future resource usage.
        """
        if not self.config["enable_predictive_maintenance"]:
            return

        monitoring = self.infrastructure_metrics.get(component_id)
        if not monitoring:
            return

        metrics_to_predict = ["cpu_usage", "memory_usage", "disk_usage"]

        for metric_name in metrics_to_predict:
            history_key = f"infra_{component_id}_{metric_name}"
            metric_history = self.metrics_history.get(history_key)

            if not metric_history or len(metric_history) < self.config["anomaly_min_samples"]:
                continue

            timestamps = np.array([m["timestamp"].timestamp() for m in metric_history])
            values = np.array([m["value"] for m in metric_history])

            # Normalize timestamps to prevent floating point issues
            first_timestamp = timestamps[0]
            timestamps_norm = timestamps - first_timestamp

            try:
                slope, intercept, r_value, p_value, std_err = linregress(timestamps_norm, values)
            except ValueError:
                continue

            # Check if the trend is significant and positive (increasing)
            if p_value < 0.05 and slope > 0:
                # Predict when it will cross a critical threshold (e.g., 90%)
                critical_threshold = 90.0

                if values[-1] >= critical_threshold: continue # Already critical

                # time = (value - intercept) / slope
                try:
                    time_to_threshold_seconds = (critical_threshold - intercept) / slope
                except ZeroDivisionError:
                    continue

                predicted_breach_timestamp = first_timestamp + time_to_threshold_seconds
                predicted_breach_datetime = datetime.fromtimestamp(predicted_breach_timestamp)

                time_now = datetime.now()

                # Only alert if the predicted breach is within a reasonable timeframe (e.g., 7 days)
                if time_now < predicted_breach_datetime < time_now + timedelta(days=7):
                    alert_name = f"{component_id}_{metric_name}_predictive_alert"

                    # Check cooldown
                    last_alert_time = self.cooldown_timestamps.get(alert_name)
                    if last_alert_time:
                        cooldown_minutes = self.config["alert_cooldown_minutes"] * 60 # 5 hours cooldown for predictive
                        if (datetime.now() - last_alert_time).total_seconds() < cooldown_minutes * 60:
                            continue
                    self.cooldown_timestamps[alert_name] = datetime.now()

                    message = (
                        f"Predictive Alert for {component_id}: {metric_name} is trending upwards "
                        f"and is predicted to cross {critical_threshold}% around {predicted_breach_datetime.isoformat()}."
                    )

                    alert = {
                        "alert_id": f"{alert_name}_{int(time.time())}",
                        "type": "predictive_maintenance",
                        "component_id": component_id,
                        "metric": metric_name,
                        "severity": AlertSeverity.INFO.value,
                        "message": message,
                        "timestamp": time_now,
                        "data": {
                            "metric": metric_name,
                            "critical_threshold": critical_threshold,
                            "predicted_breach_datetime": predicted_breach_datetime.isoformat(),
                            "trend_slope": slope,
                            "r_squared": r_value**2
                        }
                    }
                    await self._process_alert(alert)

    async def _auto_resolve_alert(self, alert_id: str, delay_seconds: int):
        """Auto-resolve alert after delay."""
        await asyncio.sleep(delay_seconds)
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]["resolved_at"] = datetime.now()
            self.active_alerts[alert_id]["status"] = "resolved"

    def _update_model_performance_score(self, model_id: str):
        """Update model performance score."""
        monitoring = self.model_metrics[model_id]
        metrics = monitoring["metrics"]

        # Calculate performance score based on recent metrics
        scores = []

        # Accuracy score (higher is better)
        if metrics["accuracy"]:
            recent_accuracy = [m["value"] for m in metrics["accuracy"][-10:]]
            avg_accuracy = sum(recent_accuracy) / len(recent_accuracy)
            scores.append(avg_accuracy)

        # Latency score (lower is better, invert)
        if metrics["latency"]:
            recent_latency = [m["value"] for m in metrics["latency"][-10:]]
            avg_latency = sum(recent_latency) / len(recent_latency)
            # Normalize latency (assuming <100ms is perfect)
            latency_score = max(0, 1 - (avg_latency / 100))
            scores.append(latency_score)

        # Memory usage score (lower is better, invert)
        if metrics["memory_usage"]:
            recent_memory = [m["value"] for m in metrics["memory_usage"][-10:]]
            avg_memory = sum(recent_memory) / len(recent_memory)
            memory_score = max(0, 1 - (avg_memory / 100))
            scores.append(memory_score)

        if scores:
            monitoring["performance_score"] = sum(scores) / len(scores)
        else:
            monitoring["performance_score"] = 0.5

    def _update_infrastructure_health_score(self, component_id: str):
        """Update infrastructure health score."""
        monitoring = self.infrastructure_metrics[component_id]
        metrics = monitoring["metrics"]

        # Calculate health score based on recent metrics
        scores = []

        # CPU usage score (lower is better)
        if metrics["cpu_usage"]:
            recent_cpu = [m["value"] for m in metrics["cpu_usage"][-10:]]
            avg_cpu = sum(recent_cpu) / len(recent_cpu)
            cpu_score = max(0, 1 - (avg_cpu / 100))
            scores.append(cpu_score)

        # Memory usage score
        if metrics["memory_usage"]:
            recent_memory = [m["value"] for m in metrics["memory_usage"][-10:]]
            avg_memory = sum(recent_memory) / len(recent_memory)
            memory_score = max(0, 1 - (avg_memory / 100))
            scores.append(memory_score)

        # Error rate score (lower is better)
        if metrics["error_rate"]:
            recent_errors = [m["value"] for m in metrics["error_rate"][-10:]]
            avg_errors = sum(recent_errors) / len(recent_errors)
            error_score = max(0, 1 - avg_errors)
            scores.append(error_score)

        if scores:
            monitoring["health_score"] = sum(scores) / len(scores)
        else:
            monitoring["health_score"] = 1.0

    def add_optimization_rule(self, rule_name: str, conditions: Dict, actions: List[Dict]):
        """Add optimization rule."""
        rule = {
            "rule_name": rule_name,
            "conditions": conditions,
            "actions": actions,
            "created_at": datetime.now(),
            "enabled": True,
            "trigger_count": 0
        }

        # Determine target type
        if "model_id" in conditions:
            target = conditions["model_id"]
            self.optimization_rules[f"model_{target}"].append(rule)
        elif "component_id" in conditions:
            target = conditions["component_id"]
            self.optimization_rules[f"infra_{target}"].append(rule)

    async def run_optimization_check(self):
        """Run optimization checks and apply actions."""
        if not self.config["auto_optimization_enabled"]:
            return

        # Check model optimizations
        for model_id, monitoring in self.model_metrics.items():
            rules = self.optimization_rules.get(f"model_{model_id}", [])
            for rule in rules:
                if await self._check_optimization_conditions(rule, monitoring):
                    await self._apply_optimization_actions(rule, {"type": "model", "id": model_id})

        # Check infrastructure optimizations
        for component_id, monitoring in self.infrastructure_metrics.items():
            rules = self.optimization_rules.get(f"infra_{component_id}", [])
            for rule in rules:
                if await self._check_optimization_conditions(rule, monitoring):
                    await self._apply_optimization_actions(rule, {"type": "infrastructure", "id": component_id})

    async def _check_optimization_conditions(self, rule: Dict, monitoring: Dict) -> bool:
        """Check if optimization conditions are met."""
        conditions = rule["conditions"]

        for condition_key, condition_value in conditions.items():
            if condition_key == "performance_score_below":
                current_score = monitoring.get("performance_score", 1.0)
                if current_score >= condition_value:
                    return False
            elif condition_key == "health_score_below":
                current_score = monitoring.get("health_score", 1.0)
                if current_score >= condition_value:
                    return False
            elif condition_key == "drift_detected":
                if condition_value and not monitoring.get("drift_detected", False):
                    return False

        return True

    async def _apply_optimization_actions(self, rule: Dict, target: Dict):
        """Apply optimization actions."""
        actions = rule["actions"]

        for action in actions:
            action_type = action["type"]

            if action_type == "scale_up":
                await self._execute_scale_action(target, "up", action)
            elif action_type == "scale_down":
                await self._execute_scale_action(target, "down", action)
            elif action_type == "retrain_model":
                await self._execute_model_retrain(target, action)
            elif action_type == "restart_service":
                await self._execute_service_restart(target, action)

            rule["trigger_count"] += 1

    async def _execute_scale_action(self, target: Dict, direction: str, action: Dict):
        """Execute scaling action."""
        # In real implementation, would integrate with orchestration system
        self.logger.info(f"Executing {direction} scale for {target['type']} {target['id']}")

    async def _execute_model_retrain(self, target: Dict, action: Dict):
        """Execute model retraining."""
        self.logger.info(f"Triggering model retrain for {target['id']}")

    async def _execute_service_restart(self, target: Dict, action: Dict):
        """Execute service restart."""
        self.logger.info(f"Restarting service {target['id']}")

    def get_model_status(self, model_id: str) -> Optional[Dict]:
        """Get model monitoring status."""
        monitoring = self.model_metrics.get(model_id)
        if not monitoring:
            return None

        return {
            "model_id": model_id,
            "status": monitoring["status"],
            "performance_score": monitoring["performance_score"],
            "drift_score": monitoring.get("drift_score", 0.0),
            "drift_detected": monitoring.get("drift_detected", False),
            "last_updated": monitoring["last_updated"],
            "metrics": {
                metric: len(values) if isinstance(values, list) else values
                for metric, values in monitoring["metrics"].items()
            }
        }

    def get_infrastructure_status(self, component_id: str) -> Optional[Dict]:
        """Get infrastructure monitoring status."""
        monitoring = self.infrastructure_metrics.get(component_id)
        if not monitoring:
            return None

        return {
            "component_id": component_id,
            "component_type": monitoring["component_type"],
            "status": monitoring["status"],
            "health_score": monitoring["health_score"],
            "last_updated": monitoring["last_updated"],
            "metrics": {
                metric: len(values) if isinstance(values, list) else values
                for metric, values in monitoring["metrics"].items()
            }
        }

    def get_active_alerts(self) -> List[Dict]:
        """Get active alerts."""
        return [
            alert for alert in self.active_alerts.values()
            if alert.get("status") != "resolved"
        ]

    def get_monitoring_metrics(self) -> Dict:
        """Get overall monitoring metrics."""
        total_models = len(self.model_metrics)
        total_components = len(self.infrastructure_metrics)
        active_alerts = len(self.get_active_alerts())

        models_with_drift = sum(
            1 for m in self.model_metrics.values()
            if m.get("drift_detected", False)
        )

        avg_model_performance = (
            sum(m["performance_score"] for m in self.model_metrics.values()) / total_models
            if total_models > 0 else 0
        )

        avg_infra_health = (
            sum(m["health_score"] for m in self.infrastructure_metrics.values()) / total_components
            if total_components > 0 else 0
        )

        return {
            "total_models": total_models,
            "total_components": total_components,
            "active_alerts": active_alerts,
            "models_with_drift": models_with_drift,
            "avg_model_performance": avg_model_performance,
            "avg_infrastructure_health": avg_infra_health,
            "monitoring_uptime": str(datetime.now() - self.config.get("start_time", datetime.now()))
        }

    async def continuous_monitoring(self):
        """Continuous monitoring and optimization."""
        while True:
            try:
                # Run optimization checks
                await self.run_optimization_check()

                # Run predictive maintenance checks for infrastructure
                for component_id in self.infrastructure_metrics.keys():
                    await self._run_predictive_maintenance_check(component_id)

                # Clean up old metrics
                cutoff_time = datetime.now() - timedelta(hours=self.config["metrics_retention_hours"])

                for metric_key, history in self.metrics_history.items():
                    # Remove old entries
                    while history and history[0]["timestamp"] < cutoff_time:
                        history.popleft()

                # Clean up resolved alerts (older than 24 hours)
                alert_cutoff = datetime.now() - timedelta(hours=24)
                resolved_alerts = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if alert.get("resolved_at") and alert["resolved_at"] < alert_cutoff
                ]

                for alert_id in resolved_alerts:
                    del self.active_alerts[alert_id]

                await asyncio.sleep(self.config["monitoring_interval"])

            except Exception as e:
                self.logger.error(f"Continuous monitoring error: {e}")
                await asyncio.sleep(60)


# Global AI infrastructure monitoring instance
ai_infrastructure_monitoring = AIInfrastructureMonitoring()


def register_ai_model_monitoring(model_id: str, model_config: Dict, monitoring_config: Optional[Dict] = None) -> bool:
    """Register AI model for monitoring."""
    return ai_infrastructure_monitoring.register_model_monitoring(model_id, model_config, monitoring_config)


def register_infrastructure_component_monitoring(
    component_id: str,
    component_type: str,
    monitoring_config: Optional[Dict] = None
) -> bool:
    """Register infrastructure component for monitoring."""
    return ai_infrastructure_monitoring.register_infrastructure_monitoring(component_id, component_type, monitoring_config)


async def record_ai_model_metrics(model_id: str, metrics: Dict[str, Union[float, int]], prediction_data: Optional[Dict] = None):
    """Record AI model metrics."""
    await ai_infrastructure_monitoring.record_model_metrics(model_id, metrics, prediction_data)


async def record_infrastructure_metrics(component_id: str, metrics: Dict[str, Union[float, int]]):
    """Record infrastructure metrics."""
    await ai_infrastructure_monitoring.record_infrastructure_metrics(component_id, metrics)


def get_ai_model_monitoring_status(model_id: str) -> Optional[Dict]:
    """Get AI model monitoring status."""
    return ai_infrastructure_monitoring.get_model_status(model_id)


def get_infrastructure_monitoring_status(component_id: str) -> Optional[Dict]:
    """Get infrastructure monitoring status."""
    return ai_infrastructure_monitoring.get_infrastructure_status(component_id)


def get_ai_monitoring_alerts() -> List[Dict]:
    """Get active AI monitoring alerts."""
    return ai_infrastructure_monitoring.get_active_alerts()


def get_ai_monitoring_metrics() -> Dict:
    """Get AI monitoring metrics."""
    return ai_infrastructure_monitoring.get_monitoring_metrics()


async def setup_simulation(monitoring: AIInfrastructureMonitoring):
    """Set up a demo simulation environment."""
    logger.info("Setting up simulation environment...")

    # Register Models
    monitoring.register_model_monitoring(
        model_id="customer_churn_predictor_v1",
        model_config={"type": "RandomForest", "version": "1.2"},
        monitoring_config={
            "drift_detection": {"threshold": 0.8, "window_size": 50}
        }
    )
    monitoring.register_model_monitoring(
        model_id="fraud_detection_network_v3",
        model_config={"type": "NeuralNetwork", "version": "3.1"},
        monitoring_config={
            "drift_detection": {"threshold": 0.9, "window_size": 100}
        }
    )

    # Register Infrastructure
    monitoring.register_infrastructure_monitoring("inference_server_cluster_1", "k8s_cluster")
    monitoring.register_infrastructure_monitoring("data_processing_pipeline_1", "kafka_stream")
    monitoring.register_infrastructure_monitoring("model_database_1", "postgres_db")

    # Add Optimization Rules
    monitoring.add_optimization_rule(
        "scale_up_on_high_latency",
        conditions={"model_id": "customer_churn_predictor_v1", "performance_score_below": 0.6},
        actions=[{"type": "scale_up", "details": {"by": 2}}]
    )
    monitoring.add_optimization_rule(
        "retrain_on_drift",
        conditions={"model_id": "fraud_detection_network_v3", "drift_detected": True},
        actions=[{"type": "retrain_model"}]
    )
    monitoring.add_optimization_rule(
        "restart_unhealthy_service",
        conditions={"component_id": "inference_server_cluster_1", "health_score_below": 0.5},
        actions=[{"type": "restart_service"}]
    )

    # Initialize reference data for drift detection
    churn_model_drift_detector = monitoring.drift_detectors.get("customer_churn_predictor_v1")
    if churn_model_drift_detector:
        churn_model_drift_detector["reference_data"] = [
            {"feature1": np.random.rand(), "feature2": np.random.randint(0, 100)} for _ in range(100)
        ]

    logger.info("Simulation environment setup complete.")


async def generate_metrics(monitoring: AIInfrastructureMonitoring, iteration: int):
    """Generate and record simulated metrics."""

    # Simulate metrics for customer_churn_predictor_v1
    churn_accuracy = 0.95 - (iteration % 20) * 0.01 # Gradual drop
    if iteration > 40 and iteration < 45: # Anomaly
        churn_accuracy *= 0.5
    await monitoring.record_model_metrics(
        "customer_churn_predictor_v1",
        {
            "accuracy": churn_accuracy,
            "latency": 50 + np.random.randint(-10, 10) + (iteration % 10) * 5,
            "cpu_usage": 30 + np.random.rand() * 5
        },
        prediction_data={"feature1": np.random.rand(), "feature2": np.random.randint(0, 100)}
    )

    # Simulate metrics for fraud_detection_network_v3, including data drift
    fraud_latency = 120 + np.random.randint(-20, 20)
    prediction_features = {"card_type": np.random.rand() * 10, "amount": np.random.rand() * 1000}
    if iteration > 60: # Introduce drift
        prediction_features["amount"] *= 1.5
    await monitoring.record_model_metrics(
        "fraud_detection_network_v3",
        {"accuracy": 0.98, "latency": fraud_latency, "memory_usage": 60 + np.random.rand() * 10},
        prediction_data=prediction_features
    )

    # Simulate infrastructure metrics
    # Normal usage with a gradual increase for predictive maintenance test
    cpu_usage = 40 + np.random.rand() * 5 + (iteration * 0.1)
    # Anomaly spike
    if 30 < iteration < 35:
        cpu_usage = 95.0
    await monitoring.record_infrastructure_metrics(
        "inference_server_cluster_1",
        {"cpu_usage": cpu_usage, "memory_usage": 55 + np.random.rand() * 3, "error_rate": np.random.rand() * 0.01}
    )

    # Simulate disk usage increase for predictive maintenance
    disk_usage = 70 + (iteration * 0.05)
    await monitoring.record_infrastructure_metrics(
        "model_database_1",
        {"disk_usage": disk_usage, "response_time": 10 + np.random.rand()}
    )


async def display_dashboard(monitoring: AIInfrastructureMonitoring):
    """Display a simple text-based dashboard."""
    print("\033[2J\033[H")  # Clear screen
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"--- AI Infrastructure Monitoring Dashboard --- ({now})")

    # Overall Status
    overall_metrics = monitoring.get_monitoring_metrics()
    print("\n--- Overall Status ---")
    print(
        f"Models Monitored: {overall_metrics['total_models']} | "
        f"Infra Components: {overall_metrics['total_components']} | "
        f"Active Alerts: {overall_metrics['active_alerts']}"
    )
    print(
        f"Avg Model Perf: {overall_metrics['avg_model_performance']:.2f} | "
        f"Avg Infra Health: {overall_metrics['avg_infrastructure_health']:.2f} | "
        f"Models w/ Drift: {overall_metrics['models_with_drift']}"
    )

    # Model Status
    print("\n--- Model Status ---")
    for model_id in monitoring.model_metrics.keys():
        status = monitoring.get_model_status(model_id)
        if status:
            drift_str = "DETECTED" if status.get('drift_detected') else f"{status.get('drift_score', 0):.2f}"
            print(f"  - {model_id:<30} | Perf Score: {status['performance_score']:.2f} | Drift Score: {drift_str}")

    # Infrastructure Status
    print("\n--- Infrastructure Status ---")
    for comp_id in monitoring.infrastructure_metrics.keys():
        status = monitoring.get_infrastructure_status(comp_id)
        if status:
            print(f"  - {comp_id:<30} | Health Score: {status['health_score']:.2f}")

    # Active Alerts
    alerts = monitoring.get_active_alerts()
    if alerts:
        print("\n--- Active Alerts ---")
        for alert in alerts:
            entity = alert.get('model_id') or alert.get('component_id') or alert.get('entity_id', 'N/A')
            print(f"  - [{alert['timestamp'].strftime('%H:%M:%S')}] [{alert['severity'].upper()}] [{alert['type']}] {entity}: {alert['message']}")

    print("\n" + "-"*50)


async def main():
    """Main function to run the simulation."""
    monitoring = AIInfrastructureMonitoring()

    # Start the background monitoring task
    monitoring_task = asyncio.create_task(monitoring.continuous_monitoring())

    # Set up the simulation entities
    await setup_simulation(monitoring)

    # Run the simulation loop
    for i in range(80): # Run for 80 iterations
        await generate_metrics(monitoring, i)
        await display_dashboard(monitoring)
        await asyncio.sleep(2)

    monitoring_task.cancel()
    try:
        await monitoring_task
    except asyncio.CancelledError:
        logger.info("Monitoring task successfully cancelled.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")