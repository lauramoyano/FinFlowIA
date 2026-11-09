import datetime as real_datetime
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.ai.schemas import ParsedPeriodDescriptor, ParsedPeriodSummaryRequest
from src.modules.ai.service import AIService
from src.modules.orchestrator.agents.period_summary_agent import PeriodSummaryAgent
from src.modules.orchestrator.conversation_store import ConversationState, ConversationStore
from src.modules.reports.repository import ReportRepository

USER_ID = uuid.uuid4()
FROZEN_TODAY = real_datetime.date(2026, 10, 28)


@pytest.fixture
def mock_ai_service() -> AsyncMock:
    return AsyncMock(spec=AIService)


@pytest.fixture
def mock_report_repo() -> AsyncMock:
    return AsyncMock(spec=ReportRepository)


@pytest.fixture
def mock_store() -> AsyncMock:
    return AsyncMock(spec=ConversationStore)


@pytest.fixture
def agent(
    mock_ai_service: AsyncMock, mock_report_repo: AsyncMock, mock_store: AsyncMock
) -> PeriodSummaryAgent:
    return PeriodSummaryAgent(ai_service=mock_ai_service, report_repo=mock_report_repo, store=mock_store)


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch: pytest.MonkeyPatch) -> None:
    """Freeze `date.today()` inside the agent module so period math is deterministic."""
    mock_date_cls = MagicMock(wraps=real_datetime.date)
    mock_date_cls.today.return_value = FROZEN_TODAY
    monkeypatch.setattr(
        "src.modules.orchestrator.agents.period_summary_agent.date", mock_date_cls
    )


def totals(income: str, expenses: str) -> dict:
    return {"total_income": Decimal(income), "total_expenses": Decimal(expenses), "transaction_count": 1}


class TestPeriodSummaryAgent:
    @pytest.mark.asyncio
    async def test_single_period_this_month(
        self, agent: PeriodSummaryAgent, mock_ai_service: AsyncMock, mock_report_repo: AsyncMock
    ) -> None:
        mock_ai_service.parse_period_summary_text.return_value = ParsedPeriodSummaryRequest(
            mode="single", period=ParsedPeriodDescriptor(type="this_month")
        )
        mock_report_repo.get_totals_by_period.return_value = totals("10000", "6000")

        result = await agent.handle("cómo me fue este mes", "conv-1", is_followup=False, user_id=USER_ID)

        assert result.kind == "period_summary_result"
        psr = result.period_summary_result
        assert psr is not None
        assert psr.previous is None
        assert psr.current.label == "este mes"
        assert psr.current.start_date == real_datetime.date(2026, 10, 1)
        assert psr.current.end_date == real_datetime.date(2026, 10, 31)
        assert psr.current.total_income == Decimal("10000")
        assert psr.current.total_expenses == Decimal("6000")
        assert psr.current.balance == Decimal("4000")
        mock_report_repo.get_totals_by_period.assert_called_once_with(
            user_id=USER_ID,
            start_date=real_datetime.date(2026, 10, 1),
            end_date=real_datetime.date(2026, 10, 31),
        )

    @pytest.mark.asyncio
    async def test_comparison_with_explicit_compare_period(
        self, agent: PeriodSummaryAgent, mock_ai_service: AsyncMock, mock_report_repo: AsyncMock
    ) -> None:
        mock_ai_service.parse_period_summary_text.return_value = ParsedPeriodSummaryRequest(
            mode="comparison",
            period=ParsedPeriodDescriptor(type="this_month"),
            compare_period=ParsedPeriodDescriptor(type="specific_month", month=9, year=2026),
        )
        mock_report_repo.get_totals_by_period.side_effect = [
            totals("10000", "6000"),
            totals("8000", "7000"),
        ]

        result = await agent.handle(
            "comparame este mes con septiembre", "conv-1", is_followup=False, user_id=USER_ID
        )

        psr = result.period_summary_result
        assert psr is not None
        assert psr.previous is not None
        assert psr.previous.label == "septiembre 2026"
        assert psr.previous.start_date == real_datetime.date(2026, 9, 1)
        assert psr.previous.end_date == real_datetime.date(2026, 9, 30)
        assert psr.previous.balance == Decimal("1000")

    @pytest.mark.asyncio
    async def test_comparison_without_explicit_compare_period_uses_previous_month(
        self, agent: PeriodSummaryAgent, mock_ai_service: AsyncMock, mock_report_repo: AsyncMock
    ) -> None:
        mock_ai_service.parse_period_summary_text.return_value = ParsedPeriodSummaryRequest(
            mode="comparison", period=ParsedPeriodDescriptor(type="this_month"), compare_period=None
        )
        mock_report_repo.get_totals_by_period.side_effect = [
            totals("10000", "6000"),
            totals("9000", "5000"),
        ]

        result = await agent.handle(
            "comparame este mes con el anterior", "conv-1", is_followup=False, user_id=USER_ID
        )

        psr = result.period_summary_result
        assert psr is not None
        assert psr.previous is not None
        assert psr.previous.label == "septiembre 2026"
        assert psr.previous.start_date == real_datetime.date(2026, 9, 1)
        assert psr.previous.end_date == real_datetime.date(2026, 9, 30)

    @pytest.mark.asyncio
    async def test_specific_month_defaults_year_to_current(
        self, agent: PeriodSummaryAgent, mock_ai_service: AsyncMock, mock_report_repo: AsyncMock
    ) -> None:
        mock_ai_service.parse_period_summary_text.return_value = ParsedPeriodSummaryRequest(
            mode="single", period=ParsedPeriodDescriptor(type="specific_month", month=1, year=None)
        )
        mock_report_repo.get_totals_by_period.return_value = totals("5000", "3000")

        result = await agent.handle("cómo me fue en enero", "conv-1", is_followup=False, user_id=USER_ID)

        psr = result.period_summary_result
        assert psr is not None
        assert psr.current.label == "enero 2026"
        assert psr.current.start_date == real_datetime.date(2026, 1, 1)
        assert psr.current.end_date == real_datetime.date(2026, 1, 31)

    @pytest.mark.asyncio
    async def test_no_period_asks_followup_and_saves_state(
        self, agent: PeriodSummaryAgent, mock_ai_service: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_ai_service.parse_period_summary_text.return_value = ParsedPeriodSummaryRequest(
            error="no_period"
        )

        result = await agent.handle("quiero un resumen", "conv-1", is_followup=False, user_id=USER_ID)

        assert result.kind == "question"
        assert result.message == "ask_period"
        mock_store.set.assert_called_once()
        saved_conversation_id, saved_state = mock_store.set.call_args.args
        assert saved_conversation_id == "conv-1"
        assert saved_state == ConversationState(
            agent="period_summary", turns=1, payload={"awaiting": "period", "accumulated_text": "quiero un resumen"}
        )

    @pytest.mark.asyncio
    async def test_followup_combines_text_and_resolves(
        self, agent: PeriodSummaryAgent, mock_ai_service: AsyncMock, mock_report_repo: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="period_summary", turns=1, payload={"awaiting": "period", "accumulated_text": "quiero un resumen"}
        )
        mock_ai_service.parse_period_summary_text.return_value = ParsedPeriodSummaryRequest(
            mode="single", period=ParsedPeriodDescriptor(type="this_month")
        )
        mock_report_repo.get_totals_by_period.return_value = totals("1000", "500")

        result = await agent.handle("de este mes", "conv-1", is_followup=True, user_id=USER_ID)

        mock_ai_service.parse_period_summary_text.assert_called_once_with("quiero un resumen. de este mes")
        assert result.kind == "period_summary_result"
        mock_store.clear.assert_called_once_with("conv-1")

    @pytest.mark.asyncio
    async def test_retry_limit_exceeded_returns_error(
        self, agent: PeriodSummaryAgent, mock_ai_service: AsyncMock, mock_store: AsyncMock
    ) -> None:
        mock_store.get.return_value = ConversationState(
            agent="period_summary",
            turns=2,
            payload={"awaiting": "period", "accumulated_text": "quiero un resumen. no sé de cuándo"},
        )
        mock_ai_service.parse_period_summary_text.return_value = ParsedPeriodSummaryRequest(
            error="no_period"
        )

        result = await agent.handle("sigo sin saber", "conv-1", is_followup=True, user_id=USER_ID)

        assert result.kind == "error"
        assert result.error_code == "follow_up_retry_limit"
        mock_store.set.assert_not_called()
        mock_store.clear.assert_called_once_with("conv-1")
