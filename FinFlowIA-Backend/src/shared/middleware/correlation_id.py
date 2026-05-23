import uuid
from collections.abc import Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store correlation ID across async boundaries
_correlation_id_ctx_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Get the current request's correlation ID from context."""
    return _correlation_id_ctx_var.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that reads or generates a correlation ID for each request.
    The ID is stored in request.state and returned in the X-Correlation-ID response header.
    This enables end-to-end request tracing across services and logs.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Use incoming header if present, otherwise generate new UUID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Store on request state for use in handlers
        request.state.correlation_id = correlation_id

        # Store in context var for use in async background tasks
        token = _correlation_id_ctx_var.set(correlation_id)

        try:
            response = await call_next(request)
        finally:
            _correlation_id_ctx_var.reset(token)

        # Always return the correlation ID in response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response
