"""
WEALTH Commodity Engine Bridge — Internal HTTP to :3456-3458.
Gold, Oil, Gas are internal engines, NOT separate organs.
WEALTH capital_market tool routes through this bridge.

Epistemic contract:
- Price/ticker data → OBSERVED
- Technical indicators (EMA, RSI, ATR) → DERIVED
- Trading signals (LONG/SHORT) → INTERPRETED, never authorization
- Ports :3456-3458 are INTERNAL ONLY — never exposed in public output

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

# Engine ports (internal only — NOT exposed via MCP)
# Source repo: ariffazil/WEALTH/engines/commodity/{gold,oil,gas}-api/
ENGINE_PORTS = {
    "gold": 3456,
    "oil": 3457,
    "gas": 3458,
}

# Engine endpoint naming:
#   /api/{asset}/ticker     — current price + indicators
#   /api/{asset}/signal_v2  — trading signal (direction, confidence)
#   /api/{asset}/signals    — recent signals list
#   /api/{asset}/macro      — macro context
#   /api/{asset}/history    — price history
#   /api/{asset}/levels     — support/resistance
#   /api/{asset}/calendar   — economic events
#   /api/{asset}/apex       — apex prediction
#   /api/{asset}/daily_brief — daily briefing
VALID_OPERATIONS = {
    "gold": {
        "ticker",
        "signal_v2",
        "signals",
        "history",
        "macro",
        "levels",
        "calendar",
        "apex",
        "daily_brief",
        "snapshot",
    },
    "oil": {
        "ticker",
        "signal_v2",
        "signals",
        "history",
        "macro",
        "levels",
        "calendar",
        "apex",
        "daily_brief",
        "snapshot",
    },
    "gas": {
        "ticker",
        "signal_v2",
        "signals",
        "history",
        "macro",
        "levels",
        "calendar",
        "apex",
        "daily_brief",
        "snapshot",
    },
}

# Public operations (documented in capital_market schema)
PUBLIC_OPERATIONS = {"snapshot", "ticker", "signal", "macro", "history", "levels"}

DEFAULT_OPERATION = None  # No default — fail if invalid

# Timeout for engine calls
ENGINE_TIMEOUT = 15.0  # seconds

# HTTP engine path prefix
ENGINE_PATH_PREFIX = "/api/{asset}/{operation}"


async def _http_get(url: str, timeout: float = ENGINE_TIMEOUT) -> dict[str, Any]:
    """Async HTTP GET with timeout and retry. Uses httpx via retry utility."""
    from wealth_core.http_retry import async_fetch_with_retry
    return await async_fetch_with_retry(
        url, timeout=timeout, provider="internal_commodity",
    )


async def call_engine(
    asset: str,
    operation: str,
    extra_params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Call an internal commodity engine (:3456-3458).

    Args:
        asset: "gold", "oil", or "gas"
        operation: Valid operation from VALID_OPERATIONS[asset]
        extra_params: Optional query parameters

    Returns:
        Engine response as dict with standard envelope.

    Raises:
        ValueError: If asset or operation is invalid.
    """
    asset = asset.lower().strip()
    operation = operation.lower().strip()

    # — Fail-closed: unknown asset —
    if asset not in ENGINE_PORTS:
        return {
            "error": True,
            "code": "UNKNOWN_ASSET",
            "message": f"Unknown asset '{asset}'. Allowed: {', '.join(sorted(ENGINE_PORTS.keys()))}",
            "asset": asset,
            "requested_operation": operation,
            "source": "wealth://commodity",
        }

    port = ENGINE_PORTS[asset]
    valid_ops = VALID_OPERATIONS[asset]

    # — Fail-closed: unknown operation (never silently fallback) —
    if operation not in valid_ops:
        return {
            "error": True,
            "code": "UNKNOWN_OPERATION",
            "message": f"Unknown operation '{operation}' for asset '{asset}'. "
            f"Allowed: {', '.join(sorted(valid_ops))}",
            "asset": asset,
            "requested_operation": operation,
            "source": "wealth://commodity",
        }

    # Build engine URL (port is internal implementation detail)
    path = ENGINE_PATH_PREFIX.format(asset=asset, operation=operation)
    url = f"http://127.0.0.1:{port}{path}"

    if extra_params:
        from urllib.parse import urlencode

        url += "?" + urlencode(extra_params)

    try:
        data = await _http_get(url)

        # Phase 1c: _http_get now returns error dicts on failure (not exceptions)
        if isinstance(data, dict) and data.get("status") == "ERROR":
            return {
                "asset": asset,
                "operation": operation,
                "source": "wealth://commodity",
                "error": True,
                "code": data.get("error_code", "ENGINE_FAILURE"),
                "message": data.get("message", "Engine returned error response"),
                "data": None,
            }

        return {
            "asset": asset,
            "operation": operation,
            "source": "wealth://commodity",
            "data": data,
            "error": False,
        }

    except Exception as e:
        return {
            "asset": asset,
            "operation": operation,
            "source": "wealth://commodity",
            "error": True,
            "code": "ENGINE_FAILURE",
            "message": str(e),
            "data": None,
        }


async def get_ticker(asset: str) -> dict[str, Any]:
    """Get latest price ticker for an asset (OBSERVED class)."""
    return await call_engine(asset, "ticker")


async def get_signal(asset: str) -> dict[str, Any]:
    """Get latest trading signal for an asset (INTERPRETED class)."""
    return await call_engine(asset, "signal_v2")


async def get_macro(asset: str) -> dict[str, Any]:
    """Get macro context for an asset (OBSERVED + DERIVED)."""
    return await call_engine(asset, "macro")


async def get_history(asset: str, limit: int = 100) -> dict[str, Any]:
    """Get price history for an asset (OBSERVED class)."""
    return await call_engine(asset, "history", {"limit": str(limit)})


async def get_levels(asset: str) -> dict[str, Any]:
    """Get support/resistance levels for an asset (DERIVED class)."""
    return await call_engine(asset, "levels")


async def get_snapshot(asset: str) -> dict[str, Any]:
    """
    Get full market snapshot for an asset.
    Aggregates ticker (OBSERVED) + signal (INTERPRETED) + macro (OBSERVED/DERIVED)
    into one response. Partial success preserved.
    """
    ticker, signal_result, macro = await asyncio.gather(
        get_ticker(asset),
        get_signal(asset),
        get_macro(asset),
    )

    snapshot = {}
    errors = {}

    if ticker.get("error"):
        errors["ticker"] = ticker["message"]
    else:
        snapshot["ticker"] = ticker.get("data")

    if signal_result.get("error"):
        errors["signal"] = signal_result["message"]
    else:
        snapshot["signal"] = signal_result.get("data")

    if macro.get("error"):
        errors["macro"] = macro["message"]
    else:
        snapshot["macro"] = macro.get("data")

    return {
        "asset": asset,
        "source": "wealth://commodity",
        "snapshot": snapshot,
        "errors": errors if errors else None,
        "partial": len(errors) > 0,
    }
