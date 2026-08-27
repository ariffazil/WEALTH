"""
WEALTH capital_market — Market data and stock analysis — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations
import json
from typing import Any

from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality
from wealth_mcp.tools.types import CoercedDict, _call_legacy_tool



def register_market(mcp):
    """Register the market tool on the given FastMCP instance."""
# ═══════════════════════════════════════════════════════════════════
# 5. capital_market — Market data and stock analysis
# ═══════════════════════════════════════════════════════════════════

@mcp.tool(
    name="capital_market",
    output_schema=WEALTH_OUTPUT_SCHEMA,
    description="Market data and commodity intelligence — observational with derived and interpreted fields. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
    tags={"domain": "market", "kind": "observational", "canonical": "v1"},
)
async def capital_market(
    mode: str,
    base: str = "USD",
    targets: str = "MYR,SGD,GBP",
    commodity: str = "brent_crude",
    indicator: str = "usd_myr",
    country: str = "MYS",
    stock_payload: CoercedDict = None,
    asset_class: str = "fx_commodity",
    session_id: str | None = None,
    trace_id: str | None = None,
    actor_id: str | None = None,
) -> dict:
    """Market data (ZEN 2026-07-11 W4). Stock fields in stock_payload."""
    # Coerce MCP transport string serialization

    m = mode.lower()
    sp: dict[str, Any] = dict(stock_payload or {})

    # ━━━ Step 9 (Phase 3 close): asset_class discriminator for crypto ━━━
    # Wires crypto_router to canonical surface. NO new tool created --
    # asset_class is an additive discriminator on the existing tool.
    # Existing modes (fx/commodity/indicator/stock/gold/oil/gas)
    # unchanged because asset_class defaults to "fx_commodity".
    if asset_class == "crypto":
        asset = sp.get("asset", "BTC")
        _valid_kinds = ("spot_price", "24h_change", "depth_top20", "tvl")
        kind = sp.get("kind") or (m if m in _valid_kinds else "spot_price")
        try:
            from wealth_core.ingest.crypto.router import CryptoRouter

            bundle = CryptoRouter().fetch(asset=asset, kind=kind)
        except Exception as e:
            # F12 RESILIENCE: router exceptions don't crash the canonical tool
            return wrap_result(
                tool_name="capital_market",
                domain="capital",
                result={
                    "status": "ERROR",
                    "error_code": "CRYPTO_ROUTER_FAILED",
                    "message": str(e),
                },
                epistemic_tag=EpistemicTag.OBSERVED,
                evidence_quality=EvidenceQuality.WEAK,
                errors=[f"crypto_router raised {type(e).__name__}: {e}"],
                session_id=session_id,
                trace_id=trace_id,
                actor_id=actor_id,
            )
        return wrap_result(
            tool_name="capital_market",
            domain="capital",
            result=bundle.model_dump(),
            epistemic_tag=EpistemicTag.OBSERVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=[
                f"crypto_router:{bundle.provider}",
                bundle.source_uri,
            ],
            session_id=session_id,
            trace_id=trace_id,
            actor_id=actor_id,
        )

    if m == "fx":
        # Phase 1c: direct import, bypass legacy dispatcher
        from internal.monolith import wealth_fx_rate
        raw = wealth_fx_rate(base=base, targets=targets)
        return wrap_result(tool_name="capital_market", domain="capital", result=raw)

    if m == "commodity":
        # Zen Phase 4: route through internal get_snapshot engine
        # instead of stale wealth_market_data legacy path.
        _COMMODITY_MAP = {
            "brent_crude": "oil",
            "wti_crude": "oil",
            "natural_gas_henry": "gas",
            "natural_gas_jkm": "gas",
            "lng_asia": "gas",
            "gold": "gold",
        }
        engine_name = _COMMODITY_MAP.get(commodity.lower().replace(" ", "_"), None)
        if engine_name:
            from wealth_core.commodity_engines import get_snapshot

            raw = await get_snapshot(engine_name)
        else:
            raw = await _call_legacy_tool(
                "wealth_market_data", {"mode": "commodity", "commodity": commodity}
            )
        # Zen C9: cross-witness metadata
        if isinstance(raw, dict):
            raw["_cross_witness"] = {
                "primary_source": "wealth_core.commodity_engines",
                "feed_type": "LIVE" if engine_name else "CACHED",
                "witness_status": "SINGLE_SOURCE",
                "note": "Cross-witness requires second independent source. Delta > 3% would raise WITNESS_DIVERGENCE.",
            }
        return wrap_result(
            tool_name="capital_market",
            domain="capital",
            result=raw,
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=["commodity_engine_live"],
            session_id=session_id,
            trace_id=trace_id,
            actor_id=actor_id,
        )

    if m == "indicator":
        # Phase 1c: direct import, bypass legacy dispatcher
        from internal.monolith import wealth_macro_indicator
        raw = wealth_macro_indicator(indicator=indicator, country=country)
        return wrap_result(tool_name="capital_market", domain="capital", result=raw)

    if m == "stock":
        # Phase 1c: direct import, bypass legacy dispatcher
        from internal.monolith import wealth_stock_analysis
        raw = await wealth_stock_analysis(
            mode=sp.get("stock_mode") or sp.get("mode") or "verify_math",
            ticker=sp.get("ticker") or "",
            entry_price=sp.get("entry_price") or 0,
            exit_price=sp.get("exit_price"),
            current_price=sp.get("current_price"),
            position_size=sp.get("position_size") or 0,
            status=sp.get("status") or sp.get("status_") or "unrealized",
            direction=sp.get("direction") or "long",
            factors=sp.get("factors"),
        )
        return wrap_result(tool_name="capital_market", domain="capital", result=raw)

    # ── Internal engine modes: gold, oil, gas ─────────────────────────
    # These call the internal commodity engines at :3456-3458.
    # WEALTH owns meaning. Engines supply evidence.
    if m in ("gold", "oil", "gas"):
        from wealth_core.commodity_engines import call_engine, get_snapshot

        # Map commodity parameter to operation (backward compat)
        # Preferred: capital_market(mode="gold", operation="snapshot")
        if "operation" in sp and sp["operation"]:
            op = sp["operation"]
        else:
            op = commodity if commodity != "brent_crude" else "snapshot"

        # Map common names to engine endpoint names
        op_map = {
            "signal": "signal_v2",
            "daily": "daily_brief",
        }
        engine_op = op_map.get(op, op)

        if engine_op == "snapshot":
            raw = await get_snapshot(m)
        else:
            raw = await call_engine(m, engine_op)

        # ── FLAME Enrichment (P2, 2026-07-25) ─────────────────────
        # For signal/daily modes, enrich raw engine output with FLAME
        # natural-language interpretation. FLAME is ADVISORY only —
        # it NEVER generates buy/sell/hold recommendations.
        flame_signal = None
        if engine_op in ("signal_v2", "daily_brief"):
            try:
                from tools.flame_client import flame_market_signal

                raw_str = json.dumps(raw) if isinstance(raw, dict) else str(raw)
                flame_signal = flame_market_signal(
                    raw_str, commodity=m, timeout_s=8
                )
            except Exception:
                pass  # FLAME is optional — never block on failure

        result = raw
        if flame_signal:
            result = {
                "engine_output": raw,
                "flame_interpretation": flame_signal,
                "_note": "FLAME interpretation is ADVISORY only. "
                "Verify with governed cascade before any capital decision.",
            }

        return wrap_result(
            tool_name="capital_market",
            domain="capital",
            result=result,
            epistemic_tag=EpistemicTag.OBSERVED
            if engine_op == "snapshot"
            else EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=[f"wealth://commodity/{m}/{engine_op}"],
            session_id=session_id,
            actor_id=actor_id,
        )

    return wrap_result(
        tool_name="capital_market",
        domain="market",
        result={
            "error": f"Unknown mode '{mode}'.",
            "valid_modes": ["fx", "commodity", "indicator", "stock", "gold", "oil", "gas"],
        },
        epistemic_tag=EpistemicTag.DERIVED,
        evidence_quality=EvidenceQuality.WEAK,
        source_attribution=["capital_market:error"],
        session_id=session_id,
        actor_id=actor_id,
    )

