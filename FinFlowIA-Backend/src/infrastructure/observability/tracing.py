"""
OpenTelemetry distributed tracing setup.
Phase 2 implementation — currently a stub that can be enabled via environment variables.
"""

import structlog

logger = structlog.get_logger(__name__)


def setup_tracing(service_name: str = "finflowia-backend", endpoint: str | None = None) -> None:
    """
    Initialize OpenTelemetry tracing.
    If OTEL_EXPORTER_OTLP_ENDPOINT is set, exports traces to the configured endpoint.
    """
    if not endpoint:
        logger.info("tracing_disabled", reason="OTEL_EXPORTER_OTLP_ENDPOINT not configured")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource

        resource = Resource(attributes={SERVICE_NAME: service_name})
        provider = TracerProvider(resource=resource)
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        trace.set_tracer_provider(provider)

        logger.info("tracing_enabled", service=service_name, endpoint=endpoint)
    except ImportError:
        logger.warning(
            "tracing_unavailable",
            reason="opentelemetry packages not installed. Add opentelemetry-sdk to deps.",
        )
