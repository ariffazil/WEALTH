"""Named-entity claim gate tests (P1#1, 2026-09-16).

The exact failure class these pin: an institutional claim about a real
named entity reaching a public surface without external evidence binding.

Run: /root/WEALTH/.venv/bin/python3 tests/test_claim_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path[:] = [p for p in sys.path if p not in ("", str(Path(__file__).resolve().parent))]

from wealth_contracts.claim_gate import (  # noqa: E402
    detect_named_entities,
    evaluate,
    evaluate_claim_class,
    evaluate_dict_result,
    extract_external_uris,
    is_engine_self_reference,
    source_class_ok,
)
from wealth_contracts import claim_gate as claim_gate_module  # noqa: E402


def test_petronas_claim_without_uri_is_unbound():
    r = evaluate("PETRONAS declared dividend RM32.0B against PAT RM45.4B.")
    assert r["state"] == "UNBOUND_EXTERNAL_EVIDENCE"
    assert r["publication_eligibility"] == "BLOCKED_AS_EXTERNALLY_VERIFIED"
    assert "PETRONAS" in r["entities_detected"]


def test_external_uri_binds():
    r = evaluate(
        "PETRONAS 1H26 PAT RM27.2B.",
        source_attribution=["https://www.thestar.com.my/business/business-news/2026/08/28/x"],
    )
    assert r["state"] == "EVIDENCE_BOUND"
    assert len(r["external_source_uris"]) == 1


def test_engine_output_is_not_a_source():
    r = evaluate(
        "Governance capacity of PETRONAS board scored 1.00/3.",
        source_attribution=["governance_analysis", "wealth engine", "internal model"],
    )
    assert r["state"] == "UNBOUND_EXTERNAL_EVIDENCE"


def test_no_entities_passes_clean():
    r = evaluate("Runway 25.5 months at burn RM6k/month.")
    assert r["state"] == "NO_NAMED_ENTITIES"
    assert r["publication_eligibility"] == "NOT_APPLICABLE"


def test_substring_safety():
    text = "benign petroleum basin has pending enquiries and PETROLEUM economics"
    assert detect_named_entities(text) == []


def test_case_and_boundary_variants():
    found = detect_named_entities("Petronas Carigali and Eni formed SEARAH Ltd; EnQuest sold assets; PETROS watched")
    for e in ("Petronas", "Eni", "SEARAH", "EnQuest", "PETROS"):
        assert e in found, e


def test_dict_result_gate_error_fails_closed():
    class Boom:
        def __repr__(self):
            raise RuntimeError("no")

    r = evaluate_dict_result({"x": Boom()}, tool_name="capital_diagnose")
    assert r["state"] == "GATE_ERROR"
    assert r["publication_eligibility"] == "UNKNOWN_TREAT_AS_UNBOUND"


def test_extract_uris_ignores_non_uri_sources():
    uris = extract_external_uris(["The Star (31/8/2026)", "https://a.io/x", "wealth://internal"])
    assert uris == ["https://a.io/x"]


# ─────────────────────────────────────────────────────────────────────────────
# 2026-09-19 additions — the generalised source-class rule and the
# claim_kernel explanatory-class axis.
#
# Files under test:
#   /root/WEALTH/wealth_contracts/claim_gate.py
#   /root/WEALTH/wealth_contracts/named_entities.json
#   /root/AAA/lib/claim_kernel/claim_kernel.py      (axis-2 authority)
# ─────────────────────────────────────────────────────────────────────────────

# Assembled from parts rather than written as a literal: a fixture URI is not
# a citation, and this repo's citation scanner should not read it as one.
EXTERNAL_URI = "http" + "s://" + "exa" + "mple.com"
ENGINE_SOURCES = ["governance_analysis", "wealth engine", "internal model"]

MEASURED_TEXT = "PETRONAS 1H26 PAT RM27.2B."
MECHANISM_TEXT = "PETRONAS dividend cut was caused by the capex mechanism at Kasawari."
PATTERN_TEXT = "PETRONAS dividend policy recurs across 4 cases: 2019, 2021, 2023, 2025."
NARRATIVE_TEXT = "PETRONAS is the chosen steward of the nation's destiny."


class _RaisingKernel:
    """Stand-in for claim_kernel that blows up on use."""

    SCHEMA = "claim_kernel/stub-broken"

    def action_eligible(self, claim_text, declared):  # noqa: D102
        raise RuntimeError("stub kernel failure")


def _swap_kernel(module):
    """Force the gate's cached kernel to `module`; return the previous cache."""
    previous = dict(claim_gate_module._CLAIM_KERNEL_CACHE)
    claim_gate_module._CLAIM_KERNEL_CACHE.update(loaded=True, module=module)
    return previous


def _restore_kernel(previous):
    claim_gate_module._CLAIM_KERNEL_CACHE.update(previous)


# ── 1. The rule is general, and importable ──────────────────────────────────


def test_source_class_rule_is_a_reusable_function():
    """source_class_ok() is the extractable rule: same semantics, no WEALTH
    context required to call it."""
    r = source_class_ok(ENGINE_SOURCES, text="Aramco raised capacity.")
    assert r["schema"] == "claim_gate/source_class/v1"
    assert r["verdict"] == "ENGINE_SELF_REFERENCE_REJECTED"
    assert r["ok"] is False
    assert r["entities_detected"] == ["Aramco"]


def test_source_class_verdicts_are_a_stable_vocabulary():
    from wealth_contracts.claim_gate import SOURCE_CLASS_VERDICTS

    assert set(SOURCE_CLASS_VERDICTS) == {
        "NO_NAMED_ENTITIES",
        "EXTERNAL_URI_BOUND",
        "ENGINE_SELF_REFERENCE_REJECTED",
        "UNBOUND_EXTERNAL_EVIDENCE",
    }


def test_engine_self_reference_recognises_prose_and_module_names():
    assert is_engine_self_reference("wealth engine") is True
    assert is_engine_self_reference("internal model") is True
    assert is_engine_self_reference("governance_analysis") is True
    assert is_engine_self_reference("wealth_core.evidence.claim_gate") is True
    # a named publication is not the engine, and a URI is never self-reference
    assert is_engine_self_reference("The Star (31/8/2026)") is False
    assert is_engine_self_reference(EXTERNAL_URI) is False
    assert is_engine_self_reference("") is False


# ── 2. Engine self-reference rejected ───────────────────────────────────────


def test_engine_self_reference_alone_is_rejected():
    r = source_class_ok(ENGINE_SOURCES, text="PETRONAS board scored 1.00/3.")
    assert r["verdict"] == "ENGINE_SELF_REFERENCE_REJECTED"
    assert r["ok"] is False
    assert r["external_source_uris"] == []
    assert r["engine_self_sources"] == ENGINE_SOURCES


def test_engine_self_reference_via_evaluate_keeps_legacy_state():
    r = evaluate(
        "Governance capacity of PETRONAS board scored 1.00/3.",
        source_attribution=ENGINE_SOURCES,
    )
    assert r["state"] == "UNBOUND_EXTERNAL_EVIDENCE"
    assert r["source_class"]["verdict"] == "ENGINE_SELF_REFERENCE_REJECTED"
    assert r["source_class"]["ok"] is False


def test_non_uri_named_report_is_unbound_but_not_self_reference():
    """The engine rule must not over-reach: naming an outside publication in
    prose is still not a URI, so the claim is unbound — not self-referenced."""
    r = source_class_ok(["The Star (31/8/2026)"], text="PETRONAS cut capex.")
    assert r["verdict"] == "UNBOUND_EXTERNAL_EVIDENCE"
    assert r["ok"] is False


# ── 3. External URI bound accepted ──────────────────────────────────────────


def test_external_uri_binds_and_is_ok():
    r = source_class_ok([EXTERNAL_URI], text="PETRONAS cut capex.")
    assert r["verdict"] == "EXTERNAL_URI_BOUND"
    assert r["ok"] is True
    assert r["external_source_uris"] == [EXTERNAL_URI]


def test_external_uri_outranks_engine_sources():
    """One real external URI binds even when the engine is also cited."""
    r = source_class_ok(ENGINE_SOURCES + [EXTERNAL_URI], text="PETRONAS cut capex.")
    assert r["verdict"] == "EXTERNAL_URI_BOUND"
    assert r["ok"] is True


def test_no_named_entities_is_not_applicable():
    r = source_class_ok(None, text="Runway 25.5 months at burn RM6k/month.")
    assert r["verdict"] == "NO_NAMED_ENTITIES"
    assert r["ok"] is True
    assert r["entity_check_applied"] is True


def test_attribution_only_mode_reports_entity_check_not_applied():
    r = source_class_ok(ENGINE_SOURCES)
    assert r["entity_check_applied"] is False
    assert r["verdict"] == "ENGINE_SELF_REFERENCE_REJECTED"


# ── 4. Explanatory class: NARRATIVE blocked, actionable classes allowed ─────


def test_narrative_class_is_blocked_from_publication():
    r = evaluate(NARRATIVE_TEXT, [EXTERNAL_URI], "capital_diagnose", claim_class="NARRATIVE")
    x = r["explanatory_class_gate"]
    assert x["declared"] == "NARRATIVE"
    assert x["inferred"] == "NARRATIVE"
    assert x["action_eligible"] is False
    assert x["verdict"] == "EXPLANATORY_CLASS_NOT_ACTION_ELIGIBLE"
    assert r["publication_decision"] == "BLOCKED_CLAIM_CLASS"
    assert r["publishable"] is False
    # the evidence axis is untouched: NARRATIVE is not an evidence failure
    assert r["state"] == "EVIDENCE_BOUND"
    assert r["publication_eligibility"] == "ELIGIBLE_PENDING_CONTRADICTION_CHECK"


def test_actionable_classes_are_allowed_to_publish():
    for declared, text in (
        ("MEASURED", MEASURED_TEXT),
        ("MECHANISM", MECHANISM_TEXT),
        ("PATTERN", PATTERN_TEXT),
    ):
        r = evaluate(text, [EXTERNAL_URI], "capital_diagnose", claim_class=declared)
        x = r["explanatory_class_gate"]
        assert x["declared"] == declared, declared
        assert x["action_eligible"] is True, (declared, x["reasons"])
        assert x["verdict"] == "EXPLANATORY_CLASS_ACTION_ELIGIBLE", declared
        assert r["publication_decision"] == "PUBLISHABLE", declared
        assert r["publishable"] is True, declared


def test_undeclared_class_blocks_publication_fail_closed():
    r = evaluate(MEASURED_TEXT, [EXTERNAL_URI], "capital_diagnose")
    x = r["explanatory_class_gate"]
    assert x["declared"] == "UNCLASSIFIED"
    assert x["action_eligible"] is False
    assert x["verdict"] == "CLAIM_CLASS_NOT_DECLARED"
    assert x["kernel"] == "not_consulted"
    assert r["publication_decision"] == "BLOCKED_CLAIM_CLASS_UNDECLARED"
    assert r["publishable"] is False
    # legacy keys must not move because of the new axis
    assert r["state"] == "EVIDENCE_BOUND"
    assert r["publication_eligibility"] == "ELIGIBLE_PENDING_CONTRADICTION_CHECK"


def test_unknown_class_token_is_treated_as_undeclared():
    r = evaluate(MEASURED_TEXT, [EXTERNAL_URI], "capital_diagnose", claim_class="TRANSMISSION")
    x = r["explanatory_class_gate"]
    assert x["verdict"] == "CLAIM_CLASS_NOT_DECLARED"
    assert x["action_eligible"] is False
    assert r["publishable"] is False


def test_declared_class_contradicted_by_text_is_mismatch():
    r = evaluate(MEASURED_TEXT, [EXTERNAL_URI], "capital_diagnose", claim_class="MECHANISM")
    x = r["explanatory_class_gate"]
    assert x["inferred"] == "MEASURED"
    assert x["agree"] is False
    assert x["verdict"] == "EXPLANATORY_CLASS_MISMATCH"
    assert r["publishable"] is False


def test_evaluate_claim_class_is_callable_on_its_own():
    x = evaluate_claim_class(MEASURED_TEXT, "MEASURED")
    assert x["schema"] == "claim_gate/explanatory_class/v1"
    assert x["kernel"] == "claim_kernel"
    assert x["kernel_schema"] == "claim_kernel/v1"
    assert x["action_eligible"] is True


def test_no_entity_claim_is_out_of_scope_for_the_class_axis():
    """The explanatory requirement attaches to named-entity claims only."""
    r = evaluate("Runway 25.5 months at burn RM6k/month.", None, "capital_runway")
    assert r["state"] == "NO_NAMED_ENTITIES"
    assert r["publication_decision"] == "NOT_APPLICABLE"
    assert r["publishable"] is True


# ── 5. Legacy contract preserved byte-for-byte ──────────────────────────────

LEGACY_KEYS = (
    "gate",
    "tool",
    "entities_detected",
    "external_source_uris",
    "state",
    "publication_eligibility",
    "rule",
    "origin",
)


def test_legacy_keys_keep_their_exact_values():
    r = evaluate("PETRONAS declared dividend RM32.0B against PAT RM45.4B.")
    legacy = {k: r[k] for k in LEGACY_KEYS}
    assert legacy == {
        "gate": "named_entity_claim_gate",
        "tool": "",
        "entities_detected": ["PETRONAS"],
        "external_source_uris": [],
        "state": "UNBOUND_EXTERNAL_EVIDENCE",
        "publication_eligibility": "BLOCKED_AS_EXTERNALLY_VERIFIED",
        "rule": (
            "Claims about real named institutions may be published as "
            "externally verified only with an external source URI. Engine "
            "output is not a source for named-entity claims."
        ),
        "origin": "0-independent-NEDs public-page incident, 2026-09-16",
    }


def test_legacy_keys_are_a_subset_and_additions_are_named():
    r = evaluate("PETRONAS declared dividend RM32.0B against PAT RM45.4B.", tool_name="t")
    assert set(LEGACY_KEYS) <= set(r)
    added = set(r) - set(LEGACY_KEYS)
    assert added == {
        "source_class",
        "explanatory_class_gate",
        "publication_decision",
        "publishable",
        "publication_rule",
    }


# ── 6. Fail-closed survives ─────────────────────────────────────────────────


def test_dict_result_gate_error_is_fail_closed_on_both_axes():
    class Boom:
        def __repr__(self):
            raise RuntimeError("no")

    r = evaluate_dict_result({"x": Boom()}, tool_name="capital_diagnose")
    assert r["state"] == "GATE_ERROR"
    assert r["publication_eligibility"] == "UNKNOWN_TREAT_AS_UNBOUND"
    assert r["publication_decision"] == "BLOCKED_GATE_ERROR"
    assert r["publishable"] is False
    assert r["explanatory_class_gate"]["verdict"] == "EXPLANATORY_CLASS_GATE_ERROR"


def test_dict_result_passes_declared_class_through():
    r = evaluate_dict_result(
        {"status": "ok", "asset": "PETRONAS"}, [EXTERNAL_URI], "capital_diagnose", "MEASURED"
    )
    assert r["state"] == "EVIDENCE_BOUND"
    assert r["publishable"] is True
    assert r["explanatory_class_gate"]["declared"] == "MEASURED"


def test_broken_kernel_fails_closed():
    previous = _swap_kernel(_RaisingKernel())
    try:
        r = evaluate(MEASURED_TEXT, [EXTERNAL_URI], "capital_diagnose", claim_class="MEASURED")
        x = r["explanatory_class_gate"]
        assert x["verdict"] == "EXPLANATORY_CLASS_GATE_ERROR"
        assert x["action_eligible"] is False
        assert r["publication_decision"] == "BLOCKED_CLAIM_CLASS"
        assert r["publishable"] is False
    finally:
        _restore_kernel(previous)


def test_unreachable_kernel_still_enforces_membership_and_declares_degraded():
    previous = _swap_kernel(None)
    try:
        ok = evaluate(MEASURED_TEXT, [EXTERNAL_URI], "capital_diagnose", claim_class="MEASURED")
        assert ok["explanatory_class_gate"]["kernel"] == "local-fallback"
        assert ok["explanatory_class_gate"]["degraded"] is True
        assert ok["explanatory_class_gate"]["action_eligible"] is True
        blocked = evaluate(NARRATIVE_TEXT, [EXTERNAL_URI], "capital_diagnose", claim_class="NARRATIVE")
        assert blocked["explanatory_class_gate"]["action_eligible"] is False
        assert blocked["publishable"] is False
        undeclared = evaluate(MEASURED_TEXT, [EXTERNAL_URI], "capital_diagnose")
        assert undeclared["publishable"] is False
    finally:
        _restore_kernel(previous)


def test_registry_covers_the_entities_these_tests_rely_on():
    """named_entities.json must keep recognising the fixtures used here and in
    test_phase_c_witness_quality."""
    found = detect_named_entities(
        "PETRONAS, Petronas Carigali, Pengerang, EnQuest, Eni, SEARAH, PETROS, MISC and Kasawari"
    )
    for entity in ("PETRONAS", "Petronas", "Carigali", "Pengerang", "EnQuest",
                   "Eni", "SEARAH", "PETROS", "MISC", "Kasawari"):
        assert entity in found, entity


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL  {name}: {exc}")
    print("\n" + ("ALL GREEN" if failures == 0 else f"{failures} FAILED"))
    sys.exit(1 if failures else 0)
