"""P0 institutional stress_index — anti silent-drop + type safety (#34/#35)."""

from __future__ import annotations

from wealth_core.institutional.stress_index import compute_stress_index


def test_empty_signals_warn_and_low_confidence():
    r = compute_stress_index("TEST_ORG")
    assert r["stress_index"] == 0.0
    # P0 #36: empty signals → INSUFFICIENT_DATA, not GREEN
    assert r["risk_level"] == "INSUFFICIENT_DATA"
    assert r["fields_missing"]
    assert any("SILENT_DEFAULT_RISK" in w for w in r["warnings"])
    assert r["confidence"] < 0.2


def test_key_personnel_string_does_not_crash():
    r = compute_stress_index(
        "TEST_ORG",
        financial_signals={"profit_change_pct": -40},
        governance_signals={"board_size": 7, "board_resignations_12m": 2},
        workforce_signals={"key_personnel_departures": "CFO, CTO, GC"},
        legal_signals={},
        exploitation_signals={},
    )
    assert r["component_scores"]["workforce"] > 0
    assert "workforce.key_personnel_departures" in r["fields_present"]


def test_key_personnel_list_and_int():
    r1 = compute_stress_index(
        "A",
        workforce_signals={"key_personnel_departures": ["CFO", "CTO"]},
        financial_signals={},
        governance_signals={},
        legal_signals={},
        exploitation_signals={},
    )
    r2 = compute_stress_index(
        "B",
        workforce_signals={"key_personnel_departures": 2},
        financial_signals={},
        governance_signals={},
        legal_signals={},
        exploitation_signals={},
    )
    assert r1["component_scores"]["workforce"] == r2["component_scores"]["workforce"]


def test_full_signals_raise_stress():
    r = compute_stress_index(
        "PETRONAS_SIM",
        financial_signals={
            "profit_change_pct": -50,
            "revenue_change_pct": -30,
            "cost_cutting_announced": True,
        },
        governance_signals={
            "board_size": 5,
            "board_resignations_12m": 3,
            "company_secretaries_as_directors": True,
            "avg_tenure_years": 2.0,
        },
        workforce_signals={
            "rightsizing_pct": 15,
            "voluntary_exits_pct": 12,
            "key_personnel_departures": ["CFO", "CTO", "GC", "CHRO"],
        },
        legal_signals={
            "active_litigation_count": 5,
            "injunction_value_musd": 600,
            "regulatory_uncertainty_score": 0.8,
        },
        exploitation_signals={
            "counterparty_payment_freeze": True,
            "interpleader_filed": True,
            "competing_claims": True,
        },
    )
    assert r["stress_index"] >= 0.6
    assert r["risk_level"] in ("RED", "CRITICAL")
    assert r["confidence"] >= 0.8
