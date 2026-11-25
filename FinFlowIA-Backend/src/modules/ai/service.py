import json
from datetime import date
from decimal import Decimal, InvalidOperation

import structlog

from src.modules.ai.cache import LLMCache
from src.modules.ai.prompts.categorization_v2 import SYSTEM_PROMPT, build_prompt_v2
from src.modules.ai.prompts.extraction_v1 import SYSTEM_PROMPT as EXTRACTION_SYSTEM_PROMPT
from src.modules.ai.prompts.extraction_v1 import build_prompt as build_extraction_prompt
from src.modules.ai.prompts.production_estimate_v1 import (
    SYSTEM_PROMPT as PRODUCTION_ESTIMATE_SYSTEM_PROMPT,
)
from src.modules.ai.prompts.production_estimate_v1 import (
    build_prompt as build_production_estimate_prompt,
)
from src.modules.ai.prompts.financial_recommendation_v1 import (
    COSTS_SYSTEM_PROMPT,
    SALE_AMOUNT_SYSTEM_PROMPT,
    build_costs_prompt,
    build_sale_amount_prompt,
)
from src.modules.ai.prompts.period_summary_v1 import SYSTEM_PROMPT as PERIOD_SUMMARY_SYSTEM_PROMPT
from src.modules.ai.prompts.period_summary_v1 import build_prompt as build_period_summary_prompt
from src.modules.ai.providers.base import LLMProvider, LLMProviderError
from src.shared.utils.text_utils import split_product_names
from src.modules.ai.schemas import (
    CategoryResult,
    ParsedPeriodDescriptor,
    ParsedPeriodSummaryRequest,
    ParsedProductionEstimateItem,
    ParsedProductionEstimateResult,
    ParsedRecommendationCosts,
    ParsedSaleAmountResult,
    ParsedSalesGoal,
    ParsedTransactionResult,
)

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

    def _extract_json_block(self, content: str) -> str:
        """Strip markdown code-block fences from an LLM response, if present."""
        json_str = content.strip()
        if "```" in json_str:
            json_str = json_str.split("```")[1].strip()
            if json_str.startswith("json"):
                json_str = json_str[4:].strip()
        return json_str

    def _parse_category(self, content: str) -> CategoryResult:
        """Parse LLM JSON response into a CategoryResult."""
        try:
            json_str = self._extract_json_block(content)
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

    def _parse_extraction(self, content: str, today: date) -> ParsedTransactionResult:
        """Parse LLM JSON response into a ParsedTransactionResult."""
        try:
            json_str = self._extract_json_block(content)
            data = json.loads(json_str)

            if data.get("error"):
                return ParsedTransactionResult(
                    description="",
                    amount=None,
                    transaction_type=None,
                    transaction_date=today,
                    category="uncategorized",
                    confidence=0.0,
                    error=str(data["error"]),
                )

            category = str(data.get("category", "other")).lower()
            if category not in VALID_CATEGORIES:
                category = "other"

            transaction_type = str(data.get("transaction_type", "")).lower()
            if transaction_type not in ("income", "expense"):
                transaction_type = None

            try:
                amount = Decimal(str(data["amount"]))
            except (KeyError, InvalidOperation):
                return ParsedTransactionResult(
                    description="",
                    amount=None,
                    transaction_type=None,
                    transaction_date=today,
                    category="uncategorized",
                    confidence=0.0,
                    error="no_amount",
                )

            try:
                transaction_date = date.fromisoformat(str(data.get("transaction_date", today)))
            except ValueError:
                transaction_date = today

            confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))

            return ParsedTransactionResult(
                description=str(data.get("description", "")).strip() or "Transacción",
                amount=amount,
                transaction_type=transaction_type,
                transaction_date=transaction_date,
                category=category,
                confidence=confidence,
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("extraction_parse_failed", content=content[:100], error=str(e))
            return ParsedTransactionResult(
                description="",
                amount=None,
                transaction_type=None,
                transaction_date=today,
                category="uncategorized",
                confidence=0.0,
                error="parse_failed",
            )

    async def parse_transaction_text(self, text: str, today: date) -> ParsedTransactionResult:
        """
        Parse a free-text chat message (e.g. "gasté 500 en nafta ayer") into
        transaction fields using AI.

        Flow: build prompt → call primary provider → fallback → parse JSON.
        Unlike categorize_transaction, this is not cached — chat messages are
        free text and rarely repeat verbatim, so caching wouldn't pay off.
        """
        full_prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\n{build_extraction_prompt(text, today)}"

        try:
            response = await self._primary.complete(
                prompt=full_prompt,
                # Reasoning-tier models (e.g. gpt-5-nano) spend part of this
                # budget on hidden reasoning tokens before any visible output,
                # so this needs real headroom beyond the ~40-token JSON reply.
                max_tokens=1024,
                temperature=0.0,
            )
        except LLMProviderError as e:
            logger.warning("primary_llm_failed", error=str(e))
            if self._fallback:
                try:
                    response = await self._fallback.complete(
                        prompt=full_prompt,
                        max_tokens=1024,
                        temperature=0.0,
                    )
                except LLMProviderError as fallback_err:
                    logger.error("fallback_llm_failed", error=str(fallback_err))
                    return ParsedTransactionResult(
                        description="",
                        amount=None,
                        transaction_type=None,
                        transaction_date=today,
                        category="uncategorized",
                        confidence=0.0,
                        error="provider_unavailable",
                    )
            else:
                return ParsedTransactionResult(
                    description="",
                    amount=None,
                    transaction_type=None,
                    transaction_date=today,
                    category="uncategorized",
                    confidence=0.0,
                    error="provider_unavailable",
                )

        return self._parse_extraction(response.content, today)

    def _parse_production_estimate(self, content: str) -> ParsedProductionEstimateResult:
        """Parse LLM JSON response into a ParsedProductionEstimateResult."""
        try:
            json_str = self._extract_json_block(content)
            data = json.loads(json_str)

            if data.get("error"):
                return ParsedProductionEstimateResult(error=str(data["error"]))

            # Any unrecognized/missing mode falls back to "quantity" — the
            # original, simpler shape — so an old or slightly-off model
            # response still parses as cost-by-quantity instead of failing.
            if data.get("mode") == "sales_goal":
                try:
                    amount = Decimal(str(data["sales_goal"]))
                except (KeyError, InvalidOperation):
                    return ParsedProductionEstimateResult(error="no_items")
                if amount <= 0:
                    return ParsedProductionEstimateResult(error="no_items")
                raw_names = data.get("product_names")
                if raw_names is None and data.get("product_name"):
                    raw_names = [data["product_name"]]
                if isinstance(raw_names, str):
                    raw_names = [raw_names]
                product_names = split_product_names(", ".join(str(n) for n in raw_names or []))
                return ParsedProductionEstimateResult(
                    sales_goal=ParsedSalesGoal(amount=amount, product_names=product_names)
                )

            items: list[ParsedProductionEstimateItem] = []
            for raw_item in data.get("items", []):
                name = str(raw_item.get("product_name", "")).strip().lower()
                try:
                    quantity = int(raw_item.get("quantity", 0))
                except (TypeError, ValueError):
                    quantity = 0
                if name and quantity > 0:
                    items.append(ParsedProductionEstimateItem(product_name=name, quantity=quantity))

            if not items:
                return ParsedProductionEstimateResult(error="no_items")

            return ParsedProductionEstimateResult(items=items)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("production_estimate_parse_failed", content=content[:100], error=str(e))
            return ParsedProductionEstimateResult(error="parse_failed")

    async def parse_production_estimate_text(self, text: str) -> ParsedProductionEstimateResult:
        """
        Parse a free-text chat message into either a cost-by-quantity
        request (e.g. "cuánto me cuesta hacer 10 tortas" → `items`) or a
        sales-goal request (e.g. "quiero vender 2000000 en la feria" →
        `sales_goal`) using AI.

        Flow: build prompt → call primary provider → fallback → parse JSON.
        Not cached, same reasoning as parse_transaction_text.
        """
        full_prompt = f"{PRODUCTION_ESTIMATE_SYSTEM_PROMPT}\n\n{build_production_estimate_prompt(text)}"

        try:
            response = await self._primary.complete(
                prompt=full_prompt,
                max_tokens=1024,
                temperature=0.0,
            )
        except LLMProviderError as e:
            logger.warning("primary_llm_failed", error=str(e))
            if self._fallback:
                try:
                    response = await self._fallback.complete(
                        prompt=full_prompt,
                        max_tokens=1024,
                        temperature=0.0,
                    )
                except LLMProviderError as fallback_err:
                    logger.error("fallback_llm_failed", error=str(fallback_err))
                    return ParsedProductionEstimateResult(items=[], error="provider_unavailable")
            else:
                return ParsedProductionEstimateResult(items=[], error="provider_unavailable")

        return self._parse_production_estimate(response.content)

    def _parse_sale_amount(self, content: str) -> ParsedSaleAmountResult:
        """Parse LLM JSON response into a ParsedSaleAmountResult."""
        try:
            json_str = self._extract_json_block(content)
            data = json.loads(json_str)

            if data.get("error"):
                return ParsedSaleAmountResult(error=str(data["error"]))

            try:
                amount = Decimal(str(data["amount"]))
            except (KeyError, InvalidOperation):
                return ParsedSaleAmountResult(error="no_amount")

            if amount <= 0:
                return ParsedSaleAmountResult(error="no_amount")

            return ParsedSaleAmountResult(amount=amount)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("sale_amount_parse_failed", content=content[:100], error=str(e))
            return ParsedSaleAmountResult(error="parse_failed")

    async def parse_sale_amount_text(self, text: str) -> ParsedSaleAmountResult:
        """
        Parse a free-text chat message (e.g. "cobré 5000, cómo lo reparto")
        into a sale amount for the financial-recommendation agent.

        Flow: build prompt → call primary provider → fallback → parse JSON.
        Not cached, same reasoning as parse_transaction_text.
        """
        full_prompt = f"{SALE_AMOUNT_SYSTEM_PROMPT}\n\n{build_sale_amount_prompt(text)}"

        try:
            response = await self._primary.complete(prompt=full_prompt, max_tokens=1024, temperature=0.0)
        except LLMProviderError as e:
            logger.warning("primary_llm_failed", error=str(e))
            if self._fallback:
                try:
                    response = await self._fallback.complete(
                        prompt=full_prompt, max_tokens=1024, temperature=0.0
                    )
                except LLMProviderError as fallback_err:
                    logger.error("fallback_llm_failed", error=str(fallback_err))
                    return ParsedSaleAmountResult(error="provider_unavailable")
            else:
                return ParsedSaleAmountResult(error="provider_unavailable")

        return self._parse_sale_amount(response.content)

    def _parse_recommendation_costs(self, content: str) -> ParsedRecommendationCosts:
        """Parse LLM JSON response into a ParsedRecommendationCosts. Never errors out —
        an unparseable or empty reply just means every cost defaults to None (0)."""

        def to_decimal(value: object) -> Decimal | None:
            if value is None:
                return None
            try:
                parsed = Decimal(str(value))
            except InvalidOperation:
                return None
            return parsed if parsed > 0 else None

        try:
            json_str = self._extract_json_block(content)
            data = json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("recommendation_costs_parse_failed", content=content[:100], error=str(e))
            return ParsedRecommendationCosts()

        return ParsedRecommendationCosts(
            insumos_cost=to_decimal(data.get("insumos_cost")),
            transporte_cost=to_decimal(data.get("transporte_cost")),
            ayudante_cost=to_decimal(data.get("ayudante_cost")),
            gastos_adicionales=to_decimal(data.get("gastos_adicionales")),
            servicios_publicos_cost=to_decimal(data.get("servicios_publicos_cost")),
        )

    async def parse_recommendation_costs_text(self, text: str) -> ParsedRecommendationCosts:
        """
        Parse a free-text chat message (e.g. "gasté 1000 en insumos y 200
        en transporte", or "ninguno") into a cost breakdown for the
        financial-recommendation agent.

        Flow: build prompt → call primary provider → fallback → parse JSON.
        Not cached. Unlike other extraction methods, failure at any stage
        (including a provider outage) degrades to "no costs mentioned"
        rather than an error — the reparto can still proceed on the full
        sale amount.
        """
        full_prompt = f"{COSTS_SYSTEM_PROMPT}\n\n{build_costs_prompt(text)}"

        try:
            response = await self._primary.complete(prompt=full_prompt, max_tokens=1024, temperature=0.0)
        except LLMProviderError as e:
            logger.warning("primary_llm_failed", error=str(e))
            if self._fallback:
                try:
                    response = await self._fallback.complete(
                        prompt=full_prompt, max_tokens=1024, temperature=0.0
                    )
                except LLMProviderError as fallback_err:
                    logger.error("fallback_llm_failed", error=str(fallback_err))
                    return ParsedRecommendationCosts()
            else:
                return ParsedRecommendationCosts()

        return self._parse_recommendation_costs(response.content)

    def _parse_period_summary(self, content: str) -> ParsedPeriodSummaryRequest:
        """Parse LLM JSON response into a ParsedPeriodSummaryRequest."""

        def to_descriptor(raw: object) -> ParsedPeriodDescriptor | None:
            if not isinstance(raw, dict):
                return None
            period_type = raw.get("type")
            if not period_type:
                return None
            month = raw.get("month")
            year = raw.get("year")
            return ParsedPeriodDescriptor(
                type=str(period_type),
                month=int(month) if isinstance(month, (int, float)) else None,
                year=int(year) if isinstance(year, (int, float)) else None,
            )

        try:
            json_str = self._extract_json_block(content)
            data = json.loads(json_str)

            if data.get("error"):
                return ParsedPeriodSummaryRequest(error=str(data["error"]))

            period = to_descriptor(data.get("period"))
            if period is None:
                return ParsedPeriodSummaryRequest(error="no_period")

            mode = data.get("mode") if data.get("mode") in ("single", "comparison") else "single"
            compare_period = to_descriptor(data.get("compare_period"))

            return ParsedPeriodSummaryRequest(mode=mode, period=period, compare_period=compare_period)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("period_summary_parse_failed", content=content[:100], error=str(e))
            return ParsedPeriodSummaryRequest(error="parse_failed")

    async def parse_period_summary_text(self, text: str) -> ParsedPeriodSummaryRequest:
        """
        Parse a free-text chat message (e.g. "cómo me fue este mes" or
        "comparame este mes con el anterior") into a period descriptor (or
        two, for a comparison) using AI.

        Flow: build prompt → call primary provider → fallback → parse JSON.
        Not cached, same reasoning as parse_transaction_text.
        """
        full_prompt = f"{PERIOD_SUMMARY_SYSTEM_PROMPT}\n\n{build_period_summary_prompt(text)}"

        try:
            response = await self._primary.complete(prompt=full_prompt, max_tokens=1024, temperature=0.0)
        except LLMProviderError as e:
            logger.warning("primary_llm_failed", error=str(e))
            if self._fallback:
                try:
                    response = await self._fallback.complete(
                        prompt=full_prompt, max_tokens=1024, temperature=0.0
                    )
                except LLMProviderError as fallback_err:
                    logger.error("fallback_llm_failed", error=str(fallback_err))
                    return ParsedPeriodSummaryRequest(error="provider_unavailable")
            else:
                return ParsedPeriodSummaryRequest(error="provider_unavailable")

        return self._parse_period_summary(response.content)
