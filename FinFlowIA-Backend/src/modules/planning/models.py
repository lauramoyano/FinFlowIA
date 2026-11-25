import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import BaseEntity


class DistributionTemplate(BaseEntity):
    """A user's saved profit-distribution template (e.g. "60% reinversión, 30% ahorro, 10% sueldo")."""

    __tablename__ = "distribution_templates"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Mi reparto")

    def __repr__(self) -> str:
        return f"<DistributionTemplate id={self.id} name={self.name!r}>"


class DistributionTemplateItem(BaseEntity):
    """One line item (label + percentage) within a DistributionTemplate."""

    __tablename__ = "distribution_template_items"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("distribution_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<DistributionTemplateItem id={self.id} label={self.label!r} percentage={self.percentage}>"


class FinancialRecommendation(BaseEntity):
    """Historical record of one run of the financial-recommendation (reparto) agent."""

    __tablename__ = "financial_recommendations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    distribution_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("distribution_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    sale_amount: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    insumos_cost: Mapped[Decimal | None] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    transporte_cost: Mapped[Decimal | None] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    ayudante_cost: Mapped[Decimal | None] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    gastos_adicionales: Mapped[Decimal | None] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    servicios_publicos_cost: Mapped[Decimal | None] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    estimated_savings: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    estimated_business_balance: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    llm_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<FinancialRecommendation id={self.id} sale_amount={self.sale_amount}>"


class FinancialRecommendationItem(BaseEntity):
    """One line item (label + amount + percentage) within a FinancialRecommendation."""

    __tablename__ = "financial_recommendation_items"

    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2), nullable=False)

    def __repr__(self) -> str:
        return f"<FinancialRecommendationItem id={self.id} label={self.label!r} amount={self.amount}>"


class BudgetPlan(BaseEntity):
    """A user's declared spending budget for one category over one period."""

    __tablename__ = "budget_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_type: Mapped[str] = mapped_column(String(10), nullable=False)
    period_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "category_id", "period_type", "period_start_date",
            name="uq_budget_plans_user_category_period",
        ),
    )

    def __repr__(self) -> str:
        return f"<BudgetPlan id={self.id} period_type={self.period_type} planned_amount={self.planned_amount}>"


class BalanceReconciliation(BaseEntity):
    """A user's manual declared-vs-calculated balance check at a point in time."""

    __tablename__ = "balance_reconciliations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    declared_balance: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    calculated_balance: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    difference: Mapped[Decimal] = mapped_column(Numeric(precision=14, scale=2), nullable=False)
    reconciled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<BalanceReconciliation id={self.id} difference={self.difference}>"
