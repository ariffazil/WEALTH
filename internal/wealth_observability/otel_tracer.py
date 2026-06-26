"""
WEALTH OpenTelemetry Tracer.

Per executive verdict Phase 1: "Add OpenTelemetry spans for every MCP call."
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Any, Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

_initialized = False


def init_wealth_tracer(
    otlp_endpoint: Optional[str] = None,
    console_export: bool = False,
) -> trace.Tracer:
    """Initialize the WEALTH OpenTelemetry tracer (idempotent)."""
    global _initialized
    if _initialized:
        return trace.get_tracer("wealth")

    resource = Resource.create(
        {
            "service.name": "WEALTH",
            "service.version": "2026.06.06",
            "arifos.organ": "WEALTH",
            "arifos.evidence_only": True,  # F13: WEALTH never executes
        }
    )

    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
        )

    if console_export:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _initialized = True
    return trace.get_tracer("wealth")


class WealthOTelTracer:
    """High-level wrapper for WEALTH tool spans."""

    def __init__(self):
        self.tracer = init_wealth_tracer()

    @contextmanager
    def span(self, name: str, attributes: Optional[dict[str, Any]] = None):
        """Context-managed span with WEALTH attribute schema."""
        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(
                        k, str(v) if not isinstance(v, (str, int, float, bool)) else v
                    )
            span.set_attribute("arifos.organ", "WEALTH")
            span.set_attribute("arifos.evidence_only", True)
            span.set_attribute("arifos.epoch", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            try:
                yield span
            except Exception as e:
                span.set_attribute("arifos.error", str(e))
                span.record_exception(e)
                raise
