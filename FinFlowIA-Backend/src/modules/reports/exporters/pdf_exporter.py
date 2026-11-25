import io

import structlog
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.modules.reports.exporters.labels import get_labels
from src.modules.reports.schemas import ReportResponse

logger = structlog.get_logger(__name__)

_HEADER_BG = colors.HexColor("#1f2937")
_ROW_ALT_BG = colors.HexColor("#f3f4f6")
_GRID = colors.HexColor("#d1d5db")


def _money(value: object) -> str:
    return f"{float(str(value)):,.2f}"


class PDFExporter:
    """Exports a ReportResponse to a PDF document (A4, summary + category table)."""

    def __init__(self, lang: str = "en") -> None:
        self._labels = get_labels(lang)

    def export(self, report: ReportResponse) -> bytes:
        logger.info(
            "pdf_export_requested",
            report_type=report.report_type,
            start_date=str(report.start_date),
            end_date=str(report.end_date),
        )
        labels = self._labels
        styles = getSampleStyleSheet()
        heading = ParagraphStyle("Heading", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title=labels["title"],
        )

        period = labels["period_value"].format(start=report.start_date, end=report.end_date)
        story: list = [
            Paragraph(labels["title"], styles["Title"]),
            Paragraph(f"<b>{labels['period']}:</b> {period}", styles["Normal"]),
            Paragraph(f"<b>{labels['report_type']}:</b> {report.report_type}", styles["Normal"]),
            Paragraph(f"<b>{labels['generated_at']}:</b> {report.generated_at}", styles["Normal"]),
            Paragraph(labels["summary"], heading),
        ]

        summary = Table(
            [
                [labels["total_income"], _money(report.total_income)],
                [labels["total_expenses"], _money(report.total_expenses)],
                [labels["net_balance"], _money(report.net_balance)],
                [labels["transaction_count"], str(report.transaction_count)],
            ],
            colWidths=[9 * cm, 8 * cm],
        )
        summary.setStyle(
            TableStyle(
                [
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, _ROW_ALT_BG]),
                    ("GRID", (0, 0), (-1, -1), 0.5, _GRID),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(summary)

        story.append(Paragraph(labels["category_breakdown"], heading))
        if report.by_category:
            rows = [[labels["category"], labels["total"], labels["count"], labels["percentage"]]]
            rows += [
                [c.category, _money(c.total), str(c.count), f"{c.percentage:.1f}%"]
                for c in report.by_category
            ]
            table = Table(rows, colWidths=[6.5 * cm, 4.5 * cm, 3 * cm, 3 * cm], repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ROW_ALT_BG]),
                        ("GRID", (0, 0), (-1, -1), 0.5, _GRID),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(table)
        else:
            story.append(Spacer(1, 4))
            story.append(Paragraph(labels["no_categories"], styles["Normal"]))

        doc.build(story)
        return buffer.getvalue()
