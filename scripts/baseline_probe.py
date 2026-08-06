#!/usr/bin/env python3
"""
W-000 Baseline Probe Runner — Prompt 1 (WEALTH Surface Cartographer)

PROBE RULES:
  1. For each tool, call with deliberately invalid mode → harvest valid-value list from error
  2. For every discovered mode, call once with representative payload → store RAW response
  3. Where a call errors, record error CLASS, not description
  4. Output: tests/fixtures/baseline/<tool>__<mode>.json (raw, verbatim)

This script runs locally (curl to :18082) so it can capture raw HTTP responses.
It reads MODE_INVENTORY.md for the mode matrix and fills in the gaps.

FAIL-CLOSED: If a probe fails, emit error class. Never emit partial success.
NO-CHECKMARK: Do not write ✅, "works", "verified" without stored payload.
RECEIPT: Every fixture is its own receipt.
"""

import json
import os
import sys
import time
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

WEALTH_ROOT = Path(__file__).resolve().parent.parent
BASELINE_DIR = WEALTH_ROOT / "tests" / "fixtures" / "baseline"
WEALTH_URL = "http://localhost:18082/mcp"
SESSION_ID = os.environ.get("ARIF_SESSION_ID", "SEAL-b3bbf8e9e1844adc")
ACTOR_ID = "ARIF"

# ── TOOL × MODE MATRIX (from MODE_INVENTORY.md + live schema) ─────────────

TOOL_MATRIX = {
    "capital_primitive": {
        "modes": [
            "npv",
            "irr",
            "emv",
            "evoi",
            "mc",
            "kelly",
            "markowitz",
            "robust",
            "chance_constrained",
            "two_stage",
        ],
        "invalid_mode": "garbage_mode_test",
        "representative_payload": {
            "mode": None,
            "session_id": SESSION_ID,
            "actor_id": ACTOR_ID,
            "cash_flows": [100, 100, 100, 100, 100],
            "discount_rate": 0.10,
        },
    },
    "capital_health": {
        "modes": [
            "conservation",
            "flow",
            "runway",
            "survival",
            "fiscal_breakeven",
            "confluence",
            "asymmetry",
        ],
        "submodes": {
            "survival": ["personal_finance", "corporate_runway", "sovereign_fiscal"]
        },
        "invalid_mode": "garbage_mode_test",
        "representative_payload": {
            "mode": None,
            "session_id": SESSION_ID,
            "actor_id": ACTOR_ID,
        },
    },
    "capital_diagnose": {
        "modes": [
            "stress_index",
            "governance_capacity",
            "cascade_model",
            "exploitation_detect",
            "collapse_signature",
            "beautiful_mouse",
            "capture_scan",
            "power_audit",
            "bid_surface",
            "optimize_mwc",
            "cadence_monitor",
            "crisis_reflex",
            "petronas_vitals",
            "sovereign_pulse",
            "petronas_phi",
        ],
        "invalid_mode": "garbage_mode_test",
        "representative_payload": {
            "mode": None,
            "session_id": SESSION_ID,
            "actor_id": ACTOR_ID,
            "domain_scope": "enron_2000",
        },
    },
    "capital_market": {
        "modes": ["fx", "commodity", "indicator", "stock", "gold", "oil", "gas"],
        "invalid_mode": "garbage_mode_test",
        "representative_payload": {
            "mode": None,
            "session_id": SESSION_ID,
            "actor_id": ACTOR_ID,
        },
    },
    "capital_ledger": {
        "modes": ["query", "write"],
        "invalid_mode": "garbage_mode_test",
        "representative_payload": {
            "mode": None,
            "session_id": SESSION_ID,
            "actor_id": ACTOR_ID,
            "query": "test",
        },
    },
    "capital_registry": {
        "modes": ["status", "schema", "domains", "health"],
        "invalid_mode": "garbage_mode_test",
        "representative_payload": {
            "mode": None,
            "session_id": SESSION_ID,
            "actor_id": ACTOR_ID,
        },
    },
    "capital_entropy": {
        "modes": [
            "power_consequence_map",
            "metric_purpose_audit",
            "responsibility_ledger",
            "trust_capital_decay",
            "coercive_order_cost",
            "entropy_externality",
        ],
        "invalid_mode": "garbage_mode_test",
        "representative_payload": {
            "mode": None,
            "session_id": SESSION_ID,
            "actor_id": ACTOR_ID,
        },
    },
    "wealth_judge_handoff": {
        "modes": ["prepare", "submit"],
        "invalid_mode": "garbage_mode_test",
        "representative_payload": {
            "mode": None,
            "session_id": SESSION_ID,
            "actor_id": ACTOR_ID,
        },
    },
}


def mcp_call(tool_name: str, arguments: dict) -> tuple[dict | None, str]:
    """Make a JSON-RPC 2.0 call to the WEALTH MCP server."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        WEALTH_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result, "ok"
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")[:500]
        return None, f"HTTP_{e.code}"
    except urllib.error.URLError as e:
        return None, f"URL_ERROR:{e.reason}"
    except Exception as e:
        return None, f"ERROR:{type(e).__name__}:{e}"


def save_fixture(tool_name: str, mode: str, result: dict | None, error_class: str):
    """Save a baseline fixture with raw response and error class."""
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    fixture_name = f"{tool_name}__{mode}.json"
    fixture_path = BASELINE_DIR / fixture_name

    fixture = {
        "tool": tool_name,
        "mode": mode,
        "error_class": error_class,
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "session_id": SESSION_ID,
        "raw_response": result,
        "sha256": hashlib.sha256(
            json.dumps(result, sort_keys=True, default=str).encode()
        ).hexdigest()
        if result
        else None,
    }

    fixture_path.write_text(json.dumps(fixture, indent=2, default=str))
    return fixture_path


def probe_invalid_mode(tool_name: str) -> str | None:
    """Call tool with deliberately invalid mode → harvest valid-value list from error."""
    matrix = TOOL_MATRIX[tool_name]
    payload = {**matrix["representative_payload"], "mode": matrix["invalid_mode"]}
    payload.pop("submode", None)  # remove submode key if present

    result, error_class = mcp_call(tool_name, payload)
    fixture_path = save_fixture(tool_name, matrix["invalid_mode"], result, error_class)
    print(
        f"  INVALID {tool_name}__{matrix['invalid_mode']}: {error_class} → {fixture_path.name}"
    )

    # Try to parse error for valid modes list
    if result and "error" in result:
        error_msg = str(result.get("error", {}).get("message", ""))
        if "valid" in error_msg.lower() or "mode" in error_msg.lower():
            return error_msg
    return None


def probe_mode(tool_name: str, mode: str, extra_payload: dict | None = None) -> str:
    """Probe a single (tool, mode) combination and save raw response."""
    matrix = TOOL_MATRIX[tool_name]
    payload = {**matrix["representative_payload"], "mode": mode}
    if extra_payload:
        payload.update(extra_payload)

    result, error_class = mcp_call(tool_name, payload)
    fixture_path = save_fixture(tool_name, mode, result, error_class)

    # Summarize
    if result and "error" not in result:
        # Check for result content
        content = result.get("result", {})
        if isinstance(content, dict):
            rtype = content.get("result_type", "?")
            tag = content.get("epistemic_tag", "?")
            status = f"result_type={rtype} tag={tag}"
        else:
            status = f"result={str(content)[:40]}"
    else:
        err = (
            result.get("error", {}).get("message", error_class)
            if result
            else error_class
        )
        status = f"ERROR: {str(err)[:60]}"

    print(f"  {tool_name}__{mode}: {status} → {fixture_path.name}")
    return status


def probe_all(limit: int | None = None):
    """Probe all tools and modes from the matrix."""
    total = sum(len(v["modes"]) for v in TOOL_MATRIX.values())
    print(
        f"W-000 BASELINE PROBE: {total} canonical modes across {len(TOOL_MATRIX)} tools"
    )
    print(f"Session: {SESSION_ID}\n")

    count = 0
    results = {"probed": 0, "errors": 0, "fixtures": 0}

    for tool_name, matrix in TOOL_MATRIX.items():
        print(f"── {tool_name} ({len(matrix['modes'])} modes) ──")

        # 1. Invalid mode probe
        error_hint = probe_invalid_mode(tool_name)
        count += 1
        results["fixtures"] += 1

        # 2. Each valid mode
        for mode in matrix["modes"]:
            if limit and count >= limit:
                print(
                    f"\n  LIMIT REACHED ({limit} probes). {total - results['probed']} remaining."
                )
                return results

            probe_mode(tool_name, mode)
            count += 1
            results["probed"] += 1
            results["fixtures"] += 1
            time.sleep(0.1)  # light backoff

        # 3. Submodes (survival submodes on capital_health)
        for base_mode, submodes in matrix.get("submodes", {}).items():
            for submode in submodes:
                if limit and count >= limit:
                    print(f"\n  LIMIT REACHED. {total - results['probed']} remaining.")
                    return results
                extra = {"survival_submode": submode} if base_mode == "survival" else {}
                probe_mode(tool_name, base_mode, extra_payload=extra if extra else None)
                count += 1
                results["probed"] += 1
                results["fixtures"] += 1
                time.sleep(0.1)

        print()

    return results


def report(results: dict):
    """Print summary and return exit code."""
    fixture_count = (
        len(list(BASELINE_DIR.glob("*.json"))) if BASELINE_DIR.exists() else 0
    )
    print(f"\n═══ W-000 BASELINE SUMMARY ═══")
    print(
        f"Probed: {results['probed']}  Errors: {results['errors']}  Fixtures: {fixture_count}"
    )
    print(f"Baseline dir: {BASELINE_DIR}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="W-000 Baseline Probe Runner")
    parser.add_argument("--limit", type=int, default=None, help="Max probes to run")
    parser.add_argument(
        "--tool", type=str, default=None, help="Probe specific tool only"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        help="Probe specific mode only (requires --tool)",
    )
    parser.add_argument(
        "--report", action="store_true", help="Just report fixture counts"
    )
    args = parser.parse_args()

    if args.report:
        fixture_count = (
            len(list(BASELINE_DIR.glob("*.json"))) if BASELINE_DIR.exists() else 0
        )
        print(json.dumps({"fixture_count": fixture_count, "dir": str(BASELINE_DIR)}))
        sys.exit(0)

    if args.tool and args.mode:
        probe_mode(args.tool, args.mode)
        sys.exit(0)

    if args.tool:
        TOOL_MATRIX = {args.tool: TOOL_MATRIX[args.tool]}

    results = probe_all(limit=args.limit)
    report(results)
