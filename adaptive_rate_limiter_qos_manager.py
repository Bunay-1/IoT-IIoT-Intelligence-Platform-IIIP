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
        self, rate_limits: Dict[str, int], config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the Adaptive Rate Limiter QoS Manager.

        Args:
            rate_limits: Dictionary mapping user IDs to their rate limits
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.logger = get_logger(__name__)

        # Rate limiting data structures
        self.rate_limits = rate_limits.copy()
        self.current_usage: Dict[str, int] = defaultdict(int)
        self.reset_times: Dict[str, float] = {}
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # QoS management
        self.priority_queues: Dict[int, asyncio.Queue] = {
            1: asyncio.Queue(maxlen=self.config["queue_size"]),
            2: asyncio.Queue(maxlen=self.config["queue_size"]),
            3: asyncio.Queue(maxlen=self.config["queue_size"]),
        }

        # Adaptive parameters
        self.adaptation_enabled = self.config.get("adaptation_enabled", True)
        self.burst_multiplier = self.config.get("burst_multiplier", 1.5)
        self.cooldown_period = self.config.get("cooldown_period", 300)  # 5 minutes

        # Monitoring
        self.monitoring_enabled = self.config.get("monitoring_enabled", True)
        self.stats: Dict[str, Any] = self._initialize_stats()

        self.logger.info("Adaptive Rate Limiter QoS Manager initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "window_seconds": 60,  # 1 minute window
            "burst_multiplier": 1.5,
            "cooldown_period": 300,
            "adaptation_enabled": True,
            "monitoring_enabled": True,
            "queue_size": 1000,
            "max_wait_time": 30,  # seconds
            "priority_weights": {1: 1.0, 2: 1.5, 3: 2.0},
        }

    def _initialize_stats(self) -> Dict[str, Any]:
        """Initialize monitoring statistics."""
        return {
            "total_requests": 0,
            "allowed_requests": 0,
            "blocked_requests": 0,
            "queue_lengths": {1: 0, 2: 0, 3: 0},
            "avg_response_time": 0.0,
            "rate_limit_hits": defaultdict(int),
            "adaptation_actions": 0,
        }

    async def enforce_rate_limits(self, request: Request) -> RateLimitResult:
        """
        Enforce adaptive rate limits for a request.

        Args:
            request: Request object to check

        Returns:
            RateLimitResult indicating if request is allowed
        """
        try:
            self.stats["total_requests"] += 1

            # Check if user has rate limit configured
            if request.user_id not in self.rate_limits:
                return RateLimitResult(
                    allowed=True,
                    remaining_requests=-1,  # Unlimited
                    reset_time=0,
                    reason="No rate limit configured",
                )

            # Clean up expired entries
            await self._cleanup_expired_entries()

            # Check current usage
            current_time = time.time()
            window_start = current_time - self.config["window_seconds"]

            # Reset counter if window expired
            if (
                request.user_id not in self.reset_times
                or current_time > self.reset_times[request.user_id]
            ):
                self.current_usage[request.user_id] = 0
                self.reset_times[request.user_id] = (
                    current_time + self.config["window_seconds"]
                )

            # Check rate limit
            base_limit = self.rate_limits[request.user_id]
            adapted_limit = await self._adapt_rate_limit(request.user_id, base_limit)

            if self.current_usage[request.user_id] >= adapted_limit:
                # Rate limit exceeded
                reset_time = self.reset_times.get(
                    request.user_id, current_time + self.config["window_seconds"]
                )
                retry_after = max(0, reset_time - current_time)

                self.stats["blocked_requests"] += 1
                self.stats["rate_limit_hits"][request.user_id] += 1

                return RateLimitResult(
                    allowed=False,
                    remaining_requests=0,
                    reset_time=reset_time,
                    retry_after=retry_after,
                    reason="Rate limit exceeded",
                )

            # Request allowed
            self.current_usage[request.user_id] += 1
            remaining = adapted_limit - self.current_usage[request.user_id]
            reset_time = self.reset_times[request.user_id]

            # Record request history
            self.request_history[request.user_id].append(
                {
                    "timestamp": current_time,
                    "endpoint": request.endpoint,
                    "priority": request.priority,
                }
            )

            self.stats["allowed_requests"] += 1

            return RateLimitResult(
                allowed=True, remaining_requests=remaining, reset_time=reset_time
            )

        except Exception as e:
            self.logger.error(f"Error enforcing rate limits: {e}")
            # Allow request on error to avoid blocking legitimate traffic
            return RateLimitResult(
                allowed=True,
                remaining_requests=-1,
                reset_time=0,
                reason=f"Error: {str(e)}",
            )

    async def _adapt_rate_limit(self, user_id: str, base_limit: int) -> int:
        """
        Adapt rate limit based on user behavior and system conditions.

        Args:
            user_id: User identifier
            base_limit: Base rate limit

        Returns:
            Adapted rate limit
        """
        if not self.adaptation_enabled:
            return base_limit

        try:
            # Analyze recent behavior
            recent_requests = list(self.request_history[user_id])
            if len(recent_requests) < 10:
                return base_limit

            # Calculate request patterns
            recent_window = time.time() - 300  # Last 5 minutes
            recent_count = sum(
                1 for r in recent_requests if r["timestamp"] > recent_window
            )

            # Adaptive logic
            adapted_limit = base_limit

            # Increase limit for well-behaved users
            if recent_count <= base_limit * 0.8:
                adapted_limit = int(base_limit * self.burst_multiplier)
                self.stats["adaptation_actions"] += 1
                self.logger.debug(
                    f"Increased rate limit for user {user_id} to {adapted_limit}"
                )

            # Decrease limit for abusive users
            elif recent_count > base_limit * 1.5:
                adapted_limit = max(1, int(base_limit * 0.5))
                self.stats["adaptation_actions"] += 1
                self.logger.debug(
                    f"Decreased rate limit for user {user_id} to {adapted_limit}"
                )

            return adapted_limit

        except Exception as e:
            self.logger.warning(f"Error adapting rate limit for user {user_id}: {e}")
            return base_limit

    async def _cleanup_expired_entries(self) -> None:
        """Clean up expired rate limit entries."""
        try:
            current_time = time.time()
            expired_users = [
                user_id
                for user_id, reset_time in self.reset_times.items()
                if current_time > reset_time
            ]

            for user_id in expired_users:
                del self.reset_times[user_id]
                self.current_usage[user_id] = 0

        except Exception as e:
            self.logger.warning(f"Error cleaning up expired entries: {e}")

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
                self.stats["queue_lengths"][priority] = queue_size

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

            # Generate QoS recommendations
            if results["queue_status"]["priority_3"] > 10:
                results["recommendations"].append(
                    "Critical: High priority queue overloaded"
                )
            elif (
                results["queue_status"]["priority_1"]
                > results["queue_status"]["priority_3"] * 2
            ):
                results["recommendations"].append(
                    "Consider increasing processing capacity for low priority requests"
                )

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

        Args:
            request: Request to submit

        Returns:
            True if request was queued, False if queue is full
        """
        try:
            queue = self.priority_queues[request.priority]

            # Check if queue has space
            if queue.full():
                self.logger.warning(f"Queue full for priority {request.priority}")
                return False

            # Add request to queue
            await queue.put(request)
            self.logger.debug(
                f"Request queued for user {request.user_id} with priority {request.priority}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error submitting request: {e}")
            return False

    async def process_queued_requests(self) -> List[Request]:
        """
        Process requests from queues in priority order.

        Returns:
            List of processed requests
        """
        try:
            processed_requests = []

            # Process in priority order (high to low)
            for priority in [3, 2, 1]:
                queue = self.priority_queues[priority]

                # Process up to batch size requests from this priority
                batch_size = min(queue.qsize(), self.config.get("batch_size", 10))

                for _ in range(batch_size):
                    try:
                        request = queue.get_nowait()
                        processed_requests.append(request)
                        queue.task_done()
                    except asyncio.QueueEmpty:
                        break

            self.logger.info(f"Processed {len(processed_requests)} queued requests")
            return processed_requests

        except Exception as e:
            self.logger.error(f"Error processing queued requests: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics.

        Returns:
            Dictionary with current statistics
        """
        stats = self.stats.copy()

        # Add real-time queue lengths
        stats["current_queue_lengths"] = {
            priority: queue.qsize() for priority, queue in self.priority_queues.items()
        }

        # Calculate rates
        total_requests = stats["total_requests"]
        if total_requests > 0:
            stats["allowance_rate"] = stats["allowed_requests"] / total_requests
            stats["block_rate"] = stats["blocked_requests"] / total_requests

        return stats

    def reset_user_limits(self, user_id: str) -> None:
        """
        Reset rate limits for a specific user.

        Args:
            user_id: User ID to reset
        """
        if user_id in self.current_usage:
            self.current_usage[user_id] = 0
            self.reset_times[user_id] = time.time() + self.config["window_seconds"]
            self.logger.info(f"Reset rate limits for user {user_id}")

    def update_rate_limit(self, user_id: str, new_limit: int) -> None:
        """
        Update rate limit for a user.

        Args:
            user_id: User ID
            new_limit: New rate limit
        """
        self.rate_limits[user_id] = new_limit
        self.logger.info(f"Updated rate limit for user {user_id} to {new_limit}")

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
