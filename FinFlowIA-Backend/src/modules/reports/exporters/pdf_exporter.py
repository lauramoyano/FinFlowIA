import structlog

from src.modules.reports.schemas import ReportResponse

logger = structlog.get_logger(__name__)


class PDFExporter:
    """
    Placeholder PDF exporter for financial reports.
    Phase 2 implementation: will use reportlab or weasyprint to generate PDF files.
    """

    def export(self, report: ReportResponse) -> bytes:
        """
        Generate a PDF report.
        Currently returns a placeholder — full implementation in Phase 2.
        """
        logger.info(
            "pdf_export_requested",
            report_type=report.report_type,
            start_date=str(report.start_date),
            end_date=str(report.end_date),
        )

        # Placeholder: returns minimal PDF-like content
        # TODO Phase 2: Implement with reportlab or weasyprint
        placeholder_content = (
            f"FinFlowIA Report\n"
            f"Type: {report.report_type}\n"
            f"Period: {report.start_date} to {report.end_date}\n"
            f"Total Income: {report.total_income}\n"
            f"Total Expenses: {report.total_expenses}\n"
            f"Net Balance: {report.net_balance}\n"
        )

        return placeholder_content.encode("utf-8")
