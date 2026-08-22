"""Redis client. Do not store plaintext secrets in Redis.

Key names live in app.utils.redis_keys. Access tokens and TOTP stay in PostgreSQL (broker_tokens).
"""

from redis.asyncio import Redis

from app.core.config import Settings

redis_client: Redis | None = None


def init_redis(settings: Settings) -> Redis:
    global redis_client
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
    redis_client = None


async def ping_redis() -> None:
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    ok = await redis_client.ping()
    if not ok:
        raise RuntimeError("Redis ping failed")
