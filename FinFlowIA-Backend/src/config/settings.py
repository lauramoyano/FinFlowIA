from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "FinanceAI"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    # Comma-separated in the environment (CORS_ORIGINS=https://a.app,https://b.app)
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    # Database
    database_url: str = "postgresql+asyncpg://financeai:local_password@localhost:5432/financeai"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379"

    # LLM
    anthropic_api_key: str = "sk-ant-placeholder"
    openai_api_key: str | None = None
    llm_provider: str = "openai"
    llm_cache_ttl_seconds: int = 3600

    # Auth / Security
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 60
    bcrypt_rounds: int = 12

    # Observability
    prometheus_enabled: bool = True
    otel_exporter_otlp_endpoint: str | None = None
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                import json

                return json.loads(value)
            return [o.strip().rstrip("/") for o in value.split(",") if o.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def _async_database_url(cls, value: object) -> object:
        """Accept the URL as hosting providers hand it out (Neon, Render, ...)."""
        if not isinstance(value, str):
            return value
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                value = "postgresql+asyncpg://" + value[len(prefix) :]
        # asyncpg does not understand libpq's sslmode / channel_binding params
        value = value.replace("sslmode=", "ssl=")
        value = value.replace("&channel_binding=require", "").replace(
            "channel_binding=require&", ""
        )
        return value


settings = Settings()
