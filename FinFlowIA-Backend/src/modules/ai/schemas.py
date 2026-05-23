from dataclasses import dataclass, field


@dataclass
class CategoryResult:
    """Result of a transaction categorization request."""

    category: str
    confidence: float
    from_cache: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


@dataclass
class LLMResponseSchema:
    """Normalized LLM response for serialization."""

    content: str
    tokens_input: int
    tokens_output: int
    model: str
    provider: str
    estimated_cost_usd: float = 0.0
