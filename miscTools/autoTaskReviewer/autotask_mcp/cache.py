"""Simple in-memory caching with TTL for API responses."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with expiration."""

    def __init__(self, data: Any, ttl: int) -> None:
        self.data = data
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > self.expires_at


class SimpleCache:
    """Thread-safe in-memory cache with TTL."""

    def __init__(self, default_ttl: int = 300) -> None:
        """
        Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
        logger.info(f"Cache initialized with TTL={default_ttl}s")

    def _generate_key(self, method: str, endpoint: str, **kwargs: Any) -> str:
        """Generate cache key from request parameters."""
        # Create deterministic key from parameters
        key_parts = [method, endpoint]
        if kwargs:
            # Sort kwargs for consistent keys
            sorted_kwargs = json.dumps(kwargs, sort_keys=True)
            key_parts.append(sorted_kwargs)

        key_string = ":".join(key_parts)
        # Use hash for shorter keys
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, method: str, endpoint: str, **kwargs: Any) -> Any | None:
        """
        Get cached response if available and not expired.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional parameters (json, params, etc.)

        Returns:
            Cached data or None if not found/expired
        """
        key = self._generate_key(method, endpoint, **kwargs)
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            logger.debug(f"Cache MISS: {method} {endpoint}")
            return None

        if entry.is_expired():
            self._misses += 1
            del self._cache[key]
            logger.debug(f"Cache EXPIRED: {method} {endpoint}")
            return None

        self._hits += 1
        logger.debug(f"Cache HIT: {method} {endpoint}")
        return entry.data

    def set(
        self,
        method: str,
        endpoint: str,
        data: Any,
        ttl: int | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Store data in cache.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Data to cache
            ttl: Time-to-live in seconds (uses default if None)
            **kwargs: Additional parameters (json, params, etc.)
        """
        key = self._generate_key(method, endpoint, **kwargs)
        cache_ttl = ttl if ttl is not None else self._default_ttl
        self._cache[key] = CacheEntry(data, cache_ttl)
        logger.debug(f"Cache SET: {method} {endpoint} (TTL={cache_ttl}s)")

    def invalidate(self, method: str, endpoint: str, **kwargs: Any) -> None:
        """
        Invalidate specific cache entry.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional parameters
        """
        key = self._generate_key(method, endpoint, **kwargs)
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache INVALIDATE: {method} {endpoint}")

    def clear(self) -> None:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cache cleanup: {len(expired_keys)} expired entries removed")

        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "entries": len(self._cache),
            "ttl": self._default_ttl,
        }


# Global cache instance
cache = SimpleCache()
