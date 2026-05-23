import uuid
from datetime import date
from decimal import Decimal

import structlog

from src.modules.dashboard.schemas import CategoryBreakdown, DashboardResponse
from src.modules.reports.repository import ReportRepository
from src.modules.transactions.repository import TransactionRepository
from src.modules.transactions.schemas import TransactionResponse
from src.shared.utils.datetime_utils import end_of_month, start_of_month

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
