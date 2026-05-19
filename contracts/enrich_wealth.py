"""
WEALTH Metabolic Enrichment Helper — Phase 2 Adoption of metabolic.v1
══════════════════════════════════════════════════════════════════════════════════

Builds MetabolicOutput dicts for WEALTH tool returns.
Injects a top-level "metabolic" key into WEALTH result dicts.

WEALTH verdict → metabolic ClaimState mapping:
  VOID          → HOLD (cannot proceed)
  888-HOLD      → HOLD (requires 888_JUDGE)
  QUALIFY       → QUALIFIED (constraints not fully met)
  SABAR         → HYPOTHESIS (awaiting conditions)
  SEAL          → VERIFIED (all checks passed)
  default       → HYPOTHESIS

WEALTH failure_flags → metabolic confidence mapping:
  INVALID_FLAGS (COMPUTATION_ERROR, ENGINE_NOT_IMPLEMENTED, etc.) → LOW
  HOLD_FLAGS (LEVERAGE_CRITICAL, SOVEREIGN_DIGNITY_LOW)          → LOW
  QUALIFY_FLAGS (NOT_RECOVERED, IRR_NOT_FOUND)                  → MODERATE
  DATA_GAP_FLAGS (NO_DATA_FETCHED, ADAPTER_NOT_FOUND)            → LOW
  no flags + SEAL verdict                                        → HIGH
  no flags + SABAR verdict                                      → MODERATE

Tool-specific witness types:
  wealth_signal_information   → SIGNAL
  wealth_boundary_governance → DOCUMENT (policy/constitutional)
  wealth_synthesize          → REPORT (multi-dimensional synthesis)

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from contracts.schemas.metabolic import (
    ClaimState,
    ConfidenceLevel,
    MetabolicOutput,
    OrganType,
    UncertaintyBand,
    WitnessType,
)

# arifOS source commit for the metabolic contract
_METABOLIC_SOURCE_COMMIT = "3c64960e"
_METABOLIC_CONTRACT_HASH = "a5826a9eb1182c4f212fda1baa55ff9f"

# ── Per-tool configuration ────────────────────────────────────────────────────


_TOOL_METABOLIC_DEFAULTS: dict[str, dict[str, Any]] = {
    "wealth_signal_information": {
        "witness_type": WitnessType.SIGNAL.value,
        "next_best_tool": "wealth_boundary_governance",
        "required_next_tests": [
            "wealth_schema_validate",
            "wealth_correlation_guard_check",
        ],
        "cross_organ_next": OrganType.WEALTH.value,
        "cross_organ_reason": "Boundary governance evaluates constitutional constraints on the signal",
    },
    "wealth_boundary_governance": {
        "witness_type": WitnessType.DOCUMENT.value,
        "next_best_tool": "wealth_synthesize",
        "required_next_tests": [
            "wealth_policy_audit",
            "wealth_score_kernel",
        ],
        "cross_organ_next": OrganType.WEALTH.value,
        "cross_organ_reason": "Synthesize aggregates boundary output into a unified capital verdict",
    },
    "wealth_synthesize": {
        "witness_type": WitnessType.REPORT.value,
        "next_best_tool": "arif_judge_deliberate",
        "required_next_tests": [
            "wealth_check_floors",
        ],
        "cross_organ_next": OrganType.ARIFOS.value,
        "cross_organ_reason": "arifOS 888_JUDGE provides final constitutional verdict on the synthesis",
        "requires_888_judge": True,
    },
}


# ── Verdict → ClaimState ─────────────────────────────────────────────────────


def _verdict_to_claim_state(verdict: str) -> ClaimState:
    """Map WEALTH verdict string to metabolic ClaimState."""
    v = str(verdict).upper()
    if v == "VOID":
        return ClaimState.HOLD
    if v == "888-HOLD":
        return ClaimState.HOLD
    if v == "QUALIFY":
        return ClaimState.QUALIFIED
    if v == "SABAR":
        return ClaimState.HYPOTHESIS
    if v == "SEAL":
        return ClaimState.VERIFIED
    return ClaimState.HYPOTHESIS


# ── Confidence ───────────────────────────────────────────────────────────────


def _derive_confidence(
    verdict: str,
    flags: list[str],
    epistemic: str = "CLAIM",
) -> ConfidenceLevel:
    """Derive metabolic confidence from WEALTH verdict, flags, and epistemic."""
    v = str(verdict).upper()
    flag_set = set(flags)

    # Critical flags always reduce confidence
    invalid_flags = {
        "COMPUTATION_ERROR",
        "ENGINE_NOT_IMPLEMENTED",
        "MISSING_REQUIRED_INPUT",
        "INPUT_REQUIRED",
    }
    hold_flags = {"LEVERAGE_CRITICAL", "LEVERAGE_DEFAULT", "SOVEREIGN_DIGNITY_LOW"}
    qualify_flags = {
        "NOT_RECOVERED",
        "IRR_NOT_FOUND",
        "NON_NORMAL_FLOWS",
        "EBITDA_PROXY_USED",
    }
    data_gap_flags = {
        "ADAPTER_NOT_FOUND",
        "NO_DATA_FETCHED",
        "NO_INPUT_BASELINE",
        "RUNWAY_UNBOUNDED",
        "EPISTEMIC_UNAVAILABLE",
    }

    if flag_set & invalid_flags:
        return ConfidenceLevel.LOW
    if flag_set & hold_flags:
        return ConfidenceLevel.LOW
    if flag_set & data_gap_flags:
        return ConfidenceLevel.LOW
    if flag_set & qualify_flags:
        return ConfidenceLevel.MODERATE

    if v in ("VOID", "888-HOLD"):
        return ConfidenceLevel.LOW
    if v == "QUALIFY":
        return ConfidenceLevel.MODERATE
    if v == "SEAL":
        return ConfidenceLevel.HIGH

    # Default: MODERATE
    return ConfidenceLevel.MODERATE


# ── Uncertainty ─────────────────────────────────────────────────────────────


def _build_uncertainty(flags: list[str], epistemic: str = "CLAIM") -> dict[str, Any]:
    """Build UncertaintyBand dict from WEALTH flags and epistemic."""
    major_unknowns: list[str] = []
    if "NO_DATA_FETCHED" in flags or "ADAPTER_NOT_FOUND" in flags:
        major_unknowns.append("No data source available")
    if "EPISTEMIC_UNAVAILABLE" in flags:
        major_unknowns.append("Epistemic layer unavailable")
    if "COMPUTATION_ERROR" in flags:
        major_unknowns.append("Computation error — results unreliable")

    epistemic_upper = epistemic.upper()
    if epistemic_upper == "HYPOTHESIS":
        omega_0 = 0.15
    elif epistemic_upper == "ESTIMATE":
        omega_0 = 0.08
    elif epistemic_upper == "PLAUSIBLE":
        omega_0 = 0.05
    elif epistemic_upper == "UNKNOWN":
        omega_0 = 0.25
    else:
        omega_0 = 0.05  # CLAIM

    return {
        "omega_0": omega_0,
        "uncertainty_range": (
            round(1.0 - omega_0 - 0.05, 4),
            round(1.0 - omega_0 + 0.05, 4),
        ),
        "major_unknowns": major_unknowns,
        "key_missing_evidence": [],
        "claim_too_certain_flag": bool(
            epistemic_upper == "CLAIM" and not major_unknowns
        ),
    }


# ── Main builder ─────────────────────────────────────────────────────────────


def build_metabolic_output(
    result: dict[str, Any],
    tool_name: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Build a MetabolicOutput dict and inject it into a WEALTH result dict.

    Returns a NEW dict (does not mutate input) with a top-level "metabolic" key.

    Parameters
    ----------
    result : dict
        The WEALTH tool result dict (already computed)
    tool_name : str
        Name of the WEALTH tool that produced the result
    session_id : str | None
        Governed session ID for audit trace

    Returns
    -------
    dict
        Copy of result with added "metabolic" key containing MetabolicOutput dict
    """
    verdict = str(result.get("governance_verdict", result.get("verdict", "SABAR")))
    flags: list[str] = result.get("failure_flags", [])
    epistemic = str(result.get("epistemic", "CLAIM"))
    status = str(result.get("status", "OK"))

    # Tool-specific config
    tool_config = _TOOL_METABOLIC_DEFAULTS.get(tool_name, {})
    requires_888 = tool_config.get("requires_888_judge", False)

    # Determine if 888_JUDGE is actually needed
    if verdict == "888-HOLD":
        requires_888 = True

    # Check if high-stakes scale
    scale_mode = str(result.get("scale_mode", "enterprise"))
    high_stakes = scale_mode in {
        "national",
        "crisis",
        "civilization",
        "sovereign",
        "agentic",
    }
    if high_stakes:
        requires_888 = True

    claim_state = _verdict_to_claim_state(verdict)
    confidence_level = _derive_confidence(verdict, flags, epistemic)
    uncertainty = _build_uncertainty(flags, epistemic)

    # Build the metabolic output
    metabolic = {
        "organ": OrganType.WEALTH.value,
        "tool_name": tool_name,
        "session_id": session_id,
        "witnesses_ingested": [],
        "witness_type": tool_config.get("witness_type", WitnessType.SIGNAL.value),
        "witness_status": "INTERPRETED",
        "decoded_entities": [],
        "anomalous_contrasts": [],
        "candidate_meanings": [],
        "constraints_checked": [],
        "model_updates": [],
        "model_target": "Wealth",
        "abstraction_guard": None,
        "literal_claims": [],
        "uncertainty": uncertainty,
        "evidence_freshness": None,
        "required_next_tests": tool_config.get("required_next_tests", []),
        "next_best_tool": tool_config.get("next_best_tool", ""),
        "cross_organ_handoff": {
            "next_best_organ": tool_config.get(
                "cross_organ_next", OrganType.WEALTH.value
            ),
            "handoff_reason": tool_config.get(
                "cross_organ_reason", "Continue capital intelligence workflow"
            ),
            "handoff_payload": {
                # verdict kept for metabolic routing — claim_state is authoritative
                "verdict": verdict,
                "confidence": confidence_level.value,
                "claim_state": claim_state.value,
                "advisory_assessment": result.get("advisory_assessment", ""),
            },
            "blocked_organs": [],
            "blocked_reason": "",
            "confidence_at_handoff": confidence_level.value,
        },
        "claim_state": claim_state.value,
        "conflict_flags": [],
        "confidence_level": confidence_level.value,
        "audit_receipt": "",
        "recommendation_only": True,
        "execution_authorized": False,
        "human_final_authority": "Arif",
        "requires_888_judge": requires_888,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "constitution_hash": _METABOLIC_SOURCE_COMMIT,
        "constitutional_boundary_notice": (
            "WEALTH is advisory-only. It computes capital thermodynamics "
            "but NEVER adjudicates constitutional verdicts. "
            "Use `claim_state` (not `verdict`) for all downstream logic. "
            "arifOS 888_JUDGE is the sole constitutional authority."
        ),
        # Schema metadata
        "_schema_version": "metabolic.v1",
        "_source_commit": _METABOLIC_SOURCE_COMMIT,
        "_contract_hash": _METABOLIC_CONTRACT_HASH,
    }

    # Return a copy of result with metabolic injected
    enriched = dict(result)
    enriched["metabolic"] = metabolic
    return enriched
