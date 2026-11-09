import uuid
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import BaseEntity


class Product(BaseEntity):
    """A product a user sells, with its per-unit insumos (input materials) cost."""

    __tablename__ = "products"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    unit_label: Mapped[str | None] = mapped_column(String(30), nullable=True)
    unit_insumos_cost: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    unit_sale_price: Mapped[Decimal | None] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_products_user_id_name"),
        CheckConstraint("unit_insumos_cost >= 0", name="ck_products_unit_insumos_cost_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r}>"


class ProductionEstimate(BaseEntity):
    """Historical record of one run of the production cost estimation agent."""

    __tablename__ = "production_estimates"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_estimated_cost: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    llm_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ProductionEstimate id={self.id} total_estimated_cost={self.total_estimated_cost}>"


class ProductionEstimateItem(BaseEntity):
    """One product line (quantity + cost snapshot) within a ProductionEstimate."""

    __tablename__ = "production_estimate_items"

    estimate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_estimates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost_snapshot: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_production_estimate_items_quantity_positive"),
    )

    def __repr__(self) -> str:
        return f"<ProductionEstimateItem id={self.id} product_id={self.product_id} quantity={self.quantity}>"
