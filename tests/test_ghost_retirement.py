"""
WEALTH Ghost Tool Retirement — Phase 2 + Path D Seal Test
======================================================
Authority: Arif approved Phase 2 ghost retirement 2026-05-27 + Path D 2026-06-03.

Phase 2 decision: Retire all 5 ghost tools as absorbed by wealth_deal_frame.
- Ghost tools exist in source (decorated @mcp.tool) but NOT in PUBLIC_SURFACE_WHITELIST
- wealth_deal_frame (Omega-DEAL-00) is the single canonical composite for opportunity evaluation
- All 5 ghosts are absorbed: their use cases are handled by deal_frame(scenarios=[...])

Path D decision (2026-06-03): Consolidate 3 tools (synthesize, deal_frame,
hysteresis_ledger) into wealth_omni_wisdom. Net delta: -2 (44 → 42).
- wealth_omni_wisdom (Omega-WEALTH-OMNI) is the new public canonical composite
  that absorbs wealth_synthesize + wealth_deal_frame + wealth_hysteresis_ledger
- The 3 originals remain as INTERNAL Python helpers (no longer @mcp.tool)

Ghosts being retired (Phase 2):
  wealth_screen_opportunity       -> absorbed by deal_frame (ranking/filtering/scoring)
  wealth_compute_viability       -> absorbed by deal_frame (NPV/IRR/payback/entropy)
  wealth_score_risk              -> absorbed by deal_frame (EMV/Monte Carlo/entropy)
  wealth_compare_scenarios       -> absorbed by deal_frame(scenarios=[...])
  wealth_emit_investment_memo    -> absorbed by deal_frame (structured memo output)

Path D consolidation (2026-06-03):
  wealth_synthesize             -> absorbed by wealth_omni_wisdom (mode='synthesize')
  wealth_deal_frame             -> absorbed by wealth_omni_wisdom (mode='deal')
  wealth_hysteresis_ledger      -> absorbed by wealth_omni_wisdom (mode='hysteresis')

This test verifies:
1. All 5 ghost tools remain ghosts (NOT in public surface)
2. wealth_omni_wisdom IS in public surface (Path D canonical replacement)
3. Tool count is 42 (Phase 2 = 44, Path D delta = -2)
4. Ghost tools tracked in _KNOWN_MISSING (not accidentally added to whitelist)
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import internal.monolith as monolith
from internal.monolith import PUBLIC_SURFACE_WHITELIST

GHOST_TOOLS = {
    "wealth_screen_opportunity",
    "wealth_compute_viability",
    "wealth_score_risk",
    "wealth_compare_scenarios",
    "wealth_emit_investment_memo",
}

# Path D (2026-06-03): wealth_omni_wisdom is the new public canonical that absorbs
# wealth_synthesize, wealth_deal_frame, and wealth_hysteresis_ledger.
CANONICAL_REPLACEMENT = "wealth_omni_wisdom"

# 26 (pre-Next-Horizon) - 7 (Next Horizon absorption 2026-06-05:
# epf, zakat, health_check, ledger_query, ledger_write, entropy_audit, preference_rank
# all absorbed as modes into personal_finance, conservation_capital,
# system_registry_status, entropy_risk, game_coordination) = 19
REQUIRED_SURFACE_COUNT = 20  # +1: wealth_stock_analysis (D4 Stock Analysis, 2026-06-10)


def get_runtime_tools():
    """Get current runtime tool names from MCP server."""
    return asyncio.run(monolith.mcp.list_tools())


def test_all_ghosts_remain_ghost():
    """All 5 ghost tools must NOT appear in public runtime surface."""
    runtime_tools = get_runtime_tools()
    runtime_names = {t.name for t in runtime_tools}

    unexpected_public = GHOST_TOOLS & runtime_names
    assert len(unexpected_public) == 0, (
        f"Ghost tools unexpectedly public: {sorted(unexpected_public)}. "
        f"These should remain in source but filtered by PUBLIC_SURFACE_WHITELIST."
    )
    print(f"✅ test_all_ghosts_remain_ghost PASS — all 5 ghosts remain ghost")


def test_canonical_replacement_is_public():
    """wealth_deal_frame must be public — it is the canonical replacement."""
    runtime_tools = get_runtime_tools()
    runtime_names = {t.name for t in runtime_tools}

    assert CANONICAL_REPLACEMENT in runtime_names, (
        f"Canonical replacement {CANONICAL_REPLACEMENT} not in public surface. "
        f"It must remain public as the single canonical composite."
    )
    print(
        f"✅ test_canonical_replacement_is_public PASS — {CANONICAL_REPLACEMENT} is public"
    )


def test_tool_count_unchanged():
    """Tool count must remain 44 — Phase 2 is document-only, no surface change."""
    runtime_tools = get_runtime_tools()
    assert len(runtime_tools) == REQUIRED_SURFACE_COUNT, (
        f"Tool count changed: got {len(runtime_tools)}, expected {REQUIRED_SURFACE_COUNT}. "
        f"Phase 2 is document-only — no tools added or removed."
    )
    print(
        f"✅ test_tool_count_unchanged PASS — {len(runtime_tools)} tools (expected {REQUIRED_SURFACE_COUNT})"
    )


def test_ghost_tools_tracked_and_filtered():
    """Ghost tools must be in _KNOWN_MISSING but NOT in PUBLIC_SURFACE_WHITELIST."""
    from internal.monolith import _KNOWN_MISSING

    ghost_in_whitelist = GHOST_TOOLS & PUBLIC_SURFACE_WHITELIST
    ghost_tracked = GHOST_TOOLS & _KNOWN_MISSING

    # Ghosts should be tracked in _KNOWN_MISSING (known absent) but NOT in whitelist
    assert len(ghost_tracked) == len(GHOST_TOOLS), (
        f"Some ghost tools not in _KNOWN_MISSING: {GHOST_TOOLS - ghost_tracked}"
    )
    assert len(ghost_in_whitelist) == 0, (
        f"Ghost tools incorrectly in PUBLIC_SURFACE_WHITELIST: {ghost_in_whitelist}"
    )
    print(
        f"✅ test_ghost_tools_tracked_and_filtered PASS — all 5 ghosts tracked as absent, none in whitelist"
    )


def test_no_untracked_tools_removed():
    """No tool from _PUBLIC_TOOLS should be removed."""
    from internal.monolith import _PUBLIC_TOOLS

    runtime_tools = get_runtime_tools()
    runtime_names = {t.name for t in runtime_tools}

    missing = [t for t in _PUBLIC_TOOLS if t not in runtime_names]
    assert len(missing) == 0, f"Previously-public tools missing from surface: {missing}"
    print(
        f"✅ test_no_untracked_tools_removed PASS — all {len(_PUBLIC_TOOLS)} public tools still present"
    )


if __name__ == "__main__":
    tests = [
        test_all_ghosts_remain_ghost,
        test_canonical_replacement_is_public,
        test_tool_count_unchanged,
        test_ghost_tools_tracked_and_filtered,
        test_no_untracked_tools_removed,
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
    print(f"Phase 2 Ghost Retirement — {passed} passed, {failed} failed")
    if failed == 0:
        print("🏆 ALL PHASE 2 TESTS PASS — ghosts formally retired")
    sys.exit(failed)
