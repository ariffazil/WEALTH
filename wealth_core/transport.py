"""
WEALTH — Transport timeout diagnostics (Fix 8).

Wraps any WEALTH tool call with timeout + structured error response.
On timeout, returns a WealthEnvelope with HOLD claim_state and transport error.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_TIMEOUT_MS = 5000


class TransportTimeoutError(asyncio.TimeoutError):
    """Raised when a WEALTH tool call exceeds the transport timeout."""


def call_with_timeout(
    tool_fn: Callable[..., T],
    *args: Any,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    tool_name: str = "unknown",
    **kwargs: Any,
) -> T | dict[str, Any]:
    """Execute a WEALTH tool call with timeout.

    If the call exceeds timeout_ms, return a HOLD envelope dict
    instead of propagating the timeout.

    Args:
        tool_fn: The WEALTH tool function to call
        timeout_ms: Timeout in milliseconds (default 5000)
        tool_name: Human-readable tool name for error messages

    Returns:
        The tool's return value, or an error envelope dict on timeout
    """
    try:
        if asyncio.iscoroutinefunction(tool_fn):
            return asyncio.run(
                asyncio.wait_for(
                    tool_fn(*args, **kwargs),
                    timeout=timeout_ms / 1000.0,
                )
            )
        else:
            return tool_fn(*args, **kwargs)
    except asyncio.TimeoutError:
        logger.warning(f"Transport timeout for {tool_name} ({timeout_ms}ms)")
        return _timeout_envelope(tool_name, timeout_ms)
    except Exception as exc:
        logger.error(f"Transport error for {tool_name}: {exc}")
        return {
            "verdict": "MATH_ERROR",
            "claim_state": "HOLD",
            "execution_authorized": "NONE",
            "recommendation_only": True,
            "epistemic_status": "DER",
            "warnings": [f"transport_error: {exc}"],
            "errors": ["transport_unreachable"],
            "data": None,
            "notes": f"Transport error calling {tool_name}: {exc}",
        }


def _timeout_envelope(tool_name: str, timeout_ms: int) -> dict[str, Any]:
    """Return a structured HOLD envelope for a transport timeout."""
    return {
        "verdict": "888_HOLD",
        "claim_state": "HOLD",
        "execution_authorized": "NONE",
        "recommendation_only": True,
        "epistemic_status": "DER",
        "data": None,
        "warnings": [f"transport_timeout — kernel degraded, do not trust output"],
        "errors": ["transport_unreachable"],
        "notes": f"Transport timeout calling {tool_name} after {timeout_ms}ms",
    }
