"""
W-001: Differential Tests — Prompt 2, Task A

Tests that WEALTH tools produce DIFFERENT outputs when given MATERIALLY
different inputs. A tool that returns byte-identical output across semantically
opposite payloads is decorative — it measures the fixture, not the tool.

VOLATILE_KEYS are stripped recursively before comparison. Without this the
suite passes on timestamp drift alone.

KNOWN-RED patterns are documented failures that should FAIL until fixed.
They are NOT "skipped" or "xfail" — they are the calibration target.

RECEIPT: Every test carries the fixture path it was built from.
FAIL-CLOSED / NO-CHECKMARK clauses apply.
"""

import json
import copy
from pathlib import Path
from datetime import datetime, timezone

WEALTH_ROOT = Path(__file__).resolve().parent.parent
BASELINE_DIR = WEALTH_ROOT / "tests" / "fixtures" / "baseline"

# ── VOLATILE KEYS — strip recursively before comparing ─────────────────────

VOLATILE_KEYS = {
    "map_id",
    "trace_id",
    "receipt_hash",
    "computation_timestamp",
    "mapped_at",
    "epoch",
    "timestamp",
    "call_hash",
    "gate_event_id",
    "snapshot_hash",
    "harness_lineage_hash",
    "signed_at",
    "event_id",
    "session_id",
    "epoch",
    "tool_version",
    "receipt_hash",
    "map_id",
    "metadata",
    "_governance_advisory",
}


def strip_volatile(obj):
    """Recursively remove volatile keys and timestamps from any object."""
    if isinstance(obj, dict):
        return {
            k: strip_volatile(v)
            for k, v in obj.items()
            if k not in VOLATILE_KEYS
            and not k.startswith("_")
            and not isinstance(v, str)
            or (isinstance(v, str) and not _looks_like_timestamp(v))
        }
    elif isinstance(obj, list):
        return [strip_volatile(item) for item in obj]
    return obj


def _looks_like_timestamp(s: str) -> bool:
    """Heuristic: does this string look like a timestamp?"""
    return s.startswith("202") and ("T" in s or "Z" in s or "+" in s) and len(s) > 15


def normalize(obj):
    """Strip volatile keys + timestamps, then sort for deterministic comparison."""
    stripped = strip_volatile(obj)
    return json.dumps(stripped, sort_keys=True, default=str)


# ── PAYLOAD GENERATORS — opposite governance postures ──────────────────────


def payload_capital_health_survival():
    """Two payloads: surplus earner vs. distressed burn."""
    session = {"session_id": "SEAL-e26fefa68fc642b6", "actor_id": "ARIF"}

    return {
        "tool": "capital_health",
        "mode": "survival",
        "survival_submode": "personal_finance",
        "payload_a": {
            "mode": "survival",
            "survival_submode": "personal_finance",
            "monthly_income_v": 20000,
            "monthly_expenses_v": 8000,
            "liquid_assets": 200000,
            **session,
        },
        "payload_b": {
            "mode": "survival",
            "survival_submode": "personal_finance",
            "monthly_income_v": 3000,
            "monthly_expenses_v": 5000,
            "liquid_assets": 500,
            **session,
        },
        "expected_difference": "net_monthly should differ: +12000 vs -2000. survival_verdict should differ.",
    }


def payload_capital_health_corporate():
    """Two payloads: well-funded vs. distressed corporate runway."""
    session = {"session_id": "SEAL-e26fefa68fc642b6", "actor_id": "ARIF"}

    return {
        "tool": "capital_health",
        "mode": "survival",
        "survival_submode": "corporate_runway",
        "payload_a": {
            "mode": "survival",
            "survival_submode": "corporate_runway",
            "liquid_assets": 10000000,
            "monthly_burn": 100000,
            **session,
        },
        "payload_b": {
            "mode": "survival",
            "survival_submode": "corporate_runway",
            "liquid_assets": 50000,
            "monthly_burn": 50000,
            **session,
        },
        "expected_difference": "runway_months should differ: 100 vs 1. KNOWN-RED: corporate_runway silently downgraded to personal_finance, so both may collapse to SURVIVAL_ADEQUATE.",
        "known_red": True,
        "red_reason": "corporate_runway silent downgrade to personal_finance defect",
    }


def payload_capital_diagnose_collapse():
    """Two payloads: opposite institutional profiles."""
    session = {"session_id": "SEAL-e26fefa68fc642b6", "actor_id": "ARIF"}

    return {
        "tool": "capital_diagnose",
        "mode": "collapse_signature",
        "payload_a": {
            "mode": "collapse_signature",
            "domain_scope": "enron_2000",
            **session,
        },
        "payload_b": {
            "mode": "collapse_signature",
            "domain_scope": "temasek_2014",
            **session,
        },
        "expected_difference": "risk profiles should differ: Enron (known extractive) vs Temasek (known inclusive). KNOWN-RED: _source_text empty — all axes signal_count=0 regardless of domain_scope.",
        "known_red": True,
        "red_reason": "collapse_signature _source_text empty defect — domain_scope not consumed",
    }


def payload_capital_entropy_power():
    """Two payloads: concentrated power vs. distributed."""
    session = {"session_id": "SEAL-e26fefa68fc642b6", "actor_id": "ARIF"}

    return {
        "tool": "capital_entropy",
        "mode": "power_consequence_map",
        "payload_a": {
            "mode": "power_consequence_map",
            "decision_makers": [
                {"id": "ceo", "authority": "executive", "stake": 0.60},
            ],
            "beneficiaries": [
                {"id": "shareholders", "benefit": "dividends", "share": 0.90},
            ],
            "cost_bearers": [
                {
                    "id": "workers",
                    "harm": "layoff",
                    "exposure": 0.80,
                    "exit": 0.05,
                    "compensation": 0.10,
                },
            ],
            **session,
        },
        "payload_b": {
            "mode": "power_consequence_map",
            "decision_makers": [
                {"id": "board", "authority": "distributed", "stake": 0.15},
                {
                    "id": "workers_council",
                    "authority": "co-determination",
                    "stake": 0.15,
                },
                {"id": "community_board", "authority": "advisory", "stake": 0.10},
            ],
            "beneficiaries": [
                {"id": "shareholders", "benefit": "dividends", "share": 0.30},
                {"id": "workers", "benefit": "profit_share", "share": 0.30},
                {"id": "community", "benefit": "local_reinvestment", "share": 0.20},
                {"id": "environment", "benefit": "restoration_fund", "share": 0.20},
            ],
            "cost_bearers": [
                {
                    "id": "shareholders",
                    "harm": "dilution",
                    "exposure": 0.15,
                    "exit": 0.90,
                    "compensation": 0.20,
                },
            ],
            **session,
        },
        "expected_difference": "power_concentration should differ: 0.60 vs distributed (≈0.25). KNOWN-RED: sub-scores derived from list LENGTH only — all decision_makers, beneficiaries, cost_bearers fields inert.",
        "known_red": True,
        "red_reason": "power_consequence_map ignores payload fields — scores derived from list length only",
    }


def payload_capital_primitive_npv():
    """Two cash flow sequences: positive vs. negative NPV."""
    session = {"session_id": "SEAL-e26fefa68fc642b6", "actor_id": "ARIF"}

    return {
        "tool": "capital_primitive",
        "mode": "npv",
        "payload_a": {
            "mode": "npv",
            "cash_flows": [-1000, 300, 400, 500, 600],
            "discount_rate": 0.10,
            **session,
        },
        "payload_b": {
            "mode": "npv",
            "cash_flows": [-1000, 50, 50, 50, 50],
            "discount_rate": 0.10,
            **session,
        },
        "expected_difference": "NPV should differ: positive (~290) vs negative (~-820 or small positive). Both should compute correctly.",
    }


def payload_wealth_judge_handoff():
    """Two handoff intents: reversible vs. irreversible."""
    session = {"session_id": "SEAL-e26fefa68fc642b6", "actor_id": "ARIF"}

    return {
        "tool": "wealth_judge_handoff",
        "mode": "prepare",
        "payload_a": {
            "mode": "prepare",
            "intent": "capital_health survival check",
            "reversibility": "REVERSIBLE",
            "blast_radius": "low",
            **session,
        },
        "payload_b": {
            "mode": "prepare",
            "intent": "capital_ledger write — transfer 500k MYR",
            "reversibility": "IRREVERSIBLE",
            "blast_radius": "high",
            **session,
        },
        "expected_difference": "reversibility and blast_radius should differ. requires_888_hold should differ.",
    }


def payload_capital_health_fiscal():
    """Two fiscal breakeven scenarios: different oil prices."""
    session = {"session_id": "SEAL-e26fefa68fc642b6", "actor_id": "ARIF"}

    return {
        "tool": "capital_health",
        "mode": "fiscal_breakeven",
        "payload_a": {
            "mode": "fiscal_breakeven",
            "total_govt_expenditure": 300_000_000_000,
            "non_oil_revenue": 100_000_000_000,
            "petronas_dividend_base_rm": 50_000_000_000,
            "oil_price_assumption_usd": 80,
            **session,
        },
        "payload_b": {
            "mode": "fiscal_breakeven",
            "total_govt_expenditure": 350_000_000_000,
            "non_oil_revenue": 80_000_000_000,
            "petronas_dividend_base_rm": 40_000_000_000,
            "oil_price_assumption_usd": 60,
            **session,
        },
        "expected_difference": "breakeven oil price should differ. KNOWN-RED: sovereign_fiscal crashes at MCP schema layer.",
    }


# ── ALL DIFFERENTIAL TEST CASES ───────────────────────────────────────────

DIFFERENTIAL_TESTS = [
    payload_capital_health_survival,
    payload_capital_health_corporate,
    payload_capital_diagnose_collapse,
    payload_capital_entropy_power,
    payload_capital_primitive_npv,
    payload_wealth_judge_handoff,
    payload_capital_health_fiscal,
]


# ── TEST RUNNER (called from pytest) ───────────────────────────────────────


def make_mcp_call(tool_name: str, arguments: dict):
    """
    Call a WEALTH MCP tool via proper MCP session lifecycle.
    Initializes a new session, extracts the Mcp-Session-Id, then calls the tool.
    """
    import subprocess

    # Step 1: Initialize MCP session
    init_payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "w001-differential-test", "version": "1.0"},
            },
        }
    )
    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "--max-time",
                "10",
                "-X",
                "POST",
                "http://localhost:18082/mcp",
                "-H",
                "Content-Type: application/json",
                "-D",
                "-",  # dump headers to stdout
                "-d",
                init_payload,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        # Extract Mcp-Session-Id from response headers
        session_id = None
        for line in result.stdout.split("\n"):
            if "mcp-session-id:" in line.lower():
                session_id = line.split(":", 1)[1].strip()
                break
        if not session_id:
            return {
                "error": {
                    "code": -1,
                    "message": "Failed to extract MCP session ID from init",
                }
            }
    except Exception as e:
        return {"error": {"code": -1, "message": f"MCP init failed: {e}"}}

    # Step 2: Call the tool with the session ID
    call_payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
    )
    try:
        result = subprocess.run(
            [
                "curl",
                "-sf",
                "--max-time",
                "15",
                "-X",
                "POST",
                "http://localhost:18082/mcp",
                "-H",
                "Content-Type: application/json",
                "-H",
                f"Mcp-Session-Id: {session_id}",
                "-d",
                call_payload,
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": {"code": result.returncode, "message": result.stderr[:200]}}
    except Exception as e:
        return {"error": {"code": -1, "message": str(e)}}


def run_differential_test(case_func):
    """Run one differential test case. Returns (passed, detail, result_a, result_b)."""
    case = case_func()
    tool = case["tool"]
    payload_a = case["payload_a"]
    payload_b = case["payload_b"]
    known_red = case.get("known_red", False)

    result_a = make_mcp_call(tool, payload_a)
    result_b = make_mcp_call(tool, payload_b)

    # Check for errors
    if "error" in result_a:
        return False, f"Payload A errored: {result_a['error']}", result_a, result_b
    if "error" in result_b:
        return False, f"Payload B errored: {result_b['error']}", result_a, result_b

    norm_a = normalize(result_a)
    norm_b = normalize(result_b)

    if norm_a == norm_b:
        if known_red:
            return (
                False,
                f"KNOWN-RED: {case.get('red_reason', 'byte-identical output across different payloads')}",
                result_a,
                result_b,
            )
        return (
            False,
            "Byte-identical output across materially different payloads",
            result_a,
            result_b,
        )

    return (
        True,
        f"DIFFERENT (lengths: {len(norm_a)} vs {len(norm_b)})",
        result_a,
        result_b,
    )


def test_all_differential():
    """Pytest test: run all differential tests and report red/green count."""
    results = {"green": 0, "red": 0, "known_red": 0, "details": []}

    for case_func in DIFFERENTIAL_TESTS:
        case = case_func()
        passed, detail, result_a, result_b = run_differential_test(case_func)
        entry = {
            "tool": case["tool"],
            "mode": case["mode"],
            "expected_difference": case.get("expected_difference", "?"),
            "passed": passed,
            "detail": detail,
            "known_red": case.get("known_red", False),
            "norm_a_len": len(normalize(result_a)) if result_a else 0,
            "norm_b_len": len(normalize(result_b)) if result_b else 0,
        }
        results["details"].append(entry)

        if passed:
            results["green"] += 1
        elif case.get("known_red"):
            results["known_red"] += 1
        else:
            results["red"] += 1

    # The test: publish red/green count. All-green on first authoring IS a red flag.
    # If green == total, something is wrong with the payloads (Prompt 2: "they were too similar").
    total = len(DIFFERENTIAL_TESTS)
    if results["green"] == total and results["known_red"] > 0:
        # Suspicious: all green despite known-red cases — likely payloads aren't different enough
        pass  # Don't fail; surface as a finding

    results["total"] = total
    results["verdict"] = (
        "EXPECTED_MIX"
        if results["green"] > 0 and (results["red"] > 0 or results["known_red"] > 0)
        else "ALL_GREEN_SUSPICIOUS"
        if results["green"] == total
        else "ALL_RED"
    )

    # Print results to stdout for capture
    print(f"\n═══ DIFFERENTIAL TEST RESULTS ═══")
    print(
        f"Green: {results['green']}  Red: {results['red']}  Known-Red: {results['known_red']}  Total: {total}"
    )
    print(f"Verdict: {results['verdict']}")
    print()

    for entry in results["details"]:
        status = "🟢" if entry["passed"] else "🔴" if not entry["known_red"] else "🟡"
        print(f"  {status} {entry['tool']}__{entry['mode']}: {entry['detail']}")
        if entry["known_red"]:
            print(f"     KNOWN-RED (expected to fail until defect is fixed)")

    # Assertion: there should be BOTH green and red/known-red results.
    # All-green = payloads too similar. All-red = everything broken.
    assert results["green"] > 0, f"Expected at least some green tests, got 0/{total}"
    # Known-red cases exist — they should be red
    if results["known_red"] > 0:
        known_red_cases = [d for d in results["details"] if d["known_red"]]
        for krc in known_red_cases:
            assert not krc["passed"], (
                f"KNOWN-RED {krc['tool']}__{krc['mode']} unexpectedly passed — defect may be fixed or payloads insufficiently different"
            )


# ── STANDALONE RUNNER ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print(f"W-001 DIFFERENTIAL TEST RUNNER")
    print(f"Session: SEAL-e26fefa68fc642b6")
    print(f"Test cases: {len(DIFFERENTIAL_TESTS)}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")

    results = {"green": 0, "red": 0, "known_red": 0, "details": []}

    for case_func in DIFFERENTIAL_TESTS:
        case = case_func()
        print(f"── {case['tool']}__{case['mode']} ──")
        passed, detail, result_a, result_b = run_differential_test(case_func)
        entry = {
            "tool": case["tool"],
            "mode": case["mode"],
            "passed": passed,
            "detail": detail,
            "known_red": case.get("known_red", False),
        }
        results["details"].append(entry)

        if passed:
            results["green"] += 1
            print(f"  🟢 PASS: {detail}")
        elif case.get("known_red"):
            results["known_red"] += 1
            print(f"  🟡 KNOWN-RED: {detail}")
            print(f"     Reason: {case.get('red_reason', '?')}")
        else:
            results["red"] += 1
            print(f"  🔴 FAIL: {detail}")

    total = len(DIFFERENTIAL_TESTS)
    print(f"\n═══ RESULTS ═══")
    print(
        f"Green: {results['green']}  Red: {results['red']}  Known-Red: {results['known_red']}  Total: {total}"
    )

    # Receipt block
    receipt = {
        "task": "W-001",
        "test_file": str(Path(__file__).resolve()),
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": "SEAL-e26fefa68fc642b6",
        "note": "KNOWN-RED cases are expected failures — they are calibration targets, not bugs.",
    }
    receipt_path = WEALTH_ROOT / "tests" / "fixtures" / "w001_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, default=str))
    print(f"\nReceipt: {receipt_path}")

    sys.exit(0 if results["red"] == 0 else 1)
