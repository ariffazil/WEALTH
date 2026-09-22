"""
WEALTH POLIX/CIVX tools — Power topology + Civilizational scenarios.

Registered as internal WEALTH tools. Not separate organs.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json
from typing import Any

from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality


def register_polix_civx(mcp):
    """Register POLIX and CIVX tools on the given FastMCP instance."""

    # ═══════════════════════════════════════════════════════════════════
    # POLIX — Power Topology Intelligence (L4)
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_polix",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description="Power topology intelligence — incentive mapping, capture detection, rent extraction analysis, rule asymmetry. MODES: topology (full power map), capture (capture risk), rents (rent flows), asymmetry (rule asymmetries). SEED CASES: malaysia_fiscal, petronas_glc (DEPRECATED for non-archival use — call with seed_case=None to refuse a static seed and require caller-supplied material fields). SIDE EFFECT: writes a vault receipt.",
        tags={"domain": "political_economy", "kind": "interpretive", "canonical": "v1"},
    )
    async def capital_polix(
        mode: str = "topology",
        seed_case: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
        caller_service: str | None = None,
    ) -> dict:
        """Power topology analysis for a domain/sector/regime.

        P0 2026-09-21 sovereign directive: drop the static seed-mode default.
        Static seeds returned the same PETRONAS/MoF/BNM actor list regardless
        of what happened this week — zero insight gain on today's news.
        seed_case is now optional; if not provided, the tool returns
        UNMEASURED + REQUIRED_MATERIAL_FIELDS so the caller knows what to
        supply. The seed cases remain available for archival/calibration use
        but are no longer the implicit default.

        FEDERATION-CONVERGENCE-P0 / P0-3 (2026-09-21) — caller_service:
        the authenticated machine channel that delegated this call
        (arifos / aforge / arifos_kernel). When supplied + a bound session
        is present, the dual-identity gate grants OBSERVE_ONLY authority
        to an anonymous subject. The argument is accepted but the
        canonical dual-identity validation lives in the session-binding
        layer (this function itself does not gate on it).
        """
        from wealth_core.polix import seed_malaysia_fiscal, seed_petronas_glc

        m = mode.lower()

        # ── Seed mode deprecated (P0 2026-09-21) ─────────────────────────
        # If no seed_case is supplied, refuse the static default and return
        # the material fields the caller must populate.
        if not seed_case:
            return wrap_result(
                tool_name="capital_polix",
                domain="political_economy",
                result={
                    "status": "UNMEASURED",
                    "error_code": "REQUIRED_MATERIAL_FIELDS",
                    "message": (
                        "capital_polix no longer accepts a static seed_case default. "
                        "Caller must supply seed_case + material_fields (actor_list, "
                        "rule_set, decision_anchors) so the topology reflects current "
                        "substrate, not last-week's seed."
                    ),
                    "required_inputs": ["seed_case", "material_fields"],
                    "available_seed_cases": ["malaysia_fiscal", "petronas_glc"],
                    "deprecation_note": "seed-mode default removed per F13 'Drop' directive 2026-09-21",
                },
                epistemic_tag=EpistemicTag.UNKNOWN,
                evidence_quality=EvidenceQuality.UNMEASURED,
                errors=["seed_case is required (static seed mode deprecated)"],
            )

        sc = seed_case.lower()

        # Load seed case
        if sc in ("malaysia_fiscal", "malaysia"):
            topo = seed_malaysia_fiscal()
        elif sc in ("petronas_glc", "petronas"):
            topo = seed_petronas_glc()
        else:
            return wrap_result(
                tool_name="capital_polix",
                domain="political_economy",
                result={
                    "status": "ERROR",
                    "error_code": "UNKNOWN_SEED_CASE",
                    "message": f"Unknown seed case '{seed_case}'. Available: malaysia_fiscal, petronas_glc",
                },
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                errors=[f"Unknown seed case: {seed_case}"],
            )

        d = topo.to_dict()

        if m == "topology":
            # Full topology
            result = d
        elif m == "capture":
            # Capture risk summary
            result = {
                "domain": d["domain"],
                "capture_score": d["capture_score"],
                "actors": [
                    {
                        "name": a["name"],
                        "capture_risk": a["capture_risk"],
                        "opacity_score": a["opacity_score"],
                    }
                    for a in d["actors"]
                ],
                "coercion_signals": d["coercion_signals"],
                "schema_version": d["schema_version"],
            }
        elif m == "rents":
            # Rent flows only
            result = {
                "domain": d["domain"],
                "rent_flows": d["rent_flows"],
                "total_estimated_annual": "UNMEASURED — requires quantitative modeling",
                "schema_version": d["schema_version"],
            }
        elif m == "asymmetry":
            # Rule asymmetries only
            result = {
                "domain": d["domain"],
                "rule_asymmetries": d["rule_asymmetries"],
                "schema_version": d["schema_version"],
            }
        else:
            return wrap_result(
                tool_name="capital_polix",
                domain="political_economy",
                result={
                    "status": "ERROR",
                    "error_code": "UNKNOWN_MODE",
                    "message": f"Unknown mode '{mode}'. Available: topology, capture, rents, asymmetry",
                },
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                errors=[f"Unknown mode: {mode}"],
            )

        result["signal_state"] = "DERIVED"
        result["signal_state_reason"] = "POLIX output is interpretive, not observed"
        return wrap_result(
            tool_name="capital_polix",
            domain="political_economy",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.MODERATE,
            source_attribution=[f"polix:seed:{sc}"],
        )

    # ═══════════════════════════════════════════════════════════════════
    # CIVX — Civilizational Scenario Intelligence (L10)
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_civx",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description="Civilizational scenario intelligence — long-horizon resilience, sovereignty, intergenerational burden. MODES: scenario (full scenario study), resilience (resilience scores), risks (key risks), assumptions (assumption axes). SEED CASES: malaysia_fiscal_2027_2040. Status: SAFE_TO_STUDY, never decision authority. SIDE EFFECT: writes a vault receipt.",
        tags={"domain": "civilizational", "kind": "scenario", "canonical": "v1"},
    )
    async def capital_civx(
        mode: str = "scenario",
        seed_case: str = "malaysia_fiscal_2027_2040",
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
        caller_service: str | None = None,
    ) -> dict:
        """Civilizational scenario analysis. SAFE_TO_STUDY only.

        FEDERATION-CONVERGENCE-P0 / P0-3 (2026-09-21): caller_service
        mirrors the dual-identity delegation chain (see capital_polix).
        """
        from wealth_core.civx import seed_malaysia_fiscal_2027_2040

        m = mode.lower()
        sc = seed_case.lower()

        if sc in ("malaysia_fiscal_2027_2040", "malaysia_fiscal", "malaysia"):
            scenario = seed_malaysia_fiscal_2027_2040()
        else:
            return wrap_result(
                tool_name="capital_civx",
                domain="civilizational",
                result={
                    "status": "ERROR",
                    "error_code": "UNKNOWN_SEED_CASE",
                    "message": f"Unknown seed case '{seed_case}'. Available: malaysia_fiscal_2027_2040",
                },
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                errors=[f"Unknown seed case: {seed_case}"],
            )

        d = scenario.to_dict()

        if m == "scenario":
            result = d
        elif m == "resilience":
            result = {
                "domain": d["domain"],
                "status": d["status"],
                "paths": [
                    {
                        "path_id": p["path_id"],
                        "name": p["name"],
                        "resilience_scores": p["resilience_scores"],
                    }
                    for p in d["paths"]
                ],
                "schema_version": d["schema_version"],
            }
        elif m == "risks":
            result = {
                "domain": d["domain"],
                "status": d["status"],
                "paths": [
                    {
                        "path_id": p["path_id"],
                        "name": p["name"],
                        "key_risks": p["key_risks"],
                        "irreversibility": p["irreversibility"],
                    }
                    for p in d["paths"]
                ],
                "schema_version": d["schema_version"],
            }
        elif m == "assumptions":
            result = {
                "domain": d["domain"],
                "status": d["status"],
                "assumption_axes": d["assumption_axes"],
                "calibration_data": d["calibration_data"],
                "limitations": d["limitations"],
                "schema_version": d["schema_version"],
            }
        else:
            return wrap_result(
                tool_name="capital_civx",
                domain="civilizational",
                result={
                    "status": "ERROR",
                    "error_code": "UNKNOWN_MODE",
                    "message": f"Unknown mode '{mode}'. Available: scenario, resilience, risks, assumptions",
                },
                epistemic_tag=EpistemicTag.INTERPRETED,
                evidence_quality=EvidenceQuality.WEAK,
                errors=[f"Unknown mode: {mode}"],
            )

        result["signal_state"] = "DERIVED"
        result["signal_state_reason"] = (
            "CIVX output is scenario/interpretive, not observed"
        )
        result["civx_status"] = d["status"]
        result["civx_warning"] = (
            "SAFE_TO_STUDY — not decision authority until calibrated"
        )
        return wrap_result(
            tool_name="capital_civx",
            domain="civilizational",
            result=result,
            epistemic_tag=EpistemicTag.INTERPRETED,
            evidence_quality=EvidenceQuality.WEAK,  # Scenario, not observed
            source_attribution=[f"civx:seed:{sc}"],
        )
