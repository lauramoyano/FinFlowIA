import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.reports.schemas import ReportRequest, ReportType
from src.modules.reports.service import ReportService


class TestReportService:
    @pytest.mark.asyncio
    async def test_generate_summary_computes_net_balance(
        self,
        report_service: ReportService,
        mock_report_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_totals_by_period.return_value = {
            "total_income": Decimal("8000.00"),
            "total_expenses": Decimal("3500.00"),
            "transaction_count": 12,
        }
        mock_report_repo.get_totals_by_category.return_value = []

        request = ReportRequest(start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        result = await report_service.generate_summary(user_id=user_id, request=request)

        assert result.net_balance == Decimal("4500.00")
        assert result.transaction_count == 12

    @pytest.mark.asyncio
    async def test_generate_summary_computes_category_percentages(
        self,
        report_service: ReportService,
        mock_report_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_totals_by_period.return_value = {
            "total_income": Decimal("0"),
            "total_expenses": Decimal("1000.00"),
            "transaction_count": 2,
        }
        mock_report_repo.get_totals_by_category.return_value = [
            {
                "category": "rent",
                "transaction_type": "expense",
                "total": Decimal("800.00"),
                "count": 1,
            },
            {
                "category": "supplies",
                "transaction_type": "expense",
                "total": Decimal("200.00"),
                "count": 1,
            },
        ]

        request = ReportRequest(start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        result = await report_service.generate_summary(user_id=user_id, request=request)

        assert result.by_category[0].percentage == 80.0
        assert result.by_category[1].percentage == 20.0

    @pytest.mark.asyncio
    async def test_generate_summary_handles_zero_activity(
        self,
        report_service: ReportService,
        mock_report_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_totals_by_period.return_value = {
            "total_income": Decimal("0"),
            "total_expenses": Decimal("0"),
            "transaction_count": 0,
        }
        mock_report_repo.get_totals_by_category.return_value = []

        request = ReportRequest(start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        result = await report_service.generate_summary(user_id=user_id, request=request)

        assert result.net_balance == Decimal("0")
        assert result.by_category == []

    @pytest.mark.asyncio
    async def test_generate_summary_passes_date_range_and_type_through(
        self,
        report_service: ReportService,
        mock_report_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_totals_by_period.return_value = {
            "total_income": Decimal("0"),
            "total_expenses": Decimal("0"),
            "transaction_count": 0,
        }
        mock_report_repo.get_totals_by_category.return_value = []

        request = ReportRequest(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            report_type=ReportType.MONTHLY,
        )
        result = await report_service.generate_summary(user_id=user_id, request=request)

        mock_report_repo.get_totals_by_period.assert_called_once_with(
            user_id=user_id, start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)
        )
        assert result.report_type == ReportType.MONTHLY
