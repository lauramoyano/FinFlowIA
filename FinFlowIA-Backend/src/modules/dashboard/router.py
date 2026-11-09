from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import User
from src.modules.dashboard.schemas import DashboardChartsResponse, DashboardResponse, Granularity
from src.modules.dashboard.service import DashboardService
from src.modules.reports.repository import ReportRepository
from src.modules.transactions.repository import TransactionRepository
from src.shared.schemas.response import ApiResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service(session: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(
        transaction_repo=TransactionRepository(session),
        report_repo=ReportRepository(session),
    )


@router.get(
    "",
    response_model=ApiResponse[DashboardResponse],
    summary="Get dashboard data for the current month",
)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> ApiResponse[DashboardResponse]:
    dashboard = await service.get_dashboard(user_id=current_user.id)
    return ApiResponse(data=dashboard)


@router.get(
    "/charts",
    response_model=ApiResponse[DashboardChartsResponse],
    summary="Get chart data for a date range and granularity",
)
async def get_dashboard_charts(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    granularity: Granularity = Query(default=Granularity.MONTH),
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> ApiResponse[DashboardChartsResponse]:
    charts = await service.get_dashboard_charts(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )
    return ApiResponse(data=charts)
