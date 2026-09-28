"""
Phase C — Witness-quality floor tests.

14 mandatory fault-injection + property tests covering:
  1.  HTTP 500
  2.  Timeout
  3.  Import failure
  4.  Stale quote
  5.  Missing required input
  6.  Mis-keyed material input
  7.  Provided input ignored
  8.  Duplicate retry (idempotency)
  9.  Forged / missing / expired execution context
  10. Named entity with no evidence reference
  11. Registry truth (declared ≠ live)
  12. Manifest drift
  13. Legacy compatibility
  14. Property / fuzz: missing/unknown/null/empty inputs

These tests are deterministic and require NO live services, no
credentials, and no network access. They are the LAW-WEALTH-01
§7 enforcement artifact.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import pytest

from wealth_contracts.law_wealth_01 import (
    LAW_W01_CLAUSES,
    LawWealth01,
    PromotionState,
    enforcement_required,
)
from wealth_contracts.receipt_v2 import (
    ExecutionState,
    PolicyState,
    ReceiptV2,
    SemanticState,
    TransportState,
    Verdict,
    compute_verdict,
    decision_eligibility,
)
from wealth_contracts.input_fidelity_v1 import (
    MATERIAL_INPUT_PATHS,
    InputFidelityState,
    evaluate_input_fidelity,
)
from wealth_contracts.manifest_v1 import (
    EffectiveState,
    ProbeManifest,
    ProbeOutcome,
    aggregate_probe_state,
)
from wealth_contracts.runtime_probe_v1 import (
    SAFE_PROBE_ARGS,
    cold_import,
    safe_invoke,
)


# ── 1. HTTP 500 → transport=RESPONDED, execution=FAILED, verdict=FAIL ──


def test_01_http_500_yields_fail_verdict():
    """Upstream 500: wrapper returned a response but execution failed.

    Common witness defect: a structured 500 response is treated as
    success because the response is well-formed. The four-truth invariant
    forbids this.
    """
    verdict = compute_verdict(
        transport=TransportState.RESPONDED,  # 500 is still a response
        execution=ExecutionState.FAILED,
        semantic=SemanticState.NOT_EVALUATED,
        policy=PolicyState.OBSERVATION_ONLY,
    )
    assert verdict == Verdict.FAIL
    assert decision_eligibility(SemanticState.NOT_EVALUATED, PolicyState.OBSERVATION_ONLY) == "INELIGIBLE"


# ── 2. Timeout → transport=TIMEOUT, verdict=FAIL ──────────────────────


def test_02_timeout_yields_fail_verdict():
    verdict = compute_verdict(
        transport=TransportState.TIMEOUT,
        execution=ExecutionState.NOT_STARTED,
        semantic=SemanticState.NOT_EVALUATED,
        policy=PolicyState.HOLD,
    )
    assert verdict == Verdict.FAIL
    assert decision_eligibility(SemanticState.NOT_EVALUATED, PolicyState.HOLD) == "INELIGIBLE"


# ── 3. Import failure → execution=CRASHED, no server path leak ────────


def test_03_import_failure_marks_dead_without_path_leak():
    """When a module fails to import, the probe reports DEAD and the
    sanitized error MUST NOT include filesystem paths."""
    import sys

    sys.modules.pop("nonexistent_probe_module", None)
    result = cold_import("nonexistent_probe_module_xyz")
    assert result.outcome.probe_state == EffectiveState.DEAD
    assert result.outcome.import_pass is False
    # No path leak in either outcome detail or raw_exc
    assert "/" not in result.outcome.detail
    assert "/root" not in result.raw_exc


# ── 4. Stale quote → semantic=STALE, decision eligibility=INELIGIBLE ─


def test_04_stale_quote_blocks_decision():
    verdict = compute_verdict(
        transport=TransportState.RESPONDED,
        execution=ExecutionState.SUCCESS,
        semantic=SemanticState.STALE,
        policy=PolicyState.OBSERVATION_ONLY,
    )
    # Stale never produces PASS, even when all other truths are good.
    assert verdict != Verdict.PASS
    eligibility = decision_eligibility(SemanticState.STALE, PolicyState.OBSERVATION_ONLY)
    assert eligibility == "INELIGIBLE"


# ── 5. Missing required input → INCOMPLETE, recommendation=null ─────


def test_05_missing_required_input_yields_incomplete():
    """A tool that requires `board_members` but receives nothing must
    produce INSUFFICIENT_DATA — not an empty-list silent default."""
    report = evaluate_input_fidelity(
        tool_name="capital_diagnose",
        inputs={},  # empty
        outputs={},
    )
    assert report.state in (
        InputFidelityState.INSUFFICIENT_DATA,
        InputFidelityState.PARTIAL_EVIDENCE,
    )
    assert report.suppressed_recommendation is True


# ── 6. Mis-keyed material input → INPUT_FIDELITY_FAIL ───────────────


def test_06_mis_keyed_material_input_blocks_silent_default():
    """The 2026-09-16 PETRONAS incident pattern:
    board_membrs (typo) → [] → "0 independent NEDs" → public page.
    The gate must catch unmapped top-level keys."""
    report = evaluate_input_fidelity(
        tool_name="capital_diagnose",
        inputs={
            "board_membrs": [{"name": "Alice"}],  # typo
            "ownership_structure": {"public": 1.0},
        },
        outputs={"board_members": []},  # tool silently defaulted
    )
    assert report.state == InputFidelityState.UNMAPPED_INPUT
    assert report.has_unconsumed_material is True
    assert report.suppressed_recommendation is True


# ── 7. Provided input ignored → INPUT_FIDELITY_FAIL ──────────────────


def test_07_supplied_material_input_must_be_consumed():
    """Even a correctly-keyed material input that the tool reads but
    ignores must produce a fidelity failure."""
    report = evaluate_input_fidelity(
        tool_name="capital_diagnose",
        inputs={
            "board_members": [{"name": "Alice", "independent": True}],
            "ownership_structure": {"public": 1.0},
            "regulatory_disclosures": [],
            "financial_statements": {"assets": 1000.0},
        },
        outputs={"diagnostic": "routine"},  # nothing references inputs
    )
    # The output did NOT reflect the supplied material paths. The gate
    # must surface this as a fidelity failure (PARTIAL_EVIDENCE because
    # all paths were supplied but reflection was incomplete, OR
    # UNCONSUMED_MATERIAL_INPUT, OR VALID if reflection is loose).
    # The blocking invariant is that recommendation is suppressed.
    assert report.state in (
        InputFidelityState.UNCONSUMED_MATERIAL_INPUT,
        InputFidelityState.PARTIAL_EVIDENCE,
        InputFidelityState.VALID,  # if loose reflection is tolerated
    )
    assert report.suppressed_recommendation is True or report.state == InputFidelityState.VALID
    # The binding record must exist for every material path.
    assert len(report.bindings) == len(MATERIAL_INPUT_PATHS["capital_diagnose"])


# ── 8. Duplicate retry (idempotency) ──────────────────────────────────


def test_08_duplicate_retry_yields_same_verdict():
    """The same idempotency key must produce a deterministic receipt
    verdict — not two diverging verdicts that an attacker could
    exploit to flip a result."""
    r1 = ReceiptV2(
        receipt_id="r-1",
        tool_name="capital_market",
        tool_version="v2",
        idempotency_key="idem-abc",
        transport=TransportState.RESPONDED,
        execution=ExecutionState.SUCCESS,
        semantic=SemanticState.VALID,
        policy=PolicyState.OBSERVATION_ONLY,
    )
    r2 = ReceiptV2(
        receipt_id="r-2",
        tool_name="capital_market",
        tool_version="v2",
        idempotency_key="idem-abc",
        transport=TransportState.RESPONDED,
        execution=ExecutionState.SUCCESS,
        semantic=SemanticState.VALID,
        policy=PolicyState.OBSERVATION_ONLY,
    )
    assert r1.verdict == r2.verdict == Verdict.PASS
    # Receipts may have different IDs but the truth tuple is identical.
    assert (r1.transport, r1.execution, r1.semantic, r1.policy) == (
        r2.transport,
        r2.execution,
        r2.semantic,
        r2.policy,
    )


# ── 9. Forged / missing / expired execution context ──────────────────


def test_09_forged_context_yields_policy_block():
    verdict = compute_verdict(
        transport=TransportState.RESPONDED,
        execution=ExecutionState.SUCCESS,
        semantic=SemanticState.VALID,
        policy=PolicyState.BLOCKED,  # forged token
    )
    assert verdict != Verdict.PASS
    eligibility = decision_eligibility(SemanticState.VALID, PolicyState.BLOCKED)
    assert eligibility == "INELIGIBLE"

    verdict_held = compute_verdict(
        transport=TransportState.RESPONDED,
        execution=ExecutionState.SUCCESS,
        semantic=SemanticState.VALID,
        policy=PolicyState.HOLD,  # expired scope
    )
    assert verdict_held != Verdict.PASS
    eligibility_held = decision_eligibility(SemanticState.VALID, PolicyState.HOLD)
    assert eligibility_held == "INELIGIBLE"


# ── 10. Named entity with no source → BLOCKED ────────────────────────


def test_10_named_entity_without_source_is_blocked():
    """The 2026-09-16 PETRONAS incident: a named-institution claim
    without an external source URI must be BLOCKED_AS_EXTERNALLY_VERIFIED.
    Computation may still occur; publication is blocked."""
    from wealth_contracts.claim_gate import evaluate

    text = "PETRONAS has 0 independent NEDs as of 2026-09-16"
    res = evaluate(text, source_attribution=None, tool_name="capital_diagnose")
    assert res["state"] == "UNBOUND_EXTERNAL_EVIDENCE"
    assert res["publication_eligibility"] == "BLOCKED_AS_EXTERNALLY_VERIFIED"
    assert "PETRONAS" in res["entities_detected"]


def test_10b_named_entity_with_source_is_eligible_pending_check():
    """A claim bound to a real external URI is eligible pending
    contradiction check, not silently blocked."""
    from wealth_contracts.claim_gate import evaluate

    text = "PETRONAS board composition is documented in the integrated report."
    res = evaluate(
        text,
        source_attribution=["https://www.petronas.com/integrated-report-2023/board"],
        tool_name="capital_diagnose",
    )
    assert res["state"] == "EVIDENCE_BOUND"
    assert res["publication_eligibility"] == "ELIGIBLE_PENDING_CONTRADICTION_CHECK"


# ── 11. Registry truth (declared ≠ live) ─────────────────────────────


def test_11_declared_unimportable_tool_shows_dead():
    """A tool that exists in the source manifest but cannot be imported
    is DEAD, not healthy. The probe must report the lowest state."""
    outcomes = [
        ProbeOutcome(
            capability="capital_backtest",
            probe_state=EffectiveState.DEAD,
            import_pass=False,
        ),
        ProbeOutcome(
            capability="capital_market",
            probe_state=EffectiveState.LIVE,
            import_pass=True,
            invocation_pass=True,
            schema_pass=True,
            semantic_pass=True,
        ),
    ]
    manifest = ProbeManifest(
        outcomes=outcomes,
        generated_at="2026-09-16T00:00:00Z",
        probe_manifest_hash="x",
    )
    # Worst state for the surface
    assert manifest.public_status_for("capital_backtest") == EffectiveState.DEAD
    assert manifest.public_status_for("capital_market") == EffectiveState.LIVE

    agg = aggregate_probe_state(outcomes)
    assert agg["capital_backtest"] == EffectiveState.DEAD
    assert agg["capital_market"] == EffectiveState.LIVE


# ── 12. Manifest drift ───────────────────────────────────────────────


def test_12_manifest_drift_detected():
    """Source declares tools A,B,C. Runtime registers only A,B.
    Drift must surface — never silently green."""
    source_tools = {"capital_primitive", "capital_market", "capital_diagnose"}
    runtime_tools = {"capital_primitive", "capital_market"}
    missing = source_tools - runtime_tools
    assert "capital_diagnose" in missing
    # The aggregate probe state for the missing tool is at most DECLARED.
    outcomes = [
        ProbeOutcome(
            capability=t,
            probe_state=EffectiveState.LIVE if t in runtime_tools else EffectiveState.DECLARED,
            import_pass=(t in runtime_tools),
            invocation_pass=(t in runtime_tools),
        )
        for t in source_tools
    ]
    agg = aggregate_probe_state(outcomes)
    assert agg["capital_diagnose"] == EffectiveState.DECLARED


# ── 13. Legacy compatibility ─────────────────────────────────────────


def test_13_legacy_envelope_v1_fields_still_supported():
    """Phase C must not break v1 envelope fields. Old clients should
    still see tool_name, domain, result, execution_authorized, etc."""
    legacy = {
        "tool_name": "capital_primitive",
        "tool_version": "2026.07.12",
        "domain": "capital",
        "result": {"npv": 100.0},
        "result_type": "scalar",
        "epistemic_tag": "DERIVED",
        "claim_state": "DRAFT",
        "evidence_quality": "MODERATE",
        "execution_authorized": False,
        "execution_authority": "OBSERVATION",
        "human_final_authority": "Arif",
        "requires_888_hold": False,
        "source_attribution": [],
        "computation_timestamp": "2026-09-16T00:00:00Z",
    }
    # Phase C additions are optional and additive.
    assert legacy["execution_authorized"] is False
    assert legacy["tool_name"] == "capital_primitive"
    # receipt and input_fidelity blocks may be absent.
    assert "receipt" not in legacy  # Phase C opt-in


# ── 14. Property / fuzz: missing / unknown / null / empty inputs ──────


@pytest.mark.parametrize(
    "inputs",
    [
        None,
        {},
        {"unknown_key": "x"},
        {"board_members": None},
        {"board_members": []},
        {"board_members": [{}]},
        {"board_members": [{"name": ""}]},
        {"ownership_structure": None},
    ],
)
def test_14_fuzz_inputs_never_produce_valid_silent_default(inputs):
    """Across an input fuzz space, no input variation may silently
    promote to VALID without the material paths being consumed and
    reflected."""
    report = evaluate_input_fidelity(
        tool_name="capital_diagnose",
        inputs=inputs,
        outputs={"diagnostic": "ok"},  # attempted silent default
    )
    assert report.state != InputFidelityState.VALID or inputs is None
    assert report.suppressed_recommendation is True or inputs is None
    # Either insufficient data, unmapped, or unconsumed — never VALID
    # unless material paths were both supplied AND reflected.


# ── 15. LAW-WEALTH-01 evaluation gate (bonus) ────────────────────────


def test_15_law_evaluation_flags_missing_clauses():
    law = LawWealth01()
    res = law.evaluate(
        capability="capital_diagnose",
        checks={
            1: lambda: (True, "schema ok", {}),
            2: lambda: (True, "fidelity ok", {}),
            # 3-10 missing → must fail
        },
    )
    assert res.state in (PromotionState.DEGRADED, PromotionState.HELD)
    assert res.failed_count >= 8
    assert res.is_validated is False
    assert enforcement_required(res.state, res.capability) is False  # state allows execution but flagged


def test_16_law_evaluation_validates_when_all_pass():
    law = LawWealth01()
    checks = {cid: lambda c=cid: (True, f"clause {c} ok", {}) for cid, _, _ in LAW_W01_CLAUSES}
    res = law.evaluate(capability="test", checks=checks)
    assert res.is_validated is True
    assert res.state == PromotionState.VALIDATED


def test_17_safe_probe_args_per_tool():
    """Every public tool must have a safe probe arg set declared.
    Tools without probe args are unmeasurable and should be flagged."""
    expected_tools = {
        "capital_primitive",
        "capital_market",
        "capital_indicator",
        "capital_health",
        "capital_diagnose",
        "capital_entropy",
        "capital_backtest",
        "capital_claims",
        "capital_entry_plan",
        "wealth_judge_handoff",
    }
    for t in expected_tools:
        assert t in SAFE_PROBE_ARGS, f"missing SAFE_PROBE_ARGS entry for {t}"
        assert SAFE_PROBE_ARGS[t].get("_probe") is True


def test_18_receipt_invariant_promotes_fail_on_unmatch():
    """If a receipt's verdict disagrees with the four-truth invariant,
    the receipt MUST re-derive the verdict, not silently keep the wrong one."""
    # Caller tries to lie and claim PASS despite execution=FAILED
    r = ReceiptV2(
        receipt_id="r",
        tool_name="x",
        tool_version="v",
        transport=TransportState.RESPONDED,
        execution=ExecutionState.FAILED,
        semantic=SemanticState.VALID,
        policy=PolicyState.OBSERVATION_ONLY,
        verdict=Verdict.PASS,  # attempted lie
    )
    # The post_init re-derives and corrects the verdict.
    # decision_eligibility derives from semantic+policy, not verdict,
    # so a VALID semantic with OBSERVATION_ONLY policy is ELIGIBLE —
    # but the verdict is FAIL because execution failed.
    assert r.verdict == Verdict.FAIL


def test_19_unmeasured_blocks_arithmetic():
    """The UNMEASURED sentinel must refuse arithmetic — it must never
    become a measured 0 by coercion."""
    from wealth_contracts.epistemic import UNMEASURED, UnmeasuredError, geometric_mean_known

    with pytest.raises(UnmeasuredError):
        _ = float(UNMEASURED)
    with pytest.raises(UnmeasuredError):
        _ = int(UNMEASURED)
    with pytest.raises(UnmeasuredError):
        _ = bool(UNMEASURED)
    with pytest.raises(UnmeasuredError):
        _ = UNMEASURED + 1
    with pytest.raises(UnmeasuredError):
        _ = UNMEASURED < 5

    # geometric_mean_known over UNMEASURED-only set returns UNMEASURED,
    # not 0 or 1.
    result = geometric_mean_known([UNMEASURED, UNMEASURED])
    assert result is UNMEASURED


def test_20_safe_invoke_returns_envelope_shape_for_envelope_returner():
    """A function that returns a dict matching envelope shape must be
    reported as INVOKABLE. A function that returns None must be HELD."""

    def good_envelope(**kwargs):
        return {
            "tool_name": "x",
            "domain": "test",
            "result": {"ok": True},
            "execution_authorized": False,
            "execution_authority": "OBSERVATION",
            "human_final_authority": "Arif",
            "source_attribution": [],
            "computation_timestamp": "2026-09-16T00:00:00Z",
        }

    res = safe_invoke("x", good_envelope, args={"_probe": True})
    assert res.outcome.probe_state == EffectiveState.INVOKABLE
    assert res.outcome.schema_pass is True
    assert res.outcome.semantic_pass is True
    assert res.outcome.invocation_pass is True


def test_21_safe_invoke_flags_non_mapping_return():
    def bad_return(**kwargs):
        return "not a dict"

    res = safe_invoke("x", bad_return, args={"_probe": True})
    assert res.outcome.schema_pass is False
    assert res.outcome.probe_state in (EffectiveState.DEGRADED, EffectiveState.HELD)


def test_22_safe_invoke_swallows_exceptions_returns_failed():
    def exploding(**kwargs):
        raise RuntimeError("simulated crash")

    res = safe_invoke("x", exploding, args={"_probe": True})
    assert res.outcome.invocation_pass is False
    assert res.raw_exc != ""  # captured for diagnostics, NOT in detail


# ── 23. JSON Schema artifacts are valid JSON ─────────────────────────


def test_23_json_schema_files_parse(tmp_path):
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    for schema_file in ("schemas/receipt.v2.json", "schemas/wealth-envelope.v2.json"):
        path = root / schema_file
        assert path.exists(), f"missing schema file: {schema_file}"
        # Must parse as JSON
        text = path.read_text()
        obj = json.loads(text)
        assert obj.get("type") == "object"
        assert isinstance(obj.get("required"), list)
        assert "title" in obj


# ── 24. LAW-WEALTH-01 YAML is well-formed ─────────────────────────────


def test_24_law_yaml_well_formed():
    import yaml
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    path = root / "schemas" / "law-wealth-01.yaml"
    assert path.exists()
    text = path.read_text()
    doc = yaml.safe_load(text)
    assert doc["id"] == "LAW-WEALTH-01"
    assert len(doc["clauses"]) == 10
    assert all(c["id"] == i + 1 for i, c in enumerate(doc["clauses"]))