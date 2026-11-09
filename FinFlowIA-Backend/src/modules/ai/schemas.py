from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class CategoryResult:
    """Result of a transaction categorization request."""

    category: str
    confidence: float
    from_cache: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class ParsedTransactionResult:
    """
    Result of parsing a free-text chat message into transaction fields.
    When `error` is set, the other fields are not reliable and must not be
    used to create a transaction — the caller should surface the error
    instead.
    """

    description: str
    amount: Decimal | None
    transaction_type: str | None
    transaction_date: date
    category: str
    confidence: float
    error: str | None = None


@dataclass
class ParsedProductionEstimateItem:
    """One product + quantity extracted from a production-estimate chat message."""

    product_name: str
    quantity: int


@dataclass
class ParsedSalesGoal:
    """A revenue target extracted from a free-text message, with the product names it mentions (may be several)."""

    amount: Decimal
    product_names: list[str] = field(default_factory=list)


@dataclass
class ParsedProductionEstimateResult:
    """
    Result of parsing a free-text chat message into either a list of
    production items (cost-by-quantity mode) or a sales goal (minimum
    units to sell mode) — exactly one of `items`/`sales_goal` is populated.
    When `error` is set, neither is reliable and must not be used.
    """

    items: list[ParsedProductionEstimateItem] = field(default_factory=list)
    sales_goal: ParsedSalesGoal | None = None
    error: str | None = None


@dataclass
class ParsedSaleAmountResult:
    """
    Result of parsing a free-text message for the financial-recommendation
    agent's sale amount. When `error` is set, `amount` is None and must not
    be used.
    """

    amount: Decimal | None = None
    error: str | None = None


@dataclass
class ParsedRecommendationCosts:
    """
    Cost breakdown extracted from a free-text message for the
    financial-recommendation agent. Any field left None means that cost
    category wasn't mentioned (or was explicitly denied) and should be
    treated as 0 — there is no error state here, every reply is valid.
    """

    insumos_cost: Decimal | None = None
    transporte_cost: Decimal | None = None
    ayudante_cost: Decimal | None = None
    gastos_adicionales: Decimal | None = None
    servicios_publicos_cost: Decimal | None = None


@dataclass
class ParsedPeriodDescriptor:
    """
    A relative time period extracted from a free-text message. `type` is
    one of "this_month" | "last_month" | "this_year" | "last_year" |
    "specific_month" (the latter using `month`/`year`, with `year`
    defaulting to the current year when omitted). Resolving this into
    actual start/end dates is the orchestrator agent's job, not the LLM's —
    date arithmetic should always be deterministic.
    """

    type: str
    month: int | None = None
    year: int | None = None


@dataclass
class ParsedPeriodSummaryRequest:
    """
    Result of parsing a free-text message for the period-summary agent.
    `mode` is "single" (one period) or "comparison" (two periods — `period`
    vs `compare_period`, the latter `None` if the user didn't name a
    specific one, in which case the agent compares against the period
    immediately before `period`). When `error` is set, nothing else is
    reliable.
    """

    mode: str | None = None
    period: ParsedPeriodDescriptor | None = None
    compare_period: ParsedPeriodDescriptor | None = None
    error: str | None = None


@dataclass
class LLMResponseSchema:
    """Normalized LLM response for serialization."""

    content: str
    tokens_input: int
    tokens_output: int
    model: str
    provider: str
    estimated_cost_usd: float = 0.0
