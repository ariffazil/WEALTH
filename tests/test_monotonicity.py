"""
W0.3 — WEALTH Monotonicity Invariant Test Suite.
DITEMPA BUKAN DIBERI — Forged 2026-08-06.

Constitutional invariant: Less evidence must NEVER improve the verdict.

For each tool-mode:
  1. Call with full evidence → record evidence_quality
  2. Call with partial evidence (drop one field) → record evidence_quality
  3. Assert: partial evidence_quality ≤ full evidence_quality

Monotonicity ranking (strongest → weakest):
  OBSERVED (5) > MODERATE (4) > WEAK (3) > MISSING/SPECULATED (2)

A tool that returns OBSERVED with partial evidence but MODERATE with full
evidence is broken — it's more confident with less information.
"""

from __future__ import annotations

import pytest

from wealth_mcp.server import create_mcp_server


def _tool_fn(name: str):
    mcp = create_mcp_server()
    return next(
        component.fn
        for key, component in mcp._local_provider._components.items()
        if key.startswith(f"tool:{name}@")
    )


_EVIDENCE_RANK = {
    "OBSERVED": 5,
    "STRONG": 5,
    "MODERATE": 4,
    "WEAK": 3,
    "MISSING": 2,
    "SPECULATED": 2,
}


def _quality_rank(envelope: dict) -> int:
    """Extract evidence quality rank from tool response."""
    eq = str(envelope.get("evidence_quality", "MISSING")).upper()
    return _EVIDENCE_RANK.get(eq, 2)


def _monotonicity_assert(full: dict, partial: dict, dropped: str) -> None:
    """Assert that partial evidence does not produce a stronger claim."""
    full_rank = _quality_rank(full)
    partial_rank = _quality_rank(partial)
    assert partial_rank <= full_rank, (
        f"MONOTONICITY VIOLATION: dropped '{dropped}' → "
        f"evidence_quality IMPROVED from {full.get('evidence_quality')} "
        f"(rank={full_rank}) to {partial.get('evidence_quality')} "
        f"(rank={partial_rank}). "
        f"Less evidence must never produce higher confidence."
    )


# ── capital_primitive ──────────────────────────────────────────────────────


class TestPrimitiveMonotonicity:
    @pytest.mark.asyncio
    async def test_npv_partial_no_discount(self):
        fn = _tool_fn("capital_primitive")
        full = await fn(
            mode="npv", cash_flows=[-1000, 300, 400, 500], discount_rate=0.1
        )
        # Tool correctly refuses without required discount_rate — monotonic.
        with pytest.raises(ValueError, match="discount_rate"):
            await fn(mode="npv", cash_flows=[-1000, 300, 400, 500])

    @pytest.mark.asyncio
    async def test_emv_partial_no_probabilities(self):
        fn = _tool_fn("capital_primitive")
        full = await fn(
            mode="emv", outcomes=[100, 50, 0], probabilities=[0.3, 0.5, 0.2]
        )
        with pytest.raises(ValueError, match="probabilities"):
            await fn(mode="emv", outcomes=[100, 50, 0])

    @pytest.mark.asyncio
    async def test_mc_partial_no_seed(self):
        fn = _tool_fn("capital_primitive")
        full = await fn(
            mode="mc",
            initial_value=100,
            growth_rate=0.05,
            volatility=0.2,
            periods=5,
            simulations=100,
            seed=42,
        )
        partial = await fn(
            mode="mc",
            initial_value=100,
            growth_rate=0.05,
            volatility=0.2,
            periods=5,
            simulations=100,
        )
        _monotonicity_assert(full, partial, "seed")


# ── capital_health ─────────────────────────────────────────────────────────


class TestHealthMonotonicity:
    @pytest.mark.asyncio
    async def test_conservation_partial_no_liabilities(self):
        fn = _tool_fn("capital_health")
        full = await fn(
            mode="conservation",
            assets=[{"name": "cash", "amount": 10000}],
            liabilities=[{"name": "mortgage", "amount": 5000}],
        )
        partial = await fn(
            mode="conservation",
            assets=[{"name": "cash", "amount": 10000}],
        )
        _monotonicity_assert(full, partial, "liabilities")

    @pytest.mark.asyncio
    async def test_flow_partial_no_expenses(self):
        fn = _tool_fn("capital_health")
        full = await fn(
            mode="flow",
            income=[{"name": "salary", "amount": 5000}],
            expenses=[{"name": "rent", "amount": 2000}],
        )
        partial = await fn(
            mode="flow",
            income=[{"name": "salary", "amount": 5000}],
        )
        _monotonicity_assert(full, partial, "expenses")

    @pytest.mark.asyncio
    async def test_runway_partial_no_conservative(self):
        fn = _tool_fn("capital_health")
        full = await fn(
            mode="runway",
            liquid_assets=10000,
            monthly_burn=1000,
            conservative_factor=0.8,
        )
        partial = await fn(mode="runway", liquid_assets=10000, monthly_burn=1000)
        _monotonicity_assert(full, partial, "conservative_factor")


# ── capital_diagnose ───────────────────────────────────────────────────────


class TestDiagnoseMonotonicity:
    @pytest.mark.asyncio
    async def test_stress_index_partial_no_governance(self):
        fn = _tool_fn("capital_diagnose")
        full = await fn(
            mode="stress_index",
            payload={
                "org_name": "TestCorp",
                "financial_signals": {"debt_to_equity": 0.5},
                "governance_signals": {"board_independence": "medium"},
            },
        )
        partial = await fn(
            mode="stress_index",
            payload={
                "org_name": "TestCorp",
                "financial_signals": {"debt_to_equity": 0.5},
            },
        )
        _monotonicity_assert(full, partial, "governance_signals")

    @pytest.mark.asyncio
    async def test_governance_capacity_partial_no_committees(self):
        fn = _tool_fn("capital_diagnose")
        full = await fn(
            mode="governance_capacity",
            payload={
                "board_members": [
                    {"name": "A", "type": "executive", "appointed_date": "2020-01-01"},
                    {
                        "name": "B",
                        "type": "independent",
                        "appointed_date": "2021-01-01",
                    },
                ],
                "committees": [{"name": "audit"}],
                "stress_level": 0.3,
            },
        )
        partial = await fn(
            mode="governance_capacity",
            payload={
                "board_members": [
                    {"name": "A", "type": "executive", "appointed_date": "2020-01-01"},
                    {
                        "name": "B",
                        "type": "independent",
                        "appointed_date": "2021-01-01",
                    },
                ],
                "stress_level": 0.3,
            },
        )
        _monotonicity_assert(full, partial, "committees")


# ── capital_entropy ────────────────────────────────────────────────────────


class TestEntropyMonotonicity:
    @pytest.mark.asyncio
    async def test_power_consequence_map_partial_no_veto(self):
        fn = _tool_fn("capital_entropy")
        full = await fn(
            mode="power_consequence_map",
            decision_makers=[{"name": "A", "role": "CEO", "benefits": "direct"}],
            beneficiaries=[{"name": "Shareholders", "benefit": "returns"}],
            cost_bearers=[{"name": "Employees", "loss": "layoffs"}],
            veto_holders=[{"name": "Board"}, {"name": "Regulator"}],
        )
        partial = await fn(
            mode="power_consequence_map",
            decision_makers=[{"name": "A", "role": "CEO", "benefits": "direct"}],
            beneficiaries=[{"name": "Shareholders", "benefit": "returns"}],
            cost_bearers=[{"name": "Employees", "loss": "layoffs"}],
        )
        _monotonicity_assert(full, partial, "veto_holders")

    @pytest.mark.asyncio
    async def test_trust_capital_decay_partial_no_balance(self):
        fn = _tool_fn("capital_entropy")
        full = await fn(
            mode="trust_capital_decay",
            trust_events=[{"event": "restatement", "severity": 0.5}],
            current_trust_balance=0.8,
        )
        partial = await fn(
            mode="trust_capital_decay",
            trust_events=[{"event": "restatement", "severity": 0.5}],
        )
        _monotonicity_assert(full, partial, "current_trust_balance")


# ── wealth_judge_handoff ───────────────────────────────────────────────────


class TestHandoffMonotonicity:
    @pytest.mark.asyncio
    async def test_prepare_partial_no_reversibility(self):
        fn = _tool_fn("wealth_judge_handoff")
        full = await fn(
            mode="prepare",
            intent="Audit TestCorp financial statements",
            reversibility="REVERSIBLE",
            blast_radius="low",
        )
        partial = await fn(
            mode="prepare",
            intent="Audit TestCorp financial statements",
        )
        _monotonicity_assert(full, partial, "reversibility")
