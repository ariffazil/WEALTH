"""
Tests for internal/organ_governance.py
Covers: WEALTH_RISK_TIERS lookups, check_governance all branches,
_call_arifOS_judge network paths (SEAL/HOLD/error).
"""
import pytest
import json
from unittest.mock import patch, MagicMock

import internal.organ_governance as og


# ── WEALTH_RISK_TIERS dict ────────────────────────────────────────────────

def test_risk_tier_readonly_tools():
    readonly_tools = [
        "wealth_mass_networth", "wealth_flow_cashflow", "wealth_flow_liquidity",
        "wealth_energy_irr", "wealth_value_npv", "wealth_time_payback",
        "wealth_probability_monte_carlo", "wealth_signal_evoi",
        "wealth_health_check", "wealth_system_registry_status",
    ]
    for t in readonly_tools:
        assert og.WEALTH_RISK_TIERS[t] == "readonly", f"{t} should be readonly"


def test_risk_tier_c2_tools():
    c2_tools = ["wealth_ledger_write", "wealth_ledger_snapshot"]
    for t in c2_tools:
        assert og.WEALTH_RISK_TIERS[t] == "c2"


def test_risk_tier_c1_tools():
    c1_tools = ["wealth_synthesize", "wealth_governance_verdict", "wealth_boundary_governance"]
    for t in c1_tools:
        assert og.WEALTH_RISK_TIERS[t] == "c1"


# ── check_governance: READONLY branch ─────────────────────────────────────

def test_check_governance_readonly():
    """READONLY tool returns READONLY verdict immediately, no judge call."""
    verdict, err = og.check_governance("wealth_mass_networth", {})
    assert verdict == "READONLY"
    assert err is None


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
        verdict, err = og.check_governance("wealth_ledger_write", {"amount": 1000})
    assert verdict == "SEAL"
    assert err is None


def test_check_governance_c2_hold_blocks():
    """C2 tool with HOLD → returns error response."""
    with _mock_httpx("HOLD"):
        verdict, err = og.check_governance("wealth_ledger_write", {"amount": 999})
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
