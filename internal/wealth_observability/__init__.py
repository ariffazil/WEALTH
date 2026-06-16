"""
WEALTH Observability — OpenTelemetry tracer for WEALTH.

Per executive verdict: "Add OpenTelemetry spans for every MCP call."
WEALTH was missing OTel — adding it now as Phase 1 of the substrate hardening.
"""

from .otel_tracer import WealthOTelTracer, init_wealth_tracer

__all__ = ["WealthOTelTracer", "init_wealth_tracer"]
