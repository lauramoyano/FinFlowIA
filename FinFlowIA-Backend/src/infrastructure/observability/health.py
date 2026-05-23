from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", include_in_schema=False)
async def health_check() -> dict:
    """Basic health check endpoint for load balancer / container health probes."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "finflowia-backend",
    }


@router.get("/health/detailed")
async def detailed_health(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Detailed health check that verifies connectivity to all dependencies.
    Returns degraded status if any dependency is unhealthy.
    """
    checks: dict = {}

    # Database check
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        logger.error("health_check_db_failed", error=str(e))
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis check
    try:
        from src.infrastructure.cache.redis_client import get_redis_client
        redis = await get_redis_client()
        await redis.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        logger.warning("health_check_redis_failed", error=str(e))
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # Determine overall status
    all_healthy = all(c["status"] == "healthy" for c in checks.values())
    overall = "healthy" if all_healthy else "degraded"

    return {
        "status": overall,
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }
