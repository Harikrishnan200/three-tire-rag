"""Response cache abstraction. Cache key: rag:{user_id}:{query_hash}. Never
shared cross-user unless explicitly marked public (not used in this app)."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any


def cache_key(user_id: str, query: str) -> str:
    query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()
    return f"rag:{user_id}:{query_hash}"


class ResponseCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None: ...


class RedisResponseCache(ResponseCache):
    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as redis

        self._client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> dict[str, Any] | None:
        raw = await self._client.get(key)
        return json.loads(raw) if raw else None

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        await self._client.set(key, json.dumps(value), ex=ttl_seconds)


class InMemoryResponseCache(ResponseCache):
    """Used for tests / environments without a running Redis instance."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    async def get(self, key: str) -> dict[str, Any] | None:
        return self._store.get(key)

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        self._store[key] = value


@lru_cache
def get_response_cache() -> ResponseCache:
    from app.core.config import get_settings

    settings = get_settings()
    try:
        cache = RedisResponseCache(settings.redis_url)
        return cache
    except Exception:  # pragma: no cover
        return InMemoryResponseCache()
