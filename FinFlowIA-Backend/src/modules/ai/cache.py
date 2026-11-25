import hashlib
import json
import re
from decimal import Decimal
from typing import Any

import structlog

from src.modules.ai.schemas import CategoryResult

logger = structlog.get_logger(__name__)


class LLMCache:
    """
    Redis-backed cache for LLM responses.
    Normalizes input before caching to maximize hit rate.
    Identical descriptions will return the cached result regardless of minor variations.
    """

    def __init__(self, redis_client: Any, ttl_seconds: int = 3600) -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds

    def _normalize_description(self, description: str) -> str:
        """Normalize description for better cache hit rate."""
        # lowercase, strip, collapse whitespace, remove special chars
        normalized = description.lower().strip()
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = re.sub(r"[^a-z0-9\s]", "", normalized)
        return normalized

    def _build_key(self, description: str, amount: Decimal) -> str:
        """Build a deterministic cache key from transaction description and amount."""
        normalized = self._normalize_description(description)
        # Round amount to avoid float precision issues
        rounded_amount = str(round(amount, 2))
        raw_key = f"llm:category:{normalized}:{rounded_amount}"
        return hashlib.sha256(raw_key.encode()).hexdigest()

    async def get(self, description: str, amount: Decimal) -> CategoryResult | None:
        """Retrieve a cached CategoryResult or return None on cache miss."""
        if self._redis is None:
            return None

        key = self._build_key(description, amount)
        try:
            cached = await self._redis.get(key)
            if cached:
                data = json.loads(cached)
                result = CategoryResult(
                    category=data["category"],
                    confidence=data["confidence"],
                    from_cache=True,
                )
                logger.debug("llm_cache_hit", key=key[:12])
                return result
        except Exception as e:
            logger.warning("llm_cache_get_error", error=str(e))

        return None

    async def set(
        self,
        description: str,
        amount: Decimal,
        result: CategoryResult,
    ) -> None:
        """Store a CategoryResult in cache."""
        if self._redis is None:
            return

        key = self._build_key(description, amount)
        try:
            data = json.dumps({"category": result.category, "confidence": result.confidence})
            await self._redis.setex(key, self._ttl, data)
            logger.debug("llm_cache_set", key=key[:12], ttl=self._ttl)
        except Exception as e:
            logger.warning("llm_cache_set_error", error=str(e))
