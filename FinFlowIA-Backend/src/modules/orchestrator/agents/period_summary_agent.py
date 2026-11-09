import uuid
from datetime import date, timedelta
from decimal import Decimal

import structlog

from src.modules.ai.schemas import ParsedPeriodDescriptor
from src.modules.ai.service import AIService
from src.modules.orchestrator.agents.types import AgentResult, PeriodSummaryData, PeriodSummaryResult
from src.modules.orchestrator.conversation_store import ConversationState, ConversationStore
from src.modules.reports.repository import ReportRepository
from src.shared.utils.datetime_utils import add_months, end_of_month, start_of_month

logger = structlog.get_logger(__name__)

MAX_FOLLOWUP_TURNS = 3

MONTH_NAMES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def _resolve_period(descriptor: ParsedPeriodDescriptor, today: date) -> tuple[date, date, str]:
    """Deterministically turn a relative period descriptor into concrete dates + a label."""
    if descriptor.type == "last_month":
        start = add_months(start_of_month(today), -1)
        return start, end_of_month(start), "el mes pasado"
    if descriptor.type == "this_year":
        return date(today.year, 1, 1), date(today.year, 12, 31), f"este año ({today.year})"
    if descriptor.type == "last_year":
        year = today.year - 1
        return date(year, 1, 1), date(year, 12, 31), str(year)
    if descriptor.type == "specific_month":
        year = descriptor.year or today.year
        month = descriptor.month or today.month
        start = date(year, month, 1)
        return start, end_of_month(start), f"{MONTH_NAMES_ES[month]} {year}"
    # "this_month" and any unrecognized type default to the current month.
    return start_of_month(today), end_of_month(today), "este mes"


def _previous_comparable_period(start: date, end: date) -> tuple[date, date, str]:
    """
    The period immediately before [start, end], same "shape" — one month
    back for a month-aligned range, one year back for a year-aligned range,
    or the same-length window right before it otherwise. Computed purely
    from resolved dates, so it works regardless of how the original period
    was expressed (relative keyword or a specific month).
    """
    if start.day == 1 and end == end_of_month(start):
        prev_start = add_months(start, -1)
        return prev_start, end_of_month(prev_start), f"{MONTH_NAMES_ES[prev_start.month]} {prev_start.year}"
    if start.month == 1 and start.day == 1 and end.month == 12 and end.day == 31:
        year = start.year - 1
        return date(year, 1, 1), date(year, 12, 31), str(year)
    length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=length - 1)
    return prev_start, prev_end, f"{prev_start.isoformat()} a {prev_end.isoformat()}"


class PeriodSummaryAgent:
    """
    Agent 2: conversational period summary and comparison. Resolves a
    relative period ("este mes", "octubre", ...) into concrete dates and
    reuses ReportRepository.get_totals_by_period — the same aggregation
    the dashboard already uses — instead of a parallel query path. The LLM
    only classifies which period(s) the user means; it never computes a
    total itself.
    """

    def __init__(
        self,
        ai_service: AIService,
        report_repo: ReportRepository,
        store: ConversationStore,
    ) -> None:
        self._ai_service = ai_service
        self._report_repo = report_repo
        self._store = store

    async def handle(
        self, text: str, conversation_id: str, is_followup: bool, user_id: uuid.UUID
    ) -> AgentResult:
        if is_followup:
            state = await self._store.get(conversation_id)
            assert state is not None, "caller must only pass is_followup=True when state exists"
            turns = state.turns + 1
            accumulated = f"{state.payload['accumulated_text']}. {text}"
            return await self._extract_and_resolve(accumulated, conversation_id, turns, user_id)

        return await self._extract_and_resolve(text, conversation_id, 1, user_id)

    async def _extract_and_resolve(
        self, text: str, conversation_id: str, turns: int, user_id: uuid.UUID
    ) -> AgentResult:
        parsed = await self._ai_service.parse_period_summary_text(text)

        if parsed.error or parsed.period is None:
            if turns < MAX_FOLLOWUP_TURNS:
                await self._store.set(
                    conversation_id,
                    ConversationState(
                        agent="period_summary",
                        turns=turns,
                        payload={"awaiting": "period", "accumulated_text": text},
                    ),
                )
                return AgentResult(kind="question", message="ask_period")
            await self._store.clear(conversation_id)
            logger.info("period_summary_agent_gave_up", turns=turns)
            return AgentResult(kind="error", error_code="follow_up_retry_limit")

        await self._store.clear(conversation_id)
        today = date.today()
        start, end, label = _resolve_period(parsed.period, today)
        current = await self._build_period_data(user_id, start, end, label)

        previous = None
        if parsed.mode == "comparison":
            if parsed.compare_period is not None:
                prev_start, prev_end, prev_label = _resolve_period(parsed.compare_period, today)
            else:
                prev_start, prev_end, prev_label = _previous_comparable_period(start, end)
            previous = await self._build_period_data(user_id, prev_start, prev_end, prev_label)

        return AgentResult(
            kind="period_summary_result",
            period_summary_result=PeriodSummaryResult(current=current, previous=previous),
        )

    async def _build_period_data(
        self, user_id: uuid.UUID, start: date, end: date, label: str
    ) -> PeriodSummaryData:
        totals = await self._report_repo.get_totals_by_period(
            user_id=user_id, start_date=start, end_date=end
        )
        income = Decimal(str(totals["total_income"]))
        expenses = Decimal(str(totals["total_expenses"]))
        return PeriodSummaryData(
            label=label,
            start_date=start,
            end_date=end,
            total_income=income,
            total_expenses=expenses,
            balance=income - expenses,
        )
