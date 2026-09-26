"""
Tests for internal/organ_governance.py
Covers: WEALTH_RISK_TIERS lookups, check_governance all branches,
_call_arifOS_judge network paths (SEAL/HOLD/error).

REPAIRED 2026-09-18 (afpass-W3). Three defects were found in this file by the
A-FORGE pass and are fixed here:

  1. ARITY — every `check_governance` / `_call_arifOS_judge` call site unpacked a
     2-tuple while the implementation returns a 3-tuple. Result: 13 of 16 tests
     raised `ValueError: too many values to unpack` and the suite was RED, so it
     gated nothing. The READONLY cross-vocabulary leak survived precisely because
     the test covering that branch could not execute.
  2. CONTRACT — the READONLY branch asserted `verdict == "READONLY"`, which was
     true, but nothing asserted what `floor_verdict["effective_verdict"]` held.
     Added: `test_readonly_branch_does_not_leak_risktier_into_verdict`.
  3. UNBOUNDED GAP — see `test_floor_mapping_gap_is_bounded` at the foot of the
     file. `capital_polix` has no CANONICAL_FLOORS entry; the original assertion
     failed on it with no owner and no size. The gap is now enumerated and fixed
     in size, so it screams if it widens instead of failing anonymously.

Evidence for the leak: /root/forge_work/2026-09-18/SKILL-DRIFT-REPORT-2026-09-18.md (D-4).
"""

import json
from unittest.mock import MagicMock, patch

import internal.organ_governance as og
from wealth_mcp import CAPITAL_TOOL_NAMES
from wealth_mcp.governance_metadata import CANONICAL_FLOORS, get_tool_floors

# The closed constitutional verdict set (arifosmcp/runtime/verdict.py).
CANONICAL_VERDICTS = {"OBSERVE_ONLY", "SEAL", "SABAR", "VOID", "HOLD", "888_HOLD"}


# ── WEALTH_RISK_TIERS dict ────────────────────────────────────────────────


def test_risk_tier_readonly_tools():
    readonly_tools = [
        "capital_primitive",
        "capital_health",
        "capital_market",
        "capital_registry",
        "wealth_flow_liquidity",
        "wealth_health_check",
        "wealth_system_registry_status",
    ]
    for tool_name in readonly_tools:
        assert og.WEALTH_RISK_TIERS[tool_name] == "readonly"


def test_risk_tier_c2_tools():
    c2_tools = ["capital_ledger", "wealth_ledger_write", "wealth_ledger_snapshot"]
    for tool_name in c2_tools:
        assert og.WEALTH_RISK_TIERS[tool_name] == "c2"


def test_risk_tier_c1_tools():
    c1_tools = [
        "capital_diagnose",
        # "capital_wisdom" DELETED 2026-08-06 — M0 audit
        "capital_entropy",
        "wealth_institutional_stress_index",
        "wealth_cascade_model",
        "wealth_governance_capacity",
        "wealth_external_exploitation_detect",
        "wealth_synthesize",
        "wealth_governance_verdict",
        "wealth_boundary_governance",
    ]
    for tool_name in c1_tools:
        assert og.WEALTH_RISK_TIERS[tool_name] == "c1"


# ── check_governance: READONLY branch ─────────────────────────────────────


def test_check_governance_readonly():
    """READONLY tool returns READONLY tier immediately, no judge call."""
    verdict, err, floor_verdict = og.check_governance("wealth_health_check", {})
    assert verdict == "READONLY"
    assert err is None
    assert isinstance(floor_verdict, dict)


def test_capital_ledger_query_is_readonly():
    with patch.object(og, "_call_arifOS_judge") as judge:
        verdict, err, floor_verdict = og.check_governance(
            "capital_ledger", {"mode": "query"}
        )
    assert verdict == "READONLY"
    assert err is None
    judge.assert_not_called()


def test_readonly_branch_does_not_leak_risktier_into_verdict():
    """REGRESSION (afpass-W3, 2026-09-18).

    The READONLY branch used to emit floor_verdict["effective_verdict"] ==
    "READONLY" — a RiskTier smuggled into the constitutional-verdict field
    (96 such emissions in /root/arifOS/VAULT999/wealth/receipts.jsonl).

    A readonly tool is not adjudicated at all, so it must either carry a member
    of CANONICAL_VERDICTS or explicitly declare that no verdict was issued.
    """
    for tool_name in ("capital_primitive", "capital_health", "capital_market"):
        tier, err, floor_verdict = og.check_governance(tool_name, {})
        ev = floor_verdict.get("effective_verdict")
        assert tier == "READONLY"
        assert err is None
        # no risk tier in the verdict slot, ever
        assert ev != "READONLY"
        assert ev != "readonly"
        # and if a verdict is present at all, it is constitutional
        if ev is not None:
            assert ev in CANONICAL_VERDICTS
        else:
            assert floor_verdict.get("verdict_issued") is False
            assert floor_verdict.get("verdict_source") == (
                "NOT_ADJUDICATED_READONLY_TIER"
            )


def test_no_floor_verdict_ever_carries_a_risk_tier():
    """The vocabulary boundary holds for every branch the module can take."""
    risk_tiers = {"READONLY", "readonly", "C1", "c1", "C2", "c2", "IRREVERSIBLE"}
    with _mock_httpx("SEAL"):
        for tool_name in ("capital_primitive", "wealth_synthesize"):
            _, _, floor_verdict = og.check_governance(tool_name, {})
            assert floor_verdict.get("effective_verdict") not in risk_tiers


# ── _call_arifOS_judge ─────────────────────────────────────────────────────


def _mock_httpx(verdict_text: str, status_code: int = 200):
    """Helper to mock httpx.Client.post returning a given verdict."""
    content_text = json.dumps({"verdict": verdict_text})
    resp_data = {"result": {"content": [{"text": content_text}]}}
    mock_response = MagicMock()
    mock_response.json.return_value = resp_data
    mock_response.status_code = status_code

    mock_client = MagicMock()
    mock_client.__enter__ = lambda s: mock_client
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = mock_response

    return patch("httpx.Client", return_value=mock_client)


def test_call_arifOS_judge_seal():
    with _mock_httpx("SEAL"):
        verdict, err, _vdata = og._call_arifOS_judge("wealth_synthesize", {}, "test-actor")
    assert verdict == "SEAL"
    assert err is None


def test_call_arifOS_judge_hold():
    with _mock_httpx("HOLD"):
        verdict, err, _vdata = og._call_arifOS_judge("wealth_synthesize", {}, "test-actor")
    assert verdict == "HOLD"
    assert err is None


def test_call_arifOS_judge_rpc_error():
    """RPC-level error in response → HOLD."""
    resp_data = {"error": {"message": "Tool not found"}}
    mock_response = MagicMock()
    mock_response.json.return_value = resp_data
    mock_client = MagicMock()
    mock_client.__enter__ = lambda s: mock_client
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = mock_response

    with patch("httpx.Client", return_value=mock_client):
        verdict, err, _vdata = og._call_arifOS_judge("wealth_synthesize", {}, "test-actor")

    assert verdict == "HOLD"
    assert err is not None
    assert "error" in err


def test_call_arifOS_judge_network_exception():
    """Network exception → HOLD with error."""
    mock_client = MagicMock()
    mock_client.__enter__ = lambda s: mock_client
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = Exception("Connection refused")

    with patch("httpx.Client", return_value=mock_client):
        verdict, err, _vdata = og._call_arifOS_judge("wealth_ledger_write", {}, "test-actor")

    assert verdict == "HOLD"
    assert err is not None


# ── check_governance: C1 branch ───────────────────────────────────────────


def test_check_governance_c1_always_proceeds():
    """C1 tools proceed regardless of arifOS verdict."""
    with _mock_httpx("HOLD"):
        verdict, err, _fv = og.check_governance("wealth_synthesize", {"key": "val"}, "test")
    assert verdict == "HOLD"
    assert err is None  # C1 never blocks, err is always None


def test_check_governance_c1_seal():
    with _mock_httpx("SEAL"):
        _verdict, err, _fv = og.check_governance("wealth_governance_verdict", {})
    assert err is None


# ── check_governance: C2 branch ───────────────────────────────────────────


def test_check_governance_c2_seal_allows():
    with _mock_httpx("SEAL"):
        verdict, err, _fv = og.check_governance(
            "capital_ledger", {"mode": "write", "amount": 1000}
        )
    assert verdict == "SEAL"
    assert err is None


def test_check_governance_c2_hold_blocks():
    """The live capital_ledger write path requires an arifOS SEAL."""
    with _mock_httpx("HOLD"):
        verdict, err, _fv = og.check_governance(
            "capital_ledger", {"mode": "write", "amount": 999}
        )
    assert verdict == "HOLD"
    assert err is not None
    assert err["error"]["code"] == -32001
    assert "SEAL" in err["error"]["message"]
    assert err["error"]["data"]["guard"] == "ORGAN_GOVERNANCE"


def test_check_governance_c2_void_blocks():
    with _mock_httpx("VOID"):
        verdict, err, _fv = og.check_governance("wealth_ledger_snapshot", {})
    assert verdict == "VOID"
    assert err is not None


# ── Unknown tool → defaults to C1 (advisory, non-blocking) ───────────────


def test_check_governance_unknown_tool():
    with _mock_httpx("SEAL"):
        _verdict, err, _fv = og.check_governance("unknown_future_tool", {})
    assert err is None  # Unknown tools treated as C1 — proceed


# ── Floor mapping coverage: bounded gap, witnessed ───────────────────────


# Tools registered in CAPITAL_TOOL_NAMES that carry NO CANONICAL_FLOORS entry.
# Sourced 2026-09-18 by diffing the two registries; NOT hand-maintained prose.
#
# This set is a DEFECT, not a design. It is bounded here so the suite proves the
# size of the hole rather than failing anonymously on whichever tool sorts first.
# An owner must decide, per tool, whether it needs a floor mapping or does not
# belong in CAPITAL_TOOL_NAMES. Do not add to this set without a ratified reason:
# a growing set means floor coverage is silently shrinking.
KNOWN_UNMAPPED_TOOLS = {"capital_civx", "capital_polix"}


def test_floor_mapping_gap_is_bounded():
    """Every registered tool is floor-mapped EXCEPT the known, enumerated gap."""
    unmapped = {t for t in CAPITAL_TOOL_NAMES if t not in CANONICAL_FLOORS}
    assert unmapped == KNOWN_UNMAPPED_TOOLS, (
        f"floor-mapping gap changed: now {sorted(unmapped)} "
        f"(known {sorted(KNOWN_UNMAPPED_TOOLS)}) — floor coverage moved"
    )


def test_floor_mappings_are_non_empty_for_mapped_tools():
    for tool_name in CAPITAL_TOOL_NAMES:
        if tool_name in KNOWN_UNMAPPED_TOOLS:
            continue
        assert CANONICAL_FLOORS[tool_name], f"{tool_name} has an empty floor scope"


def test_capital_ledger_declares_f13():
    assert "F13" in get_tool_floors("capital_ledger")
