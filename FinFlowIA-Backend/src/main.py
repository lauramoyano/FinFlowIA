from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from src.config.settings import settings
from src.infrastructure.cache.redis_client import close_redis_client, get_redis_client
from src.infrastructure.observability.health import router as health_router
from src.infrastructure.observability.tracing import setup_tracing
from src.modules.auth.router import router as auth_router
from src.modules.dashboard.router import router as dashboard_router
from src.modules.reports.router import router as reports_router
from src.modules.transactions.category_router import router as categories_router
from src.modules.transactions.router import router as transactions_router
from src.shared.middleware.correlation_id import CorrelationIdMiddleware
from src.shared.middleware.error_handler import register_exception_handlers
from src.shared.middleware.logging import RequestLoggingMiddleware

logger = structlog.get_logger(__name__)


def configure_structlog() -> None:
    """Configure structlog for JSON structured logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    configure_structlog()

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        debug=settings.debug,
    )

    # Initialize Redis connection
    try:
        redis = await get_redis_client()
        await redis.ping()
        logger.info("redis_connected")
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))

    # Initialize tracing
    setup_tracing(
        service_name="finflowia-backend",
        endpoint=settings.otel_exporter_otlp_endpoint,
    )

    logger.info("application_ready", app_name=settings.app_name)

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await close_redis_client()
    logger.info("application_stopped")


def create_app() -> FastAPI:
    """Factory function for the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description="FinFlowIA — AI-powered financial management for small businesses",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # ─── Middleware (order matters: first added = outermost) ─────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # ─── Rate limiting ────────────────────────────────────────────────────────
    from src.infrastructure.security.rate_limiter import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

    # ─── Exception handlers ───────────────────────────────────────────────────
    register_exception_handlers(app)

    # ─── Routers ─────────────────────────────────────────────────────────────
    API_PREFIX = "/api/v1"

    app.include_router(health_router)
    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(transactions_router, prefix=API_PREFIX)
    app.include_router(categories_router, prefix=API_PREFIX)
    app.include_router(reports_router, prefix=API_PREFIX)
    app.include_router(dashboard_router, prefix=API_PREFIX)

    # ─── Prometheus metrics endpoint ─────────────────────────────────────────
    if settings.prometheus_enabled:
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)

    return app


app = create_app()
