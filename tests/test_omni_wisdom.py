"""
WEALTH Omni Wisdom — Path D Seal Test
======================================
Authority: Arif SEALed 2026-06-03.

Tests the wealth_omni_wisdom consolidation tool:
  - mode='synthesize' → routes to internal wealth_synthesize
  - mode='deal' → routes to internal wealth_deal_frame
  - mode='hysteresis' → routes to internal wealth_hysteresis_ledger
  - mode='omni' → parallel fan-out + F01 fusion (strictest verdict wins)

Net surface delta from Path D: 44 → 42 tools.
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import internal.monolith as monolith
from internal.monolith import wealth_omni_wisdom


# ─── Mode coverage ─────────────────────────────────────────────────────────


def test_omni_unknown_mode_returns_hold():
    """Unknown mode must return wisdom_verdict=HOLD with structured error."""
    result = asyncio.run(wealth_omni_wisdom(mode="invalid_mode"))
    assert result["wisdom_verdict"] == "HOLD"
    assert "Unknown mode" in result["error"]
    assert result["telemetry"]["mode_executed"] == "none"
    print("✅ test_omni_unknown_mode_returns_hold PASS")


def test_omni_synthesize_mode_routes_to_synth():
    """mode='synthesize' produces a synthesis bundle."""
    result = asyncio.run(
        wealth_omni_wisdom(
            mode="synthesize",
            decision_context={
                "description": "test synthesis routing",
                "capital_type": "enterprise",
            },
        )
    )
    assert "wisdom_verdict" in result
    assert result["wisdom_verdict"] in {"SEAL", "HOLD", "STOP"}
    assert "synthesis" in result
    assert result["synthesis"]["omega_verdict"] == "Ω-WEALTH-00"
    assert result["telemetry"]["mode_executed"] == "synthesize"
    assert result["telemetry"]["parallel"] is False
    print("✅ test_omni_synthesize_mode_routes_to_synth PASS")


def test_omni_deal_mode_routes_to_deal():
    """mode='deal' produces a deal bundle with structure_verdict."""
    result = asyncio.run(
        wealth_omni_wisdom(
            mode="deal",
            decision_context={"description": "test deal routing"},
            deal_params={
                "initial_investment": 100000.0,
                "cash_flows": [30000, 40000, 50000],
                "terminal_value": 0.0,
                "discount_rate": 0.10,
            },
        )
    )
    assert result["wisdom_verdict"] in {"SEAL", "HOLD", "STOP"}
    assert "deal" in result
    assert result["deal"]["omega_verdict"] == "Ω-DEAL-00"
    assert "structure_verdict" in result["deal"]
    assert "risk_flags" in result["deal"]
    assert result["telemetry"]["mode_executed"] == "deal"
    print("✅ test_omni_deal_mode_routes_to_deal PASS")


def test_omni_hysteresis_mode_routes_to_ledger():
    """mode='hysteresis' produces a hysteresis bundle with path_state.

    F01 defensive: if sub-engine fails (e.g. no Supabase in test env), the
    omni returns wisdom_verdict=HOLD with a structured error in telemetry,
    but the routing intent is still observable via mode_executed and path_state.
    """
    result = asyncio.run(
        wealth_omni_wisdom(
            mode="hysteresis",
            decision_context={"description": "test hysteresis routing"},
            path_params={"current_state": "GROWTH", "limit": 5},
        )
    )
    # F01: verdict may be HOLD if sub-engine errored; structure must be present
    assert result["wisdom_verdict"] in {"SEAL", "HOLD", "STOP"}
    assert "hysteresis" in result
    assert result["hysteresis"]["omega_path"] == "Ω-WEALTH-12"
    assert result["hysteresis"]["path_state"] == "GROWTH"
    assert result["telemetry"]["mode_executed"] == "hysteresis"
    print("✅ test_omni_hysteresis_mode_routes_to_ledger PASS (routing verified)")


def test_omni_omni_mode_fanout_and_fusion():
    """mode='omni' runs all 3 in parallel and fuses under F01 (strictest wins)."""
    result = asyncio.run(
        wealth_omni_wisdom(
            mode="omni",
            decision_context={
                "description": "test omni fanout",
                "capital_type": "financial",
            },
            deal_params={"initial_investment": 1000.0, "cash_flows": [500, 500]},
            path_params={"current_state": "COLLAPSE"},  # → STOP
        )
    )
    # F01: strictest wins. COLLAPSE → STOP, so wisdom_verdict must be STOP
    assert result["wisdom_verdict"] == "STOP"
    assert "synthesis" in result
    assert "deal" in result
    assert "hysteresis" in result
    assert result["telemetry"]["mode_executed"] == "omni"
    assert result["telemetry"]["parallel"] is True
    assert "sub_verdicts" in result["telemetry"]
    print("✅ test_omni_omni_mode_fanout_and_fusion PASS (F01 strictest-wins verified)")


def test_omni_fusion_strictest_wins():
    """F01 Reversibility: when verdicts disagree, strictest wins."""
    from internal.monolith import _wisdom_fuse

    # All SEAL → SEAL
    assert _wisdom_fuse(["SEAL", "SEAL", "SEAL"]) == ("SEAL", 1.0)
    # Mix → STOP (strictest)
    assert _wisdom_fuse(["SEAL", "HOLD", "STOP"]) == ("STOP", 0.6)
    # Mix → HOLD (no STOP present)
    assert _wisdom_fuse(["SEAL", "HOLD", "HOLD"]) == ("HOLD", 0.6)
    # Empty → HOLD
    assert _wisdom_fuse([]) == ("HOLD", 0.0)
    print("✅ test_omni_fusion_strictest_wins PASS (4 cases verified)")


def test_omni_registered_in_mcp():
    """wealth_omni_wisdom must be in the public MCP surface (44 → 42)."""
    runtime_tools = asyncio.run(monolith.mcp.list_tools())
    runtime_names = {t.name for t in runtime_tools}
    assert "wealth_omni_wisdom" in runtime_names
    # The 3 absorbed tools MUST NOT be in the public surface
    for absorbed in (
        "wealth_synthesize",
        "wealth_deal_frame",
        "wealth_hysteresis_ledger",
    ):
        assert absorbed not in runtime_names, (
            f"{absorbed} should be internal, not public"
        )
    # Count must be 42 (Path D end-state)
    assert len(runtime_tools) == 42, f"Expected 42 tools, got {len(runtime_tools)}"
    print(
        f"✅ test_omni_registered_in_mcp PASS (42 tools, omni present, 3 absorbed internal)"
    )


# ─── Run all tests ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_omni_unknown_mode_returns_hold,
        test_omni_synthesize_mode_routes_to_synth,
        test_omni_deal_mode_routes_to_deal,
        test_omni_hysteresis_mode_routes_to_ledger,
        test_omni_omni_mode_fanout_and_fusion,
        test_omni_fusion_strictest_wins,
        test_omni_registered_in_mcp,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"❌ {t.__name__} FAIL: {e}")
            failed += 1
    print(f"\n{'=' * 60}")
    print(f"Path D Omni Wisdom — {passed} passed, {failed} failed")
    if failed == 0:
        print("🏆 OMNI WISDOM SEALED — 42 tools, 4 modes, F01 fusion live")
    sys.exit(failed)
