import uuid
from decimal import Decimal

import structlog

from src.modules.reports.repository import ReportRepository
from src.modules.reports.schemas import CategorySummary, ReportRequest, ReportResponse
from src.shared.utils.datetime_utils import utcnow

logger = structlog.get_logger(__name__)


class ReportService:
    """Business logic for generating financial reports."""

    def __init__(self, repo: ReportRepository) -> None:
        self._repo = repo

    async def generate_summary(
        self,
        user_id: uuid.UUID,
        request: ReportRequest,
    ) -> ReportResponse:
        """Generate a summary report for the given date range."""
        logger.info(
            "generating_report",
            user_id=str(user_id),
            report_type=request.report_type,
            start_date=str(request.start_date),
            end_date=str(request.end_date),
        )

        totals = await self._repo.get_totals_by_period(
            user_id=user_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        category_rows = await self._repo.get_totals_by_category(
            user_id=user_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        total_income = Decimal(str(totals["total_income"]))
        total_expenses = Decimal(str(totals["total_expenses"]))
        grand_total = total_income + total_expenses

        by_category = []
        for row in category_rows:
            total = Decimal(str(row["total"]))
            percentage = float(total / grand_total * 100) if grand_total > 0 else 0.0
            by_category.append(
                CategorySummary(
                    category=row["category"],
                    total=total,
                    count=row["count"],
                    percentage=round(percentage, 2),
                )
            )

        return ReportResponse(
            report_type=request.report_type,
            start_date=request.start_date,
            end_date=request.end_date,
            total_income=total_income,
            total_expenses=total_expenses,
            net_balance=total_income - total_expenses,
            transaction_count=totals["transaction_count"],
            by_category=by_category,
            generated_at=utcnow().isoformat(),
        )
