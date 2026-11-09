import uuid
from datetime import date
from decimal import Decimal

import structlog

from src.modules.dashboard.schemas import (
    CategoryBreakdown,
    DashboardChartsResponse,
    DashboardResponse,
    Granularity,
    TimeSeriesPoint,
)
from src.modules.reports.repository import ReportRepository
from src.modules.transactions.repository import TransactionRepository
from src.modules.transactions.schemas import TransactionResponse
from src.shared.utils.datetime_utils import (
    end_of_month,
    format_bucket_label,
    iter_bucket_starts,
    start_of_month,
)

logger = structlog.get_logger(__name__)


class DashboardService:
    """Aggregates data from multiple repositories to build the dashboard view."""

    def __init__(
        self,
        transaction_repo: TransactionRepository,
        report_repo: ReportRepository,
    ) -> None:
        self._transaction_repo = transaction_repo
        self._report_repo = report_repo

    async def get_dashboard(
        self,
        user_id: uuid.UUID,
        reference_date: date | None = None,
    ) -> DashboardResponse:
        """
        Build the dashboard for the current month.
        Aggregates income, expenses, category breakdown, and recent transactions.
        """
        today = reference_date or date.today()
        start = start_of_month(today)
        end = end_of_month(today)

        period_label = today.strftime("%B %Y")

        logger.info(
            "building_dashboard",
            user_id=str(user_id),
            period=period_label,
        )

        # Aggregate totals
        totals = await self._report_repo.get_totals_by_period(
            user_id=user_id, start_date=start, end_date=end
        )

        # Category breakdown
        category_rows = await self._report_repo.get_totals_by_category(
            user_id=user_id, start_date=start, end_date=end
        )

        total_income = Decimal(str(totals["total_income"]))
        total_expenses = Decimal(str(totals["total_expenses"]))
        grand_total = total_income + total_expenses

        by_category = []
        for row in category_rows:
            total = Decimal(str(row["total"]))
            percentage = float(total / grand_total * 100) if grand_total > 0 else 0.0
            by_category.append(
                CategoryBreakdown(
                    category=row["category"],
                    transaction_type=row["transaction_type"],
                    total=total,
                    count=row["count"],
                    percentage=round(percentage, 2),
                )
            )

        # Recent transactions (last 10)
        recent, _ = await self._transaction_repo.list_by_user(
            user_id=user_id,
            limit=10,
            offset=0,
        )
        recent_responses = [TransactionResponse.model_validate(t) for t in recent]

        return DashboardResponse(
            total_income=total_income,
            total_expenses=total_expenses,
            balance=total_income - total_expenses,
            by_category=by_category,
            recent_transactions=recent_responses,
            period_label=period_label,
        )

    async def get_dashboard_charts(
        self,
        user_id: uuid.UUID,
        start_date: date,
        end_date: date,
        granularity: Granularity,
    ) -> DashboardChartsResponse:
        """Build chart-ready time series + category breakdown for a date range."""
        raw_points = await self._report_repo.get_time_series(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity.value,
        )
        by_bucket = {p["bucket"]: p for p in raw_points}

        time_series = []
        for bucket_start in iter_bucket_starts(start_date, end_date, granularity.value):
            row = by_bucket.get(bucket_start)
            time_series.append(
                TimeSeriesPoint(
                    period=format_bucket_label(bucket_start, granularity.value),
                    date=bucket_start,
                    income=row["income"] if row else Decimal("0"),
                    expense=row["expense"] if row else Decimal("0"),
                )
            )

        category_rows = await self._report_repo.get_totals_by_category(
            user_id=user_id, start_date=start_date, end_date=end_date
        )
        grand_total = sum((Decimal(str(row["total"])) for row in category_rows), Decimal("0"))

        by_category = []
        for row in category_rows:
            total = Decimal(str(row["total"]))
            percentage = float(total / grand_total * 100) if grand_total > 0 else 0.0
            by_category.append(
                CategoryBreakdown(
                    category=row["category"],
                    transaction_type=row["transaction_type"],
                    total=total,
                    count=row["count"],
                    percentage=round(percentage, 2),
                )
            )

        return DashboardChartsResponse(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            time_series=time_series,
            by_category=by_category,
        )
