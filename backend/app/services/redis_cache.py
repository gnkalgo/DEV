"""Optional Redis JSON cache with silent fallback when Redis is unavailable."""

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_client: aioredis.Redis | None = None
_redis_disabled = False


async def get_redis() -> aioredis.Redis | None:
    global _client, _redis_disabled
    if _redis_disabled:
        return None
    if _client is None:
        try:
            client = aioredis.from_url(settings.redis_url, decode_responses=True)
            await client.ping()
            _client = client
        except Exception as exc:
            logger.warning("Redis unavailable, cache disabled: %s", exc)
            _redis_disabled = True
            return None
    return _client


async def cache_get(key: str) -> Any | None:
    client = await get_redis()
    if not client:
        return None
    try:
        raw = await client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int) -> bool:
    client = await get_redis()
    if not client:
        return False
    try:
        await client.set(key, json.dumps(value), ex=ttl_seconds)
        return True
    except Exception:
        return False


async def cache_delete_prefix(prefix: str) -> None:
    client = await get_redis()
    if not client:
        return
    try:
        keys = [k async for k in client.scan_iter(match=f"{prefix}*")]
        if keys:
            await client.delete(*keys)
    except Exception:
        return
