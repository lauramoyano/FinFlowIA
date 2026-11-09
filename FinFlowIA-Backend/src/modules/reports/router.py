from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import User
from src.modules.reports.exporters.csv_exporter import CSVExporter
from src.modules.reports.exporters.pdf_exporter import PDFExporter
from src.modules.reports.repository import ReportRepository
from src.modules.reports.schemas import ReportRequest, ReportResponse, ReportType
from src.modules.reports.service import ReportService
from src.shared.schemas.response import ApiResponse

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_report_service(session: AsyncSession = Depends(get_db)) -> ReportService:
    return ReportService(repo=ReportRepository(session))


@router.get(
    "/summary",
    response_model=ApiResponse[ReportResponse],
    summary="Generate a financial summary report",
)
async def get_summary(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    report_type: ReportType = Query(default=ReportType.SUMMARY),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> ApiResponse[ReportResponse]:
    request = ReportRequest(
        start_date=start_date,
        end_date=end_date,
        report_type=report_type,
    )
    report = await service.generate_summary(user_id=current_user.id, request=request)
    return ApiResponse(data=report)


@router.get(
    "/export",
    summary="Export report as CSV or PDF",
)
async def export_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    lang: str = Query(default="en", pattern="^(en|es)$", description="Language of the exported labels"),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> Response:
    request = ReportRequest(start_date=start_date, end_date=end_date)
    report = await service.generate_summary(user_id=current_user.id, request=request)

    if format == "pdf":
        exporter = PDFExporter(lang=lang)
        content = exporter.export(report)
        media_type = "application/pdf"
        filename = f"report_{start_date}_{end_date}.pdf"
    else:
        exporter_csv = CSVExporter(lang=lang)
        content = exporter_csv.export(report)
        media_type = "text/csv"
        filename = f"report_{start_date}_{end_date}.csv"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
