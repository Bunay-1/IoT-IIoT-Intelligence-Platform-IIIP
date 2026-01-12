"""
Adaptive Rate Limiter QoS Manager Module

This module implements intelligent rate limiting and Quality of Service (QoS)
management for API requests. It provides adaptive rate limiting based on
user behavior, system load, and priority levels.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Request:
    """Request data structure."""

    user_id: str
    endpoint: str
    method: str
    timestamp: float
    priority: int = 1  # 1=low, 2=medium, 3=high
    cost: int = 1 # Cost of the request
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    remaining_requests: int
    reset_time: float
    retry_after: Optional[float] = None
    reason: Optional[str] = None


class RateLimitingStrategy(Enum):
    """Defines different rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    TOKEN_BUCKET = "token_bucket"

class QoSProfile(Enum):
    """Defines different Quality of Service profiles."""
    CRITICAL = "critical"
    HIGH = "high"
    DEFAULT = "default"
    LOW = "low"
    BACKGROUND = "background"


class RateLimitError(Exception):
    """Base exception for rate limiting errors."""
    pass


class QoSError(Exception):
    """Base exception for QoS management errors."""
    pass


class TimeSeriesForecaster:
    """A mock time-series forecaster for predicting request load."""
    def __init__(self):
        self._model_trained = False

    def train(self, request_history: deque):
        # Simulate training on timestamps
        if len(request_history) > 50:
            self._model_trained = True
            # In a real model, we'd analyze frequencies, trends, etc.

    def predict(self, user_id: str, future_window_seconds: int) -> float:
        """Predict the number of requests in a future window."""
        if not self._model_trained:
            return 0.0 # Cannot predict without a trained model
        # Simulate a prediction: base rate + some noise
        # A real model would use seasonality, trend, etc.
        base_rate = np.random.uniform(0.5, 1.5)
        predicted_count = base_rate * future_window_seconds
        return predicted_count


class AdaptiveRateLimiterQoSManager:
    """
    Adaptive Rate Limiter and QoS Manager for API requests.

    This class provides intelligent rate limiting that adapts to user behavior
    and system conditions, while managing Quality of Service for different
    types of requests.
    """

    def __init__(
        self, qos_profiles: Dict[QoSProfile, Dict[str, Any]], config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the Adaptive Rate Limiter QoS Manager with QoS profiles.
        """
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        self.logger = get_logger(__name__)

        # QoS-based rate limiting
        self.qos_profiles = qos_profiles
        self.user_qos: Dict[str, QoSProfile] = {}
        self.dynamic_limits: Dict[str, int] = {}

        # State for rate limiting strategies
        self.strategy = self.config.get("strategy", RateLimitingStrategy.FIXED_WINDOW)
        # Fixed window state
        self.current_usage: Dict[str, int] = defaultdict(int)
        self.reset_times: Dict[str, float] = {}
        # Token bucket state
        self.tokens: Dict[str, float] = defaultdict(float)
        self.last_token_refill: Dict[str, float] = {}

        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.config["history_maxlen"]))

        # QoS management (simplified, as logic is now profile-based)
        self.priority_queues: Dict[int, asyncio.Queue] = {
            p: asyncio.Queue() for p in range(1, 4)
        }

        # Adaptive parameters
        self.adaptation_enabled = self.config.get("adaptation_enabled", True)
        self.cooldown_period = self.config.get("cooldown_period", 300)

        # ML Integration
        self.forecaster = TimeSeriesForecaster()
        self.user_forecasters: Dict[str, TimeSeriesForecaster] = {}

        # Monitoring
        self.monitoring_enabled = self.config.get("monitoring_enabled", True)
        self.stats: Dict[str, Any] = self._initialize_stats()

        # Circuit Breaker state
        self.circuit_breakers: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"state": "closed", "failures": 0, "last_failure_time": 0}
        )
        self.failure_threshold = self.config.get("failure_threshold", 10)
        self.breaker_reset_timeout = self.config.get("breaker_reset_timeout", 60)

        self.logger.info("Adaptive Rate Limiter QoS Manager initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "window_seconds": 60,
            "cooldown_period": 300,
            "adaptation_enabled": True,
            "monitoring_enabled": True,
            "queue_size": 1000,
            "history_maxlen": 5000,
        }

    def _initialize_stats(self) -> Dict[str, Any]:
        """Initialize monitoring statistics."""
        return {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "requests_by_profile": defaultdict(int),
            "active_adaptations": 0,
            "rate_limit_hits": defaultdict(int),
        }

    def set_user_qos_profile(self, user_id: str, profile: QoSProfile):
        """Assign a QoS profile to a user."""
        self.user_qos[user_id] = profile
        # Initialize dynamic limit with the profile's base limit
        self.dynamic_limits[user_id] = self.qos_profiles[profile]['limit_per_minute']
        self.logger.info(f"Set QoS profile for user {user_id} to {profile.name}")

    async def enforce_rate_limits(self, request: Request) -> RateLimitResult:
        if self.strategy == RateLimitingStrategy.TOKEN_BUCKET:
            return await self._enforce_token_bucket(request)
        else: # Default to FIXED_WINDOW
            return await self._enforce_fixed_window(request)

    async def _enforce_fixed_window(self, request: Request) -> RateLimitResult:
        """Enforce rate limits using the fixed window algorithm."""
        self.stats["total_requests"] += 1
        user_id = request.user_id
        profile = self.user_qos.get(user_id, QoSProfile.DEFAULT)
        self.stats["requests_by_profile"][profile.name] += 1

        current_limit = self.dynamic_limits.get(user_id)
        if current_limit is None:
            self.set_user_qos_profile(user_id, profile)
            current_limit = self.dynamic_limits[user_id]

        current_time = time.time()
        if current_time > self.reset_times.get(user_id, 0):
            self.current_usage[user_id] = 0
            self.reset_times[user_id] = current_time + self.config["window_seconds"]
            await self._adapt_rate_limit(user_id, profile)
            current_limit = self.dynamic_limits[user_id]

        if (self.current_usage[user_id] + request.cost) > current_limit:
            self.stats["blocked_requests"] += 1
            return RateLimitResult(allowed=False, remaining_requests=0, reset_time=self.reset_times[user_id], reason="Fixed window limit exceeded.")

        self.current_usage[user_id] += request.cost
        self.stats["allowed_requests"] += 1
        self.request_history[user_id].append(request)
        return RateLimitResult(allowed=True, remaining_requests=current_limit - self.current_usage[user_id], reset_time=self.reset_times[user_id])

    async def _enforce_token_bucket(self, request: Request) -> RateLimitResult:
        """Enforce rate limits using the token bucket algorithm."""
        self.stats["total_requests"] += 1
        user_id = request.user_id
        profile = self.user_qos.get(user_id, QoSProfile.DEFAULT)
        self.stats["requests_by_profile"][profile.name] += 1

        profile_rules = self.qos_profiles[profile]
        bucket_capacity = profile_rules.get('burst_multiplier', 1.5) * profile_rules['limit_per_minute']
        refill_rate = profile_rules['limit_per_minute'] / self.config["window_seconds"]

        current_time = time.time()
        last_refill = self.last_token_refill.get(user_id, current_time)
        time_delta = current_time - last_refill

        new_tokens = time_delta * refill_rate
        current_tokens = self.tokens.get(user_id, bucket_capacity)
        self.tokens[user_id] = min(bucket_capacity, current_tokens + new_tokens)
        self.last_token_refill[user_id] = current_time

        if self.tokens[user_id] < request.cost:
            self.stats["blocked_requests"] += 1
            return RateLimitResult(allowed=False, remaining_requests=int(self.tokens[user_id]), reset_time=time.time() + (request.cost - self.tokens[user_id]) / refill_rate, reason="Not enough tokens.")

        self.tokens[user_id] -= request.cost
        self.stats["allowed_requests"] += 1
        self.request_history[user_id].append(request)
        return RateLimitResult(allowed=True, remaining_requests=int(self.tokens[user_id]), reset_time=time.time() + 1)

    async def predict_future_load(self, user_id: str) -> float:
        """Train a user-specific model and predict future load."""
        if user_id not in self.user_forecasters:
            self.user_forecasters[user_id] = TimeSeriesForecaster()

        forecaster = self.user_forecasters[user_id]
        history = self.request_history[user_id]

        forecaster.train(history)
        predicted_load = forecaster.predict(user_id, self.config["window_seconds"])

        if predicted_load > 0:
            self.logger.info(f"ML Prediction for {user_id}: {predicted_load:.2f} requests in the next {self.config['window_seconds']}s.")
        return predicted_load

    async def _adapt_rate_limit(self, user_id: str, profile: QoSProfile):
        """
        Adapt rate limit based on long-term user behavior and QoS profile.
        """
        if not self.adaptation_enabled:
            return

        profile_rules = self.qos_profiles[profile]
        base_limit = profile_rules['limit_per_minute']
        current_limit = self.dynamic_limits.get(user_id, base_limit)
        new_limit = current_limit

        # --- Proactive Adaptation using ML Prediction ---
        predicted_load = await self.predict_future_load(user_id)
        if predicted_load > 0:
            # If predicted load is significantly higher than the base limit, proactively increase the limit
            if predicted_load > base_limit * 1.2 and profile not in [QoSProfile.LOW, QoSProfile.BACKGROUND]:
                burst_multiplier = profile_rules.get('burst_multiplier', 1.5)
                # Allow bursting but cap it
                proactive_limit = min(int(predicted_load * 1.1), int(base_limit * burst_multiplier))
                new_limit = max(new_limit, proactive_limit)
                self.logger.info(f"Proactively adjusted limit for {user_id} to {new_limit} based on prediction.")

        # --- Reactive Adaptation based on past usage ---
        history = self.request_history[user_id]
        if len(history) > 100: # Need sufficient data for reactive part
            analysis_window = time.time() - 3600
            relevant_requests = [r for r in history if r.timestamp > analysis_window]
            if relevant_requests:
                avg_rpm = len(relevant_requests) / 60.0

                # If usage is consistently low, gently lower the limit towards the base
                if avg_rpm < (base_limit * 0.5):
                    new_limit = max(base_limit, int(new_limit * 0.95))
                # If usage is very high, apply throttling (especially for low priority)
                elif avg_rpm > (base_limit * 1.5) and profile in [QoSProfile.LOW, QoSProfile.BACKGROUND]:
                    new_limit = max(int(base_limit * 0.8), int(new_limit * 0.9))

        if new_limit != current_limit:
            self.dynamic_limits[user_id] = new_limit
            self.stats["active_adaptations"] += 1
            self.logger.info(f"Adapted rate limit for user {user_id} ({profile.name}) from {current_limit} to {new_limit}")

    async def manage_qos(self) -> Dict[str, Any]:
        """
        Manage Quality of Service for queued requests.

        Returns:
            QoS management results
        """
        try:
            self.logger.info("Managing QoS for queued requests")

            results = {
                "processed_requests": 0,
                "queue_status": {},
                "priority_distribution": {},
                "recommendations": [],
            }

            # Check queue status
            for priority in [3, 2, 1]:  # High priority first
                queue = self.priority_queues[priority]
                queue_size = queue.qsize()
                results["queue_status"][f"priority_{priority}"] = queue_size

                # Process high priority requests first
                if priority == 3 and queue_size > 0:
                    results["recommendations"].append(
                        "High priority requests pending - prioritize processing"
                    )

            # Analyze priority distribution
            total_queued = sum(results["queue_status"].values())
            if total_queued > 0:
                for priority, size in results["queue_status"].items():
                    percentage = (size / total_queued) * 100
                    results["priority_distribution"][priority] = f"{percentage:.1f}%"

            self.logger.info(
                f"QoS management completed. Queued requests: {total_queued}"
            )
            return results

        except Exception as e:
            self.logger.error(f"Error managing QoS: {e}")
            raise QoSError(f"Failed to manage QoS: {e}") from e

    async def submit_request(self, request: Request) -> bool:
        """
        Submit a request to the appropriate priority queue.
        """
        try:
            queue = self.priority_queues[request.priority]
            if queue.full():
                self.logger.warning(f"Queue full for priority {request.priority}")
                return False
            await queue.put(request)
            return True
        except Exception as e:
            self.logger.error(f"Error submitting request: {e}")
            return False

    async def process_queued_requests(self) -> List[Request]:
        """
        Process requests from queues in priority order.
        """
        processed_requests = []
        for priority in sorted(self.priority_queues.keys(), reverse=True):
            queue = self.priority_queues[priority]
            batch_size = min(queue.qsize(), self.config.get("batch_size", 10))

            temp_requeue = []
            for _ in range(batch_size):
                if queue.empty():
                    break
                request = queue.get_nowait()
                if self._check_circuit_breaker(request.endpoint):
                    processed_requests.append(request)
                else:
                    # Circuit breaker is open, requeue the request for later
                    temp_requeue.append(request)
                queue.task_done()

            # Put back requests for endpoints with open circuit breakers
            for req in temp_requeue:
                queue.put_nowait(req)

        if processed_requests:
            self.logger.info(f"Processed {len(processed_requests)} queued requests")

        await self._escalate_old_requests()
        return processed_requests

    def record_endpoint_failure(self, endpoint: str):
        """Record a failure for a specific endpoint to manage circuit breaker state."""
        breaker = self.circuit_breakers[endpoint]
        if breaker["state"] == "open":
            return # Already open

        breaker["failures"] += 1
        breaker["last_failure_time"] = time.time()
        if breaker["failures"] >= self.failure_threshold:
            breaker["state"] = "open"
            self.logger.warning(f"Circuit breaker for endpoint {endpoint} has been opened.")

    def _check_circuit_breaker(self, endpoint: str) -> bool:
        """Check the state of the circuit breaker for an endpoint. Returns True if closed."""
        breaker = self.circuit_breakers[endpoint]
        if breaker["state"] == "open":
            if time.time() - breaker["last_failure_time"] > self.breaker_reset_timeout:
                # Half-open state: allow one request to test the endpoint
                breaker["state"] = "half-open"
                self.logger.info(f"Circuit breaker for {endpoint} is now half-open.")
                return True
            return False
        elif breaker["state"] == "half-open":
            # Let one request through, then re-evaluate. If it succeeds, we'll close the breaker.
            # If it fails, it will re-open.
            return True
        return True # Closed

    def record_endpoint_success(self, endpoint: str):
        """Record a success for an endpoint to close the circuit breaker."""
        breaker = self.circuit_breakers[endpoint]
        if breaker["state"] != "closed":
            self.logger.info(f"Circuit breaker for endpoint {endpoint} is now closed.")
        breaker["state"] = "closed"
        breaker["failures"] = 0

    async def _escalate_old_requests(self, age_threshold_seconds: int = 300):
        """Escalate priority of requests that have been in the queue for too long."""
        for priority in [1, 2]: # Escalate from low and medium
            queue = self.priority_queues[priority]
            next_queue = self.priority_queues[priority + 1]

            items_to_requeue = []
            while not queue.empty():
                request = await queue.get()
                if time.time() - request.timestamp > age_threshold_seconds and not next_queue.full():
                    request.priority += 1
                    await next_queue.put(request)
                    self.logger.info(f"Escalated request for user {request.user_id} to priority {request.priority}.")
                else:
                    items_to_requeue.append(request)

            # Put back the items that were not escalated
            for item in items_to_requeue:
                await queue.put(item)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current monitoring statistics.
        """
        stats = self.stats.copy()
        stats["current_queue_lengths"] = {p: q.qsize() for p, q in self.priority_queues.items()}
        stats["dynamic_user_limits"] = self.dynamic_limits

        total = stats["total_requests"]
        if total > 0:
            stats["block_rate_percent"] = (stats["blocked_requests"] / total) * 100

        return stats

    async def is_request_allowed(self, request: Request) -> bool:
        """
        Check if a request is allowed (legacy method for compatibility).

        Args:
            request: Request to check

        Returns:
            True if allowed, False otherwise
        """
        result = await self.enforce_rate_limits(request)
        return result.allowed

if __name__ == "__main__":
    async def main():
        print("--- Adaptive Rate Limiter & QoS Manager Demonstration ---")

        # Define QoS profiles
        qos_profiles = {
            QoSProfile.DEFAULT: {'limit_per_minute': 100, 'burst_multiplier': 1.5},
            QoSProfile.HIGH: {'limit_per_minute': 500, 'burst_multiplier': 2.0},
            QoSProfile.LOW: {'limit_per_minute': 50, 'burst_multiplier': 1.1},
        }

        manager = AdaptiveRateLimiterQoSManager(qos_profiles, {"strategy": RateLimitingStrategy.TOKEN_BUCKET})

        # 1. User QoS Profiles & Request Cost
        print("\n--- 1. User QoS Profiles & Request Cost ---")
        manager.set_user_qos_profile("user_high_prio", QoSProfile.HIGH)
        manager.set_user_qos_profile("user_low_prio", QoSProfile.LOW)

        # High-cost request from low-prio user
        heavy_request = Request("user_low_prio", "/heavy_op", "POST", time.time(), priority=1, cost=40)
        result = await manager.enforce_rate_limits(heavy_request)
        print(f"Heavy request from low-prio user allowed: {result.allowed}. Tokens remaining: {result.remaining_requests}")

        light_request = Request("user_high_prio", "/light_op", "GET", time.time(), priority=3, cost=1)
        result = await manager.enforce_rate_limits(light_request)
        print(f"Light request from high-prio user allowed: {result.allowed}. Tokens remaining: {result.remaining_requests}")

        # 2. ML-driven Proactive Adaptation
        print("\n--- 2. ML-driven Proactive Adaptation ---")
        # Simulate a history of high traffic for a user
        for i in range(150):
            req = Request("user_high_prio", "/light_op", "GET", time.time() - (150 - i), cost=1)
            manager.request_history["user_high_prio"].append(req)

        print("Simulating new window to trigger adaptation...")
        await manager._adapt_rate_limit("user_high_prio", QoSProfile.HIGH)
        print(f"Adapted limits: {manager.dynamic_limits.get('user_high_prio')}")

        # 3. Circuit Breaker Demonstration
        print("\n--- 3. Circuit Breaker ---")
        failing_endpoint = "/failing_service"
        for _ in range(manager.failure_threshold):
            manager.record_endpoint_failure(failing_endpoint)

        req = Request("some_user", failing_endpoint, "GET", time.time(), priority=2)
        await manager.submit_request(req)

        processed = await manager.process_queued_requests()
        print(f"Request to failing endpoint processed: {failing_endpoint in [p.endpoint for p in processed]}")
        print(f"Circuit breaker state for {failing_endpoint}: {manager.circuit_breakers[failing_endpoint]['state']}")

        # Let's say the service recovers
        manager.record_endpoint_success(failing_endpoint)
        print(f"Circuit breaker state after success: {manager.circuit_breakers[failing_endpoint]['state']}")

        # 4. Priority Escalation
        print("\n--- 4. Priority Escalation ---")
        old_request = Request("patient_user", "/slow_endpoint", "GET", time.time() - 350, priority=1)
        await manager.submit_request(old_request)
        print(f"Queue sizes before escalation: Low={manager.priority_queues[1].qsize()}, Medium={manager.priority_queues[2].qsize()}")
        await manager._escalate_old_requests(age_threshold_seconds=300)
        print(f"Queue sizes after escalation: Low={manager.priority_queues[1].qsize()}, Medium={manager.priority_queues[2].qsize()}")


    asyncio.run(main())
