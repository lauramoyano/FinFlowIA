# multi-stage production build
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install uv

COPY pyproject.toml ./
# Create a minimal lock if uv.lock doesn't exist
RUN uv sync --no-dev 2>/dev/null || pip install -r <(uv export --no-dev 2>/dev/null || echo "") || true

# Copy source files for build
COPY src/ ./src/

FROM python:3.12-slim AS runner

WORKDIR /app

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Install production deps
RUN pip install uv
COPY pyproject.toml ./
RUN uv sync --no-dev || pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic[email] pydantic-settings python-jose[cryptography] passlib[bcrypt] httpx tenacity structlog prometheus-client anthropic openai redis[hiredis] python-multipart

# Copy application source
COPY --from=builder /app/src ./src/

RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH="/app"
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
