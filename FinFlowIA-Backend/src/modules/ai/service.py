import json
from decimal import Decimal

import structlog

from src.modules.ai.cache import LLMCache
from src.modules.ai.prompts.categorization_v2 import SYSTEM_PROMPT, build_prompt_v2
from src.modules.ai.providers.base import LLMProvider, LLMProviderError
from src.modules.ai.schemas import CategoryResult

logger = structlog.get_logger(__name__)

VALID_CATEGORIES = frozenset([
    "food", "transport", "utilities", "supplies", "marketing",
    "payroll", "rent", "equipment", "sales", "services", "other", "uncategorized",
])


class AIService:
    """
    Facade for AI/LLM operations with caching, fallback, and error handling.
    Orchestrates: cache check → prompt building → primary provider → fallback → cache store.
    """

    def __init__(
        self,
        primary: LLMProvider,
        fallback: LLMProvider | None,
        cache: LLMCache,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._cache = cache

    def _parse_category(self, content: str) -> CategoryResult:
        """Parse LLM JSON response into a CategoryResult."""
        try:
            # Extract JSON even if wrapped in markdown code blocks
            json_str = content.strip()
            if "```" in json_str:
                json_str = json_str.split("```")[1].strip()
                if json_str.startswith("json"):
                    json_str = json_str[4:].strip()

            data = json.loads(json_str)
            category = str(data.get("category", "other")).lower()
            confidence = float(data.get("confidence", 0.5))

            if category not in VALID_CATEGORIES:
                category = "other"
            confidence = max(0.0, min(1.0, confidence))

            return CategoryResult(category=category, confidence=confidence)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("category_parse_failed", content=content[:100], error=str(e))
            return CategoryResult(category="other", confidence=0.5)

    async def categorize_transaction(
        self,
        description: str,
        amount: Decimal,
        prompt_version: str = "v2",
    ) -> CategoryResult:
        """
        Categorize a transaction description using AI.

        Flow:
        1. Check Redis cache
        2. Build prompt from versioned template
        3. Call primary LLM provider
        4. On failure, try fallback provider
        5. On total failure, return 'uncategorized' with 0.0 confidence
        6. Cache successful result
        """
        # 1. Check cache
        cached = await self._cache.get(description, amount)
        if cached:
            try:
                from src.infrastructure.observability.metrics import llm_cache_hits
                llm_cache_hits.labels(result="hit").inc()
            except ImportError:
                pass
            return cached

        try:
            from src.infrastructure.observability.metrics import llm_cache_hits
            llm_cache_hits.labels(result="miss").inc()
        except ImportError:
            pass

        # 2. Build prompt
        user_prompt = build_prompt_v2(description, amount)
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

        # 3. Call primary with fallback
        try:
            response = await self._primary.complete(
                prompt=full_prompt,
                max_tokens=128,
                temperature=0.0,
            )
        except LLMProviderError as e:
            logger.warning("primary_llm_failed", error=str(e))
            if self._fallback:
                try:
                    response = await self._fallback.complete(
                        prompt=full_prompt,
                        max_tokens=128,
                        temperature=0.0,
                    )
                except LLMProviderError as fallback_err:
                    logger.error("fallback_llm_failed", error=str(fallback_err))
                    return CategoryResult(category="uncategorized", confidence=0.0)
            else:
                return CategoryResult(category="uncategorized", confidence=0.0)

        # 4. Parse and cache result
        result = self._parse_category(response.content)
        await self._cache.set(description, amount, result)

        return result
