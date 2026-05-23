import csv
import io

from src.modules.reports.schemas import ReportResponse


class CSVExporter:
    """Exports a ReportResponse to CSV format."""

    def export(self, report: ReportResponse) -> bytes:
        """
        Convert a report to CSV bytes.
        Returns UTF-8 encoded CSV with BOM for Excel compatibility.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header section
        writer.writerow(["FinFlowIA - Financial Report"])
        writer.writerow(["Report Type", report.report_type])
        writer.writerow(["Period", f"{report.start_date} to {report.end_date}"])
        writer.writerow(["Generated At", report.generated_at])
        writer.writerow([])

        # Summary section
        writer.writerow(["Summary"])
        writer.writerow(["Total Income", str(report.total_income)])
        writer.writerow(["Total Expenses", str(report.total_expenses)])
        writer.writerow(["Net Balance", str(report.net_balance)])
        writer.writerow(["Transaction Count", str(report.transaction_count)])
        writer.writerow([])

        # Category breakdown
        writer.writerow(["Category Breakdown"])
        writer.writerow(["Category", "Total", "Count", "Percentage"])
        for cat in report.by_category:
            writer.writerow([
                cat.category,
                str(cat.total),
                str(cat.count),
                f"{cat.percentage:.1f}%",
            ])

        # Return UTF-8 with BOM for Excel compatibility
        return ("\ufeff" + output.getvalue()).encode("utf-8")
