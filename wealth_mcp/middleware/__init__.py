"""WEALTH Evidence Middleware — W0.
Enforces verification integrity on every tool call.
Catches: silent input dropping, verdict conflicts, null→green coercion.
"""

from wealth_mcp.middleware.evidence_middleware import WealthEvidenceMiddleware

__all__ = ["WealthEvidenceMiddleware"]
