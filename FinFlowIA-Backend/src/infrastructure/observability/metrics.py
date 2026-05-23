from prometheus_client import Counter, Gauge, Histogram

# ─── Business Metrics ───────────────────────────────────────────────────────

transactions_created = Counter(
    "transactions_created_total",
    "Total number of transactions created",
    ["type", "category"],
)

active_users = Gauge(
    "active_users_current",
    "Number of currently active users (last 15 minutes)",
)

# ─── LLM Metrics ────────────────────────────────────────────────────────────

llm_request_duration = Histogram(
    "llm_request_duration_seconds",
    "Duration of LLM API calls in seconds",
    ["provider", "model", "prompt_version"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

llm_tokens_used = Counter(
    "llm_tokens_used_total",
    "Total number of LLM tokens consumed",
    ["provider", "model", "direction"],  # direction: input | output
)

llm_cost_usd = Counter(
    "llm_cost_usd_total",
    "Estimated total LLM cost in USD",
    ["provider", "model"],
)

llm_cache_hits = Counter(
    "llm_cache_hits_total",
    "LLM cache hit/miss events",
    ["result"],  # result: hit | miss
)

llm_errors = Counter(
    "llm_errors_total",
    "Total LLM API errors",
    ["provider", "error_type"],
)

# ─── HTTP API Metrics ────────────────────────────────────────────────────────

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status_code"],
)

# ─── Database Metrics ────────────────────────────────────────────────────────

db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
)

db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)
