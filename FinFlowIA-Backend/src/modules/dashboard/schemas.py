from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

from src.modules.transactions.enums import TransactionType
from src.modules.transactions.schemas import TransactionResponse


class CategoryBreakdown(BaseModel):
    """Category total for dashboard display."""

    category: str
    transaction_type: TransactionType
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


class Granularity(str, Enum):
    DAY = "day"
    MONTH = "month"
    YEAR = "year"


class TimeSeriesPoint(BaseModel):
    """Income/expense totals for a single bucket in a time series."""

    period: str  # bucket label: "2026-01-05" / "2026-01" / "2026"
    date: date  # bucket start date
    income: Decimal
    expense: Decimal


class DashboardChartsResponse(BaseModel):
    """Chart-ready aggregates for a date range and granularity."""

    start_date: date
    end_date: date
    granularity: Granularity
    time_series: list[TimeSeriesPoint]
    by_category: list[CategoryBreakdown]
