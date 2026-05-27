"""
WEALTH Ghost Tool Retirement — Phase 2 Seal Test
==============================================
Authority: Arif approved Phase 2 ghost retirement 2026-05-27

Phase 2 decision: Retire all 5 ghost tools as absorbed by wealth_deal_frame.
- Ghost tools exist in source (decorated @mcp.tool) but NOT in PUBLIC_SURFACE_WHITELIST
- wealth_deal_frame (Omega-DEAL-00) is the single canonical composite for opportunity evaluation
- All 5 ghosts are absorbed: their use cases are handled by deal_frame(scenarios=[...])

Ghosts being retired:
  wealth_screen_opportunity       -> absorbed by deal_frame (ranking/filtering/scoring)
  wealth_compute_viability       -> absorbed by deal_frame (NPV/IRR/payback/entropy)
  wealth_score_risk              -> absorbed by deal_frame (EMV/Monte Carlo/entropy)
  wealth_compare_scenarios       -> absorbed by deal_frame(scenarios=[...])
  wealth_emit_investment_memo    -> absorbed by deal_frame (structured memo output)

This test verifies:
1. All 5 ghost tools remain ghosts (NOT in public surface)
2. wealth_deal_frame IS in public surface (canonical replacement)
3. Tool count remains 44 (no new tools added)
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

CANONICAL_REPLACEMENT = "wealth_deal_frame"

REQUIRED_SURFACE_COUNT = 44


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
    print(f"✅ test_canonical_replacement_is_public PASS — {CANONICAL_REPLACEMENT} is public")


def test_tool_count_unchanged():
    """Tool count must remain 44 — Phase 2 is document-only, no surface change."""
    runtime_tools = get_runtime_tools()
    assert len(runtime_tools) == REQUIRED_SURFACE_COUNT, (
        f"Tool count changed: got {len(runtime_tools)}, expected {REQUIRED_SURFACE_COUNT}. "
        f"Phase 2 is document-only — no tools added or removed."
    )
    print(f"✅ test_tool_count_unchanged PASS — {len(runtime_tools)} tools (expected {REQUIRED_SURFACE_COUNT})")


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
    print(f"✅ test_ghost_tools_tracked_and_filtered PASS — all 5 ghosts tracked as absent, none in whitelist")


def test_no_untracked_tools_removed():
    """No tool from _PUBLIC_TOOLS should be removed."""
    from internal.monolith import _PUBLIC_TOOLS

    runtime_tools = get_runtime_tools()
    runtime_names = {t.name for t in runtime_tools}

    missing = [t for t in _PUBLIC_TOOLS if t not in runtime_names]
    assert len(missing) == 0, (
        f"Previously-public tools missing from surface: {missing}"
    )
    print(f"✅ test_no_untracked_tools_removed PASS — all {len(_PUBLIC_TOOLS)} public tools still present")


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
