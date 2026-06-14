#!/usr/bin/env bash
# ============================================================================
# split_monolith.sh — Monolith Decomposition Plan (WEALTH)
#
# THIS IS A PLAN DOCUMENT — NOT A RUN SCRIPT
# The monolith (17,302 lines, ~25 public tools) cannot be split atomically
# without thorough testing. This script documents the TARGET STRUCTURE and
# the EXTRACTION METHOD for each tool.
#
# WARNING: Do NOT run this on the live monolith without 888_HOLD approval.
# The monolith is a production service. Any split must:
#   1. Be done on a branch
#   2. Preserve the original as import facade
#   3. Pass ALL existing tests before deployment
#
# DITEMPA BUKAN DIBERI — Forged, Not Given.
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEALTH_ROOT="$(dirname "$SCRIPT_DIR")"
INTERNAL_DIR="${WEALTH_ROOT}/internal"
MONOLITH="${INTERNAL_DIR}/monolith.py"

echo "=== WEALTH Monolith Split Plan ==="
echo "Monolith: ${MONOLITH}"
echo "Target:   ${INTERNAL_DIR}/engines/ (tool modules)"
echo ""

# ── Tool Extraction Map ──────────────────────────────────────────────────────
# Each entry: LINE_RANGE | TOOL_NAME | TARGET_FILE | Ω-ID
#
# NOTE: Line numbers are approximate. Recalculate before actual extraction.

TOOLS=$(cat << 'EOF'
# ── L1 Canonical Physics Organs ──
# wealth_conservation_capital  | 11581-11610   | engines/conservation.py   | Ω-WEALTH-01
# wealth_flow_liquidity        | 11613-11639   | engines/flow.py           | Ω-WEALTH-02
# wealth_gradient_price        | 11642-11654   | engines/gradient.py       | Ω-WEALTH-03
# wealth_entropy_risk          | 11657-11970   | engines/entropy.py        | Ω-WEALTH-04
# wealth_energy_productivity   | 11800-11970   | engines/energy.py         | Ω-WEALTH-05
# wealth_time_discount         | 11971-11997   | engines/time.py           | Ω-WEALTH-06
# wealth_inertia_leverage      | 11998-12095   | engines/inertia.py        | Ω-WEALTH-07
# wealth_field_macro           | 12096-12298   | engines/field.py          | Ω-WEALTH-08
# wealth_signal_information    | 12299-12467   | engines/signal.py         | Ω-WEALTH-09
# wealth_game_coordination     | 12468-12547   | engines/game.py           | Ω-WEALTH-10
# wealth_boundary_governance   | 12548-12993   | engines/boundary.py       | Ω-WEALTH-11

# ── L0 Kernel Surface ──
# wealth_system_registry_status | 13028-13249  | engines/registry.py      | Ω-WEALTH-00
# wealth_omni_wisdom           | 13250-14786   | engines/omni_wisdom.py    | Ω-WEALTH-OMNI
# wealth_agent_path            | 9180-9293     | engines/agent_path.py     | Ω-WEALTH-PATH

# ── L2 Specialists ──
# wealth_governance_verdict    | 9100-9136     | engines/verdict.py        | Ω-WEALTH-VERDICT
# wealth_inequality_kernel     | 15402-15645   | engines/inequality.py     | Ω-WEALTH-IEQ

# ── D1/D3/D4 Domain Tools ──
# wealth_personal_finance      | 1274-1439     | personal_finance.py (EXISTS)
# wealth_market_data           | 1659-1930     | market_data.py (EXISTS)
# wealth_stock_analysis        | 2458-3049     | stock/__init__.py (EXISTS)

# ── Survival Engine ──
# wealth_survival_engine       | 4907-5268     | engines/survival.py       | Ω-SURVIVAL

# ── Internal Engines (not @mcp.tool, but called by the above) ──
# networth_state               | 4718-4772     | engines/_conservation.py
# cashflow_flow                | 4776-4910     | engines/_flow.py
# growth_velocity              | 4668-4714     | engines/_time.py
# emv_risk                     | 4520-4562     | engines/_entropy.py
# npv_reward                   | 4404-4437     | engines/_time.py
# irr_yield                    | 4441-4480     | engines/_time.py
# payback_time                 | 4642-4664     | engines/_time.py
# crisis_triage                | 5715-5810     | engines/_survival.py
EOF
)

echo "=== Extraction Method ==="
echo ""
echo "For each tool function (decorated with @mcp.tool):"
echo "  1. Extract function body + decorator + docstring"
echo "  2. Create file at engines/<name>.py with:"
echo "     - Ω-header docstring"
echo "     - All required imports (from monolith.py's top section)"
echo "     - The tool function only (not internal helpers)"
echo "  3. In monolith.py, replace tool body with:"
echo "       from .engines.<name> import <function>"
echo "       __all__ += ['<function>']"
echo ""
echo "=== Internal Helpers ==="
echo "Internal functions (networth_state, cashflow_flow, etc.) should be"
echo "extracted to _prefixed modules in engines/ AFTER their callers."
echo ""
echo "=== Testing Gate ==="
echo "Before any branch is merged:"
echo "  pytest tests/ -q --tb=short"
echo "  python -c 'from internal.monolith import *; print(\"All imports OK\")'"
echo ""

echo "=== Target Module Tree ==="
cat << 'TREE'
internal/
├── monolith.py              ← Import facade (re-exports from engines/)
├── engines/
│   ├── __init__.py
│   ├── conservation.py      ← Ω-WEALTH-01 wealth_conservation_capital
│   ├── flow.py              ← Ω-WEALTH-02 wealth_flow_liquidity
│   ├── gradient.py          ← Ω-WEALTH-03 wealth_gradient_price
│   ├── entropy.py           ← Ω-WEALTH-04 wealth_entropy_risk
│   ├── energy.py            ← Ω-WEALTH-05 wealth_energy_productivity
│   ├── time.py              ← Ω-WEALTH-06 wealth_time_discount
│   ├── inertia.py           ← Ω-WEALTH-07 wealth_inertia_leverage
│   ├── field.py             ← Ω-WEALTH-08 wealth_field_macro
│   ├── signal.py            ← Ω-WEALTH-09 wealth_signal_information
│   ├── game.py              ← Ω-WEALTH-10 wealth_game_coordination
│   ├── boundary.py          ← Ω-WEALTH-11 wealth_boundary_governance
│   ├── registry.py          ← Ω-WEALTH-00 wealth_system_registry_status
│   ├── omni_wisdom.py       ← Ω-WEALTH-OMNI wealth_omni_wisdom
│   ├── agent_path.py        ← Ω-WEALTH-PATH wealth_agent_path
│   ├── verdict.py           ← Ω-WEALTH-VERDICT wealth_governance_verdict
│   ├── inequality.py        ← Ω-WEALTH-IEQ wealth_inequality_kernel
│   └── survival.py          ← Ω-SURVIVAL wealth_survival_engine
├── market_data.py           ← D3 (already separate)
├── personal_finance.py      ← D1 (already separate)
├── stock/                   ← D4 (already separate)
│   └── ...
├── db_schema.py             ← Database schema (already separate)
├── kernel_math.py           ← Math helpers (already separate)
└── ...
TREE

echo ""
echo "=== Phase Plan (recommended order) ==="
echo "Phase 1: Extract survival engine (fewest deps)"
echo "Phase 2: Extract gradient + conservation (pure math, no side effects)"
echo "Phase 3: Extract time + energy + entropy (medium deps)"
echo "Phase 4: Extract field + signal + game + boundary (heavier deps)"
echo "Phase 5: Extract omni_wisdom + inequality (heaviest)"
echo "Phase 6: Convert monolith.py to pure import facade"
echo "Phase 7: Full test suite pass + seal"
