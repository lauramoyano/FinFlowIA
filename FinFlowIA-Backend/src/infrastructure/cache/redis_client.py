from typing import Any

import structlog
import redis.asyncio as aioredis

from src.config.settings import settings

logger = structlog.get_logger(__name__)

_redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """Get or create the Redis async client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        logger.info("redis_client_created", url=settings.redis_url)
    return _redis_client


async def close_redis_client() -> None:
    """Close the Redis connection on application shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("redis_client_closed")


async def get_redis() -> aioredis.Redis | None:
    """FastAPI dependency that provides the Redis client, or None if unavailable."""
    try:
        client = await get_redis_client()
        await client.ping()
        return client
    except Exception as e:
        logger.warning("redis_unavailable", error=str(e))
        return None
