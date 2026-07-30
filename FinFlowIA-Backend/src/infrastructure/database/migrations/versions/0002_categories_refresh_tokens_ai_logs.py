"""add categories, refresh_tokens, ai_categorization_logs

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-16

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Mirrors src/modules/transactions/enums.py::CategoryType and the VALID_CATEGORIES
# set in src/modules/ai/service.py. 'other' and 'uncategorized' apply to both
# transaction types, so they get one row per type.
DEFAULT_CATEGORIES: list[tuple[str, str]] = [
    ("food", "expense"),
    ("transport", "expense"),
    ("utilities", "expense"),
    ("supplies", "expense"),
    ("marketing", "expense"),
    ("payroll", "expense"),
    ("rent", "expense"),
    ("equipment", "expense"),
    ("other", "expense"),
    ("uncategorized", "expense"),
    ("sales", "income"),
    ("services", "income"),
    ("other", "income"),
    ("uncategorized", "income"),
]


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id", "name", "transaction_type", name="uq_categories_user_name_type"
        ),
        sa.CheckConstraint(
            "transaction_type IN ('income', 'expense')", name="ck_categories_type_valid"
        ),
    )
    op.create_index("ix_categories_id", "categories", ["id"])
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    categories_table = sa.table(
        "categories",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("transaction_type", sa.String),
        sa.column("is_default", sa.Boolean),
    )
    op.bulk_insert(
        categories_table,
        [
            {"id": uuid.uuid4(), "name": name, "transaction_type": tx_type, "is_default": True}
            for name, tx_type in DEFAULT_CATEGORIES
        ],
    )

    op.add_column(
        "transactions",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_transactions_category_id",
        "transactions",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    op.create_table(
        "ai_categorization_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("transaction_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("model", sa.String(length=50), nullable=False),
        sa.Column("prompt_version", sa.String(length=20), nullable=False),
        sa.Column("input_description", sa.Text(), nullable=False),
        sa.Column("result_category", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("tokens_input", sa.Integer(), nullable=False),
        sa.Column("tokens_output", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("from_cache", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ai_categorization_logs_id", "ai_categorization_logs", ["id"])
    op.create_index(
        "ix_ai_categorization_logs_transaction_id", "ai_categorization_logs", ["transaction_id"]
    )


def downgrade() -> None:
    op.drop_table("ai_categorization_logs")
    op.drop_table("refresh_tokens")
    op.drop_constraint("fk_transactions_category_id", "transactions", type_="foreignkey")
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_column("transactions", "category_id")
    op.drop_table("categories")
