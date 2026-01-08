"""
Intelligent Auto-scaling Module

This module implements AI-powered auto-scaling for the IoT IIoT platform,
predicting load patterns and automatically adjusting resource allocation.
"""

import asyncio
import math
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from utils.logging_config import get_logger

logger = get_logger(__name__)


class ScalingAction(Enum):
    """Scaling actions."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_ACTION = "no_action"


class ScalingStrategy(Enum):
    """Scaling strategies."""
    REACTIVE = "reactive"
    PREDICTIVE = "predictive"
    HYBRID = "hybrid"


class ResourceType(Enum):
    """Types of resources to scale."""
    CPU_INSTANCES = "cpu_instances"
    MEMORY_INSTANCES = "memory_instances"
    STORAGE_VOLUMES = "storage_volumes"
    NETWORK_BANDWIDTH = "network_bandwidth"


class IntelligentAutoScaling:
    """
    AI-powered auto-scaling system.

    Features:
    - Predictive scaling using ML models
    - Reactive scaling based on thresholds
    - Multi-resource scaling (CPU, memory, storage)
    - Cost optimization
    - Anomaly detection
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()

        # Scaling policies
        self.scaling_policies: Dict[str, Dict] = {}

        # Metrics history
        self.metrics_history: Dict[str, deque] = {}
        self.prediction_models: Dict[str, RandomForestRegressor] = {}
        self.scalers: Dict[str, StandardScaler] = {}

        # Current scaling state
        self.current_capacity: Dict[str, float] = {}
        self.scaling_cooldowns: Dict[str, datetime] = {}

        # Scaling history
        self.scaling_history: List[Dict] = []

        # Anomaly detection
        self.anomaly_thresholds: Dict[str, float] = {}

        self.logger = get_logger(__name__)
        self.logger.info("Intelligent Auto-scaling initialized")

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "scaling_strategy": ScalingStrategy.HYBRID.value,
            "metrics_window_size": 100,
            "prediction_horizon": 30,  # minutes
            "scaling_cooldown": 300,  # seconds
            "cpu_scale_up_threshold": 0.8,
            "cpu_scale_down_threshold": 0.3,
            "memory_scale_up_threshold": 0.85,
            "memory_scale_down_threshold": 0.4,
            "min_instances": 1,
            "max_instances": 50,
            "scale_up_factor": 1.5,
            "scale_down_factor": 0.7,
            "cost_optimization_weight": 0.3,
            "anomaly_detection_enabled": True,
            "prediction_confidence_threshold": 0.7,
        }

    def register_scaling_policy(
        self,
        service_name: str,
        resource_type: ResourceType,
        config: Optional[Dict] = None
    ):
        """
        Register scaling policy for a service/resource.

        Args:
            service_name: Name of the service
            resource_type: Type of resource to scale
            config: Policy configuration
        """
        policy_key = f"{service_name}_{resource_type.value}"

        policy = config or self._get_default_policy_config(resource_type)

        self.scaling_policies[policy_key] = {
            "service_name": service_name,
            "resource_type": resource_type.value,
            "config": policy,
            "created_at": datetime.now(),
            "enabled": True
        }

        # Initialize metrics history
        self.metrics_history[policy_key] = deque(maxlen=self.config["metrics_window_size"])

        # Initialize current capacity
        self.current_capacity[policy_key] = policy.get("initial_capacity", self.config["min_instances"])

        # Initialize prediction model
        self._initialize_prediction_model(policy_key)

        self.logger.info(f"Registered scaling policy: {policy_key}")

    def _get_default_policy_config(self, resource_type: ResourceType) -> Dict:
        """Get default policy configuration for resource type."""
        base_config = {
            "strategy": self.config["scaling_strategy"],
            "min_capacity": self.config["min_instances"],
            "max_capacity": self.config["max_instances"],
            "initial_capacity": self.config["min_instances"],
            "scale_up_factor": self.config["scale_up_factor"],
            "scale_down_factor": self.config["scale_down_factor"],
            "cooldown_period": self.config["scaling_cooldown"],
        }

        # Resource-specific thresholds
        if resource_type == ResourceType.CPU_INSTANCES:
            base_config.update({
                "scale_up_threshold": self.config["cpu_scale_up_threshold"],
                "scale_down_threshold": self.config["cpu_scale_down_threshold"],
                "metric_name": "cpu_utilization"
            })
        elif resource_type == ResourceType.MEMORY_INSTANCES:
            base_config.update({
                "scale_up_threshold": self.config["memory_scale_up_threshold"],
                "scale_down_threshold": self.config["memory_scale_down_threshold"],
                "metric_name": "memory_utilization"
            })

        return base_config

    def _initialize_prediction_model(self, policy_key: str):
        """Initialize ML model for predictive scaling."""
        self.prediction_models[policy_key] = RandomForestRegressor(
            n_estimators=50,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.scalers[policy_key] = StandardScaler()

    async def record_metric(
        self,
        service_name: str,
        resource_type: ResourceType,
        metric_value: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Record metric value for scaling analysis.

        Args:
            service_name: Service name
            resource_type: Resource type
            metric_value: Metric value (0-1 for utilization)
            timestamp: Metric timestamp
        """
        policy_key = f"{service_name}_{resource_type.value}"

        if policy_key not in self.metrics_history:
            return

        metric_entry = {
            "value": metric_value,
            "timestamp": timestamp or datetime.now(),
            "service": service_name,
            "resource_type": resource_type.value
        }

        self.metrics_history[policy_key].append(metric_entry)

        # Check for immediate scaling action
        await self._evaluate_scaling_action(policy_key)

    async def _evaluate_scaling_action(self, policy_key: str):
        """Evaluate if scaling action is needed."""
        if policy_key not in self.scaling_policies:
            return

        policy = self.scaling_policies[policy_key]
        if not policy["enabled"]:
            return

        # Check cooldown
        if policy_key in self.scaling_cooldowns:
            if datetime.now() < self.scaling_cooldowns[policy_key]:
                return

        # Get current metrics
        metrics = list(self.metrics_history[policy_key])
        if not metrics:
            return

        current_metric = metrics[-1]["value"]
        config = policy["config"]

        # Determine scaling action
        action = await self._determine_scaling_action(
            policy_key, current_metric, metrics, config
        )

        if action != ScalingAction.NO_ACTION:
            await self._execute_scaling_action(policy_key, action, config)

    async def _determine_scaling_action(
        self,
        policy_key: str,
        current_metric: float,
        metrics: List[Dict],
        config: Dict
    ) -> ScalingAction:
        """Determine scaling action based on strategy."""
        strategy = ScalingStrategy(config.get("strategy", "reactive"))

        if strategy == ScalingStrategy.REACTIVE:
            return self._reactive_scaling_decision(current_metric, config)

        elif strategy == ScalingStrategy.PREDICTIVE:
            return await self._predictive_scaling_decision(policy_key, metrics, config)

        elif strategy == ScalingStrategy.HYBRID:
            reactive_action = self._reactive_scaling_decision(current_metric, config)
            predictive_action = await self._predictive_scaling_decision(policy_key, metrics, config)

            # Combine decisions
            return self._combine_scaling_decisions(reactive_action, predictive_action)

        return ScalingAction.NO_ACTION

    def _reactive_scaling_decision(self, current_metric: float, config: Dict) -> ScalingAction:
        """Make reactive scaling decision based on current metrics."""
        scale_up_threshold = config.get("scale_up_threshold", 0.8)
        scale_down_threshold = config.get("scale_down_threshold", 0.3)

        if current_metric >= scale_up_threshold:
            return ScalingAction.SCALE_UP
        elif current_metric <= scale_down_threshold:
            return ScalingAction.SCALE_DOWN

        return ScalingAction.NO_ACTION

    async def _predictive_scaling_decision(
        self,
        policy_key: str,
        metrics: List[Dict],
        config: Dict
    ) -> ScalingAction:
        """Make predictive scaling decision using ML."""
        if len(metrics) < 10:  # Need minimum data for prediction
            return ScalingAction.NO_ACTION

        try:
            # Prepare data for prediction
            values = [m["value"] for m in metrics[-50:]]  # Last 50 points
            timestamps = [m["timestamp"] for m in metrics[-50:]]

            # Create features
            features = self._extract_prediction_features(values, timestamps)

            # Train/update model if needed
            await self._update_prediction_model(policy_key, features, values)

            # Make prediction
            prediction = self._predict_future_load(policy_key, features)

            # Determine action based on prediction
            return self._prediction_to_action(prediction, config)

        except Exception as e:
            self.logger.error(f"Predictive scaling failed: {e}")
            return ScalingAction.NO_ACTION

    def _extract_prediction_features(self, values: List[float], timestamps: List[datetime]) -> np.ndarray:
        """Extract features for prediction model."""
        if len(values) < 5:
            return np.array([])

        # Basic statistical features
        features = [
            np.mean(values),
            np.std(values),
            np.min(values),
            np.max(values),
            values[-1],  # Current value
            values[-1] - values[-2] if len(values) > 1 else 0,  # Trend
        ]

        # Time-based features
        if len(timestamps) > 1:
            time_diffs = [(timestamps[i] - timestamps[i-1]).total_seconds()
                         for i in range(1, len(timestamps))]
            features.extend([
                np.mean(time_diffs),
                np.std(time_diffs)
            ])

        return np.array(features).reshape(1, -1)

    async def _update_prediction_model(self, policy_key: str, features: np.ndarray, values: List[float]):
        """Update prediction model with new data."""
        if len(values) < 10:
            return

        model = self.prediction_models[policy_key]
        scaler = self.scalers[policy_key]

        # Prepare training data
        X = []
        y = []

        for i in range(len(features) - 1):
            X.append(features[i].flatten())
            y.append(values[i + 1])  # Predict next value

        if len(X) < 5:
            return

        X = np.array(X)
        y = np.array(y)

        # Scale features
        X_scaled = scaler.fit_transform(X)

        # Train model
        model.fit(X_scaled, y)

    def _predict_future_load(self, policy_key: str, features: np.ndarray) -> float:
        """Predict future load."""
        model = self.prediction_models[policy_key]
        scaler = self.scalers[policy_key]

        features_scaled = scaler.transform(features)
        prediction = model.predict(features_scaled)[0]

        return max(0.0, min(1.0, prediction))  # Clamp to [0,1]

    def _prediction_to_action(self, prediction: float, config: Dict) -> ScalingAction:
        """Convert prediction to scaling action."""
        confidence = abs(prediction - 0.5) * 2  # Convert to 0-1 confidence

        if confidence < self.config["prediction_confidence_threshold"]:
            return ScalingAction.NO_ACTION

        scale_up_threshold = config.get("scale_up_threshold", 0.8)
        scale_down_threshold = config.get("scale_down_threshold", 0.3)

        if prediction >= scale_up_threshold:
            return ScalingAction.SCALE_UP
        elif prediction <= scale_down_threshold:
            return ScalingAction.SCALE_DOWN

        return ScalingAction.NO_ACTION

    def _combine_scaling_decisions(self, reactive: ScalingAction, predictive: ScalingAction) -> ScalingAction:
        """Combine reactive and predictive scaling decisions."""
        # If both agree, take that action
        if reactive == predictive:
            return reactive

        # If reactive says scale up, prioritize it
        if reactive == ScalingAction.SCALE_UP:
            return ScalingAction.SCALE_UP

        # If predictive says scale up with high confidence, consider it
        if predictive == ScalingAction.SCALE_UP:
            return ScalingAction.SCALE_UP

        # Default to no action if conflicting
        return ScalingAction.NO_ACTION

    async def _execute_scaling_action(self, policy_key: str, action: ScalingAction, config: Dict):
        """Execute scaling action."""
        current_capacity = self.current_capacity[policy_key]

        if action == ScalingAction.SCALE_UP:
            new_capacity = min(
                config["max_capacity"],
                math.ceil(current_capacity * config["scale_up_factor"])
            )
        elif action == ScalingAction.SCALE_DOWN:
            new_capacity = max(
                config["min_capacity"],
                math.floor(current_capacity * config["scale_down_factor"])
            )
        else:
            return

        if new_capacity != current_capacity:
            # Execute scaling
            success = await self._perform_scaling(policy_key, current_capacity, new_capacity)

            if success:
                self.current_capacity[policy_key] = new_capacity

                # Record scaling event
                scaling_event = {
                    "policy_key": policy_key,
                    "action": action.value,
                    "old_capacity": current_capacity,
                    "new_capacity": new_capacity,
                    "timestamp": datetime.now(),
                    "trigger": "automatic"
                }
                self.scaling_history.append(scaling_event)

                # Set cooldown
                self.scaling_cooldowns[policy_key] = datetime.now() + timedelta(
                    seconds=config["cooldown_period"]
                )

                self.logger.info(f"Scaled {policy_key}: {current_capacity} -> {new_capacity}")

    async def _perform_scaling(self, policy_key: str, old_capacity: float, new_capacity: float) -> bool:
        """Perform actual scaling operation."""
        # Placeholder - in real implementation would interface with
        # cloud provider APIs (AWS ECS, Kubernetes HPA, etc.)

        try:
            # Simulate scaling operation
            await asyncio.sleep(0.1)  # Simulate API call delay

            # Simulate success/failure
            import random
            success = random.random() > 0.05  # 95% success rate

            if success:
                self.logger.info(f"Successfully scaled {policy_key} from {old_capacity} to {new_capacity}")
            else:
                self.logger.error(f"Failed to scale {policy_key}")

            return success

        except Exception as e:
            self.logger.error(f"Scaling operation failed: {e}")
            return False

    async def manual_scaling(
        self,
        service_name: str,
        resource_type: ResourceType,
        target_capacity: float
    ) -> bool:
        """
        Manually trigger scaling.

        Args:
            service_name: Service name
            resource_type: Resource type
            target_capacity: Target capacity

        Returns:
            Scaling success
        """
        policy_key = f"{service_name}_{resource_type.value}"

        if policy_key not in self.scaling_policies:
            return False

        config = self.scaling_policies[policy_key]["config"]
        min_cap = config["min_capacity"]
        max_cap = config["max_capacity"]

        if not (min_cap <= target_capacity <= max_cap):
            return False

        current_capacity = self.current_capacity[policy_key]
        success = await self._perform_scaling(policy_key, current_capacity, target_capacity)

        if success:
            self.current_capacity[policy_key] = target_capacity

            scaling_event = {
                "policy_key": policy_key,
                "action": "manual_scale",
                "old_capacity": current_capacity,
                "new_capacity": target_capacity,
                "timestamp": datetime.now(),
                "trigger": "manual"
            }
            self.scaling_history.append(scaling_event)

        return success

    def get_scaling_status(self) -> Dict[str, Dict]:
        """Get current scaling status."""
        status = {}

        for policy_key, policy in self.scaling_policies.items():
            status[policy_key] = {
                "service_name": policy["service_name"],
                "resource_type": policy["resource_type"],
                "current_capacity": self.current_capacity.get(policy_key, 0),
                "min_capacity": policy["config"]["min_capacity"],
                "max_capacity": policy["config"]["max_capacity"],
                "enabled": policy["enabled"],
                "cooldown_until": self.scaling_cooldowns.get(policy_key),
                "last_scaling": self._get_last_scaling_event(policy_key)
            }

        return status

    def _get_last_scaling_event(self, policy_key: str) -> Optional[Dict]:
        """Get last scaling event for policy."""
        policy_events = [event for event in self.scaling_history
                        if event["policy_key"] == policy_key]

        if policy_events:
            return max(policy_events, key=lambda x: x["timestamp"])

        return None

    def get_scaling_history(self, policy_key: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get scaling history."""
        history = self.scaling_history

        if policy_key:
            history = [event for event in history if event["policy_key"] == policy_key]

        # Sort by timestamp descending
        history.sort(key=lambda x: x["timestamp"], reverse=True)

        return history[:limit]

    def get_metrics_history(self, policy_key: str, limit: int = 100) -> List[Dict]:
        """Get metrics history for policy."""
        if policy_key not in self.metrics_history:
            return []

        history = list(self.metrics_history[policy_key])
        return history[-limit:]

    async def optimize_costs(self):
        """Optimize scaling for cost efficiency."""
        # Analyze scaling patterns and adjust policies for cost optimization
        for policy_key, policy in self.scaling_policies.items():
            await self._optimize_policy_costs(policy_key, policy)

    async def _optimize_policy_costs(self, policy_key: str, policy: Dict):
        """Optimize individual policy for costs."""
        # Analyze recent scaling history
        recent_events = [
            event for event in self.scaling_history
            if event["policy_key"] == policy_key and
            event["timestamp"] > datetime.now() - timedelta(days=7)
        ]

        if not recent_events:
            return

        # Calculate utilization patterns
        scale_up_events = [e for e in recent_events if e["action"] == ScalingAction.SCALE_UP.value]
        scale_down_events = [e for e in recent_events if e["action"] == ScalingAction.SCALE_DOWN.value]

        # If frequent scaling, adjust thresholds
        if len(scale_up_events) > len(scale_down_events) * 2:
            # Too many scale-ups, increase scale-up threshold
            config = policy["config"]
            config["scale_up_threshold"] = min(0.95, config["scale_up_threshold"] + 0.05)
            self.logger.info(f"Optimized scale-up threshold for {policy_key}")

    async def detect_anomalies(self) -> List[Dict]:
        """Detect scaling anomalies."""
        anomalies = []

        for policy_key, metrics in self.metrics_history.items():
            if len(metrics) < 10:
                continue

            values = [m["value"] for m in metrics]

            # Simple anomaly detection using statistical methods
            mean = np.mean(values)
            std = np.std(values)

            threshold = self.anomaly_thresholds.get(policy_key, 3.0)  # 3-sigma

            for i, value in enumerate(values):
                if abs(value - mean) > threshold * std:
                    anomaly = {
                        "policy_key": policy_key,
                        "timestamp": metrics[i]["timestamp"],
                        "value": value,
                        "expected_mean": mean,
                        "deviation": abs(value - mean),
                        "severity": "high" if abs(value - mean) > threshold * std * 2 else "medium"
                    }
                    anomalies.append(anomaly)

        return anomalies

    async def continuous_scaling_monitor(self):
        """Continuous scaling monitoring loop."""
        while True:
            try:
                # Check all policies for scaling actions
                for policy_key in self.scaling_policies.keys():
                    await self._evaluate_scaling_action(policy_key)

                # Cost optimization
                await self.optimize_costs()

                # Anomaly detection
                if self.config["anomaly_detection_enabled"]:
                    anomalies = await self.detect_anomalies()
                    for anomaly in anomalies:
                        self.logger.warning(f"Scaling anomaly detected: {anomaly}")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Scaling monitor error: {e}")
                await asyncio.sleep(30)


# Global auto-scaling instance
intelligent_auto_scaling = IntelligentAutoScaling()


def register_auto_scaling_policy(
    service_name: str,
    resource_type: str,
    config: Optional[Dict] = None
):
    """Register auto-scaling policy."""
    intelligent_auto_scaling.register_scaling_policy(
        service_name, ResourceType(resource_type), config
    )


async def record_resource_metric(
    service_name: str,
    resource_type: str,
    metric_value: float
):
    """Record resource metric."""
    await intelligent_auto_scaling.record_metric(
        service_name, ResourceType(resource_type), metric_value
    )


async def manual_scale(
    service_name: str,
    resource_type: str,
    target_capacity: float
) -> bool:
    """Manually scale resource."""
    return await intelligent_auto_scaling.manual_scaling(
        service_name, ResourceType(resource_type), target_capacity
    )


def get_scaling_status() -> Dict[str, Dict]:
    """Get scaling status."""
    return intelligent_auto_scaling.get_scaling_status()


def get_scaling_history(policy_key: Optional[str] = None) -> List[Dict]:
    """Get scaling history."""
    return intelligent_auto_scaling.get_scaling_history(policy_key)