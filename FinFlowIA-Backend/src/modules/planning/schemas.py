from decimal import Decimal

from pydantic import BaseModel


class FinancialRecommendationItemResponse(BaseModel):
    """One line item of a completed reparto recommendation."""

    label: str
    amount: Decimal
    percentage: Decimal


class FinancialRecommendationResponse(BaseModel):
    """Result of a completed financial-recommendation (reparto) estimate."""

    items: list[FinancialRecommendationItemResponse]
    sale_amount: Decimal
    total_costs: Decimal
    net_amount: Decimal
    estimated_savings: Decimal
    estimated_business_balance: Decimal
    pending_debt_total: Decimal
    insumos_linked_products: list[str] | None = None
