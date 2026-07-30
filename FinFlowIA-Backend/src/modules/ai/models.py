import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import BaseEntity


class AICategorizationLog(BaseEntity):
    """
    SQLAlchemy model persisting every LLM categorization call.

    Backs the Prometheus counters in infrastructure/observability/metrics.py
    with queryable history: cost/accuracy analysis over time, and the source
    dataset for offline prompt evaluation (RFC section 8.5) both need rows
    that outlive Prometheus's retention window.
    """

    __tablename__ = "ai_categorization_logs"

    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    input_description: Mapped[str] = mapped_column(Text, nullable=False)
    result_category: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(precision=4, scale=3), nullable=False)
    tokens_input: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_output: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=6), nullable=False)
    from_cache: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AICategorizationLog id={self.id} provider={self.provider} "
            f"category={self.result_category!r}>"
        )
