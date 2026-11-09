import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateProductRequest(BaseModel):
    """
    Request schema for registering a new product in the catalog via the
    dedicated /products page. unit_sale_price is required here (the DB
    column itself is nullable — the chat can register a product without a
    price when a calculation doesn't need one).
    """

    name: str = Field(min_length=1, max_length=150)
    unit_label: str | None = Field(default=None, max_length=30)
    unit_insumos_cost: Decimal = Field(ge=0, decimal_places=2)
    unit_sale_price: Decimal = Field(ge=0, decimal_places=2)


class UpdateProductRequest(BaseModel):
    """Request schema for partially updating a product."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    unit_label: str | None = Field(default=None, max_length=30)
    unit_insumos_cost: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    unit_sale_price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    """Response schema for a single product."""

    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    unit_label: str | None
    unit_insumos_cost: Decimal
    unit_sale_price: Decimal | None
    is_active: bool


class ProductionEstimateItemResponse(BaseModel):
    """One resolved line item within a production cost estimate."""

    product_name: str
    quantity: int
    unit_cost: Decimal
    subtotal: Decimal


class ProductionEstimateResponse(BaseModel):
    """Result of a completed production cost estimate (all items resolved)."""

    items: list[ProductionEstimateItemResponse]
    total_estimated_cost: Decimal
    projected_revenue: Decimal | None = None
    estimated_profit: Decimal | None = None


class SalesGoalItemResponse(BaseModel):
    """One product's share of a sales goal."""

    product_name: str
    quantity_needed: int
    unit_sale_price: Decimal
    unit_insumos_cost: Decimal
    insumos_investment: Decimal
    projected_revenue: Decimal
    estimated_profit: Decimal


class SalesGoalResponse(BaseModel):
    """Result of a completed sales-goal estimate (minimum units to sell to hit a revenue target)."""

    goal_amount: Decimal
    items: list[SalesGoalItemResponse]
    insumos_investment: Decimal
    projected_revenue: Decimal
    estimated_profit: Decimal
