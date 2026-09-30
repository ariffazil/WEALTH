"""collapse_signature calibration suite (LAW-WEALTH-01 release 1, 2026-09-16).

Runs the known-outcome fixture corpus through the LIVE compute path
(v1 profile + calibrated v2 overlay), asserts class expectations, and
writes the calibration record artifact.

The pinned regression: the petronas_adversarial_paraphrase case scored
risk_level=MINIMAL with zero signals on v1 (2026-09-16 live probe) — it
must fire on v2.

Run: /root/WEALTH/.venv/bin/python3 tests/test_collapse_calibration.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path[:] = [p for p in sys.path if p not in ("", str(Path(__file__).resolve().parent))]

from wealth_core.collapse_signature.scanner import compute_collapse_risk  # noqa: E402

CASES_PATH = ROOT / "tests/calibration/collapse_cases.json"
RECORD_PATH = ROOT / "tests/calibration/collapse_signature_calibration_2026-09-16.json"

_FIRED_LEVELS = {"MODERATE", "ELEVATED", "HIGH", "CRITICAL"}


def _level(result: dict) -> str:
    return str((result.get("risk") or {}).get("risk_level", "") or "").upper()


def _has_signal(result: dict) -> bool:
    return bool(result.get("quantitative_triggers")) or bool(
        result.get("semantic_mechanism_hits")
    )


def run_case(case: dict) -> dict:
    result = compute_collapse_risk(case["text"])
    level = _level(result)
    hard = len(result.get("quantitative_triggers") or [])
    sem = len(result.get("semantic_mechanism_hits") or [])
    cov = (result.get("evidence_coverage") or {}).get("ratio")
    verdict = result.get("calibrated_verdict") or result.get("verdict_discipline")

    cls = case["class"]
    if cls == "POSITIVE":
        passed = (level in _FIRED_LEVELS or _has_signal(result)) and level != "MINIMAL"
    elif cls == "NEGATIVE":
        passed = hard == 0 and level not in {"ELEVATED", "HIGH", "CRITICAL"}
    elif cls == "AMBIGUOUS":
        passed = level != "MINIMAL" or bool(verdict)
    else:  # SPARSE
        passed = result.get("verdict_discipline") == "INSUFFICIENT_DATA" or level != "MINIMAL"

    return {
        "id": case["id"],
        "class": cls,
        "risk_level": level or None,
        "quant_triggers": hard,
        "semantic_hits": sem,
        "coverage": cov,
        "calibrated_verdict": verdict,
        "pass": passed,
    }


def main() -> int:
    cases = json.loads(CASES_PATH.read_text())["cases"]
    results = [run_case(c) for c in cases]

    # Live-corpus smoke (informational, not gating): real Enron 1999 AR text
    corpus_note = None
    try:
        from wealth_core.collapse_signature.historical import load_corpus

        ar = load_corpus("enron_1999_ar")
        if ar:
            r = compute_collapse_risk(ar[:20000])
            corpus_note = {
                "corpus": "enron_1999_ar[:20000]",
                "risk_level": _level(r),
                "quant": len(r.get("quantitative_triggers") or []),
                "semantic": len(r.get("semantic_mechanism_hits") or []),
            }
    except Exception as exc:  # noqa: BLE001
        corpus_note = {"error": str(exc)[:120]}

    failed = [r for r in results if not r["pass"]]
    record = {
        "artifact": "collapse_signature_calibration",
        "release": "LAW-WEALTH-01 release 1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "detector_version": "calibrated_v2_2026-09-16",
        "corpus_file": str(CASES_PATH.relative_to(ROOT)),
        "corpus_sha256": hashlib.sha256(CASES_PATH.read_bytes()).hexdigest()[:16],
        "verdict": "ALL_GREEN" if not failed else f"{len(failed)}_FAILED",
        "results": results,
        "live_corpus_smoke": corpus_note,
        "pinned_regression": {
            "case": "petronas_adversarial_paraphrase",
            "v1_observed": "MINIMAL / 0 signals (2026-09-16 live probe)",
            "v2_expected": "fired (quant or semantic) with risk != MINIMAL",
        },
        "discipline": (
            "MINIMAL risk requires adequate evidence coverage and zero "
            "quantitative and semantic triggers; hard triggers floor risk at "
            "MODERATE (ELEVATED across >=2 axes); thin evidence yields "
            "INSUFFICIENT_DATA with named missing fields."
        ),
    }
    RECORD_PATH.write_text(json.dumps(record, indent=2, ensure_ascii=False))

    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"{mark}  {r['id']:36s} [{r['class']:8s}] level={r['risk_level'] or '-':10s} q={r['quant_triggers']} s={r['semantic_hits']} cov={r['coverage']}")
    print(f"\ncorpus smoke: {corpus_note}")
    print(f"record: {RECORD_PATH.relative_to(ROOT)}")
    print("ALL GREEN" if not failed else f"{len(failed)} FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
