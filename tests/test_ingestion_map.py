"""
W-002 — WEALTH Ingestion Map.
DITEMPA BUKAN DIBERI — Forged 2026-08-06.

For each declared input field on every tool: call with field present vs absent.
Identical normalized output → field is DEAD (not consumed).

Uses normalize() from test_differential.py to strip volatile keys.
"""

from __future__ import annotations

import json
import pytest

from wealth_mcp.server import create_mcp_server

# Reuse normalize from W-001
import sys

sys.path.insert(0, "/root/WEALTH/tests")
from test_differential import normalize, _tool_fn


def _ingestion_test(
    tool: str, mode: str, field_to_drop: str, full_args: dict, partial_args: dict
):
    """Core ingestion test: identical normalized output → field is dead."""
    fn = _tool_fn(tool)
    import asyncio

    loop = asyncio.get_event_loop()

    full_result = loop.run_until_complete(fn(mode=mode, **full_args))
    partial_result = loop.run_until_complete(fn(mode=mode, **partial_args))

    full_normalized = normalize(full_result.get("result", {}))
    partial_normalized = normalize(partial_result.get("result", {}))

    full_str = json.dumps(full_normalized, sort_keys=True, default=str)
    partial_str = json.dumps(partial_normalized, sort_keys=True, default=str)

    if full_str == partial_str:
        return "dead", full_str
    return "live", None


# ═══════════════════════════════════════════════════════════════════════════
# capital_health — KNOWN DEAD: assets, liabilities, income, expenses
# ═══════════════════════════════════════════════════════════════════════════


class TestHealthIngestion:
    @pytest.mark.asyncio
    async def test_conservation_assets_live(self):
        """assets must affect conservation output."""
        fn = _tool_fn("capital_health")
        r1 = await fn(
            mode="conservation",
            assets=[{"name": "cash", "amount": 10000}],
            liabilities=[{"name": "debt", "amount": 5000}],
        )
        r2 = await fn(
            mode="conservation",
            assets=[{"name": "cash", "amount": 50000}],
            liabilities=[{"name": "debt", "amount": 5000}],
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, "DEAD: assets do not affect conservation output"

    @pytest.mark.asyncio
    async def test_conservation_liabilities_live(self):
        fn = _tool_fn("capital_health")
        r1 = await fn(
            mode="conservation",
            assets=[{"name": "cash", "amount": 10000}],
            liabilities=[{"name": "debt", "amount": 5000}],
        )
        r2 = await fn(
            mode="conservation",
            assets=[{"name": "cash", "amount": 10000}],
            liabilities=[{"name": "debt", "amount": 50000}],
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, "DEAD: liabilities do not affect conservation output"

    @pytest.mark.asyncio
    async def test_flow_income_live(self):
        fn = _tool_fn("capital_health")
        r1 = await fn(
            mode="flow",
            income=[{"name": "salary", "amount": 5000}],
            expenses=[{"name": "rent", "amount": 2000}],
        )
        r2 = await fn(
            mode="flow",
            income=[{"name": "salary", "amount": 15000}],
            expenses=[{"name": "rent", "amount": 2000}],
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, "DEAD: income does not affect flow output"

    @pytest.mark.asyncio
    async def test_flow_expenses_live(self):
        fn = _tool_fn("capital_health")
        r1 = await fn(
            mode="flow",
            income=[{"name": "salary", "amount": 5000}],
            expenses=[{"name": "rent", "amount": 2000}],
        )
        r2 = await fn(
            mode="flow",
            income=[{"name": "salary", "amount": 5000}],
            expenses=[{"name": "rent", "amount": 8000}],
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, "DEAD: expenses do not affect flow output"

    @pytest.mark.asyncio
    async def test_survival_submode_corporate_vs_personal(self):
        """survival_submode must route to different computation paths."""
        fn = _tool_fn("capital_health")
        r1 = await fn(
            mode="survival",
            survival_submode="corporate_runway",
            liquid_assets=100000,
            monthly_burn=10000,
        )
        r2 = await fn(
            mode="survival",
            survival_submode="personal_finance",
            liquid_assets=100000,
            monthly_burn=10000,
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, "DEAD: survival_submode does not route to different paths"


# ═══════════════════════════════════════════════════════════════════════════
# capital_entropy — power_consequence_map: suspect sub-score list-length dependency
# ═══════════════════════════════════════════════════════════════════════════


class TestEntropyIngestion:
    @pytest.mark.asyncio
    async def test_pcm_decision_makers_count_affects(self):
        """Adding a decision maker must change the power concentration score."""
        fn = _tool_fn("capital_entropy")
        r1 = await fn(
            mode="power_consequence_map",
            decision_makers=[{"name": "A", "role": "CEO", "benefits": "direct"}],
            beneficiaries=[{"name": "Shareholders", "benefit": "returns"}],
            cost_bearers=[{"name": "Employees", "loss": "layoffs"}],
        )
        r2 = await fn(
            mode="power_consequence_map",
            decision_makers=[
                {"name": "A", "role": "CEO", "benefits": "direct"},
                {"name": "B", "role": "CFO", "benefits": "direct"},
            ],
            beneficiaries=[{"name": "Shareholders", "benefit": "returns"}],
            cost_bearers=[{"name": "Employees", "loss": "layoffs"}],
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, "DEAD: decision_makers count does not affect pcm"

    @pytest.mark.asyncio
    async def test_pcm_beneficiaries_count_affects(self):
        """Adding a beneficiary must change output."""
        fn = _tool_fn("capital_entropy")
        r1 = await fn(
            mode="power_consequence_map",
            decision_makers=[{"name": "A", "role": "CEO", "benefits": "direct"}],
            beneficiaries=[{"name": "Shareholders", "benefit": "returns"}],
            cost_bearers=[{"name": "Employees", "loss": "layoffs"}],
        )
        r2 = await fn(
            mode="power_consequence_map",
            decision_makers=[{"name": "A", "role": "CEO", "benefits": "direct"}],
            beneficiaries=[
                {"name": "Shareholders", "benefit": "returns"},
                {"name": "Executives", "benefit": "bonuses"},
            ],
            cost_bearers=[{"name": "Employees", "loss": "layoffs"}],
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, "DEAD: beneficiaries count does not affect pcm"

    @pytest.mark.asyncio
    async def test_pcm_cost_bearers_count_affects(self):
        """Adding a cost bearer must change output."""
        fn = _tool_fn("capital_entropy")
        r1 = await fn(
            mode="power_consequence_map",
            decision_makers=[{"name": "A", "role": "CEO", "benefits": "direct"}],
            beneficiaries=[{"name": "Shareholders", "benefit": "returns"}],
            cost_bearers=[{"name": "Employees", "loss": "layoffs"}],
        )
        r2 = await fn(
            mode="power_consequence_map",
            decision_makers=[{"name": "A", "role": "CEO", "benefits": "direct"}],
            beneficiaries=[{"name": "Shareholders", "benefit": "returns"}],
            cost_bearers=[
                {"name": "Employees", "loss": "layoffs"},
                {"name": "Community", "loss": "pollution"},
            ],
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, "DEAD: cost_bearers count does not affect pcm"

    @pytest.mark.asyncio
    async def test_pcm_veto_holders_presence_affects(self):
        """veto_holders presence must change veto_concentration."""
        fn = _tool_fn("capital_entropy")
        r1 = await fn(
            mode="power_consequence_map",
            decision_makers=[{"name": "A", "role": "CEO", "benefits": "direct"}],
            beneficiaries=[{"name": "Shareholders", "benefit": "returns"}],
            cost_bearers=[{"name": "Employees", "loss": "layoffs"}],
        )
        r2 = await fn(
            mode="power_consequence_map",
            decision_makers=[{"name": "A", "role": "CEO", "benefits": "direct"}],
            beneficiaries=[{"name": "Shareholders", "benefit": "returns"}],
            cost_bearers=[{"name": "Employees", "loss": "layoffs"}],
            veto_holders=["Board", "Regulator"],
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, "DEAD: veto_holders does not affect pcm"


# ═══════════════════════════════════════════════════════════════════════════
# capital_diagnose — text-classifier modes: do material fields matter?
# ═══════════════════════════════════════════════════════════════════════════


class TestDiagnoseIngestion:
    @pytest.mark.asyncio
    async def test_stress_index_financial_signals_live(self):
        """stress_index recognizes only 21 specific dotted field names.
        Any field not in that vocabulary is silently dropped.
        This test uses RECOGNIZED field: financial.profit_change_pct."""
        fn = _tool_fn("capital_diagnose")
        r1 = await fn(
            mode="stress_index",
            payload={
                "org_name": "CorpA",
                "financial.profit_change_pct": 0.0,
            },
        )
        r2 = await fn(
            mode="stress_index",
            payload={
                "org_name": "CorpA",
                "financial.profit_change_pct": -75.0,
            },
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, (
            "DEAD: recognized field financial.profit_change_pct does not affect stress_index"
        )

    @pytest.mark.asyncio
    async def test_collapse_signature_text_affects(self):
        """Different scenario text must produce different collapse output.
        FAILING HERE = the tool is a text classifier that sees nothing."""
        fn = _tool_fn("capital_diagnose")
        r1 = await fn(
            mode="collapse_signature",
            payload={
                "scenario": "Stable company with transparent reporting, independent board, no related-party transactions."
            },
        )
        r2 = await fn(
            mode="collapse_signature",
            payload={
                "scenario": "Company with off-balance-sheet vehicles, related-party transactions, mark-to-market accounting, and flat cash flow despite 50% revenue growth."
            },
        )
        n1 = json.dumps(normalize(r1.get("result", {})), sort_keys=True, default=str)
        n2 = json.dumps(normalize(r2.get("result", {})), sort_keys=True, default=str)
        assert n1 != n2, "DEAD: collapse_signature text does not differentiate"


# ═══════════════════════════════════════════════════════════════════════════
# capital_health — tool_name misreporting bug
# ═══════════════════════════════════════════════════════════════════════════


class TestToolNameIntegrity:
    @pytest.mark.asyncio
    async def test_capital_health_reports_correct_tool_name(self):
        """capital_health must report tool_name='capital_health', not 'capital_market'."""
        fn = _tool_fn("capital_health")
        r = await fn(
            mode="conservation",
            assets=[{"name": "cash", "amount": 1000}],
            liabilities=[{"name": "debt", "amount": 500}],
        )
        assert r.get("tool_name") == "capital_health", (
            f"TOOL_NAME_MISMATCH: reported {r.get('tool_name')}"
        )


class TestCapitalMarketToolName:
    @pytest.mark.asyncio
    async def test_capital_market_reports_correct_tool_name(self):
        """capital_market must report tool_name='capital_market'."""
        fn = _tool_fn("capital_market")
        r = await fn(mode="indicator", country="MYS")
        assert r.get("tool_name") == "capital_market", (
            f"TOOL_NAME_MISMATCH: reported {r.get('tool_name')}"
        )
