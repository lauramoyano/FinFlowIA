from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.ai.schemas import ParsedTransactionResult
from src.modules.ai.service import AIService
from src.modules.transactions.categorizer import TransactionTextParser


@pytest.fixture
def mock_ai_service() -> AsyncMock:
    return AsyncMock(spec=AIService)


class TestTransactionTextParser:
    @pytest.mark.asyncio
    async def test_parse_returns_result_from_ai_service(self, mock_ai_service: AsyncMock) -> None:
        mock_ai_service.parse_transaction_text.return_value = ParsedTransactionResult(
            description="Nafta",
            amount=Decimal("500.00"),
            transaction_type="expense",
            transaction_date=date(2026, 10, 11),
            category="transport",
            confidence=0.9,
        )
        parser = TransactionTextParser(ai_service=mock_ai_service)

        result = await parser.parse("gasté 500 en nafta ayer")

        assert result.category == "transport"
        assert result.amount == Decimal("500.00")
        assert result.error is None
        mock_ai_service.parse_transaction_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_returns_parse_failed_when_ai_service_raises(
        self, mock_ai_service: AsyncMock
    ) -> None:
        mock_ai_service.parse_transaction_text.side_effect = RuntimeError("boom")
        parser = TransactionTextParser(ai_service=mock_ai_service)

        result = await parser.parse("algo")

        assert result.error == "parse_failed"
        assert result.amount is None
