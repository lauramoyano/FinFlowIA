"""Parsing and provider-fallback tests for the non-categorization AIService methods.

The LLM is always mocked: these tests pin down how raw model output is turned
into typed results, and how the service degrades when providers fail.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.ai.cache import LLMCache
from src.modules.ai.providers.base import LLMProviderError, LLMResponse
from src.modules.ai.service import AIService

TODAY = date(2026, 11, 25)


def _response(content: str) -> LLMResponse:
    return LLMResponse(content=content, tokens_input=1, tokens_output=1, model="m", provider="p")


def _service(content: str | None = None, *, fallback_content: str | None = None,
             primary_fails: bool = False, fallback_fails: bool = False,
             with_fallback: bool = True) -> AIService:
    primary = AsyncMock()
    if primary_fails:
        primary.complete.side_effect = LLMProviderError("down")
    else:
        primary.complete.return_value = _response(content or "{}")

    fallback = None
    if with_fallback:
        fallback = AsyncMock()
        if fallback_fails:
            fallback.complete.side_effect = LLMProviderError("down too")
        else:
            fallback.complete.return_value = _response(fallback_content or content or "{}")

    cache = AsyncMock(spec=LLMCache)
    cache.get.return_value = None
    return AIService(primary=primary, fallback=fallback, cache=cache)


# --------------------------------------------------------------------- helpers
def test_extract_json_block_strips_fences() -> None:
    svc = _service()
    assert svc._extract_json_block('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert svc._extract_json_block('  {"a": 1}  ') == '{"a": 1}'


def test_parse_category_clamps_and_validates() -> None:
    svc = _service()
    result = svc._parse_category('{"category": "FOOD", "confidence": 3}')
    assert (result.category, result.confidence) == ("food", 1.0)
    assert svc._parse_category('{"category": "nonsense", "confidence": 0.4}').category == "other"
    assert svc._parse_category("not json").category == "other"


# ------------------------------------------------------------- extraction
class TestParseExtraction:
    def test_valid_expense(self) -> None:
        raw = (
            '{"description": " nafta ", "amount": 500, "transaction_type": "expense",'
            ' "category": "transport", "transaction_date": "2026-11-20", "confidence": 0.9}'
        )
        result = _service()._parse_extraction(raw, TODAY)
        assert result.amount == Decimal("500")
        assert result.description == "nafta"
        assert result.transaction_type == "expense"
        assert result.transaction_date == date(2026, 11, 20)
        assert result.error is None

    def test_model_error_is_propagated(self) -> None:
        result = _service()._parse_extraction('{"error": "not_a_transaction"}', TODAY)
        assert result.error == "not_a_transaction"
        assert result.amount is None

    def test_missing_amount(self) -> None:
        result = _service()._parse_extraction('{"description": "x"}', TODAY)
        assert result.error == "no_amount"

    def test_bad_values_fall_back_to_defaults(self) -> None:
        raw = (
            '{"amount": "10", "transaction_type": "weird", "category": "zzz",'
            ' "transaction_date": "ayer", "confidence": 9}'
        )
        result = _service()._parse_extraction(raw, TODAY)
        assert result.transaction_type is None
        assert result.category == "other"
        assert result.transaction_date == TODAY
        assert result.confidence == 1.0
        assert result.description == "Transacción"

    def test_unparseable(self) -> None:
        assert _service()._parse_extraction("garbage", TODAY).error == "parse_failed"

    @pytest.mark.asyncio
    async def test_provider_outage(self) -> None:
        svc = _service(primary_fails=True, fallback_fails=True)
        assert (await svc.parse_transaction_text("hola", TODAY)).error == "provider_unavailable"
        svc = _service(primary_fails=True, with_fallback=False)
        assert (await svc.parse_transaction_text("hola", TODAY)).error == "provider_unavailable"

    @pytest.mark.asyncio
    async def test_fallback_is_used_when_primary_fails(self) -> None:
        svc = _service(primary_fails=True, fallback_content='{"amount": 7}')
        result = await svc.parse_transaction_text("gasté 7", TODAY)
        assert result.amount == Decimal("7")


# --------------------------------------------------------- production estimate
class TestParseProductionEstimate:
    def test_quantity_items(self) -> None:
        raw = '{"items": [{"product_name": " Tortas ", "quantity": 10}, {"product_name": "x", "quantity": 0}]}'
        result = _service()._parse_production_estimate(raw)
        assert [(i.product_name, i.quantity) for i in result.items] == [("tortas", 10)]

    def test_no_items(self) -> None:
        assert _service()._parse_production_estimate('{"items": []}').error == "no_items"

    def test_sales_goal_with_product_list(self) -> None:
        raw = '{"mode": "sales_goal", "sales_goal": 2000000, "product_names": ["tortas", "alfajores"]}'
        goal = _service()._parse_production_estimate(raw).sales_goal
        assert goal is not None
        assert goal.amount == Decimal("2000000")
        assert goal.product_names == ["tortas", "alfajores"]

    def test_sales_goal_accepts_legacy_single_name(self) -> None:
        raw = '{"mode": "sales_goal", "sales_goal": 100, "product_name": "tortas"}'
        goal = _service()._parse_production_estimate(raw).sales_goal
        assert goal is not None and goal.product_names == ["tortas"]

    def test_sales_goal_without_amount_or_non_positive(self) -> None:
        svc = _service()
        assert svc._parse_production_estimate('{"mode": "sales_goal"}').error == "no_items"
        assert svc._parse_production_estimate('{"mode": "sales_goal", "sales_goal": 0}').error == "no_items"

    def test_error_and_garbage(self) -> None:
        svc = _service()
        assert svc._parse_production_estimate('{"error": "unclear"}').error == "unclear"
        assert svc._parse_production_estimate("garbage").error == "parse_failed"

    @pytest.mark.asyncio
    async def test_flow_and_outage(self) -> None:
        ok = _service('{"items": [{"product_name": "tortas", "quantity": 3}]}')
        assert (await ok.parse_production_estimate_text("3 tortas")).items[0].quantity == 3
        down = _service(primary_fails=True, fallback_fails=True)
        assert (await down.parse_production_estimate_text("x")).error == "provider_unavailable"
        no_fb = _service(primary_fails=True, with_fallback=False)
        assert (await no_fb.parse_production_estimate_text("x")).error == "provider_unavailable"
        via_fb = _service(primary_fails=True, fallback_content='{"items": [{"product_name": "a", "quantity": 1}]}')
        assert (await via_fb.parse_production_estimate_text("x")).items


# ------------------------------------------------------------- sale amount
class TestParseSaleAmount:
    def test_valid(self) -> None:
        assert _service()._parse_sale_amount('{"amount": 5000}').amount == Decimal("5000")

    def test_invalid_variants(self) -> None:
        svc = _service()
        assert svc._parse_sale_amount('{"amount": -1}').error == "no_amount"
        assert svc._parse_sale_amount('{"amount": "abc"}').error == "no_amount"
        assert svc._parse_sale_amount("{}").error == "no_amount"
        assert svc._parse_sale_amount('{"error": "x"}').error == "x"
        assert svc._parse_sale_amount("garbage").error == "parse_failed"

    @pytest.mark.asyncio
    async def test_flow_and_outage(self) -> None:
        assert (await _service('{"amount": 9}').parse_sale_amount_text("cobré 9")).amount == Decimal("9")
        assert (await _service(primary_fails=True, fallback_fails=True)
                .parse_sale_amount_text("x")).error == "provider_unavailable"
        assert (await _service(primary_fails=True, with_fallback=False)
                .parse_sale_amount_text("x")).error == "provider_unavailable"
        assert (await _service(primary_fails=True, fallback_content='{"amount": 4}')
                .parse_sale_amount_text("x")).amount == Decimal("4")


# ---------------------------------------------------------- recommendation costs
class TestParseRecommendationCosts:
    def test_valid_and_partial(self) -> None:
        raw = '{"insumos_cost": 1000, "transporte_cost": 200, "ayudante_cost": 0, "gastos_adicionales": "x"}'
        costs = _service()._parse_recommendation_costs(raw)
        assert costs.insumos_cost == Decimal("1000")
        assert costs.transporte_cost == Decimal("200")
        assert costs.ayudante_cost is None  # zero means "not mentioned"
        assert costs.gastos_adicionales is None  # unparseable
        assert costs.servicios_publicos_cost is None

    def test_garbage_degrades_to_empty(self) -> None:
        assert _service()._parse_recommendation_costs("garbage").insumos_cost is None

    @pytest.mark.asyncio
    async def test_flow_and_outage_degrade_to_no_costs(self) -> None:
        got = await _service('{"insumos_cost": 50}').parse_recommendation_costs_text("50 insumos")
        assert got.insumos_cost == Decimal("50")
        for svc in (_service(primary_fails=True, fallback_fails=True),
                    _service(primary_fails=True, with_fallback=False)):
            assert (await svc.parse_recommendation_costs_text("x")).insumos_cost is None
        via_fb = _service(primary_fails=True, fallback_content='{"insumos_cost": 5}')
        assert (await via_fb.parse_recommendation_costs_text("x")).insumos_cost == Decimal("5")


# ------------------------------------------------------------- period summary
class TestParsePeriodSummary:
    def test_single(self) -> None:
        result = _service()._parse_period_summary('{"mode": "single", "period": {"type": "this_month"}}')
        assert result.mode == "single"
        assert result.period is not None and result.period.type == "this_month"
        assert result.compare_period is None

    def test_comparison_with_month_year(self) -> None:
        raw = (
            '{"mode": "comparison", "period": {"type": "month", "month": 10, "year": 2026},'
            ' "compare_period": {"type": "last_month"}}'
        )
        result = _service()._parse_period_summary(raw)
        assert result.mode == "comparison"
        assert result.period is not None and (result.period.month, result.period.year) == (10, 2026)
        assert result.compare_period is not None

    def test_unknown_mode_defaults_to_single(self) -> None:
        raw = '{"mode": "weird", "period": {"type": "today"}}'
        assert _service()._parse_period_summary(raw).mode == "single"

    def test_missing_period_error_and_garbage(self) -> None:
        svc = _service()
        assert svc._parse_period_summary("{}").error == "no_period"
        assert svc._parse_period_summary('{"period": {"month": 1}}').error == "no_period"
        assert svc._parse_period_summary('{"error": "x"}').error == "x"
        assert svc._parse_period_summary("garbage").error == "parse_failed"

    @pytest.mark.asyncio
    async def test_flow_and_outage(self) -> None:
        ok = _service('{"period": {"type": "today"}}')
        assert (await ok.parse_period_summary_text("hoy")).period is not None
        assert (await _service(primary_fails=True, fallback_fails=True)
                .parse_period_summary_text("x")).error == "provider_unavailable"
        assert (await _service(primary_fails=True, with_fallback=False)
                .parse_period_summary_text("x")).error == "provider_unavailable"
        assert (await _service(primary_fails=True, fallback_content='{"period": {"type": "today"}}')
                .parse_period_summary_text("x")).period is not None


# ------------------------------------------------------------- categorization
class TestCategorizeFallback:
    @pytest.mark.asyncio
    async def test_cache_hit_short_circuits(self) -> None:
        svc = _service('{"category": "food", "confidence": 0.9}')
        cached = svc._parse_category('{"category": "rent", "confidence": 0.8}')
        svc._cache.get.return_value = cached
        assert (await svc.categorize_transaction("alquiler", Decimal("1"))).category == "rent"
        svc._primary.complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_then_uncategorized(self) -> None:
        via_fb = _service(primary_fails=True, fallback_content='{"category": "food", "confidence": 0.7}')
        assert (await via_fb.categorize_transaction("pan", Decimal("1"))).category == "food"
        down = _service(primary_fails=True, fallback_fails=True)
        assert (await down.categorize_transaction("pan", Decimal("1"))).category == "uncategorized"
        no_fb = _service(primary_fails=True, with_fallback=False)
        assert (await no_fb.categorize_transaction("pan", Decimal("1"))).category == "uncategorized"
