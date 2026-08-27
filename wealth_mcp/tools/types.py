"""
WEALTH shared types and coercion helpers for per-tool modules.

Extracted from canonical.py (Phase 1a split) to avoid duplication.
DITEMPA BUKAN DIBERI — Forged from the SVB backtest, not given.
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from pydantic import BeforeValidator


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
