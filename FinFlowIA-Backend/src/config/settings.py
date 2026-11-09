from pydantic_settings import BaseSettings, SettingsConfigDict


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
    cors_origins: list[str] = ["http://localhost:5173"]

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


settings = Settings()
