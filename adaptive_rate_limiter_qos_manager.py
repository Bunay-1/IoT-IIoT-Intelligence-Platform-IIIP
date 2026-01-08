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
from typing import Any, Dict, List, Optional, Tuple, Union

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
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    remaining_requests: int
    reset_time: float
    retry_after: Optional[float] = None
    reason: Optional[str] = None


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
        self.config = config or self._get_default_config()
        self.logger = get_logger(__name__)

        # QoS-based rate limiting
        self.qos_profiles = qos_profiles
        self.user_qos: Dict[str, QoSProfile] = {}
        self.dynamic_limits: Dict[str, int] = {}

        # State for rate limiting
        self.current_usage: Dict[str, int] = defaultdict(int)
        self.reset_times: Dict[str, float] = {}
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.config["history_maxlen"]))

        # QoS management (simplified, as logic is now profile-based)
        self.priority_queues: Dict[int, asyncio.Queue] = {
            p: asyncio.Queue(maxlen=self.config["queue_size"]) for p in range(1, 4)
        }

        # Adaptive parameters
        self.adaptation_enabled = self.config.get("adaptation_enabled", True)
        self.cooldown_period = self.config.get("cooldown_period", 300)

        # Monitoring
        self.monitoring_enabled = self.config.get("monitoring_enabled", True)
        self.stats: Dict[str, Any] = self._initialize_stats()

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
        """
        Enforce adaptive, QoS-profile-based rate limits for a request.
        """
        self.stats["total_requests"] += 1
        user_id = request.user_id

        # Get user's QoS profile, default if not set
        profile = self.user_qos.get(user_id, QoSProfile.DEFAULT)
        self.stats["requests_by_profile"][profile.name] += 1

        # Get the current dynamic limit for the user
        current_limit = self.dynamic_limits.get(user_id)
        if current_limit is None:
            # User not seen before, initialize from profile
            self.set_user_qos_profile(user_id, profile)
            current_limit = self.dynamic_limits[user_id]

        # Check and reset window
        current_time = time.time()
        if current_time > self.reset_times.get(user_id, 0):
            self.current_usage[user_id] = 0
            self.reset_times[user_id] = current_time + self.config["window_seconds"]
            # Trigger adaptation at the start of a new window
            await self._adapt_rate_limit(user_id, profile)
            current_limit = self.dynamic_limits[user_id] # Fetch updated limit

        # Enforce limit
        if self.current_usage[user_id] >= current_limit:
            self.stats["blocked_requests"] += 1
            self.stats["rate_limit_hits"][user_id] += 1
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_time=self.reset_times[user_id],
                retry_after=self.reset_times[user_id] - current_time,
                reason=f"Rate limit exceeded for {profile.name} profile.",
            )

        # Allow request
        self.current_usage[user_id] += 1
        self.stats["allowed_requests"] += 1
        self.request_history[user_id].append(request)

        return RateLimitResult(
            allowed=True,
            remaining_requests=current_limit - self.current_usage[user_id],
            reset_time=self.reset_times[user_id],
        )

    async def _adapt_rate_limit(self, user_id: str, profile: QoSProfile):
        """
        Adapt rate limit based on long-term user behavior and QoS profile.
        """
        if not self.adaptation_enabled:
            return

        profile_rules = self.qos_profiles[profile]
        base_limit = profile_rules['limit_per_minute']

        history = self.request_history[user_id]
        if len(history) < 100: # Need sufficient data
            return

        # Analyze traffic over a longer period (e.g., 1 hour)
        analysis_window = time.time() - 3600
        relevant_requests = [r for r in history if r.timestamp > analysis_window]

        if not relevant_requests:
            return

        # Calculate average requests per minute over the last hour
        avg_rpm = len(relevant_requests) / 60.0

        current_limit = self.dynamic_limits.get(user_id, base_limit)
        new_limit = current_limit

        # Adaptive Logic based on QoS profile
        if avg_rpm < (base_limit * 0.7):
            # Consistently underusing, increase limit up to burst threshold
            increase_factor = profile_rules.get('burst_multiplier', 1.2)
            new_limit = min(int(current_limit * 1.1), int(base_limit * increase_factor))
        elif avg_rpm > (base_limit * 1.2):
            # Consistently overusing
            if profile in [QoSProfile.LOW, QoSProfile.BACKGROUND]:
                # Aggressively throttle low-priority users
                new_limit = max(int(base_limit * 0.7), int(current_limit * 0.9))
            else:
                # Gently throttle higher-priority users
                new_limit = max(base_limit, int(current_limit * 0.95))

        if new_limit != current_limit:
            self.dynamic_limits[user_id] = new_limit
            self.stats["active_adaptations"] += 1
            self.logger.info(f"Adapted rate limit for user {user_id} ({profile.name}) from {current_limit} to {new_limit} based on avg RPM of {avg_rpm:.2f}")

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
            for _ in range(batch_size):
                if queue.empty():
                    break
                processed_requests.append(queue.get_nowait())
                queue.task_done()

        if processed_requests:
            self.logger.info(f"Processed {len(processed_requests)} queued requests")
        return processed_requests

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
