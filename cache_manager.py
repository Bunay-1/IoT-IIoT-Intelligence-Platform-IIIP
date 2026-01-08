"""
Advanced caching layer with Redis and in-memory fallback
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Advanced caching manager with Redis and memory fallback."""

    def __init__(self, redis_client=None, default_ttl: int = 300):
        self.redis = redis_client
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())

    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_expired(self):
        """Background task to clean up expired memory cache entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Clean up every minute
                now = datetime.now().timestamp()
                expired_keys = []

                for key, data in self.memory_cache.items():
                    if data["expires_at"] < now:
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.memory_cache[key]

                if expired_keys:
                    logger.debug(
                        f"Cleaned up {len(expired_keys)} expired cache entries"
                    )

            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")

    def _make_key(self, *args, **kwargs) -> str:
        """Create a consistent cache key."""
        key_parts = list(args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(str(part) for part in key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Try Redis first
        if self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    logger.debug(f"Cache hit (Redis): {key}")
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        # Fallback to memory cache
        if key in self.memory_cache:
            data = self.memory_cache[key]
            if data["expires_at"] > datetime.now().timestamp():
                logger.debug(f"Cache hit (Memory): {key}")
                return data["value"]
            else:
                del self.memory_cache[key]

        logger.debug(f"Cache miss: {key}")
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now().timestamp() + ttl

        # Store in Redis
        if self.redis:
            try:
                await self.redis.setex(key, ttl, json.dumps(value))
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")

        # Store in memory as fallback
        self.memory_cache[key] = {"value": value, "expires_at": expires_at}

        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        success = True

        # Delete from Redis
        if self.redis:
            try:
                await self.redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis cache delete error: {e}")
                success = False

        # Delete from memory
        if key in self.memory_cache:
            del self.memory_cache[key]

        return success

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        count = 0

        # Clear from Redis
        if self.redis:
            try:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
                    count += len(keys)
            except Exception as e:
                logger.warning(f"Redis cache clear pattern error: {e}")

        # Clear from memory (simple implementation)
        keys_to_delete = [
            k for k in self.memory_cache.keys() if pattern.replace("*", "") in k
        ]
        for key in keys_to_delete:
            del self.memory_cache[key]
            count += 1

        return count

    async def get_or_set(self, key: str, getter_func, ttl: Optional[int] = None):
        """Get from cache or set if not exists."""
        value = await self.get(key)
        if value is not None:
            return value

        # Get fresh data
        value = await getter_func()
        if value is not None:
            await self.set(key, value, ttl)

        return value

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        memory_count = len(self.memory_cache)

        redis_info = {}
        if self.redis:
            try:
                info = await self.redis.info()
                redis_info = {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "0B"),
                    "total_keys": await self.redis.dbsize(),
                }
            except Exception as e:
                redis_info = {"error": str(e)}

        return {
            "memory_cache_entries": memory_count,
            "redis_info": redis_info,
            "timestamp": datetime.now().isoformat(),
        }


# Global cache manager instance
cache_manager = CacheManager()
