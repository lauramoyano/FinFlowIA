"""add products.unit_sale_price

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-19

Nullable: the production-estimate chat agent can register a new product
with only its insumos cost (a plain cost estimate never needs a sale
price), and backfills the price later only when a sales-goal calculation
actually needs it. The dedicated /products page requires it via its own
Pydantic schema, not a DB constraint.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products", sa.Column("unit_sale_price", sa.Numeric(precision=14, scale=2), nullable=True)
    )
    op.create_check_constraint(
        "ck_products_unit_sale_price_non_negative",
        "products",
        "unit_sale_price IS NULL OR unit_sale_price >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_products_unit_sale_price_non_negative", "products", type_="check")
    op.drop_column("products", "unit_sale_price")
