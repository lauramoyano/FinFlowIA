from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class LLMResponse:
    """Normalized response from any LLM provider."""

    content: str
    tokens_input: int
    tokens_output: int
    model: str
    provider: str


@dataclass
class CategoryResult:
    """Result of a transaction categorization."""

    category: str
    confidence: float
    from_cache: bool = False


class LLMProviderError(Exception):
    """Raised when an LLM provider call fails."""

    pass


@runtime_checkable
class LLMProvider(Protocol):
    """
    Protocol defining the interface for all LLM providers.
    Any provider (Anthropic, OpenAI, etc.) must implement this contract.
    Follows the Open/Closed Principle: new providers can be added without
    modifying existing code.
    """

    async def complete(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Send a prompt to the LLM and return a normalized response."""
        ...
