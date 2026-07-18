"""
WEALTH Commodity Engine Bridge — Internal HTTP to :3456-3458.
Gold, Oil, Gas are internal engines, NOT separate organs.
WEALTH capital_market tool routes through this bridge.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

# Engine ports (internal only — NOT exposed via MCP)
ENGINE_PORTS = {
    "gold": 3456,
    "oil": 3457,
    "gas": 3458,
}

# Supported operations per engine
# Engine actual endpoints:
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

DEFAULT_OPERATION = "snapshot"

# Timeout for engine calls
ENGINE_TIMEOUT = 15.0  # seconds


async def call_engine(
    asset: str,
    operation: str = DEFAULT_OPERATION,
    extra_params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Call an internal commodity engine (:3456-3458).

    Args:
        asset: "gold", "oil", or "gas"
        operation: "ticker", "signal", "signals", "history", "macro",
                   "levels", "calendar", "apex", "snapshot", "regime"
        extra_params: Optional query parameters

    Returns:
        Engine response as dict
    """
    asset = asset.lower().strip()
    operation = operation.lower().strip()

    if asset not in ENGINE_PORTS:
        return {
            "error": True,
            "message": f"Unknown asset '{asset}'. Valid: {', '.join(ENGINE_PORTS.keys())}",
            "asset": asset,
        }

    port = ENGINE_PORTS[asset]
    valid_ops = VALID_OPERATIONS[asset]

    if operation not in valid_ops:
        operation = DEFAULT_OPERATION

    path = f"/api/{asset}/{operation}"
    url = f"http://127.0.0.1:{port}{path}"

    try:
        import urllib.request

        req = urllib.request.Request(url, method="GET")
        if extra_params:
            from urllib.parse import urlencode

            url += "?" + urlencode(extra_params)
            req = urllib.request.Request(url, method="GET")

        with urllib.request.urlopen(req, timeout=ENGINE_TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)

        return {
            "asset": asset,
            "operation": operation,
            "source": f"engine:{asset}:{port}",
            "data": data,
            "error": False,
        }

    except Exception as e:
        return {
            "asset": asset,
            "operation": operation,
            "source": f"engine:{asset}:{port}",
            "error": True,
            "message": str(e),
            "data": None,
        }


async def get_ticker(asset: str) -> dict[str, Any]:
    """Get latest price ticker for an asset."""
    return await call_engine(asset, "ticker")


async def get_signal(asset: str) -> dict[str, Any]:
    """Get latest trading signal for an asset."""
    return await call_engine(asset, "signal_v2")


async def get_macro(asset: str) -> dict[str, Any]:
    """Get macro context for an asset."""
    return await call_engine(asset, "macro")


async def get_history(asset: str, limit: int = 100) -> dict[str, Any]:
    """Get price history for an asset."""
    return await call_engine(asset, "history", {"limit": str(limit)})


async def get_levels(asset: str) -> dict[str, Any]:
    """Get support/resistance levels for an asset."""
    return await call_engine(asset, "levels")


async def get_snapshot(asset: str) -> dict[str, Any]:
    """
    Get full market snapshot for an asset.
    Aggregates ticker + signal + macro into one response.
    """
    ticker, signal, macro = await asyncio.gather(
        get_ticker(asset),
        get_signal(asset),
        get_macro(asset),
    )

    return {
        "asset": asset,
        "snapshot": {
            "ticker": ticker.get("data"),
            "signal": signal.get("data"),
            "macro": macro.get("data"),
        },
        "sources": {
            "ticker": ticker.get("source"),
            "signal": signal.get("source"),
            "macro": macro.get("source"),
        },
        "errors": {
            k: v.get("error")
            for k, v in [("ticker", ticker), ("signal", signal), ("macro", macro)]
            if v.get("error")
        },
    }
