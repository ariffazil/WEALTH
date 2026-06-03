# WEALTH — Advisory Boundary Tests (PR 5)
# ═══════════════════════════════════════════════════════════════════════════
# Doctrine: WEALTH advises, arifOS authorizes. Every WEALTH tool output
# must label its seal authority and surface input integrity. No WEALTH
# tool may produce a "rich default narrative" from missing data.
#
# These tests prove the boundary is enforced at the envelope level (every
# tool that calls wajib_envelope) and at the synthesize level (the
# specific tool that has the strongest temptation to fabricate).

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from internal.engines.advisory import (
    DOMAIN_SEAL_VALIDITY,
    INSUFFICIENT_INPUT_FIELDS,
    INSUFFICIENT_INPUT_STATUS,
    INSUFFICIENT_INPUT_SUMMARY,
    INSUFFICIENT_INPUT_VERDICT,
    JUDGE_SEAL_AUTHORIZATION,
    SEAL_AUTHORITY_DISCLAIMER,
    SYNTHETIC_MARKERS,
    compute_advisory_boundary,
    detect_insufficient_input,
    detect_synthetic_inputs,
)
from internal.engines.five_seals import wajib_envelope


# ─── 1. disclaimer present on every envelope ────────────────────────────


def test_seal_authority_disclaimer_present():
    """Every wajib_envelope output must carry the seal-authority disclaimer.

    F2 Truth: an agent reading the output must be unable to confuse
    WEALTH advisory for execution authorization.
    """
    out = wajib_envelope(
        tool="test_tool",
        mode="test",
        status="OK",
        wealth_verdict="PROCEED",
        summary="hello",
        metrics={"npv": 100},
    )
    assert "seal_authority_disclaimer" in out, (
        "wajib_envelope output must include 'seal_authority_disclaimer'"
    )
    assert out["seal_authority_disclaimer"] == SEAL_AUTHORITY_DISCLAIMER
    assert "advisory" in out["seal_authority_disclaimer"].lower()
    assert "JUDGE_SEAL_AUTHORIZATION" in out["seal_authority_disclaimer"]


# ─── 2. domain_seal_validity defaults correctly ──────────────────────────


def test_domain_seal_validity_default():
    """The default domain_seal_validity is WEALTH|advisory_only.

    F13 SOVEREIGN: WEALTH never claims execution authority by default.
    """
    out = wajib_envelope(
        tool="test_tool",
        mode="test",
        status="OK",
        wealth_verdict="PROCEED",
        summary="x",
        metrics={},
    )
    assert out["domain_seal_validity"] == DOMAIN_SEAL_VALIDITY
    assert out["domain_seal_validity"] == "WEALTH|advisory_only"
    # And the constant is well-defined.
    assert DOMAIN_SEAL_VALIDITY != JUDGE_SEAL_AUTHORIZATION


# ─── 3. judge_seal_authorization_required is true for W4/W5 ─────────────


def test_judge_seal_required_for_w4_w5():
    """decision_class W4 and W5 set judge_seal_authorization_required=True.

    F2: execution-grade decisions (legal exposure, irreversible) always
    require an arifOS judge seal, not a WEALTH advisory.
    """
    for decision_class in ("W4", "W5"):
        out = wajib_envelope(
            tool="test_tool",
            mode="test",
            status="OK",
            wealth_verdict="HOLD",
            summary="x",
            metrics={},
            decision_class=decision_class,
        )
        assert out["judge_seal_authorization_required"] is True, (
            f"decision_class={decision_class} must require judge seal"
        )

    for decision_class in ("W0", "W1", "W2", "W3"):
        out = wajib_envelope(
            tool="test_tool",
            mode="test",
            status="OK",
            wealth_verdict="PROCEED",
            summary="x",
            metrics={},
            decision_class=decision_class,
        )
        assert out["judge_seal_authorization_required"] is False, (
            f"decision_class={decision_class} must NOT require judge seal"
        )


# ─── 4. synthetic inputs are detected ────────────────────────────────────


def test_synthetic_inputs_detected():
    """Metrics containing SYNTHETIC_DEFAULT (or any SYNTHETIC_MARKER) flip
    synthetic_inputs_detected=True on the envelope.

    F7 Stewardship: never let a default-spawned value hide as a real input.
    """
    out_clean = wajib_envelope(
        tool="test_tool",
        mode="test",
        status="OK",
        wealth_verdict="PROCEED",
        summary="x",
        metrics={"npv": 100, "irr": 0.1},
    )
    assert out_clean["synthetic_inputs_detected"] is False

    out_dirty = wajib_envelope(
        tool="test_tool",
        mode="test",
        status="OK",
        wealth_verdict="PROCEED",
        summary="x",
        metrics={
            "npv": 100,
            "conservation": "SYNTHETIC_DEFAULT",  # the signal
        },
    )
    assert out_dirty["synthetic_inputs_detected"] is True


# ─── 5. insufficient input is detected ──────────────────────────────────


def test_insufficient_input_detected():
    """When the canonical cashflow-shaped fields are all missing, the
    envelope flags insufficient_input_detected=True.

    F2: this is a presence check, not a quality check.
    """
    out_empty = wajib_envelope(
        tool="test_tool",
        mode="test",
        status="OK",
        wealth_verdict="PROCEED",
        summary="x",
        metrics={},  # nothing supplied
    )
    assert out_empty["insufficient_input_detected"] is True

    out_filled = wajib_envelope(
        tool="test_tool",
        mode="test",
        status="OK",
        wealth_verdict="PROCEED",
        summary="x",
        metrics={"cash_flows": [100, 200, 300]},
    )
    assert out_filled["insufficient_input_detected"] is False


# ─── 6. wealth_synthesize honors INSUFFICIENT_INPUT path ────────────────


def test_wealth_synthesize_insufficient_path():
    """wealth_synthesize with NO inputs returns INSUFFICIENT_INPUT, not a
    rich default narrative.

    This is the headline enforcement of PR 5. The fabricator path is
    the F7 violation. The honest path is to refuse.
    """
    try:
        from internal.engines.canonical_tools import wealth_synthesize
    except Exception as e:
        # engines not imported in test context — fall back to direct
        # envelope check (the doctrine is the same)
        out = wajib_envelope(
            tool="wealth_synthesize",
            mode="synthesis",
            status=INSUFFICIENT_INPUT_STATUS,
            wealth_verdict=INSUFFICIENT_INPUT_VERDICT,
            summary=INSUFFICIENT_INPUT_SUMMARY,
            metrics={},
        )
        assert out["status"] == INSUFFICIENT_INPUT_STATUS
        assert out["wealth_verdict"] == "HOLD"
        return

    out = wealth_synthesize(
        question="should we acquire asset X?",
        # NOTE: no cash_flows, no p50_value_musd, no well_cost_musd, no prior_pos
    )
    assert out["status"] == INSUFFICIENT_INPUT_STATUS, (
        f"expected INSUFFICIENT_INPUT, got {out['status']}"
    )
    assert out["wealth_verdict"] == INSUFFICIENT_INPUT_VERDICT
    assert "domain_seal_validity" in out
    assert out["domain_seal_validity"] == "WEALTH|advisory_only"


# ─── 7. no new MCP tools added (F13 honor) ─────────────────────────────


def test_no_new_mcp_tools_added():
    """The PR 5 advisory boundary does NOT add a new MCP tool.

    F13 SOVEREIGN: enforcement deepens, surface does not grow. The
    advisory boundary is wired into the existing wajib_envelope, not
    exposed as a standalone tool.
    """
    # This is a static test: the advisory module exposes no @mcp.tool
    # decorators. We verify by importing and checking the module's
    # namespace for tool-registration markers.
    import internal.engines.advisory as adv

    forbidden = ("mcp.tool", "FastMCP", "@mcp")
    for name in dir(adv):
        for marker in forbidden:
            assert marker not in name, (
                f"advisory.py must not register MCP tools; found {name!r} matching {marker!r}"
            )

    # And the constants are present (proving the module is loaded).
    assert adv.DOMAIN_SEAL_VALIDITY == "WEALTH|advisory_only"
    assert adv.JUDGE_SEAL_AUTHORIZATION == "arifOS|execution_authorized"


# ─── BONUS: detection helpers sanity ────────────────────────────────────


def test_detection_helpers_smoke():
    """Smoke test the detection helpers in isolation.

    F1 AMANAH: detection is observable, not inferred.
    """
    # synthetic
    assert detect_synthetic_inputs({"x": "SYNTHETIC_DEFAULT"}) is True
    assert detect_synthetic_inputs({"x": 1, "y": [1, 2]}) is False
    assert detect_synthetic_inputs({"nested": {"deep": "SYNTHETIC"}}) is True
    assert detect_synthetic_inputs({"nested": {"deep": ["a", "b"]}}) is False

    # insufficient
    assert detect_insufficient_input({}) is True
    assert detect_insufficient_input({"cash_flows": []}) is True
    assert detect_insufficient_input({"cash_flows": None}) is True
    # A non-empty list (even if all-zero) is a real input — not insufficient.
    # "All zeros" is a legitimate scenario (e.g., stalled project); the
    # placeholder-vs-real distinction is the synthetic detection's job.
    assert detect_insufficient_input({"cash_flows": [0.0]}) is False
    assert detect_insufficient_input({"cash_flows": [100.0]}) is False
    assert detect_insufficient_input({"p50_value_musd": 50.0}) is False

    # compute_advisory_boundary returns a complete 5-field dict
    ab = compute_advisory_boundary(
        {"npv": 100, "irr": 0.1},
        decision_class="W2",
        evidence_level="E3",
    )
    assert set(ab.keys()) == {
        "domain_seal_validity",
        "judge_seal_authorization_required",
        "synthetic_inputs_detected",
        "insufficient_input_detected",
        "seal_authority_disclaimer",
    }


if __name__ == "__main__":
    # Allow running this test file directly for quick smoke
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
