"""
WEALTH shared types and coercion helpers for per-tool modules.

Extracted from canonical.py (Phase 1a split) to avoid duplication.
DITEMPA BUKAN DIBERI — Forged from the SVB backtest, not given.
"""

from __future__ import annotations

import datetime as _dt
import json
from enum import Enum
from typing import Annotated, Any

from pydantic import BeforeValidator


# ── L1 Market Signal Typing (2026-09-16) ──────────────────────────────
# Every market data point carries a signal_state that tells the consumer
# exactly what kind of evidence they're looking at.
# Brent/gold incident proof: a number without state is theatre.
class SignalState(str, Enum):
    """Market signal freshness/state classification.

    LIVE:              Fresh from source, observed right now.
    HISTORICAL_STALE:  Data exists but exceeds freshness window.
    UNAVAILABLE:       Source returned no data.
    CONFLICTED:        Multiple sources disagree beyond threshold.
    DERIVED:           Computed from other data, not directly observed.
    ASSUMED:           Filled with default/assumption, not sourced.
    """
    LIVE = "LIVE"
    HISTORICAL_STALE = "HISTORICAL_STALE"
    UNAVAILABLE = "UNAVAILABLE"
    CONFLICTED = "CONFLICTED"
    DERIVED = "DERIVED"
    ASSUMED = "ASSUMED"


def classify_signal_state(
    data: Any,
    source_available: bool = True,
    is_cached: bool = False,
    cache_age_seconds: float | None = None,
    max_fresh_seconds: float = 300,  # 5 min default freshness window
    sources_agree: bool = True,
    is_derived: bool = False,
    is_assumed: bool = False,
) -> dict[str, Any]:
    """Classify a market signal's freshness/state.

    Returns dict with signal_state, signal_state_reason, and data_age_seconds.
    The four-truth T_semantic uses this to determine if output is decision-eligible.
    """
    reasons = []
    age = cache_age_seconds

    # Priority order: UNAVAILABLE > CONFLICTED > ASSUMED > STALE > DERIVED > LIVE
    if not source_available or data is None:
        return {
            "signal_state": SignalState.UNAVAILABLE.value,
            "signal_state_reason": "source returned no data",
            "data_age_seconds": None,
        }

    if not sources_agree:
        reasons.append("multiple sources disagree")
        return {
            "signal_state": SignalState.CONFLICTED.value,
            "signal_state_reason": "; ".join(reasons),
            "data_age_seconds": age,
        }

    if is_assumed:
        return {
            "signal_state": SignalState.ASSUMED.value,
            "signal_state_reason": "filled with default/assumption",
            "data_age_seconds": age,
        }

    if is_cached and age is not None and age > max_fresh_seconds:
        return {
            "signal_state": SignalState.HISTORICAL_STALE.value,
            "signal_state_reason": f"cache age {age:.0f}s > max {max_fresh_seconds:.0f}s",
            "data_age_seconds": age,
        }

    if is_derived:
        return {
            "signal_state": SignalState.DERIVED.value,
            "signal_state_reason": "computed from other data, not directly observed",
            "data_age_seconds": age,
        }

    return {
        "signal_state": SignalState.LIVE.value,
        "signal_state_reason": "fresh from source",
        "data_age_seconds": age or 0,
    }


def _coerce_json_string(v: Any) -> Any:
    """Coerce MCP transport string serialization back to native types.

    FastMCP/Pydantic validates parameters BEFORE function body runs.
    This validator runs at schema level via Annotated[..., BeforeValidator].
    """
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (json.JSONDecodeError, ValueError):
            return v
    return v


def _coerce_dict_to_list_of_dicts(v: Any) -> Any:
    """Coerce a single dict into list-of-dicts. F1 AMANAH: prevents silent
    input dropping when MCP transport serializes a single dict instead of
    a list of dicts. Applies to all CoercedDictList parameters."""
    v = _coerce_json_string(v)
    if isinstance(v, dict):
        return [v]
    return v


# Schema-level coerced types — Pydantic validates AFTER coercion
CoercedList = Annotated[list[float] | None, BeforeValidator(_coerce_json_string)]
CoercedIntList = Annotated[list[int] | None, BeforeValidator(_coerce_json_string)]
CoercedDict = Annotated[dict | None, BeforeValidator(_coerce_json_string)]
CoercedDictList = Annotated[list[dict] | None, BeforeValidator(_coerce_json_string)]
CoercedDictListStrict = Annotated[
    list[dict] | None, BeforeValidator(_coerce_dict_to_list_of_dicts)
]
CoercedStrList = Annotated[list[str] | None, BeforeValidator(_coerce_json_string)]


# ── Helper: resolve legacy engines by direct import (ZEN 2026-07-11 W5) ──
async def _call_legacy_tool(tool_name: str, arguments: dict) -> dict:
    """Dispatch to in-process engine functions (legacy MCP names as keys)."""
    from wealth_mcp import (
        CAPITAL_TOOL_NAMES,
        PUBLIC_TOOL_NAMES,
        WEALTH_VERSION,
    )

    args = dict(arguments or {})
    try:
        if tool_name in ("wealth_market_data", "market_data"):
            from internal.monolith import wealth_market_data

            if str(args.get("mode", "")).lower() == "indicator":
                args = {**args, "mode": "macro"}
            result = wealth_market_data(**args)
            return result if isinstance(result, dict) else {"result": result}

        if tool_name in ("wealth_stock_analysis", "stock_analysis"):
            from internal.monolith import wealth_stock_analysis

            result = await wealth_stock_analysis(**args)
            return result if isinstance(result, dict) else {"result": result}

        if tool_name in ("wealth_vault_query", "vault_query"):
            from host.governance.vault_supabase import query_vault999_async

            q = args.get("query") or args.get("asset_id") or ""
            raw = await query_vault999_async(
                query=str(q),
                limit=int(args.get("limit") or 10),
                session_id=args.get("session_id"),
            )
            return {
                "query": raw.get("query", q),
                "earth_refs": raw.get("earth_refs", []),
                "count": raw.get("count", 0),
                "vault_seal": raw.get("vault_seal", "VAULT999"),
                "status": "OK",
                "read_only": True,
            }

        if tool_name in ("wealth_vault_write", "vault_write"):
            import asyncio

            from host.governance.vault_supabase import append_vault999

            action = str(args.get("tx_type") or args.get("action") or "capital_tx")
            record = {
                "tool": "capital_ledger",
                "action": action,
                "payload": {
                    "amount": args.get("amount"),
                    "amount_satoshi": args.get("amount_satoshi"),
                    "currency": args.get("currency"),
                    "description": args.get("description"),
                    "payment_hash": args.get("payment_hash"),
                },
                "verdict": "SEAL",
                "session_id": args.get("session_id"),
                "trace_id": args.get("trace_id"),
                "actor_id": args.get("actor_id"),
            }
            result = await asyncio.to_thread(append_vault999, record)
            if not isinstance(result, dict):
                return {
                    "status": "ERROR",
                    "error": "VAULT999 append returned no observable result.",
                }

            persistence = result.get("persistence") or {
                "status": "UNCONFIRMED",
                "error": "VAULT999 append did not report persistence state.",
            }
            response = {
                "status": persistence.get("status", "UNCONFIRMED"),
                "action": action,
                "persistence": persistence,
                "integrity": result.get("integrity"),
            }
            vault_id = result.get("event_id") or result.get("ledger_id")
            chain_hash = result.get("chain_hash")
            if vault_id:
                response["vault_id"] = vault_id
            if chain_hash:
                response["chain_hash"] = chain_hash
            return response

        if tool_name in (
            "wealth_registry_status",
            "wealth_system_registry_status",
            "registry_status",
        ):
            from internal.monolith import wealth_system_registry_status

            result = await wealth_system_registry_status(
                mode=str(args.get("mode") or "registry")
            )
            return result if isinstance(result, dict) else {"result": result}

        if tool_name in ("wealth_schema", "schema"):
            return {
                "organ": "WEALTH",
                "version": WEALTH_VERSION,
                "role": "Capital Intelligence for arifOS federation",
                "authority": "WEALTH computes. arifOS judges. Arif decides.",
                "canonical_tools": list(CAPITAL_TOOL_NAMES),
                "canonical_tool_count": len(CAPITAL_TOOL_NAMES),
                "public_tools": list(PUBLIC_TOOL_NAMES),
                "public_tool_count": len(PUBLIC_TOOL_NAMES),
                "legacy_mcp_dispatch": "direct_import",
            }

        if tool_name in ("wealth_survival_engine", "survival_engine"):
            from internal.monolith import wealth_survival_engine

            result = await wealth_survival_engine(**args)
            return result if isinstance(result, dict) else {"result": result}

        if tool_name in ("wealth_omni_wisdom", "omni_wisdom"):
            from internal.monolith import wealth_omni_wisdom

            result = await wealth_omni_wisdom(**args)
            return result if isinstance(result, dict) else {"result": result}

        return {
            "error": f"legacy_dispatch_failed: {tool_name}",
            "detail": "no direct import mapping for this legacy name",
        }
    except TypeError as e:
        return {
            "error": f"legacy_dispatch_failed: {tool_name}",
            "detail": f"TypeError: {e}",
            "arguments_keys": sorted(args.keys()),
        }
    except Exception as e:
        return {
            "error": f"legacy_dispatch_failed: {tool_name}",
            "detail": f"{type(e).__name__}: {e}",
        }
