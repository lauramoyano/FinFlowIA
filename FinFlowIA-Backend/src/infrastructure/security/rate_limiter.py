import time
from collections import defaultdict
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class InMemoryRateLimiter:
    """
    Simple in-memory token bucket rate limiter.
    For production use, replace with Redis-backed sliding window rate limiter.
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        self._requests_per_minute = requests_per_minute
        self._window_seconds = 60
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if a request is within rate limits for the given key."""
        now = time.time()
        window_start = now - self._window_seconds

        # Remove expired timestamps
        self._buckets[key] = [ts for ts in self._buckets[key] if ts > window_start]

        if len(self._buckets[key]) < self._requests_per_minute:
            self._buckets[key].append(now)
            return True

        return False

    def get_remaining(self, key: str) -> int:
        """Get the number of remaining requests for the given key."""
        now = time.time()
        window_start = now - self._window_seconds
        recent = [ts for ts in self._buckets.get(key, []) if ts > window_start]
        return max(0, self._requests_per_minute - len(recent))


_auth_limiter = InMemoryRateLimiter(requests_per_minute=10)
_api_limiter = InMemoryRateLimiter(requests_per_minute=100)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that applies rate limiting based on client IP.
    Auth endpoints have stricter limits to prevent brute-force attacks.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Apply stricter limits to auth endpoints
        if path.startswith("/api/v1/auth"):
            limiter = _auth_limiter
            limit_type = "auth"
        else:
            limiter = _api_limiter
            limit_type = "api"

        if not limiter.is_allowed(client_ip):
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                path=path,
                limit_type=limit_type,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please slow down.",
                    }
                },
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(limiter.get_remaining(client_ip))
        return response
