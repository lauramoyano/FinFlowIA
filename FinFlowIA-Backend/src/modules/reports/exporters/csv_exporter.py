import csv
import io

from src.modules.reports.exporters.labels import get_labels
from src.modules.reports.schemas import ReportResponse


class CSVExporter:
    """Exports a ReportResponse to CSV format."""

    def __init__(self, lang: str = "en") -> None:
        self._labels = get_labels(lang)

    def export(self, report: ReportResponse) -> bytes:
        """
        Convert a report to CSV bytes.
        Returns UTF-8 encoded CSV with BOM for Excel compatibility.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        labels = self._labels

        # Header section
        writer.writerow([labels["title"]])
        writer.writerow([labels["report_type"], report.report_type])
        writer.writerow([labels["period"], labels["period_value"].format(start=report.start_date, end=report.end_date)])
        writer.writerow([labels["generated_at"], report.generated_at])
        writer.writerow([])

        # Summary section
        writer.writerow([labels["summary"]])
        writer.writerow([labels["total_income"], str(report.total_income)])
        writer.writerow([labels["total_expenses"], str(report.total_expenses)])
        writer.writerow([labels["net_balance"], str(report.net_balance)])
        writer.writerow([labels["transaction_count"], str(report.transaction_count)])
        writer.writerow([])

        # Category breakdown
        writer.writerow([labels["category_breakdown"]])
        writer.writerow([labels["category"], labels["total"], labels["count"], labels["percentage"]])
        for cat in report.by_category:
            writer.writerow([
                cat.category,
                str(cat.total),
                str(cat.count),
                f"{cat.percentage:.1f}%",
            ])

        # Return UTF-8 with BOM for Excel compatibility
        return ("\ufeff" + output.getvalue()).encode("utf-8")
