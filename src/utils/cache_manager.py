"""
Advanced caching layer with Redis and in-memory fallback

This module has been enhanced with detailed statistics tracking (hits, misses,
hit rate), a size limit for the in-memory cache to prevent uncontrolled growth,
and a convenient decorator for caching function results.
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from functools import wraps

# Setup basic logging for standalone execution
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CacheManager:
    """
    Advanced caching manager with Redis, memory fallback, detailed stats,
    and a function caching decorator.
    """

    def __init__(self, redis_client=None, default_ttl: int = 300, memory_max_size: int = 1000):
        self.redis = redis_client
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.memory_max_size = memory_max_size

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup_task(self):
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())

    async def stop_cleanup_task(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_expired(self):
        while True:
            await asyncio.sleep(60)
            now = datetime.now().timestamp()
            expired_keys = [k for k, v in self.memory_cache.items() if v["expires_at"] < now]

            for key in expired_keys:
                del self.memory_cache[key]
                self.evictions += 1

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _make_key(self, *args, **kwargs) -> str:
        key_parts = list(args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(str(part) for part in key_parts)
        return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"

    async def get(self, key: str) -> Optional[Any]:
        # Try Redis first
        if self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    logger.debug(f"Cache hit (Redis): {key}")
                    self.hits += 1
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis cache GET error: {e}")

        # Fallback to memory cache
        if key in self.memory_cache:
            data = self.memory_cache[key]
            if data["expires_at"] > datetime.now().timestamp():
                logger.debug(f"Cache hit (Memory): {key}")
                self.hits += 1
                return data["value"]
            else:
                del self.memory_cache[key]
                self.evictions += 1

        logger.debug(f"Cache miss: {key}")
        self.misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        ttl = ttl or self.default_ttl
        expires_at = datetime.now().timestamp() + ttl

        # Store in Redis
        if self.redis:
            try:
                await self.redis.setex(key, ttl, json.dumps(value))
            except Exception as e:
                logger.warning(f"Redis cache SET error: {e}")

        # Enforce memory cache size limit
        if len(self.memory_cache) >= self.memory_max_size:
            self._evict_from_memory()

        # Store in memory as fallback
        self.memory_cache[key] = {"value": value, "expires_at": expires_at}
        return True

    def _evict_from_memory(self):
        """Evicts items from memory cache to respect max_size."""
        # Simple strategy: remove a random item.
        # For LRU/LFU, a more complex data structure would be needed.
        if not self.memory_cache:
            return

        key_to_evict = random.choice(list(self.memory_cache.keys()))
        del self.memory_cache[key_to_evict]
        self.evictions += 1
        logger.debug(f"Evicted memory cache item: {key_to_evict} to maintain size limit.")

    async def get_or_set(self, key: str, getter_func: Callable, ttl: Optional[int] = None):
        value = await self.get(key)
        if value is not None:
            return value

        value = await getter_func()
        if value is not None:
            await self.set(key, value, ttl)
        return value

    async def get_stats(self) -> Dict[str, Any]:
        memory_count = len(self.memory_cache)
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests) * 100 if total_requests > 0 else 0

        redis_info = {}
        if self.redis:
            try:
                info = await self.redis.info()
                redis_info = {"used_memory": info.get("used_memory_human", "0B")}
            except Exception as e:
                redis_info = {"error": str(e)}

        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_entries": memory_count,
            "memory_cache_max_size": self.memory_max_size,
            "redis_info": redis_info,
        }

    def cached_function(self, ttl: Optional[int] = None):
        """Decorator to cache the result of a function."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                key = self._make_key(func.__name__, *args, **kwargs)

                # Check cache first
                cached_value = await self.get(key)
                if cached_value is not None:
                    return cached_value

                # If not in cache, call the function
                result = await func(*args, **kwargs)

                # Store the result in cache
                await self.set(key, result, ttl=ttl)

                return result
            return wrapper
        return decorator


# --- Demonstration ---
async def main():
    print("--- Initializing CacheManager Demonstration ---")
    # Using a smaller size for demo purposes
    cache_manager = CacheManager(memory_max_size=5)

    print("\n--- 1. Basic Get/Set and Stats Tracking ---")
    await cache_manager.set("user:1", {"name": "Alice", "email": "alice@example.com"})
    await cache_manager.get("user:1") # Hit
    await cache_manager.get("user:2") # Miss
    await cache_manager.get("user:1") # Hit

    stats = await cache_manager.get_stats()
    print(f"Stats after basic operations: {stats}")
    assert stats['hits'] == 2
    assert stats['misses'] == 1

    print("\n--- 2. Cache Eviction (Size Limit) ---")
    for i in range(10):
        await cache_manager.set(f"key:{i}", f"value:{i}")

    stats = await cache_manager.get_stats()
    print(f"Stats after adding 10 items (max_size=5): {stats}")
    assert stats['memory_cache_entries'] <= 5
    assert stats['evictions'] >= 5

    print("\n--- 3. Function Caching with Decorator ---")

    @cache_manager.cached_function(ttl=60)
    async def fetch_heavy_data(user_id: int):
        print(f"    -> Running original function for user_id: {user_id}")
        await asyncio.sleep(0.1) # Simulate slow operation
        return {"data": f"Some heavy data for user {user_id}", "timestamp": time.time()}

    print("First call to fetch_heavy_data(101)...")
    result1 = await fetch_heavy_data(101)
    print(f"Result 1: {result1['data']}")

    print("\nSecond call to fetch_heavy_data(101) (should be cached)...")
    result2 = await fetch_heavy_data(101)
    print(f"Result 2: {result2['data']}")
    assert result1['timestamp'] == result2['timestamp'] # Timestamps must match if cached

    print("\nFirst call to fetch_heavy_data(102)...")
    await fetch_heavy_data(102)

    final_stats = await cache_manager.get_stats()
    print(f"\nFinal Stats: {final_stats}")
    # Previous hits/misses + 1 miss and 1 hit from the decorator
    assert final_stats['misses'] >= stats['misses'] + 2 # user:2, key:0-4, fetch(101), fetch(102)
    assert final_stats['hits'] >= stats['hits'] + 1   # fetch(101) second call

    print("\n--- Demonstration Finished ---")


if __name__ == "__main__":
    asyncio.run(main())
