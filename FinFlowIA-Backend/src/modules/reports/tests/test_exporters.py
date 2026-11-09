from decimal import Decimal

from src.modules.reports.exporters.csv_exporter import CSVExporter
from src.modules.reports.exporters.pdf_exporter import PDFExporter
from src.modules.reports.schemas import CategorySummary, ReportResponse, ReportType


def make_report(with_categories: bool = True) -> ReportResponse:
    return ReportResponse(
        report_type=ReportType.SUMMARY,
        start_date="2026-01-01",
        end_date="2026-01-31",
        total_income=Decimal("8000.00"),
        total_expenses=Decimal("3500.00"),
        net_balance=Decimal("4500.00"),
        transaction_count=12,
        by_category=[CategorySummary(category="food", total=Decimal("1200"), count=5, percentage=34.3)]
        if with_categories
        else [],
        generated_at="2026-02-01T00:00:00",
    )


class TestPDFExporter:
    def test_produces_a_valid_pdf(self) -> None:
        content = PDFExporter(lang="es").export(make_report())

        assert content.startswith(b"%PDF-")
        assert content.rstrip().endswith(b"%%EOF")

    def test_empty_report_still_valid_pdf(self) -> None:
        assert PDFExporter().export(make_report(with_categories=False)).startswith(b"%PDF-")


class TestCSVExporter:
    def test_spanish_labels(self) -> None:
        text = CSVExporter(lang="es").export(make_report()).decode("utf-8")

        assert "Ingresos totales" in text
        assert "Desglose por categoría" in text

    def test_default_stays_english(self) -> None:
        assert "Total Income" in CSVExporter().export(make_report()).decode("utf-8")
