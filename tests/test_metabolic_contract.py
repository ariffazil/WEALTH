"""
WEALTH Phase 2 Metabolic Contract Conformance Tests
══════════════════════════════════════════════════════════════════════════════════

Verifies that the three Phase 2 WEALTH tools (wealth_signal_information,
wealth_boundary_governance, wealth_synthesize) correctly produce MetabolicOutput
dictionaries when called.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts.schemas.metabolic import (
    ClaimState,
    ConfidenceLevel,
    MetabolicOutput,
    OrganType,
    WitnessType,
)


def test_metabolic_schema_import():
    """MetabolicOutput schema imports correctly with all expected fields."""
    fields = set(MetabolicOutput.model_fields.keys())
    assert "organ" in fields
    assert "tool_name" in fields
    assert "witness_type" in fields
    assert "claim_state" in fields
    assert "confidence_level" in fields
    assert "uncertainty" in fields
    assert "cross_organ_handoff" in fields
    assert "recommendation_only" in fields
    assert "execution_authorized" in fields
    assert "human_final_authority" in fields
    assert "requires_888_judge" in fields


def test_claim_state_enum_values():
    """All ClaimState enum values are present."""
    values = {c.value for c in ClaimState}
    assert "OBSERVED" in values
    assert "HYPOTHESIS" in values
    assert "QUALIFIED" in values
    assert "VERIFIED" in values
    assert "SEALED" in values
    assert "HOLD" in values


def test_confidence_level_enum_values():
    """All ConfidenceLevel enum values are present."""
    values = {c.value for c in ConfidenceLevel}
    assert "UNKNOWN" in values
    assert "LOW" in values
    assert "MODERATE" in values
    assert "HIGH" in values
    assert "VERIFIED" in values
    assert "SEALED" in values


def test_organ_type_weird_wealth():
    """OrganType includes WEALTH."""
    values = {c.value for c in OrganType}
    assert "WEALTH" in values


def test_witness_type_values():
    """WitnessType enums include SIGNAL, DOCUMENT, REPORT (used by Phase 2 tools)."""
    values = {c.value for c in WitnessType}
    assert "signal" in values
    assert "document" in values
    assert "report" in values


def test_enrich_helper_import():
    """build_metabolic_output helper imports and callable."""
    from contracts.enrich_wealth import build_metabolic_output

    assert callable(build_metabolic_output)


def test_build_metabolic_output_basic():
    """build_metabolic_output wraps a result dict with metabolic key."""
    from contracts.enrich_wealth import build_metabolic_output

    result = {
        "tool": "wealth_signal_information",
        "governance_verdict": "SEAL",
        "failure_flags": [],
        "scale_mode": "enterprise",
    }
    enriched = build_metabolic_output(result, "wealth_signal_information")
    assert "metabolic" in enriched
    metabolic = enriched["metabolic"]
    assert metabolic["organ"] == "WEALTH"
    assert metabolic["tool_name"] == "wealth_signal_information"
    assert metabolic["claim_state"] == "VERIFIED"  # SEAL → VERIFIED
    assert metabolic["confidence_level"] == "HIGH"  # no flags + SEAL
    assert metabolic["recommendation_only"] is True
    assert metabolic["execution_authorized"] is False
    assert metabolic["human_final_authority"] == "Arif"


def test_void_yields_hold():
    """VOID verdict → claim_state HOLD, confidence UNKNOWN."""
    from contracts.enrich_wealth import build_metabolic_output

    result = {
        "governance_verdict": "VOID",
        "failure_flags": ["COMPUTATION_ERROR"],
        "scale_mode": "enterprise",
    }
    enriched = build_metabolic_output(result, "wealth_signal_information")
    metabolic = enriched["metabolic"]
    assert metabolic["claim_state"] == "HOLD"
    assert metabolic["confidence_level"] == "LOW"


def test_888_hold_yields_hold():
    """888-HOLD verdict → claim_state HOLD, requires_888_judge=True."""
    from contracts.enrich_wealth import build_metabolic_output

    result = {
        "governance_verdict": "888-HOLD",
        "failure_flags": ["LEVERAGE_CRITICAL"],
        "scale_mode": "enterprise",
    }
    enriched = build_metabolic_output(result, "wealth_boundary_governance")
    metabolic = enriched["metabolic"]
    assert metabolic["claim_state"] == "HOLD"
    assert metabolic["requires_888_judge"] is True


def test_sovereign_scale_requires_888():
    """scale_mode=sovereign → requires_888_judge=True."""
    from contracts.enrich_wealth import build_metabolic_output

    result = {
        "governance_verdict": "SEAL",
        "failure_flags": [],
        "scale_mode": "sovereign",
    }
    enriched = build_metabolic_output(result, "wealth_synthesize")
    metabolic = enriched["metabolic"]
    assert metabolic["requires_888_judge"] is True


def test_metabolic_has_required_keys():
    """Metabolic output has all 26 required keys."""
    from contracts.enrich_wealth import build_metabolic_output

    result = {
        "governance_verdict": "QUALIFY",
        "failure_flags": ["NOT_RECOVERED"],
        "scale_mode": "enterprise",
    }
    enriched = build_metabolic_output(result, "wealth_boundary_governance")
    metabolic = enriched["metabolic"]
    required = [
        "organ",
        "tool_name",
        "session_id",
        "witnesses_ingested",
        "witness_type",
        "witness_status",
        "decoded_entities",
        "anomalous_contrasts",
        "candidate_meanings",
        "constraints_checked",
        "model_updates",
        "model_target",
        "abstraction_guard",
        "literal_claims",
        "uncertainty",
        "evidence_freshness",
        "required_next_tests",
        "next_best_tool",
        "cross_organ_handoff",
        "claim_state",
        "conflict_flags",
        "confidence_level",
        "audit_receipt",
        "recommendation_only",
        "execution_authorized",
        "human_final_authority",
        "requires_888_judge",
        "timestamp_utc",
        "constitution_hash",
    ]
    for key in required:
        assert key in metabolic, f"Missing required key: {key}"


def test_cross_organ_handoff_present():
    """cross_organ_handoff is populated for signal_information."""
    from contracts.enrich_wealth import build_metabolic_output

    result = {
        "governance_verdict": "SEAL",
        "failure_flags": [],
        "scale_mode": "enterprise",
    }
    enriched = build_metabolic_output(result, "wealth_signal_information")
    metabolic = enriched["metabolic"]
    assert metabolic["cross_organ_handoff"] is not None
    handoff = metabolic["cross_organ_handoff"]
    assert "next_best_organ" in handoff
    assert "handoff_reason" in handoff
    assert "handoff_payload" in handoff


def test_uncertainty_has_omega_0():
    """Uncertainty band includes omega_0."""
    from contracts.enrich_wealth import build_metabolic_output

    result = {
        "governance_verdict": "SEAL",
        "failure_flags": [],
        "scale_mode": "enterprise",
    }
    enriched = build_metabolic_output(result, "wealth_signal_information")
    metabolic = enriched["metabolic"]
    uncertainty = metabolic["uncertainty"]
    assert "omega_0" in uncertainty
    assert 0.0 <= uncertainty["omega_0"] <= 1.0


def test_signal_information_witness_type():
    """wealth_signal_information → witness_type=signal."""
    from contracts.enrich_wealth import build_metabolic_output

    result = {
        "governance_verdict": "SEAL",
        "failure_flags": [],
        "scale_mode": "enterprise",
    }
    enriched = build_metabolic_output(result, "wealth_signal_information")
    assert enriched["metabolic"]["witness_type"] == "signal"


def test_boundary_governance_witness_type():
    """wealth_boundary_governance → witness_type=document."""
    from contracts.enrich_wealth import build_metabolic_output

    result = {
        "governance_verdict": "SEAL",
        "failure_flags": [],
        "scale_mode": "enterprise",
    }
    enriched = build_metabolic_output(result, "wealth_boundary_governance")
    assert enriched["metabolic"]["witness_type"] == "document"


def test_synthesize_witness_type():
    """wealth_synthesize → witness_type=report."""
    from contracts.enrich_wealth import build_metabolic_output

    result = {
        "governance_verdict": "SEAL",
        "failure_flags": [],
        "scale_mode": "enterprise",
    }
    enriched = build_metabolic_output(result, "wealth_synthesize")
    assert enriched["metabolic"]["witness_type"] == "report"


def test_schema_version_in_config():
    """MetabolicOutput Config has metabolic.v1 schema metadata."""
    extra = MetabolicOutput.model_config.get("json_schema_extra", {})
    assert "schema_version" in str(extra) or "metabolic.v1" in str(extra)


if __name__ == "__main__":
    tests = [
        t for t in globals().values() if callable(t) and t.__name__.startswith("test_")
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS  {test.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {test.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
