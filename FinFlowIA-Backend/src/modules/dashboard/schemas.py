from decimal import Decimal

from pydantic import BaseModel

from src.modules.transactions.schemas import TransactionResponse


class CategoryBreakdown(BaseModel):
    """Category total for dashboard display."""

    category: str
    total: Decimal
    count: int
    percentage: float


class DashboardResponse(BaseModel):
    """Aggregated dashboard data for the current user."""

    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal
    by_category: list[CategoryBreakdown]
    recent_transactions: list[TransactionResponse]
    period_label: str  # e.g., "May 2026"
