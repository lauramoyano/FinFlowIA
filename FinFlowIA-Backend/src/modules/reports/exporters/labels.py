LABELS: dict[str, dict[str, str]] = {
    "en": {
        "title": "FinFlowIA - Financial Report",
        "report_type": "Report Type",
        "period": "Period",
        "period_value": "{start} to {end}",
        "generated_at": "Generated At",
        "summary": "Summary",
        "total_income": "Total Income",
        "total_expenses": "Total Expenses",
        "net_balance": "Net Balance",
        "transaction_count": "Transaction Count",
        "category_breakdown": "Category Breakdown",
        "category": "Category",
        "total": "Total",
        "count": "Count",
        "percentage": "Percentage",
        "no_categories": "No transactions in this period.",
    },
    "es": {
        "title": "FinFlowIA - Reporte financiero",
        "report_type": "Tipo de reporte",
        "period": "Período",
        "period_value": "{start} a {end}",
        "generated_at": "Generado el",
        "summary": "Resumen",
        "total_income": "Ingresos totales",
        "total_expenses": "Gastos totales",
        "net_balance": "Balance neto",
        "transaction_count": "Cantidad de transacciones",
        "category_breakdown": "Desglose por categoría",
        "category": "Categoría",
        "total": "Total",
        "count": "Cantidad",
        "percentage": "Participación",
        "no_categories": "No hay transacciones en este período.",
    },
}


def get_labels(lang: str) -> dict[str, str]:
    """Labels for `lang`, falling back to English for any unsupported language."""
    return LABELS.get(lang, LABELS["en"])
