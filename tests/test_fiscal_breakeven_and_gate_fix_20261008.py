"""Tests for 2026-10-08 fixes: petroleum_direct_revenue + dividend_brent_sensitivity.

Backed by live defect receipts (VAULT999):
- 45825c37: fiscal_breakeven produced RM148b deficit (missing direct petroleum
  revenue) and nonsense breakeven USD 3505 with uncalibrated Brent sensitivity.
- 2026-10-08T16:15:55Z: wealth_synthesize VOID — semantic gate loopback deadlock
  when HERMES itself was the caller.
"""

import asyncio

import pytest

from wealth_core.risk import fiscal_breakeven_oil_price
from wealth_mcp import hermes_gate
from wealth_mcp.hermes_gate import GateTransportError, run_semantic_gate


# ── Defect 1: petroleum_direct_revenue ────────────────────────────────────


def test_deficit_without_petroleum_direct_revenue_warns():
    r = fiscal_breakeven_oil_price(
        total_government_expenditure=470.0,
        non_oil_revenue=302.0,
        petronas_dividend_base_rm=20.0,
        oil_price_assumption_usd=70.0,
    )
    # Backward compat: same deficit shape as the old buggy model...
    assert r["current_deficit_rm_b"] == 148.0
    # ...but now with an explicit NOT_MODED warning instead of silent omission
    assert any("petroleum_direct_revenue NOT_MODED" in w for w in r["warnings"])


def test_deficit_with_petroleum_direct_revenue():
    r = fiscal_breakeven_oil_price(
        total_government_expenditure=470.0,
        non_oil_revenue=302.0,
        petronas_dividend_base_rm=20.0,
        oil_price_assumption_usd=70.0,
        petroleum_direct_revenue=50.0,
    )
    # 470 - 302 - 20 - 50 = 98 (vs 148 without the term)
    assert r["current_deficit_rm_b"] == 98.0
    assert r["petroleum_direct_revenue_rm_b"] == 50.0
    # No NOT_MODED warning when the term is supplied
    assert not any("NOT_MODED" in w for w in r["warnings"])


def test_uncalibrated_brent_sensitivity_warns():
    r = fiscal_breakeven_oil_price(
        total_government_expenditure=470.0,
        non_oil_revenue=302.0,
        petronas_dividend_base_rm=20.0,
        oil_price_assumption_usd=70.0,
    )
    assert any("UNCALIBRATED" in w for w in r["warnings"])
    assert r["dividend_brent_sensitivity"] is None


def test_calibrated_brent_sensitivity_folds_into_sensitivity():
    r_uncal = fiscal_breakeven_oil_price(
        total_government_expenditure=470.0,
        non_oil_revenue=302.0,
        petronas_dividend_base_rm=20.0,
        oil_price_assumption_usd=70.0,
    )
    r_cal = fiscal_breakeven_oil_price(
        total_government_expenditure=470.0,
        non_oil_revenue=302.0,
        petronas_dividend_base_rm=20.0,
        oil_price_assumption_usd=70.0,
        dividend_brent_sensitivity=0.20,
    )
    assert r_cal["fiscal_sensitivity_rm_b_per_usd"] == round(
        r_uncal["fiscal_sensitivity_rm_b_per_usd"] + 0.20, 3
    )
    assert not any("UNCALIBRATED" in w for w in r_cal["warnings"])


def test_backward_compat_output_shape():
    """Old callers get every old field back, plus new optional fields."""
    r = fiscal_breakeven_oil_price(
        total_government_expenditure=470.0,
        non_oil_revenue=302.0,
        petronas_dividend_base_rm=20.0,
        oil_price_assumption_usd=70.0,
    )
    for key in (
        "breakeven_price_usd",
        "current_oil_price_usd",
        "fiscal_pressure",
        "current_deficit_rm_b",
        "deficit_pct_of_gdp",
        "target_deficit_pct",
        "additional_oil_revenue_needed_rm_b",
        "fiscal_sensitivity_rm_b_per_usd",
        "petronas_dividend_base_rm_b",
        "non_oil_revenue_rm_b",
        "total_govt_expenditure_rm_b",
        "epistemic_tag",
        "confidence_band",
        "breakeven_error",
        "caveat",
    ):
        assert key in r, f"missing legacy field {key}"
    assert "petroleum_direct_revenue_rm_b" in r
    assert "dividend_brent_sensitivity" in r
    assert "warnings" in r


# ── Defect 2: semantic gate self-caller exemption ─────────────────────────

_PROSE_ARGS = {"omega_invariants": {"note": "one person's spending is another's income"}}


@pytest.fixture(autouse=True)
def _reset_circuit():
    """Isolate global circuit-breaker state so these tests cannot pollute
    other test modules (learned the hard way: real loopback attempts trip
    the breaker for every test that runs after this file)."""
    saved = dict(hermes_gate._CIRCUIT)
    hermes_gate._CIRCUIT.update(
        consecutive_failures=0, opened_at=None, last_good_verdict=None
    )
    yield
    hermes_gate._CIRCUIT.clear()
    hermes_gate._CIRCUIT.update(saved)


def _mock_transport_down(monkeypatch):
    """Make any loopback attempt fail fast (no real network in tests)."""
    monkeypatch.setattr(
        hermes_gate,
        "_mcp_claim_validate",
        lambda *a, **k: (_ for _ in ()).throw(GateTransportError("mocked down")),
    )


def test_gate_self_caller_exempt_from_loopback(monkeypatch):
    """HERMES as caller must NOT loopback to itself (deadlock)."""
    calls: list = []
    real = hermes_gate._mcp_claim_validate

    def spy(*a, **k):
        calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(hermes_gate, "_mcp_claim_validate", spy)
    state = asyncio.run(
        run_semantic_gate("wealth_synthesize", dict(_PROSE_ARGS), actor_id="hermes")
    )
    assert state["status"] == "SKIPPED"
    assert state["outcome"] == "GATE_SELF_EXEMPT"
    assert state["error_code"] == ""
    assert calls == []  # provably no loopback attempt


def test_gate_hermes_variant_prefix_exempt(monkeypatch):
    _mock_transport_down(monkeypatch)
    state = asyncio.run(
        run_semantic_gate("wealth_synthesize", dict(_PROSE_ARGS), actor_id="HERMES-asi")
    )
    assert state["outcome"] == "GATE_SELF_EXEMPT"


def test_gate_other_actor_still_gated_fail_closed(monkeypatch):
    """Non-HERMES actors keep full fail-closed behavior on transport loss."""
    _mock_transport_down(monkeypatch)
    state = asyncio.run(
        run_semantic_gate("wealth_synthesize", dict(_PROSE_ARGS), actor_id="qwen-code")
    )
    assert state["outcome"] == "UNAVAILABLE"
    assert state["status"] == "BLOCKED"
    assert state["error_code"] == "SEMANTIC_GATE_UNAVAILABLE"


def test_gate_anonymous_actor_still_gated_fail_closed(monkeypatch):
    _mock_transport_down(monkeypatch)
    state = asyncio.run(run_semantic_gate("wealth_synthesize", dict(_PROSE_ARGS)))
    assert state["outcome"] == "UNAVAILABLE"
    assert state["status"] == "BLOCKED"
