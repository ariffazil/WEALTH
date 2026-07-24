"""
Tests for internal/organ_governance.py
Covers: WEALTH_RISK_TIERS lookups, check_governance all branches,
_call_arifOS_judge network paths (SEAL/HOLD/error).
"""
import json
from unittest.mock import MagicMock, patch

import internal.organ_governance as og
from wealth_mcp import CAPITAL_TOOL_NAMES
from wealth_mcp.governance_metadata import CANONICAL_FLOORS, get_tool_floors


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
        "capital_wisdom",
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


def test_all_canonical_tools_have_explicit_floor_mappings():
    for tool_name in CAPITAL_TOOL_NAMES:
        assert tool_name in CANONICAL_FLOORS

    assert "F13" in get_tool_floors("capital_ledger")


# ── check_governance: READONLY branch ─────────────────────────────────────

def test_check_governance_readonly():
    """READONLY tool returns READONLY verdict immediately, no judge call."""
    verdict, err = og.check_governance("wealth_health_check", {})
    assert verdict == "READONLY"
    assert err is None


def test_capital_ledger_query_is_readonly():
    with patch.object(og, "_call_arifOS_judge") as judge:
        verdict, err = og.check_governance("capital_ledger", {"mode": "query"})
    assert verdict == "READONLY"
    assert err is None
    judge.assert_not_called()


# ── _call_arifOS_judge ─────────────────────────────────────────────────────

def _mock_httpx(verdict_text: str, status_code: int = 200):
    """Helper to mock httpx.Client.post returning a given verdict."""
    content_text = json.dumps({"verdict": verdict_text})
    resp_data = {
        "result": {
            "content": [{"text": content_text}]
        }
    }
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
        verdict, err = og._call_arifOS_judge("wealth_synthesize", {}, "test-actor")
    assert verdict == "SEAL"
    assert err is None


def test_call_arifOS_judge_hold():
    with _mock_httpx("HOLD"):
        verdict, err = og._call_arifOS_judge("wealth_synthesize", {}, "test-actor")
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
        verdict, err = og._call_arifOS_judge("wealth_synthesize", {}, "test-actor")

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
        verdict, err = og._call_arifOS_judge("wealth_ledger_write", {}, "test-actor")

    assert verdict == "HOLD"
    assert err is not None


# ── check_governance: C1 branch ───────────────────────────────────────────

def test_check_governance_c1_always_proceeds():
    """C1 tools proceed regardless of arifOS verdict."""
    with _mock_httpx("HOLD"):
        verdict, err = og.check_governance("wealth_synthesize", {"key": "val"}, "test")
    assert verdict == "HOLD"
    assert err is None  # C1 never blocks, err is always None


def test_check_governance_c1_seal():
    with _mock_httpx("SEAL"):
        verdict, err = og.check_governance("wealth_governance_verdict", {})
    assert err is None


# ── check_governance: C2 branch ───────────────────────────────────────────

def test_check_governance_c2_seal_allows():
    with _mock_httpx("SEAL"):
        verdict, err = og.check_governance(
            "capital_ledger", {"mode": "write", "amount": 1000}
        )
    assert verdict == "SEAL"
    assert err is None


def test_check_governance_c2_hold_blocks():
    """The live capital_ledger write path requires an arifOS SEAL."""
    with _mock_httpx("HOLD"):
        verdict, err = og.check_governance(
            "capital_ledger", {"mode": "write", "amount": 999}
        )
    assert verdict == "HOLD"
    assert err is not None
    assert err["error"]["code"] == -32001
    assert "SEAL" in err["error"]["message"]
    assert err["error"]["data"]["guard"] == "ORGAN_GOVERNANCE"


def test_check_governance_c2_void_blocks():
    with _mock_httpx("VOID"):
        verdict, err = og.check_governance("wealth_ledger_snapshot", {})
    assert verdict == "VOID"
    assert err is not None


# ── Unknown tool → defaults to C1 (advisory, non-blocking) ───────────────

def test_check_governance_unknown_tool():
    with _mock_httpx("SEAL"):
        verdict, err = og.check_governance("unknown_future_tool", {})
    assert err is None  # Unknown tools treated as C1 — proceed
