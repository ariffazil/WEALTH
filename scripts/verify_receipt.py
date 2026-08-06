#!/usr/bin/env python3
"""
WEALTH Receipt Verifier — Prompt 5 (Standing Role)

Produces NO code and NO analysis. Only output: ACCEPT or REJECT on another
agent's claim. Has no authority to approve work — only to refuse claims
lacking receipts. That asymmetry is the point.

Usage:
    python scripts/verify_receipt.py <report_path>          # single report
    python scripts/verify_receipt.py --dir <directory>       # batch
    python scripts/verify_receipt.py --carry-forward         # verify carry_forward claims
    python scripts/verify_receipt.py --mode-inventory        # verify MODE_INVENTORY.md

FAIL-CLOSED: If you cannot verify, emit REJECTED:verifier_error:<reason>.
NEVER emit partial acceptance.
"""

import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path


WEALTH_ROOT = Path(__file__).resolve().parent.parent
BASELINE_DIR = WEALTH_ROOT / "tests" / "fixtures" / "baseline"
MODE_INVENTORY_PATH = WEALTH_ROOT / "docs" / "MODE_INVENTORY.md"
CARRY_FORWARD_PATH = Path("/root/.local/share/arifos/carry_forward.json")

# ── REJECT RULES ──────────────────────────────────────────────────────────

REJECT_RULES = {
    "R1_CHECKMARK": {
        "desc": "✅, 'works', 'verified', or coverage % without stored raw payload",
        "patterns": ["✅", "verified", "works", "working"],
    },
    "R2_DEPLOY_DRIFT": {
        "desc": "source_commit == deployed_commit asserted without live probe",
    },
    "R3_FIXTURE_STALE": {
        "desc": "before == after sha256 while claiming change",
    },
    "R4_FIRST_GREEN": {
        "desc": "all-green test suite on first authoring",
        "patterns": ["8/8", "all pass", "all green", "100% pass", "0 failures"],
    },
    "R5_SCORE_NO_FILE": {
        "desc": "ΔS, Eureka, FQ, Ω₀ scored on session where no file changed",
        "score_fields": ["ΔS", "Eureka", "FQ", "Ω₀"],
    },
    "R6_MODE_NO_RESPONSE": {
        "desc": "mode listed as reachable with no stored response or error class",
    },
    "R7_TOOL_READY_NO_TEST": {
        "desc": "tool described as 'ready'/'wired'/'chained' without differential test",
        "patterns": ["ready", "wired", "chained", "complete", "done"],
    },
    "R8_VERDICT_NO_COVERAGE": {
        "desc": "verdict reported without accompanying coverage ratio",
        "verdict_terms": [
            "SEAL",
            "HOLD",
            "SABAR",
            "VOID",
            "PARTIAL",
            "INSUFFICIENT_EVIDENCE",
        ],
    },
}


def reject(reason: str, detail: str = "") -> dict:
    """Emit a structured rejection."""
    return {
        "verdict": "REJECTED",
        "reason": reason,
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }


def accept() -> dict:
    """Emit acceptance."""
    return {
        "verdict": "ACCEPT",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }


# ── CHECKS ────────────────────────────────────────────────────────────────


def check_r1_checkmark(report_text: str) -> dict | None:
    """R1: ✅, 'works', 'verified', or coverage % without stored raw payload path."""
    for pattern in REJECT_RULES["R1_CHECKMARK"]["patterns"]:
        if pattern in report_text.lower():
            # Check if there's a payload path nearby
            has_payload = any(
                marker in report_text
                for marker in [
                    "fixtures/baseline/",
                    ".json",
                    "raw payload",
                    "stored at",
                    "payload:",
                    "fixture:",
                ]
            )
            if not has_payload:
                return reject(
                    "R1_CHECKMARK", f"Found '{pattern}' without stored raw payload path"
                )
    return None


def check_r3_fixture_stale(report_text: str) -> dict | None:
    """R3: before-fix SHA256 == after-fix SHA256 while claiming a change."""
    import re

    sha_matches = re.findall(r"sha256[: ]+([a-f0-9]{64})", report_text.lower())
    if len(sha_matches) >= 2:
        before_sha = sha_matches[0]
        after_sha = sha_matches[1]
        if before_sha == after_sha:
            change_words = [
                "changed",
                "fixed",
                "updated",
                "modified",
                "refactored",
                "added",
                "removed",
            ]
            if any(w in report_text.lower() for w in change_words):
                return reject(
                    "R3_FIXTURE_STALE",
                    f"before={before_sha[:12]} == after={after_sha[:12]} while claiming change",
                )
    return None


def check_r4_first_green(report_text: str) -> dict | None:
    """R4: all-green test suite reported on first authoring."""
    for pattern in REJECT_RULES["R4_FIRST_GREEN"]["patterns"]:
        if pattern in report_text.lower():
            # Check context for "first" / "initial" indicators
            first_indicators = ["first", "initial", "on first", "authoring"]
            if any(ind in report_text.lower() for ind in first_indicators):
                return reject(
                    "R4_FIRST_GREEN",
                    f"All-green claimed on first authoring: '{pattern}'",
                )
    return None


def check_r5_score_no_file(report_text: str) -> dict | None:
    """R5: ΔS, Eureka, FQ, Ω₀ scored on session where no file changed."""
    scored_fields = []
    for field in REJECT_RULES["R5_SCORE_NO_FILE"]["score_fields"]:
        if field.lower() in report_text.lower():
            scored_fields.append(field)

    if scored_fields:
        # Check if any file change is claimed
        file_change_indicators = [
            "git diff",
            "changed file",
            "modified",
            "created file",
            "wrote",
            "edited",
            "committed",
            "diff --stat",
            ".py",
            ".json",
            ".md",
            ".yaml",
            ".toml",
        ]
        has_file_change = any(
            ind in report_text.lower() for ind in file_change_indicators
        )
        if not has_file_change:
            return reject(
                "R5_SCORE_NO_FILE",
                f"Scored {scored_fields} on session with no file changes detected",
            )
    return None


def check_r6_mode_no_response(report_text: str, baseline_fixtures: set) -> dict | None:
    """R6: mode listed as reachable with no stored response or error class."""
    import re

    # Find mode claims: "mode X: ✅ reachable" or similar
    mode_claims = re.findall(
        r"(\w+)\s*[:=]\s*✅\s*(?:reachable|valid|working)",
        report_text,
    )
    rejected = []
    for mode_name in set(mode_claims):
        # Check if there's a stored fixture
        fixture_exists = any(mode_name.lower() in f.lower() for f in baseline_fixtures)
        if not fixture_exists:
            # Also check for error class mention
            error_indicators = [
                "error:",
                "INTERNAL_ERROR",
                "SCHEMA_VIOLATION",
                "crashed",
                "FATAL",
            ]
            error_nearby = any(err in report_text for err in error_indicators)
            if not error_nearby:
                rejected.append(mode_name)

    if rejected:
        return reject(
            "R6_MODE_NO_RESPONSE",
            f"Modes claimed reachable without stored fixture or error class: {rejected[:5]}",
        )
    return None


def check_r7_tool_ready_no_test(report_text: str) -> dict | None:
    """R7: tool described as 'ready'/'wired'/'chained' without differential test row."""
    for pattern in REJECT_RULES["R7_TOOL_READY_NO_TEST"]["patterns"]:
        if pattern in report_text.lower():
            test_indicators = [
                "test_differential",
                "differential test",
                "red/green",
                "test_",
                "pytest",
                "assert",
                ".test.",
                "confusion matrix",
                "control set",
            ]
            has_test = any(ind in report_text.lower() for ind in test_indicators)
            if not has_test:
                return reject(
                    "R7_TOOL_READY_NO_TEST",
                    f"Tool described as '{pattern}' without differential test evidence",
                )
    return None


def check_r8_verdict_no_coverage(report_text: str) -> dict | None:
    """R8: verdict reported without accompanying coverage ratio."""
    import re

    for term in REJECT_RULES["R8_VERDICT_NO_COVERAGE"]["verdict_terms"]:
        # Look for verdict assertions, not code examples
        verdict_pattern = re.compile(rf"(?:verdict|result)[:=]\s*{term}", re.IGNORECASE)
        if verdict_pattern.search(report_text):
            # Check for coverage ratio nearby
            coverage_indicators = [
                "coverage",
                "ratio",
                "known/total",
                "known:",
                "total:",
            ]
            has_coverage = any(
                ind in report_text.lower() for ind in coverage_indicators
            )
            if not has_coverage:
                return reject(
                    "R8_VERDICT_NO_COVERAGE",
                    f"Verdict '{term}' reported without coverage ratio",
                )
    return None


# ── VERIFY ENTRYPOINT ─────────────────────────────────────────────────────


def verify_report(report_text: str, baseline_fixtures: set | None = None) -> dict:
    """
    Run all REJECT rules against a report.

    Returns:
        {"verdict": "ACCEPT", ...} or {"verdict": "REJECTED", "reason": ..., "detail": ...}
    """
    if baseline_fixtures is None:
        baseline_fixtures = set()

    checks = [
        check_r1_checkmark(report_text),
        check_r3_fixture_stale(report_text),
        check_r4_first_green(report_text),
        check_r5_score_no_file(report_text),
        check_r6_mode_no_response(report_text, baseline_fixtures),
        check_r7_tool_ready_no_test(report_text),
        check_r8_verdict_no_coverage(report_text),
    ]

    for result in checks:
        if result is not None and result.get("verdict") == "REJECTED":
            return result

    return accept()


def verify_carry_forward() -> dict:
    """Verify claims in carry_forward.json against baseline fixtures."""
    if not CARRY_FORWARD_PATH.exists():
        return reject("VERIFIER_ERROR", "carry_forward.json not found")

    cf = json.loads(CARRY_FORWARD_PATH.read_text())
    completed = cf.get("completed_this_session", [])
    open_loops = cf.get("open_loops_888_HOLD", [])

    # Check completed claims
    results = []
    for claim in completed:
        # Does this claim reference a specific deliverable?
        if "MODE_INVENTORY.md" in claim and "53 modes" in claim:
            # Check: does MODE_INVENTORY.md actually have 53 modes cataloged?
            if MODE_INVENTORY_PATH.exists():
                inventory_text = MODE_INVENTORY_PATH.read_text()
                mode_count = inventory_text.count("| `")
                # Count actual probed modes
                probed_count = inventory_text.count(
                    "reachable ✅"
                ) + inventory_text.count("crashed ❌")
                results.append(
                    {
                        "claim": claim[:80],
                        "check": "MODE_INVENTORY.md completeness",
                        "finding": f"Modes probed: {probed_count}, total: 53, fixtures: {len(list(BASELINE_DIR.glob('*.json')))}",
                        "note": "W-000 baseline self-reports 43 modes not yet probed. Fixture count is the receipt."
                        if probed_count < 20
                        else "",
                    }
                )

        if "THREE_CANONICAL_LAWS sealed" in claim:
            results.append(
                {
                    "claim": claim[:80],
                    "check": "Canonical laws substantiation",
                    "finding": "Three laws claimed sealed — verify VAULT999 seal IDs exist for each",
                }
            )

    # Check baseline fixture count vs. modes claimed
    fixture_count = (
        len(list(BASELINE_DIR.glob("*.json"))) if BASELINE_DIR.exists() else 0
    )
    total_modes_claimed = 53

    report = {
        "verdict": "REJECTED" if fixture_count < 10 else "ACCEPT",
        "reason": f"R6_MODE_NO_RESPONSE: {fixture_count}/{total_modes_claimed} baseline fixtures"
        if fixture_count < total_modes_claimed
        else None,
        "checks": results,
        "baseline_fixture_count": fixture_count,
        "total_modes_claimed": total_modes_claimed,
        "completed_claims": len(completed),
        "open_loops": len(open_loops),
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }

    if fixture_count < total_modes_claimed:
        report["verdict"] = "REJECTED"
        report["reason"] = (
            f"R6_MODE_NO_RESPONSE: {fixture_count}/{total_modes_claimed} baseline fixtures exist. W-000 claim of '53 modes cataloged' lacks complete receipts."
        )
    else:
        report["verdict"] = "ACCEPT"

    return report


def verify_mode_inventory() -> dict:
    """Verify MODE_INVENTORY.md claims against baseline fixtures."""
    if not MODE_INVENTORY_PATH.exists():
        return reject("VERIFIER_ERROR", "MODE_INVENTORY.md not found")

    inventory_text = MODE_INVENTORY_PATH.read_text()
    baseline_fixtures = (
        set(f.name for f in BASELINE_DIR.glob("*.json"))
        if BASELINE_DIR.exists()
        else set()
    )

    # Count modes marked as reachable ✅
    import re

    reachable_modes = re.findall(r"\|\s*`(\w+)`\s*\|\s*✅\s*\|", inventory_text)
    degraded_modes = re.findall(
        r"\|\s*`(\w+)`\s*\|\s*✅\s*\(degraded\)\s*\|", inventory_text
    )
    crashed_modes = re.findall(r"\|\s*`(\w+)`\s*\|\s*❌\s*\|", inventory_text)

    all_claimed = reachable_modes + degraded_modes + crashed_modes
    modes_with_fixtures = []
    modes_without_fixtures = []

    for mode in all_claimed:
        matching = [f for f in baseline_fixtures if mode in f]
        if matching:
            modes_with_fixtures.append(mode)
        else:
            modes_without_fixtures.append(mode)

    not_probed = len(re.findall(r"Not yet probed", inventory_text))

    return {
        "verdict": "REJECTED" if modes_without_fixtures else "ACCEPT",
        "reachable_claimed": len(reachable_modes),
        "degraded_claimed": len(degraded_modes),
        "crashed_claimed": len(crashed_modes),
        "not_yet_probed": not_probed,
        "modes_with_fixtures": modes_with_fixtures,
        "modes_without_fixtures": modes_without_fixtures,
        "total_fixtures": len(baseline_fixtures),
        "reason": (
            f"R6_MODE_NO_RESPONSE: {len(modes_without_fixtures)} modes claimed reachable/degraded/crashed "
            f"without stored baseline fixtures: {modes_without_fixtures[:10]}"
            if modes_without_fixtures
            else None
        ),
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }


# ── CLI ───────────────────────────────────────────────────────────────────


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: verify_receipt.py <report_path> | --dir <dir> | --carry-forward | --mode-inventory"
        )
        print()
        print("REJECT RULES:")
        for rule_id, rule in REJECT_RULES.items():
            print(f"  {rule_id}: {rule['desc']}")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--carry-forward":
        result = verify_carry_forward()
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result.get("verdict") == "ACCEPT" else 1)

    elif arg == "--mode-inventory":
        result = verify_mode_inventory()
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result.get("verdict") == "ACCEPT" else 1)

    elif arg == "--dir":
        if len(sys.argv) < 3:
            print("ERROR: --dir requires a directory path")
            sys.exit(1)
        dir_path = Path(sys.argv[2])
        if not dir_path.exists():
            print(
                json.dumps(
                    reject("VERIFIER_ERROR", f"Directory not found: {dir_path}"),
                    indent=2,
                )
            )
            sys.exit(1)

        baseline_fixtures = (
            set(f.name for f in BASELINE_DIR.glob("*.json"))
            if BASELINE_DIR.exists()
            else set()
        )
        all_results = []
        for report_file in sorted(dir_path.glob("*")):
            if report_file.suffix in (".md", ".txt", ".json", ".jsonl"):
                report_text = report_file.read_text()
                result = verify_report(report_text, baseline_fixtures)
                result["report_file"] = str(report_file)
                all_results.append(result)

        print(json.dumps(all_results, indent=2, default=str))
        rejected = [r for r in all_results if r.get("verdict") == "REJECTED"]
        sys.exit(len(rejected))

    elif arg == "--rules":
        for rule_id, rule in REJECT_RULES.items():
            print(f"  {rule_id}: {rule['desc']}")

    else:
        report_path = Path(arg)
        if not report_path.exists():
            print(
                json.dumps(
                    reject("VERIFIER_ERROR", f"Report not found: {report_path}"),
                    indent=2,
                )
            )
            sys.exit(1)

        report_text = report_path.read_text()
        baseline_fixtures = (
            set(f.name for f in BASELINE_DIR.glob("*.json"))
            if BASELINE_DIR.exists()
            else set()
        )
        result = verify_report(report_text, baseline_fixtures)
        result["report_file"] = str(report_path)
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result.get("verdict") == "ACCEPT" else 1)


if __name__ == "__main__":
    main()
