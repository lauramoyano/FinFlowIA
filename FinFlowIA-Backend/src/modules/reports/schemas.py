import uuid
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ReportType(str, Enum):
    SUMMARY = "summary"
    BY_CATEGORY = "by_category"
    MONTHLY = "monthly"


class ReportRequest(BaseModel):
    """Request schema for generating a financial report."""

    start_date: date
    end_date: date
    report_type: ReportType = ReportType.SUMMARY


class CategorySummary(BaseModel):
    """Aggregated totals per category."""

    category: str
    total: Decimal
    count: int
    percentage: float


class ReportResponse(BaseModel):
    """Full report response including period, totals, and category breakdown."""

    report_type: ReportType
    start_date: date
    end_date: date
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    transaction_count: int
    by_category: list[CategorySummary]
    generated_at: str
