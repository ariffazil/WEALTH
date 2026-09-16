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
    evaluate_dict_result,
    extract_external_uris,
)


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
