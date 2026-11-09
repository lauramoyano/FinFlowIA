from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.ai.schemas import ParsedTransactionResult
from src.modules.orchestrator.agents.classification_agent import ClassificationAgent
from src.modules.orchestrator.conversation_store import ConversationState, ConversationStore
from src.modules.transactions.categorizer import TransactionTextParser


@pytest.fixture
def mock_parser() -> AsyncMock:
    return AsyncMock(spec=TransactionTextParser)


@pytest.fixture
def mock_store() -> AsyncMock:
    return AsyncMock(spec=ConversationStore)


@pytest.fixture
def agent(mock_parser: AsyncMock, mock_store: AsyncMock) -> ClassificationAgent:
    return ClassificationAgent(parser=mock_parser, store=mock_store)


class TestClassificationAgent:
    @pytest.mark.asyncio
    async def test_missing_amount_asks_followup_and_saves_state(
        self, agent: ClassificationAgent, mock_parser: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_parser.parse.return_value = ParsedTransactionResult(
            description="",
            amount=None,
            transaction_type=None,
            transaction_date=date(2026, 10, 18),
            category="uncategorized",
            confidence=0.0,
            error="no_amount",
        )

        result = await agent.handle("gasté en nafta", "conv-1", is_followup=False)

        assert result.kind == "question"
        assert result.message == "ask_amount"
        mock_store.set.assert_called_once()
        saved_conversation_id, saved_state = mock_store.set.call_args.args
        assert saved_conversation_id == "conv-1"
        assert saved_state == ConversationState(
            agent="classification", turns=1, payload={"accumulated_text": "gasté en nafta"}
        )
        mock_store.clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_followup_combines_text_and_confirms_when_amount_found(
        self, agent: ClassificationAgent, mock_parser: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="classification", turns=1, payload={"accumulated_text": "gasté en nafta"}
        )
        mock_parser.parse.return_value = ParsedTransactionResult(
            description="Nafta",
            amount=Decimal("500.00"),
            transaction_type="expense",
            transaction_date=date(2026, 10, 18),
            category="transport",
            confidence=0.9,
        )

        result = await agent.handle("500", "conv-1", is_followup=True)

        mock_parser.parse.assert_called_once_with("gasté en nafta. 500")
        assert result.kind == "confirm_transaction"
        assert result.draft is not None
        assert result.draft.amount == Decimal("500.00")
        mock_store.clear.assert_called_once_with("conv-1")

    @pytest.mark.asyncio
    async def test_gives_up_after_max_followup_turns(
        self, agent: ClassificationAgent, mock_parser: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="classification", turns=2, payload={"accumulated_text": "gasté en algo. no se cuanto"}
        )
        mock_parser.parse.return_value = ParsedTransactionResult(
            description="",
            amount=None,
            transaction_type=None,
            transaction_date=date(2026, 10, 18),
            category="uncategorized",
            confidence=0.0,
            error="no_amount",
        )

        result = await agent.handle("todavia no se", "conv-1", is_followup=True)

        assert result.kind == "error"
        assert result.error_code == "follow_up_retry_limit"
        mock_store.set.assert_not_called()
        mock_store.clear.assert_called_once_with("conv-1")

    @pytest.mark.asyncio
    async def test_non_amount_error_is_returned_as_is(
        self, agent: ClassificationAgent, mock_parser: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_parser.parse.return_value = ParsedTransactionResult(
            description="",
            amount=None,
            transaction_type=None,
            transaction_date=date(2026, 10, 18),
            category="uncategorized",
            confidence=0.0,
            error="not_a_transaction",
        )

        result = await agent.handle("hola como estas", "conv-1", is_followup=False)

        assert result.kind == "error"
        assert result.error_code == "not_a_transaction"
