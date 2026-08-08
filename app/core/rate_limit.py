"""Fixed-window per-user rate limiting, configurable requests/minute."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from functools import lru_cache


class RateLimiter(ABC):
    @abstractmethod
    async def is_allowed(self, user_id: str, limit_per_minute: int) -> bool: ...


class RedisRateLimiter(RateLimiter):
    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as redis

        self._client = redis.from_url(redis_url, decode_responses=True)

    async def is_allowed(self, user_id: str, limit_per_minute: int) -> bool:
        window = int(time.time() // 60)
        key = f"ratelimit:{user_id}:{window}"
        count = await self._client.incr(key)
        if count == 1:
            await self._client.expire(key, 60)
        return count <= limit_per_minute


class InMemoryRateLimiter(RateLimiter):
    """Used for tests / environments without a running Redis instance."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    async def is_allowed(self, user_id: str, limit_per_minute: int) -> bool:
        window = int(time.time() // 60)
        key = f"{user_id}:{window}"
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key] <= limit_per_minute


@lru_cache
def get_rate_limiter() -> RateLimiter:
    from app.core.config import get_settings

    settings = get_settings()
    try:
        return RedisRateLimiter(settings.redis_url)
    except Exception:  # pragma: no cover
        return InMemoryRateLimiter()
