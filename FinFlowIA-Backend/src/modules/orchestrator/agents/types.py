from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from src.modules.ai.schemas import ParsedTransactionResult

AgentResultKind = Literal[
    "question",
    "confirm_transaction",
    "estimate_result",
    "sales_goal_result",
    "financial_recommendation_result",
    "period_summary_result",
    "agent_unavailable",
    "error",
]


@dataclass
class ProductionEstimateResultItem:
    """One resolved line item within a completed production cost estimate."""

    product_name: str
    quantity: int
    unit_cost: Decimal
    subtotal: Decimal


@dataclass
class ProductionEstimateResult:
    """A fully resolved production cost estimate (every item matched to a catalog cost)."""

    items: list[ProductionEstimateResultItem]
    total_estimated_cost: Decimal
    # Only when every item has a known sale price: links the cost to a profit.
    projected_revenue: Decimal | None = None
    estimated_profit: Decimal | None = None


@dataclass
class SalesGoalItem:
    """One product's share of a sales goal."""

    product_name: str
    quantity_needed: int
    unit_sale_price: Decimal
    unit_insumos_cost: Decimal
    insumos_investment: Decimal
    projected_revenue: Decimal
    estimated_profit: Decimal


@dataclass
class SalesGoalResult:
    """
    Result of a completed sales-goal estimate: the minimum units of each
    product to sell to hit a revenue target (split evenly when several
    products are named), plus the insumos investment needed and the
    projected profit.
    """

    goal_amount: Decimal
    items: list[SalesGoalItem]
    insumos_investment: Decimal
    projected_revenue: Decimal
    estimated_profit: Decimal


@dataclass
class FinancialRecommendationResultItem:
    """One line item of a completed reparto recommendation."""

    label: str
    amount: Decimal
    percentage: Decimal


@dataclass
class FinancialRecommendationResult:
    """
    Result of a completed financial-recommendation (reparto) estimate:
    how to split the net amount of a sale after its associated costs.
    """

    items: list[FinancialRecommendationResultItem]
    sale_amount: Decimal
    total_costs: Decimal
    net_amount: Decimal
    estimated_savings: Decimal
    estimated_business_balance: Decimal
    pending_debt_total: Decimal
    # Set when the insumos cost was recalled from a previous estimate of
    # these products instead of being typed again.
    insumos_linked_products: list[str] | None = None


@dataclass
class PeriodSummaryData:
    """Income/expense/balance totals for one resolved date range."""

    label: str
    start_date: date
    end_date: date
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal


@dataclass
class PeriodSummaryResult:
    """
    Result of a completed period-summary request. `previous` is populated
    only for a comparison request (explicit or auto-computed "the period
    right before `current`").
    """

    current: PeriodSummaryData
    previous: PeriodSummaryData | None = None


@dataclass
class AgentResult:
    """
    Normalized outcome of one orchestrator agent handling one turn.

    - "question": `message` is a code (e.g. "ask_amount") the frontend maps
      to a translated string; `message_params` fills in any interpolation
      the translation needs (e.g. {"product": "torta"}). The caller should
      reply with the same conversation_id to continue.
    - "confirm_transaction": `draft` has the parsed transaction fields.
    - "estimate_result": `estimate` has the resolved production cost estimate.
    - "sales_goal_result": `sales_goal_result` has the resolved sales-goal estimate.
    - "financial_recommendation_result": `financial_recommendation_result` has
      the resolved reparto recommendation.
    - "period_summary_result": `period_summary_result` has the resolved
      period summary (plus a comparison period, if requested).
    - "agent_unavailable": `agent` names the recognized-but-unbuilt agent.
    - "error": `error_code` mirrors ParsedTransactionResult.error codes.
    """

    kind: AgentResultKind
    message: str | None = None
    message_params: dict[str, str] | None = None
    draft: ParsedTransactionResult | None = None
    estimate: ProductionEstimateResult | None = None
    sales_goal_result: SalesGoalResult | None = None
    financial_recommendation_result: FinancialRecommendationResult | None = None
    period_summary_result: PeriodSummaryResult | None = None
    agent: str | None = None
    error_code: str | None = None
