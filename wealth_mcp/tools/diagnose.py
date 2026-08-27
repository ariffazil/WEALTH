"""
WEALTH capital_diagnose — Abductive institutional diagnostics — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations
from typing import Any

from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality
from wealth_mcp.tools.types import CoercedDict, CoercedDictListStrict, CoercedStrList


def register_diagnose(mcp):
    """Register the diagnose tool on the given FastMCP instance."""
    # ═══════════════════════════════════════════════════════════════════
    # 3. capital_diagnose — Abductive institutional diagnostics
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_diagnose",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description="Abductive institutional diagnostics — inference from partial evidence across stress, governance, and institutional domains. SIDE EFFECT: writes a vault receipt to /root/VAULT999/wealth/receipts.jsonl (per wealth-organ.service.d/receipts-write.conf). Receipts include call_status=PASS/FAIL and input hashes.",
        tags={"domain": "institutional", "kind": "abductive", "canonical": "v1"},
    )
    async def capital_diagnose(
        mode: str,
        domain_scope: str = "",
        payload: CoercedDict = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        """Mode-dispatched institutional diagnostics (ZEN 2026-07-11 W3).

        Surface: mode, domain_scope, payload. Mode-specific fields in payload.
        domain_scope: unknown fields REJECTED by engines (not zeroed). Math unchanged.
        """
        # Coerce MCP transport string serialization

        m = str(mode).lower()
        p: dict[str, Any] = dict(payload or {})

        if m == "stress_index":
            from wealth_core.institutional import compute_stress_index

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_stress_index(
                    p.get("org_name") or "",
                    p.get("financial_signals") or {},
                    p.get("governance_signals") or {},
                    p.get("workforce_signals") or {},
                    p.get("legal_signals") or {},
                    p.get("exploitation_signals") or {},
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "financial_signals",
                    "governance_signals",
                    "workforce_signals",
                ],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "governance_capacity":
            from wealth_core.institutional import compute_governance_capacity

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_governance_capacity(
                    p.get("board_members") or [],
                    p.get("committees") or [],
                    float(p.get("stress_level", 0.3)),
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["governance_analysis"],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "cascade_model":
            from wealth_core.institutional import compute_cascade

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_cascade(
                    p.get("timeline") or [], p.get("intervention_scenario")
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["cascade_model"],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "exploitation_detect":
            from wealth_core.institutional import compute_exploitation

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_exploitation(
                    p.get("counterparty_actions") or [],
                    p.get("institution_state") or {},
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["exploitation_detection"],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "collapse_signature":
            from wealth_core.collapse_signature.scanner import compute_collapse_risk

            return wrap_result(
                tool_name="capital_diagnose",
                domain="collapse",
                result=compute_collapse_risk(
                    p.get("scenario") or p.get("domain_scope") or ""
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["collapse_corpus:enron,pdvsa,pemex,1mdb,worldcom"],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "beautiful_mouse":
            from wealth_core.collapse_signature.beautiful_mouse import (
                compute_beautiful_mouse_score,
            )

            return wrap_result(
                tool_name="capital_diagnose",
                domain="collapse",
                result=compute_beautiful_mouse_score(p.get("text") or ""),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["calhoun_phase_c_indicators"],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "capture_scan":
            from wealth_core.power.capture_detector import detect_capture

            advice = p.get("advice_text") or ""
            src_model = p.get("source_model") or ""

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=detect_capture(
                    scenario=advice,
                    actors=p.get("actors") or [],
                    context=p.get("context") or {"source_model": src_model},
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                source_attribution=[f"model:{src_model}"] if src_model else [],
            )

        if m == "power_audit":
            from wealth_core.power import audit_power

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=audit_power(
                    p.get("scenario") or "",
                    actors=p.get("actor_list"),
                    context=p.get("context"),
                ),
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                source_attribution=["scenario_text_analysis"],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m in ("petronas_vitals", "sovereign_pulse", "petronas_phi"):
            # COMPUTE_ONLY distance-to-trip organ — no allocation, no trade signal
            from wealth_core.petronas_vitals import compute_petronas_vitals

            result = compute_petronas_vitals(
                tripwires=p.get("tripwires"),
                weights=p.get("weights"),
            )
            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=result,
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "PETRONAS Group FRA FY2025 IFR",
                    "wealth_core.petronas_vitals",
                    "arif-fazil.com/vitals",
                ],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "bid_surface":
            from wealth_mcp.tools.bid_surface import compute_bid_surface

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=compute_bid_surface(p.get("bids") or []),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["bid_scoring_surface"],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "optimize_mwc":
            from wealth_mcp.tools.optimize_mwc import compute_mwc

            return wrap_result(
                tool_name="capital_diagnose",
                domain="power",
                result=compute_mwc(
                    p.get("players") or [],
                    float(p.get("majority_threshold", 0.5)),
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["mwc_optimization"],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "cadence_monitor":
            from wealth_core.institutional.cadence import compute_cadence

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_cadence(
                    approval_cycles=p.get("approval_cycles"),
                    payment_cycles=p.get("payment_cycles"),
                    meeting_logs=p.get("meeting_logs"),
                    contract_signatures=p.get("contract_signatures"),
                    budget_releases=p.get("budget_releases"),
                    org_name=p.get("org_name", domain_scope),
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "approval_cycle_trend",
                    "payment_cycle_trend",
                    "meeting_decision_ratio",
                    "contract_velocity",
                    "budget_release_timing",
                ],
                session_id=session_id,
                actor_id=actor_id,
            )

        if m == "crisis_reflex":
            from wealth_core.institutional.crisis_reflex import compute_crisis_reflex

            return wrap_result(
                tool_name="capital_diagnose",
                domain="institutional",
                result=compute_crisis_reflex(
                    capital_allocation=p.get("capital_allocation"),
                    capability_moves=p.get("capability_moves"),
                    truth_events=p.get("truth_events"),
                    burden_data=p.get("burden_data"),
                    decision_shifts=p.get("decision_shifts"),
                    recovery_data=p.get("recovery_data"),
                    external_events=p.get("external_events"),
                    dignity_data=p.get("dignity_data"),
                    org_name=p.get("org_name", domain_scope),
                ),
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "capital_allocation",
                    "capability_moves",
                    "truth_events",
                    "burden_distribution",
                    "decision_shifts",
                    "recovery_investment",
                    "external_posture",
                    "human_dignity",
                ],
                session_id=session_id,
                actor_id=actor_id,
            )

        # ═══ REGIME MAP — TradeMaster distillation (2026-08-18) ═══
        if m == "regime_map":
            import sys as _sys

            _wealth_root = "/root/WEALTH"
            if _wealth_root not in _sys.path:
                _sys.path.insert(0, _wealth_root)

            from wealth_core.regime_map import compute_regime_map

            # Accept OHLCV data in payload: {closes: [...], highs: [...], lows: [...]}
            closes = p.get("closes") or []
            highs = p.get("highs") or []
            lows = p.get("lows") or []
            window = int(p.get("window", 20))
            atr_period = int(p.get("atr_period", 14))

            if not closes or not highs or not lows:
                return wrap_result(
                    tool_name="capital_diagnose",
                    domain="market",
                    result={
                        "status": "ERROR",
                        "error_code": "MISSING_DATA",
                        "message": "regime_map requires payload.closes, payload.highs, payload.lows (arrays of float)",
                    },
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    session_id=session_id,
                    actor_id=actor_id,
                )

            result = compute_regime_map(closes, highs, lows, window, atr_period)
            return wrap_result(
                tool_name="capital_diagnose",
                domain="market",
                result={
                    "current_regime": result.current_regime,
                    "current_confidence": result.current_confidence,
                    "volatility_state": result.volatility_state,
                    "trend_strength": result.trend_strength,
                    "regime_distribution": result.regime_distribution,
                    "transitions": [
                        {
                            "from": t.from_regime,
                            "to": t.to_regime,
                            "count": t.count,
                            "probability": t.probability,
                        }
                        for t in result.transitions
                    ],
                    "recent_bars": result.regime_bars,
                    "distribution_shift_detected": result.distribution_shift_detected,
                    "shift_severity": result.shift_severity,
                    "bars_analyzed": result.bars_analyzed,
                    "window_size": result.window_size,
                },
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "regime_map_engine",
                    "distribution_shift_detection",
                ],
                session_id=session_id,
                actor_id=actor_id,
            )

        # Loop 9 fix: return structured error for unknown mode (was: ValueError with incomplete mode list)
        _VALID_MODES = [
            "stress_index",
            "governance_capacity",
            "cascade_model",
            "exploitation_detect",
            "collapse_signature",
            "beautiful_mouse",
            "capture_scan",
            "power_audit",
            "bid_surface",
            "optimize_mwc",
            "cadence_monitor",
            "crisis_reflex",
            "petronas_vitals",
            "sovereign_pulse",
            "petronas_phi",
            "regime_map",
        ]
        return wrap_result(
            tool_name="capital_diagnose",
            domain="institutional",
            result={
                "status": "ERROR",
                "error_code": "UNKNOWN_MODE",
                "message": f"Unknown mode '{mode}'. Valid: {', '.join(_VALID_MODES)}",
                "valid_modes": _VALID_MODES,
            },
            epistemic_tag=EpistemicTag.ASSUMED,
            evidence_quality=EvidenceQuality.MISSING,
            errors=[f"Unknown mode '{mode}'. Valid: {', '.join(_VALID_MODES)}"],
            session_id=session_id,
            actor_id=actor_id,
        )

    # capital_wisdom DELETED 2026-08-06 — M0 audit. Normative synthesis
    # violates 'WEALTH computes, arifOS frames'. F13 directive: DELETE.
    # 120 lines removed. arifOS owns framing; WEALTH owns computation.
