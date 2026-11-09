from typing import Literal

from pydantic import BaseModel, Field

from src.modules.planning.schemas import FinancialRecommendationResponse
from src.modules.production.schemas import ProductionEstimateResponse, SalesGoalResponse
from src.modules.reports.schemas import PeriodSummaryResponse
from src.modules.transactions.schemas import ParsedTransactionResponse


class OrchestratorMessageRequest(BaseModel):
    """Request schema for sending one chat message to the orchestrator."""

    conversation_id: str | None = None
    text: str = Field(min_length=1, max_length=500)


class OrchestratorMessageResponse(BaseModel):
    """
    Response schema for one orchestrator turn.

    - "question": the agent needs another piece of data; `message` is a
      code (e.g. "ask_amount", "ask_unit_cost") the frontend maps to a
      translated string, interpolated with `message_params` when present
      (e.g. {"product": "torta"}). Reply with the same `conversation_id` to
      continue.
    - "confirm_transaction": `draft` has the full parsed transaction, same
      shape as POST /transactions/parse.
    - "estimate_result": `estimate` has the resolved production cost
      estimate (every item matched to a catalog cost).
    - "sales_goal_result": `sales_goal` has the resolved sales-goal estimate
      (minimum units to sell, insumos investment, projected profit).
    - "financial_recommendation_result": `financial_recommendation` has the
      resolved reparto recommendation (how to split a sale's net amount).
    - "period_summary_result": `period_summary` has the resolved period
      summary (plus a comparison period, if requested).
    - "agent_unavailable": `agent` names a recognized agent with no
      implementation (not currently used — all 4 agents are implemented —
      kept for forward-compatibility with a future 5th agent).
    - "error": `error_code` mirrors ParsedTransactionResponse.error, plus
      "follow_up_retry_limit" when the follow-up loop gives up.
    """

    conversation_id: str
    kind: Literal[
        "question",
        "confirm_transaction",
        "estimate_result",
        "sales_goal_result",
        "financial_recommendation_result",
        "period_summary_result",
        "agent_unavailable",
        "error",
    ]
    message: str | None = None
    message_params: dict[str, str] | None = None
    draft: ParsedTransactionResponse | None = None
    estimate: ProductionEstimateResponse | None = None
    sales_goal: SalesGoalResponse | None = None
    financial_recommendation: FinancialRecommendationResponse | None = None
    period_summary: PeriodSummaryResponse | None = None
    agent: str | None = None
    error_code: str | None = None
