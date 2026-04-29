import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from internal.invariants import get_g_score
from internal.monolith import mcp, wealth_future_value


def test_g_score_engine_imports_and_runs():
    result = get_g_score({"trust_index": 0.7, "maruah_score": 0.6})

    assert set(
        {
            "g_score",
            "delta_s",
            "lyapunov_lambda",
            "omega_capacity",
            "entropy_s",
            "verdict",
            "regime",
        }
    ).issubset(result)


def test_primitive_response_uses_canonical_tool_name():
    envelope = wealth_future_value(
        mode="npv",
        initial_investment=1000.0,
        cash_flows=[1200.0],
        discount_rate=0.1,
    )

    assert envelope["task"] == "wealth_future_value"
    assert envelope["canonical_tool"] == "wealth_future_value"
    assert "g_score" in envelope
    assert "risk" in envelope
    assert "verdict" in envelope["risk"]


def test_mcp_exports_only_13_canonical_tools():
    tool_names = {tool.name for tool in asyncio.run(mcp.list_tools())}

    assert tool_names == {
        "wealth_future_value",
        "wealth_present_expect",
        "wealth_future_simulate",
        "wealth_info_value",
        "wealth_truth_validate",
        "wealth_survival_liquidity",
        "wealth_survival_leverage",
        "wealth_rule_enforce",
        "wealth_allocate_optimize",
        "wealth_game_coordinate",
        "wealth_sense_ingest",
        "wealth_past_record",
        "wealth_future_steward",
    }
