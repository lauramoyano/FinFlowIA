import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.dashboard.service import DashboardService
from src.modules.transactions.models import Transaction


class TestDashboardService:
    @pytest.mark.asyncio
    async def test_get_dashboard_aggregates_totals_and_balance(
        self,
        dashboard_service: DashboardService,
        mock_report_repo: AsyncMock,
        mock_transaction_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_totals_by_period.return_value = {
            "total_income": Decimal("5000.00"),
            "total_expenses": Decimal("2000.00"),
            "transaction_count": 10,
        }
        mock_report_repo.get_totals_by_category.return_value = []
        mock_transaction_repo.list_by_user.return_value = ([], 0)

        result = await dashboard_service.get_dashboard(user_id=user_id)

        assert result.total_income == Decimal("5000.00")
        assert result.total_expenses == Decimal("2000.00")
        assert result.balance == Decimal("3000.00")

    @pytest.mark.asyncio
    async def test_get_dashboard_computes_category_percentages(
        self,
        dashboard_service: DashboardService,
        mock_report_repo: AsyncMock,
        mock_transaction_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_totals_by_period.return_value = {
            "total_income": Decimal("0"),
            "total_expenses": Decimal("400.00"),
            "transaction_count": 2,
        }
        mock_report_repo.get_totals_by_category.return_value = [
            {
                "category": "food",
                "transaction_type": "expense",
                "total": Decimal("300.00"),
                "count": 1,
            },
            {
                "category": "transport",
                "transaction_type": "expense",
                "total": Decimal("100.00"),
                "count": 1,
            },
        ]
        mock_transaction_repo.list_by_user.return_value = ([], 0)

        result = await dashboard_service.get_dashboard(user_id=user_id)

        assert result.by_category[0].category == "food"
        assert result.by_category[0].percentage == 75.0
        assert result.by_category[1].percentage == 25.0

    @pytest.mark.asyncio
    async def test_get_dashboard_handles_zero_totals_without_dividing_by_zero(
        self,
        dashboard_service: DashboardService,
        mock_report_repo: AsyncMock,
        mock_transaction_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_totals_by_period.return_value = {
            "total_income": Decimal("0"),
            "total_expenses": Decimal("0"),
            "transaction_count": 0,
        }
        mock_report_repo.get_totals_by_category.return_value = [
            {
                "category": "other",
                "transaction_type": "expense",
                "total": Decimal("0"),
                "count": 0,
            }
        ]
        mock_transaction_repo.list_by_user.return_value = ([], 0)

        result = await dashboard_service.get_dashboard(user_id=user_id)

        assert result.by_category[0].percentage == 0.0
        assert result.balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_dashboard_maps_recent_transactions(
        self,
        dashboard_service: DashboardService,
        mock_report_repo: AsyncMock,
        mock_transaction_repo: AsyncMock,
        user_id: uuid.UUID,
        sample_transaction: Transaction,
    ) -> None:
        mock_report_repo.get_totals_by_period.return_value = {
            "total_income": Decimal("1000.00"),
            "total_expenses": Decimal("0"),
            "transaction_count": 1,
        }
        mock_report_repo.get_totals_by_category.return_value = []
        mock_transaction_repo.list_by_user.return_value = ([sample_transaction], 1)

        result = await dashboard_service.get_dashboard(user_id=user_id)

        assert len(result.recent_transactions) == 1
        assert result.recent_transactions[0].id == sample_transaction.id
        mock_transaction_repo.list_by_user.assert_called_once_with(
            user_id=user_id, limit=10, offset=0
        )

    @pytest.mark.asyncio
    async def test_get_dashboard_queries_full_calendar_month(
        self,
        dashboard_service: DashboardService,
        mock_report_repo: AsyncMock,
        mock_transaction_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_totals_by_period.return_value = {
            "total_income": Decimal("0"),
            "total_expenses": Decimal("0"),
            "transaction_count": 0,
        }
        mock_report_repo.get_totals_by_category.return_value = []
        mock_transaction_repo.list_by_user.return_value = ([], 0)

        # 2026 is not a leap year — exercises the 28-day February boundary.
        await dashboard_service.get_dashboard(
            user_id=user_id, reference_date=date(2026, 2, 10)
        )

        mock_report_repo.get_totals_by_period.assert_called_once_with(
            user_id=user_id, start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)
        )
