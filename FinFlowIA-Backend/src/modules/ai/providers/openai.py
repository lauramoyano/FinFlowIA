import structlog

from src.modules.ai.providers.base import LLMProvider, LLMProviderError, LLMResponse

logger = structlog.get_logger(__name__)


class OpenAIProvider:
    """
    LLM provider implementation using the OpenAI API.
    Used as a fallback when the primary Anthropic provider is unavailable.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._client = None  # Lazy initialization

    def _get_client(self):  # type: ignore
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def complete(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Send a prompt to OpenAI and return a normalized response."""
        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.choices[0].message.content or ""
            tokens_in = response.usage.prompt_tokens if response.usage else 0
            tokens_out = response.usage.completion_tokens if response.usage else 0

            logger.debug(
                "openai_response",
                model=self._model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )

            return LLMResponse(
                content=content,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                model=self._model,
                provider="openai",
            )

        except Exception as e:
            logger.error("openai_api_error", error=str(e), model=self._model)
            raise LLMProviderError(f"OpenAI API error: {e}") from e
