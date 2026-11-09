from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.ai.cache import LLMCache
from src.modules.ai.providers.base import LLMProviderError, LLMResponse
from src.modules.ai.schemas import CategoryResult
from src.modules.ai.service import AIService


@pytest.fixture
def mock_primary() -> AsyncMock:
    mock = AsyncMock()
    mock.complete.return_value = LLMResponse(
        content='{"category": "food", "confidence": 0.95}',
        tokens_input=50,
        tokens_output=10,
        model="claude-haiku-4-5-20251001",
        provider="anthropic",
    )
    return mock


@pytest.fixture
def mock_fallback() -> AsyncMock:
    mock = AsyncMock()
    mock.complete.return_value = LLMResponse(
        content='{"category": "other", "confidence": 0.5}',
        tokens_input=50,
        tokens_output=10,
        model="gpt-4o-mini",
        provider="openai",
    )
    return mock


@pytest.fixture
def mock_cache() -> AsyncMock:
    mock = AsyncMock(spec=LLMCache)
    mock.get.return_value = None  # cache miss by default
    return mock


@pytest.fixture
def ai_service(mock_primary: AsyncMock, mock_fallback: AsyncMock, mock_cache: AsyncMock) -> AIService:
    return AIService(primary=mock_primary, fallback=mock_fallback, cache=mock_cache)


class TestAIService:
    @pytest.mark.asyncio
    async def test_categorize_returns_result_from_primary(
        self,
        ai_service: AIService,
        mock_primary: AsyncMock,
    ) -> None:
        result = await ai_service.categorize_transaction(
            description="Almuerzo restaurante",
            amount=Decimal("25.00"),
        )
        assert result.category == "food"
        assert result.confidence == 0.95
        mock_primary.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_categorize_uses_cache_when_available(
        self,
        ai_service: AIService,
        mock_primary: AsyncMock,
        mock_cache: AsyncMock,
    ) -> None:
        mock_cache.get.return_value = CategoryResult(
            category="transport", confidence=0.88, from_cache=True
        )
        result = await ai_service.categorize_transaction(
            description="Uber",
            amount=Decimal("15.00"),
        )
        assert result.category == "transport"
        assert result.from_cache is True
        mock_primary.complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_categorize_falls_back_when_primary_fails(
        self,
        ai_service: AIService,
        mock_primary: AsyncMock,
        mock_fallback: AsyncMock,
    ) -> None:
        mock_primary.complete.side_effect = LLMProviderError("API timeout")
        result = await ai_service.categorize_transaction(
            description="Test transaction",
            amount=Decimal("100.00"),
        )
        assert result.category == "other"
        mock_fallback.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_categorize_returns_uncategorized_when_all_providers_fail(
        self,
        mock_cache: AsyncMock,
        mock_primary: AsyncMock,
        mock_fallback: AsyncMock,
    ) -> None:
        mock_primary.complete.side_effect = LLMProviderError("Primary failed")
        mock_fallback.complete.side_effect = LLMProviderError("Fallback failed")

        service = AIService(primary=mock_primary, fallback=mock_fallback, cache=mock_cache)
        result = await service.categorize_transaction(
            description="Mystery transaction",
            amount=Decimal("50.00"),
        )
        assert result.category == "uncategorized"
        assert result.confidence == 0.0


class TestAIServiceParseTransactionText:
    @pytest.mark.asyncio
    async def test_parse_returns_fields_from_primary(
        self,
        ai_service: AIService,
        mock_primary: AsyncMock,
    ) -> None:
        mock_primary.complete.return_value = LLMResponse(
            content=(
                '{"description": "Nafta", "amount": 500.00, "transaction_type": "expense", '
                '"transaction_date": "2026-10-11", "category": "transport", "confidence": 0.9}'
            ),
            tokens_input=60,
            tokens_output=20,
            model="claude-haiku-4-5-20251001",
            provider="anthropic",
        )
        result = await ai_service.parse_transaction_text(
            text="gasté 500 en nafta ayer", today=date(2026, 10, 12)
        )
        assert result.description == "Nafta"
        assert result.amount == Decimal("500.00")
        assert result.transaction_type == "expense"
        assert result.transaction_date == date(2026, 10, 11)
        assert result.category == "transport"
        assert result.error is None
        mock_primary.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_does_not_use_cache(
        self,
        ai_service: AIService,
        mock_cache: AsyncMock,
        mock_primary: AsyncMock,
    ) -> None:
        mock_primary.complete.return_value = LLMResponse(
            content=(
                '{"description": "Venta", "amount": 1000, "transaction_type": "income", '
                '"transaction_date": "2026-10-12", "category": "sales", "confidence": 0.8}'
            ),
            tokens_input=40,
            tokens_output=15,
            model="claude-haiku-4-5-20251001",
            provider="anthropic",
        )
        await ai_service.parse_transaction_text(text="cobré 1000 de una venta", today=date(2026, 10, 12))
        mock_cache.get.assert_not_called()
        mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_parse_returns_no_amount_error_when_model_reports_it(
        self,
        ai_service: AIService,
        mock_primary: AsyncMock,
    ) -> None:
        mock_primary.complete.return_value = LLMResponse(
            content='{"error": "no_amount"}',
            tokens_input=20,
            tokens_output=5,
            model="claude-haiku-4-5-20251001",
            provider="anthropic",
        )
        result = await ai_service.parse_transaction_text(text="hola", today=date(2026, 10, 12))
        assert result.error == "no_amount"
        assert result.amount is None

    @pytest.mark.asyncio
    async def test_parse_falls_back_when_primary_fails(
        self,
        ai_service: AIService,
        mock_primary: AsyncMock,
        mock_fallback: AsyncMock,
    ) -> None:
        mock_primary.complete.side_effect = LLMProviderError("API timeout")
        mock_fallback.complete.return_value = LLMResponse(
            content=(
                '{"description": "Compra", "amount": 200, "transaction_type": "expense", '
                '"transaction_date": "2026-10-12", "category": "other", "confidence": 0.6}'
            ),
            tokens_input=40,
            tokens_output=15,
            model="gpt-4o-mini",
            provider="openai",
        )
        result = await ai_service.parse_transaction_text(text="pagué 200", today=date(2026, 10, 12))
        assert result.error is None
        assert result.amount == Decimal("200")
        mock_fallback.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_returns_provider_unavailable_when_all_fail(
        self,
        mock_cache: AsyncMock,
        mock_primary: AsyncMock,
        mock_fallback: AsyncMock,
    ) -> None:
        mock_primary.complete.side_effect = LLMProviderError("Primary failed")
        mock_fallback.complete.side_effect = LLMProviderError("Fallback failed")

        service = AIService(primary=mock_primary, fallback=mock_fallback, cache=mock_cache)
        result = await service.parse_transaction_text(text="algo", today=date(2026, 10, 12))
        assert result.error == "provider_unavailable"
