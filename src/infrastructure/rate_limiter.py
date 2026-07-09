"""
Rate limiting module for API protection
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter implementation."""

    def __init__(self, rate: float = 10.0, capacity: int = 100):
        """
        Initialize rate limiter.

        Args:
            rate: Tokens per second
            capacity: Maximum bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.buckets: Dict[
            str, Tuple[float, float]
        ] = {}  # key -> (tokens, last_update)
        self._lock = asyncio.Lock()

    async def acquire(self, key: str, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.

        Args:
            key: Identifier for the bucket (e.g., IP address, user ID)
            tokens: Number of tokens to acquire

        Returns:
            True if tokens were acquired, False otherwise
        """
        async with self._lock:
            now = time.time()

            if key not in self.buckets:
                self.buckets[key] = (self.capacity, now)
                current_tokens, last_update = self.buckets[key]
            else:
                current_tokens, last_update = self.buckets[key]

            # Add tokens based on time passed
            elapsed = now - last_update
            current_tokens = min(self.capacity, current_tokens + elapsed * self.rate)

            # Check if we have enough tokens
            if current_tokens >= tokens:
                current_tokens -= tokens
                self.buckets[key] = (current_tokens, now)

                logger.debug(f"Rate limit: {key} acquired {tokens} tokens")
                return True
            else:
                logger.warning(f"Rate limit exceeded for {key}")
                return False

    def get_remaining_tokens(self, key: str) -> float:
        """Get remaining tokens for a key."""
        if key not in self.buckets:
            return self.capacity

        current_tokens, last_update = self.buckets[key]
        elapsed = time.time() - last_update
        return min(self.capacity, current_tokens + elapsed * self.rate)

    def reset(self, key: str):
        """Reset bucket for a key."""
        self.buckets[key] = (self.capacity, time.time())
        logger.info(f"Rate limit reset for {key}")


class SlidingWindowRateLimiter:
    """Sliding window rate limiter for more precise control."""

    def __init__(self, window_size: int = 60, max_requests: int = 100):
        """
        Initialize sliding window rate limiter.

        Args:
            window_size: Window size in seconds
            max_requests: Maximum requests per window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        async with self._lock:
            now = time.time()

            # Remove old requests outside the window
            self.requests[key] = [
                req_time
                for req_time in self.requests[key]
                if now - req_time < self.window_size
            ]

            # Check if under limit
            if len(self.requests[key]) < self.max_requests:
                self.requests[key].append(now)
                return True
            else:
                logger.warning(f"Sliding window rate limit exceeded for {key}")
                return False


# Global rate limiter instances
api_limiter = RateLimiter(rate=10.0, capacity=100)  # 10 requests/second, burst 100
auth_limiter = RateLimiter(rate=5.0, capacity=20)  # 5 auth attempts/second, burst 20
websocket_limiter = SlidingWindowRateLimiter(
    window_size=60, max_requests=1000
)  # 1000 WS messages/minute
