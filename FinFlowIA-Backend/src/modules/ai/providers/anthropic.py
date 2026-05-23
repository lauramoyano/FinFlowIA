import structlog
import anthropic

from src.modules.ai.providers.base import LLMProvider, LLMProviderError, LLMResponse

logger = structlog.get_logger(__name__)

# Cost constants for claude-haiku-4-5-20251001
COST_PER_INPUT_TOKEN = 0.00000025   # $0.25/M tokens
COST_PER_OUTPUT_TOKEN = 0.00000125  # $1.25/M tokens


class AnthropicProvider:
    """
    LLM provider implementation using the Anthropic Claude API.
    Uses claude-haiku-4-5-20251001 for fast, cost-effective categorization.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-haiku-4-5-20251001",
    ) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Send a prompt to Claude and return a normalized response with token tracking."""
        try:
            from src.infrastructure.observability.metrics import (
                llm_request_duration,
                llm_tokens_used,
                llm_cost_usd,
            )

            with llm_request_duration.labels(
                provider="anthropic",
                model=self._model,
                prompt_version="current",
            ).time():
                response = await self._client.messages.create(
                    model=self._model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )

            tokens_in = response.usage.input_tokens
            tokens_out = response.usage.output_tokens

            llm_tokens_used.labels(
                provider="anthropic", model=self._model, direction="input"
            ).inc(tokens_in)
            llm_tokens_used.labels(
                provider="anthropic", model=self._model, direction="output"
            ).inc(tokens_out)

            cost = (tokens_in * COST_PER_INPUT_TOKEN) + (tokens_out * COST_PER_OUTPUT_TOKEN)
            llm_cost_usd.labels(provider="anthropic", model=self._model).inc(cost)

            content = response.content[0].text if response.content else ""

            logger.debug(
                "anthropic_response",
                model=self._model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                estimated_cost_usd=round(cost, 6),
            )

            return LLMResponse(
                content=content,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                model=self._model,
                provider="anthropic",
            )

        except anthropic.APIError as e:
            logger.error("anthropic_api_error", error=str(e), model=self._model)
            raise LLMProviderError(f"Anthropic API error: {e}") from e
