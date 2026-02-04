from datetime import datetime, timedelta
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: dict = {}

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache if it exists and hasn't expired."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                logger.debug(f"Cache expired for key: {key}")
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl_hours: int) -> None:
        """Store a value in cache with a TTL."""
        expiry = datetime.now() + timedelta(hours=ttl_hours)
        self._cache[key] = (value, expiry)
        logger.debug(f"Cache set for key: {key}, expires at: {expiry}")

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.info("Cache cleared")

    def cleanup(self) -> int:
        """Remove expired entries and return count of removed items."""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items() if now >= expiry
        ]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)


# Global cache instance
cache = SimpleCache()
