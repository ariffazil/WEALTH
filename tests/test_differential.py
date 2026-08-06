"""
WEALTH Differential Content-Sensitivity Test.
DITEMPA BUKAN DIBERI — Forged 2026-08-06.

For each tool-mode: two payloads differing in SUBSTANCE must not return
identical `result` fields. Content-blind tools (e.g., power_consequence_map
dropping structured input→identical output) are caught here.

This is the FIRST real receipt of the WEALTH backtest workstream.
Red tests = content-blind tools. Green tests = content-sensitive tools.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from wealth_mcp.server import create_mcp_server


# ── Helpers ────────────────────────────────────────────────────────────────


def _tool_fn(name: str):
    """Extract raw tool function from MCP server (bypasses governance wrapper)."""
    mcp = create_mcp_server()
    return next(
        component.fn
        for key, component in mcp._local_provider._components.items()
        if key.startswith(f"tool:{name}@")
    )


# ── W-001 normalize() with VOLATILE_KEYS (per spec 2026-08-06) ────────────

VOLATILE_KEYS: frozenset[str] = frozenset(
    {
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
        "cost_id",
        "receipt_id",
        "analyzed_at",
        "_governance_advisory",
        "_w0_evidence_gate",
        "_id",
        "uuid",
    }
)


def normalize(obj: dict | list | Any) -> dict | list | Any:
    """Strip volatile keys recursively.

    Without this, every test passes on timestamp drift alone and the
    suite is decorative.
    """
    if isinstance(obj, dict):
        return {
            k: normalize(v)
            for k, v in obj.items()
            if k not in VOLATILE_KEYS and not k.startswith("_")
        }
    if isinstance(obj, list):
        return [normalize(v) for v in obj]
    return obj


def _result_hash(envelope: dict) -> str:
    """Stable hash of the result field after recursive volatile-key stripping."""
    return json.dumps(
        normalize(envelope.get("result", {})), sort_keys=True, default=str
    )


# ── capital_primitive ──────────────────────────────────────────────────────


class TestPrimitiveDifferential:
    """capital_primitive: pure math — must be content-sensitive."""

    @pytest.mark.asyncio
    async def test_npv_different_cashflows(self):
        fn = _tool_fn("capital_primitive")
        r1 = await fn(mode="npv", cash_flows=[-1000, 300, 400, 500], discount_rate=0.1)
        r2 = await fn(mode="npv", cash_flows=[-1000, 600, 700, 800], discount_rate=0.1)
        assert _result_hash(r1) != _result_hash(r2), (
            "npv must differ for different cash flows"
        )

    @pytest.mark.asyncio
    async def test_emv_different_outcomes(self):
        fn = _tool_fn("capital_primitive")
        r1 = await fn(mode="emv", outcomes=[100, 50, 0], probabilities=[0.3, 0.5, 0.2])
        r2 = await fn(mode="emv", outcomes=[200, 100, 0], probabilities=[0.3, 0.5, 0.2])
        assert _result_hash(r1) != _result_hash(r2), (
            "emv must differ for different outcomes"
        )

    @pytest.mark.asyncio
    async def test_mc_different_growth(self):
        fn = _tool_fn("capital_primitive")
        r1 = await fn(
            mode="mc",
            initial_value=100,
            growth_rate=0.05,
            volatility=0.2,
            periods=5,
            simulations=100,
            seed=42,
        )
        r2 = await fn(
            mode="mc",
            initial_value=100,
            growth_rate=0.15,
            volatility=0.2,
            periods=5,
            simulations=100,
            seed=42,
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "mc must differ for different growth rates"
        )

    @pytest.mark.asyncio
    async def test_kelly_different_odds(self):
        fn = _tool_fn("capital_primitive")
        r1 = await fn(mode="kelly", win_prob=0.6, odds=2.0)
        r2 = await fn(mode="kelly", win_prob=0.4, odds=3.0)
        assert _result_hash(r1) != _result_hash(r2), (
            "kelly must differ for different inputs"
        )


# ── capital_health ─────────────────────────────────────────────────────────


class TestHealthDifferential:
    """capital_health: deductive — must be content-sensitive."""

    @pytest.mark.asyncio
    async def test_conservation_different_assets(self):
        fn = _tool_fn("capital_health")
        r1 = await fn(
            mode="conservation",
            assets=[
                {"name": "cash", "value": 10000},
                {"name": "house", "value": 500000},
            ],
            liabilities=[{"name": "mortgage", "value": 300000}],
        )
        r2 = await fn(
            mode="conservation",
            assets=[
                {"name": "cash", "value": 50000},
                {"name": "house", "value": 800000},
            ],
            liabilities=[{"name": "mortgage", "value": 100000}],
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "conservation must differ for different assets"
        )

    @pytest.mark.asyncio
    async def test_flow_different_income(self):
        fn = _tool_fn("capital_health")
        r1 = await fn(
            mode="flow",
            income=[{"name": "salary", "amount": 5000}],
            expenses=[{"name": "rent", "amount": 2000}],
        )
        r2 = await fn(
            mode="flow",
            income=[{"name": "salary", "amount": 12000}],
            expenses=[{"name": "rent", "amount": 2000}],
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "flow must differ for different incomes"
        )

    @pytest.mark.asyncio
    async def test_runway_different_liquid(self):
        fn = _tool_fn("capital_health")
        r1 = await fn(mode="runway", liquid_assets=10000, monthly_burn=1000)
        r2 = await fn(mode="runway", liquid_assets=50000, monthly_burn=1000)
        assert _result_hash(r1) != _result_hash(r2), (
            "runway must differ for different liquid assets"
        )

    @pytest.mark.asyncio
    async def test_asymmetry_different_scenarios(self):
        fn = _tool_fn("capital_health")
        r1 = await fn(
            mode="asymmetry",
            upside_scenarios=[100, 200, 300],
            downside_scenarios=[-50, -100, -150],
        )
        r2 = await fn(
            mode="asymmetry",
            upside_scenarios=[500, 600, 700],
            downside_scenarios=[-50, -100, -150],
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "asymmetry must differ for different scenarios"
        )


# ── capital_diagnose ───────────────────────────────────────────────────────


class TestDiagnoseDifferential:
    """capital_diagnose: abductive — MUST be content-sensitive.
    This is the tool that failed the Enron backtest."""

    @pytest.mark.asyncio
    async def test_stress_index_different_signals(self):
        fn = _tool_fn("capital_diagnose")
        r1 = await fn(
            mode="stress_index",
            payload={
                "org_name": "Enron",
                "financial_signals": {
                    "debt_to_equity": 0.9,
                    "off_balance_sheet": "extensive",
                },
                "governance_signals": {"board_independence": "low"},
            },
        )
        r2 = await fn(
            mode="stress_index",
            payload={
                "org_name": "Berkshire Hathaway",
                "financial_signals": {
                    "debt_to_equity": 0.2,
                    "off_balance_sheet": "none",
                },
                "governance_signals": {"board_independence": "high"},
            },
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "stress_index MUST differ for Enron vs Berkshire. "
            "Identical results = content-blind = Defect A (backtest)."
        )

    @pytest.mark.asyncio
    async def test_governance_capacity_different_boards(self):
        fn = _tool_fn("capital_diagnose")
        r1 = await fn(
            mode="governance_capacity",
            payload={
                "board_members": [
                    {"name": "A", "type": "executive", "appointed_date": "2018-01-01"},
                    {
                        "name": "B",
                        "type": "independent",
                        "appointed_date": "2019-06-01",
                    },
                    {"name": "C", "type": "executive", "appointed_date": "2020-03-01"},
                ],
                "committees": [{"name": "audit"}],
                "stress_level": 0.3,
            },
        )
        r2 = await fn(
            mode="governance_capacity",
            payload={
                "board_members": [
                    {"name": "A", "type": "executive", "appointed_date": "2018-01-01"},
                    {
                        "name": "B",
                        "type": "independent",
                        "appointed_date": "2019-06-01",
                    },
                    {
                        "name": "C",
                        "type": "independent",
                        "appointed_date": "2020-03-01",
                    },
                    {
                        "name": "D",
                        "type": "independent",
                        "appointed_date": "2021-01-01",
                    },
                    {
                        "name": "E",
                        "type": "independent",
                        "appointed_date": "2022-01-01",
                    },
                    {"name": "F", "type": "executive", "appointed_date": "2019-01-01"},
                    {
                        "name": "G",
                        "type": "independent",
                        "appointed_date": "2023-01-01",
                    },
                ],
                "committees": [{"name": "audit"}, {"name": "risk"}, {"name": "comp"}],
                "stress_level": 0.8,
            },
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "governance_capacity must differ for different boards"
        )

    @pytest.mark.asyncio
    async def test_cascade_model_different_timelines(self):
        fn = _tool_fn("capital_diagnose")
        r1 = await fn(
            mode="cascade_model",
            payload={
                "timeline": [{"event": "profit warning", "month": 1}],
                "intervention_scenario": {"action": "none", "timing": "never"},
            },
        )
        r2 = await fn(
            mode="cascade_model",
            payload={
                "timeline": [
                    {"event": "profit warning", "month": 1},
                    {"event": "CEO resigns", "month": 3},
                    {"event": "default", "month": 6},
                ],
                "intervention_scenario": {
                    "action": "bailout",
                    "timing": "month_5",
                    "amount_bn": 50,
                },
            },
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "cascade_model must differ for different timelines"
        )

    @pytest.mark.asyncio
    async def test_exploitation_detect_different_actions(self):
        fn = _tool_fn("capital_diagnose")
        r1 = await fn(
            mode="exploitation_detect",
            payload={
                "counterparty_actions": [
                    {"action": "standard trade", "claimed_rationale": "hedging"},
                ],
                "institution_state": {"oversight": "active"},
            },
        )
        r2 = await fn(
            mode="exploitation_detect",
            payload={
                "counterparty_actions": [
                    {"action": "wash trade", "claimed_rationale": "market making"},
                    {"action": "round-trip", "claimed_rationale": "revenue growth"},
                    {"action": "mark-to-model", "claimed_rationale": "illiquid assets"},
                ],
                "institution_state": {"oversight": "captured"},
            },
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "exploitation_detect must differ for different actions"
        )

    @pytest.mark.asyncio
    async def test_beautiful_mouse_different_text(self):
        fn = _tool_fn("capital_diagnose")
        r1 = await fn(
            mode="beautiful_mouse",
            payload={"text": "Quarterly earnings exceeded expectations."},
        )
        r2 = await fn(
            mode="beautiful_mouse",
            payload={"text": "We cannot explain the discrepancy. Trust us."},
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "beautiful_mouse must differ for different text"
        )


# ── capital_entropy ────────────────────────────────────────────────────────


class TestEntropyDifferential:
    """capital_entropy: THE content-blind suspect from the backtest.
    power_consequence_map returned identical sub-scores for different actors."""

    @pytest.mark.asyncio
    async def test_power_consequence_map_different_actors(self):
        """THE DIFFERENTIAL TEST — this is the one the backtest proved broken."""
        fn = _tool_fn("capital_entropy")
        r1 = await fn(
            mode="power_consequence_map",
            decision_makers=[
                {"name": "Fastow", "role": "CFO", "benefits": "direct"},
                {"name": "Skilling", "role": "CEO", "benefits": "direct"},
            ],
            beneficiaries=[{"name": "Enron shareholders", "benefit": "paper gains"}],
            cost_bearers=[{"name": "Employees", "loss": "pension collapse"}],
        )
        r2 = await fn(
            mode="power_consequence_map",
            decision_makers=[
                {"name": "Buffett", "role": "CEO", "benefits": "salary_only"},
                {"name": "Munger", "role": "Vice Chair", "benefits": "salary_only"},
            ],
            beneficiaries=[
                {"name": "Berkshire shareholders", "benefit": "long_term_value"}
            ],
            cost_bearers=[{"name": "None identified", "loss": "none"}],
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "power_consequence_map MUST differ for Enron-style vs Berkshire-style actors. "
            "IDENTICAL = CONFIRMED CONTENT-BLIND = backtest Defect C."
        )

    @pytest.mark.asyncio
    async def test_metric_purpose_audit_different_purposes(self):
        fn = _tool_fn("capital_entropy")
        r1 = await fn(
            mode="metric_purpose_audit",
            declared_purpose="Maximize shareholder value through transparent reporting",
            current_kpis=[{"name": "EPS", "target": "grow 15%"}],
            actual_behaviors=["quarterly guidance", "transparent disclosures"],
        )
        r2 = await fn(
            mode="metric_purpose_audit",
            declared_purpose="Optimize executive bonus pool through aggressive accounting",
            current_kpis=[
                {"name": "mark-to-market revenue", "target": "unlimited growth"}
            ],
            actual_behaviors=[
                "off-balance-sheet vehicles",
                "related-party transactions",
            ],
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "metric_purpose_audit must differ for different purposes"
        )

    @pytest.mark.asyncio
    async def test_trust_capital_decay_different_events(self):
        fn = _tool_fn("capital_entropy")
        r1 = await fn(
            mode="trust_capital_decay",
            trust_events=[{"event": "earnings_restatement", "severity": 0.8}],
            current_trust_balance=0.9,
        )
        r2 = await fn(
            mode="trust_capital_decay",
            trust_events=[
                {"event": "earnings_restatement", "severity": 0.8},
                {"event": "CEO_indictment", "severity": 0.95},
                {"event": "auditor_disqualified", "severity": 0.9},
            ],
            current_trust_balance=0.3,
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "trust_capital_decay must differ for different events"
        )


# ── capital_ledger ─────────────────────────────────────────────────────────


class TestLedgerDifferential:
    """capital_ledger: query mode should be content-sensitive."""

    @pytest.mark.asyncio
    async def test_query_different_terms(self):
        fn = _tool_fn("capital_ledger")
        r1 = await fn(mode="query", query="gold", limit=5)
        r2 = await fn(mode="query", query="oil_and_gas_royalty", limit=5)
        assert _result_hash(r1) != _result_hash(r2), (
            "query must differ for different search terms"
        )


# ── wealth_judge_handoff ───────────────────────────────────────────────────


class TestHandoffDifferential:
    """wealth_judge_handoff: different intents must produce different results."""

    @pytest.mark.asyncio
    async def test_prepare_different_intents(self):
        fn = _tool_fn("wealth_judge_handoff")
        r1 = await fn(mode="prepare", intent="Audit Enron FY1999 financial statements")
        r2 = await fn(
            mode="prepare",
            intent="Audit Berkshire Hathaway FY2024 financial statements",
        )
        assert _result_hash(r1) != _result_hash(r2), (
            "handoff prepare must differ for different intents"
        )


# ── capital_registry ───────────────────────────────────────────────────────
# EXEMPT: registry is inherently content-invariant (no payload to differentiate).
# Modes: status, schema, domains, health — all return organ-level metadata.
# Differential test not applicable; tested via test_registry_truth.py.


# ── capital_market ─────────────────────────────────────────────────────────
# EXEMPT from differential test: depends on live network data (FX, commodities).
# A differential test on live data would be unstable (market moves between calls).
# Content-sensitivity for capital_market is verified via:
#   1. The mode-dispatch logic (different modes → different code paths)
#   2. Integration tests (separate suite)
