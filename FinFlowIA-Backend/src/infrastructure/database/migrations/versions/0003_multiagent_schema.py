"""add multiagent schema: debt columns on transactions, distribution
templates, financial recommendations, products/production estimates,
budget plans, balance reconciliations

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-14

Ported from a hand-written schema sketch that assumed bigint/bigserial
ids — this project's users/categories/transactions all use UUID primary
keys (see 0001/0002), so every id/FK here is UUID instead, matching the
existing convention. Every table also gets both created_at AND updated_at
(not just created_at on the "historical record" tables like
financial_recommendations/production_estimates) for consistency with
BaseEntity, which every ORM model in this codebase inherits from —
ai_categorization_logs (0002) already sets this precedent for log-like
tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # Debt modeling: reuse `transactions` with recurrence + installments
    # instead of a separate `debts` table.
    # ---------------------------------------------------------------
    op.add_column("transactions", sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("transactions", sa.Column("recurrence_interval", sa.String(length=20), nullable=True))
    op.add_column("transactions", sa.Column("installments_total", sa.Integer(), nullable=True))
    op.add_column("transactions", sa.Column("installments_paid", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("transactions", sa.Column("parent_transaction_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.create_foreign_key(
        "fk_transactions_parent_transaction_id",
        "transactions",
        "transactions",
        ["parent_transaction_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_transactions_parent_transaction_id", "transactions", ["parent_transaction_id"])
    op.create_index(
        "ix_transactions_recurring", "transactions", ["user_id"], postgresql_where=sa.text("is_recurring = true")
    )

    op.create_check_constraint(
        "ck_transactions_recurrence_interval",
        "transactions",
        "recurrence_interval IS NULL OR recurrence_interval IN ('weekly', 'biweekly', 'monthly')",
    )
    op.create_check_constraint(
        "ck_transactions_installments",
        "transactions",
        "installments_paid <= COALESCE(installments_total, installments_paid)",
    )

    # ---------------------------------------------------------------
    # Distribution templates (Agent: recomendación financiera)
    # ---------------------------------------------------------------
    op.create_table(
        "distribution_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, server_default="Mi reparto"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_distribution_templates_id", "distribution_templates", ["id"])
    op.create_index("ix_distribution_templates_user_id", "distribution_templates", ["user_id"])

    op.create_table(
        "distribution_template_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("percentage", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["template_id"], ["distribution_templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "percentage >= 0 AND percentage <= 100", name="ck_distribution_template_items_percentage"
        ),
    )
    op.create_index("ix_distribution_template_items_id", "distribution_template_items", ["id"])
    op.create_index(
        "ix_distribution_template_items_template_id", "distribution_template_items", ["template_id"]
    )

    # ---------------------------------------------------------------
    # Financial recommendations: history/traceability of each
    # get_financial_recommendation call
    # ---------------------------------------------------------------
    op.create_table(
        "financial_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("distribution_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sale_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("insumos_cost", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("transporte_cost", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("ayudante_cost", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("gastos_adicionales", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("servicios_publicos_cost", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("estimated_savings", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("estimated_business_balance", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("llm_explanation", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["distribution_template_id"], ["distribution_templates.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_financial_recommendations_id", "financial_recommendations", ["id"])
    op.create_index("ix_financial_recommendations_user_id", "financial_recommendations", ["user_id"])

    op.create_table(
        "financial_recommendation_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("percentage", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["recommendation_id"], ["financial_recommendations.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "percentage >= 0 AND percentage <= 100", name="ck_financial_recommendation_items_percentage"
        ),
    )
    op.create_index("ix_financial_recommendation_items_id", "financial_recommendation_items", ["id"])
    op.create_index(
        "ix_financial_recommendation_items_recommendation_id",
        "financial_recommendation_items",
        ["recommendation_id"],
    )

    # ---------------------------------------------------------------
    # Products + production cost estimation (Agent 3)
    # ---------------------------------------------------------------
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("unit_label", sa.String(length=30), nullable=True),
        sa.Column("unit_insumos_cost", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "name", name="uq_products_user_id_name"),
        sa.CheckConstraint("unit_insumos_cost >= 0", name="ck_products_unit_insumos_cost_non_negative"),
    )
    op.create_index("ix_products_id", "products", ["id"])
    op.create_index("ix_products_user_id", "products", ["user_id"])

    op.create_table(
        "production_estimates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_estimated_cost", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("llm_explanation", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_production_estimates_id", "production_estimates", ["id"])
    op.create_index("ix_production_estimates_user_id", "production_estimates", ["user_id"])

    op.create_table(
        "production_estimate_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("estimate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_cost_snapshot", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["estimate_id"], ["production_estimates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("quantity > 0", name="ck_production_estimate_items_quantity_positive"),
    )
    op.create_index("ix_production_estimate_items_id", "production_estimate_items", ["id"])
    op.create_index(
        "ix_production_estimate_items_estimate_id", "production_estimate_items", ["estimate_id"]
    )

    # ---------------------------------------------------------------
    # Budget plans (declared budget per category + period)
    # ---------------------------------------------------------------
    op.create_table(
        "budget_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_type", sa.String(length=10), nullable=False),
        sa.Column("period_start_date", sa.Date(), nullable=False),
        sa.Column("planned_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id", "category_id", "period_type", "period_start_date", name="uq_budget_plans_user_category_period"
        ),
        sa.CheckConstraint("period_type IN ('month', 'year')", name="ck_budget_plans_period_type_valid"),
        sa.CheckConstraint("planned_amount >= 0", name="ck_budget_plans_planned_amount_non_negative"),
    )
    op.create_index("ix_budget_plans_id", "budget_plans", ["id"])
    op.create_index("ix_budget_plans_user_id", "budget_plans", ["user_id"])

    # ---------------------------------------------------------------
    # Balance reconciliations
    # ---------------------------------------------------------------
    op.create_table(
        "balance_reconciliations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("declared_balance", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("calculated_balance", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("difference", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_balance_reconciliations_id", "balance_reconciliations", ["id"])
    op.create_index("ix_balance_reconciliations_user_id", "balance_reconciliations", ["user_id"])


def downgrade() -> None:
    op.drop_table("balance_reconciliations")
    op.drop_table("budget_plans")
    op.drop_table("production_estimate_items")
    op.drop_table("production_estimates")
    op.drop_table("products")
    op.drop_table("financial_recommendation_items")
    op.drop_table("financial_recommendations")
    op.drop_table("distribution_template_items")
    op.drop_table("distribution_templates")

    op.drop_constraint("ck_transactions_installments", "transactions", type_="check")
    op.drop_constraint("ck_transactions_recurrence_interval", "transactions", type_="check")
    op.drop_index("ix_transactions_recurring", table_name="transactions")
    op.drop_index("ix_transactions_parent_transaction_id", table_name="transactions")
    op.drop_constraint("fk_transactions_parent_transaction_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "parent_transaction_id")
    op.drop_column("transactions", "installments_paid")
    op.drop_column("transactions", "installments_total")
    op.drop_column("transactions", "recurrence_interval")
    op.drop_column("transactions", "is_recurring")
