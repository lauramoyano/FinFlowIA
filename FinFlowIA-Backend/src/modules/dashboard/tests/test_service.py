import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.modules.dashboard.schemas import Granularity
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


class TestDashboardServiceCharts:
    @pytest.mark.asyncio
    async def test_get_dashboard_charts_passes_granularity_to_repository(
        self,
        dashboard_service: DashboardService,
        mock_report_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_time_series.return_value = []
        mock_report_repo.get_totals_by_category.return_value = []

        await dashboard_service.get_dashboard_charts(
            user_id=user_id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            granularity=Granularity.MONTH,
        )

        mock_report_repo.get_time_series.assert_called_once_with(
            user_id=user_id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            granularity="month",
        )

    @pytest.mark.asyncio
    async def test_get_dashboard_charts_fills_gaps_for_empty_buckets(
        self,
        dashboard_service: DashboardService,
        mock_report_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_time_series.return_value = [
            {"bucket": date(2026, 1, 1), "income": Decimal("100"), "expense": Decimal("50")},
            {"bucket": date(2026, 3, 1), "income": Decimal("200"), "expense": Decimal("0")},
        ]
        mock_report_repo.get_totals_by_category.return_value = []

        result = await dashboard_service.get_dashboard_charts(
            user_id=user_id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            granularity=Granularity.MONTH,
        )

        assert len(result.time_series) == 3
        assert result.time_series[1].period == "2026-02"
        assert result.time_series[1].income == Decimal("0")
        assert result.time_series[1].expense == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_dashboard_charts_day_granularity_buckets_daily(
        self,
        dashboard_service: DashboardService,
        mock_report_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_time_series.return_value = [
            {"bucket": date(2026, 1, 1), "income": Decimal("10"), "expense": Decimal("0")},
            {"bucket": date(2026, 1, 3), "income": Decimal("0"), "expense": Decimal("5")},
        ]
        mock_report_repo.get_totals_by_category.return_value = []

        result = await dashboard_service.get_dashboard_charts(
            user_id=user_id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            granularity=Granularity.DAY,
        )

        assert [p.period for p in result.time_series] == [
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
        ]

    @pytest.mark.asyncio
    async def test_get_dashboard_charts_year_granularity_labels_as_year_string(
        self,
        dashboard_service: DashboardService,
        mock_report_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_time_series.return_value = []
        mock_report_repo.get_totals_by_category.return_value = []

        result = await dashboard_service.get_dashboard_charts(
            user_id=user_id,
            start_date=date(2025, 6, 1),
            end_date=date(2026, 6, 1),
            granularity=Granularity.YEAR,
        )

        assert [p.period for p in result.time_series] == ["2025", "2026"]

    @pytest.mark.asyncio
    async def test_get_dashboard_charts_includes_transaction_type_in_category_breakdown(
        self,
        dashboard_service: DashboardService,
        mock_report_repo: AsyncMock,
        user_id: uuid.UUID,
    ) -> None:
        mock_report_repo.get_time_series.return_value = []
        mock_report_repo.get_totals_by_category.return_value = [
            {
                "category": "food",
                "transaction_type": "expense",
                "total": Decimal("100.00"),
                "count": 1,
            },
        ]

        result = await dashboard_service.get_dashboard_charts(
            user_id=user_id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            granularity=Granularity.MONTH,
        )

        assert result.by_category[0].transaction_type == "expense"
        assert result.by_category[0].percentage == 100.0
