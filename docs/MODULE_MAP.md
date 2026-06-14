# WEALTH Module Map — Canonical Tool Architecture

> **Version:** 2026.06.14  
> **Status:** LIVE (monolith.py) → TARGET (split modules)  
> **Doctrine:** DITEMPA BUKAN DIBERI

---

## Architecture Overview

WEALTH has **25 public MCP tools** organized in a 3-layer hierarchy:

```
L0 — Kernel Surface  (3 tools: registry, omni_wisdom, agent_path)
L1 — Physics Organs  (11 tools: conservation, flow, gradient, entropy, energy, time, inertia, field, signal, game, boundary)
L2 — Specialists     (2 tools: governance_verdict, inequality_kernel)
D1/D3/D4 — Domains  (3 tools: personal_finance, market_data, stock_analysis)
```

Plus survival engine (Ω-SURVIVAL) which absorbs legacy cashflow/liquidity/runway wrappers.

---

## Current Layout (LIVE — monolith.py, 17,302 lines)

| Ω-ID | Tool | Lines | File | Status |
|------|------|-------|------|--------|
| L0 | `wealth_system_registry_status` | 13028–13249 | `internal/monolith.py` | `@mcp.tool` |
| L0 | `wealth_omni_wisdom` | 13250–14786 | `internal/monolith.py` | `@mcp.tool` |
| L0 | `wealth_agent_path` | 9180–9293 | `internal/monolith.py` | `@mcp.tool` |
| Ω-WEALTH-01 | `wealth_conservation_capital` | 11581–11610 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-WEALTH-02 | `wealth_flow_liquidity` | 11613–11639 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-WEALTH-03 | `wealth_gradient_price` | 11642–11654 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-WEALTH-04 | `wealth_entropy_risk` | 11657–11970 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-WEALTH-05 | `wealth_energy_productivity` | 11800–11970 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-WEALTH-06 | `wealth_time_discount` | 11971–11997 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-WEALTH-07 | `wealth_inertia_leverage` | 11998–12095 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-WEALTH-08 | `wealth_field_macro` | 12096–12298 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-WEALTH-09 | `wealth_signal_information` | 12299–12467 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-WEALTH-10 | `wealth_game_coordination` | 12468–12547 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-WEALTH-11 | `wealth_boundary_governance` | 12548–12993 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-VERDICT | `wealth_governance_verdict` | 9100–9136 | `internal/monolith.py` | `@mcp.tool` |
| Ω-IEQ | `wealth_inequality_kernel` | 15402–15645 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| Ω-SURVIVAL | `wealth_survival_engine` | 4907–5268 | `internal/monolith.py` | `@mcp.tool` |
| D1 | `wealth_personal_finance` | 1274–1439 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| D3 | `wealth_market_data` | 1659–1930 | `internal/monolith.py` | `@mcp.tool(name=...)` |
| D4 | `wealth_stock_analysis` | 2458–3049 | `internal/monolith.py` | `@mcp.tool(name=..., task=True)` |

### Already-Separated Files

| Module | File | Notes |
|--------|------|-------|
| D1 Personal Finance | `internal/personal_finance.py` | Standalone module, imported by monolith |
| D3 Market Data | `internal/market_data.py` | Standalone module, imported by monolith |
| D4 Stock Analysis | `internal/stock/` | Package with ~10 sub-files |
| DB Schema | `internal/db_schema.py` | PostgreSQL schema helpers |
| Kernel Math | `internal/kernel_math.py` | Math primitives (NPV, IRR, EMV, PI) |
| Invariants | `internal/invariants.py` | Invariant validation |
| Governance | `internal/governance.py` | ForgeLaw, kappa, psi |
| Organ Governance | `internal/organ_governance.py` | Organ-level governance |
| Federation Memory | `internal/federation_memory.py` | Cross-organ memory |

### Legacy Tools (MCP-decorated, being absorbed)

| Tool | Lines | Status |
|------|-------|--------|
| `wealth_future_steward` | 7771–7808 | Active `@mcp.tool()` |
| `vault_write` | 7811–7870 | Active `@mcp.tool()` |
| `vaultwrite` alias | 7873–7893 | Active `@mcp.tool()` |
| `vaultquery` alias | 7896–7910 | Active `@mcp.tool()` |
| `vault_query` | 7913–8000+ | Active `@mcp.tool()` |
| `wealth_coupling_correlation` | 8718–8728 | Active `@mcp.tool()` |
| `wealth_pressure_triage` | 8806–8815 | Active `@mcp.tool()` |
| `wealth_stewardship_civilization` | 8818–8836 | Active `@mcp.tool()` |
| `wealth_measurement_schema` | 8842–8849 | Active `@mcp.tool()` |
| `wealth_boundary_floors` | 9051–9087 | Active `@mcp.tool()` |
| `wealth_boundary_policy` | 9088–9098 | Active `@mcp.tool()` |
| `wealth_field_game` | 9137–9153 | Active `@mcp.tool()` |
| `wealth_field_equilibrium` | 9154–9167 | Active `@mcp.tool()` |
| `wealth_preference_rank` | 9168–9178 | Active `@mcp.tool()` |

### Removed / Absorbed Tools

| Tool | Absorbed Into | Date |
|------|---------------|------|
| `wealth_hysteresis_ledger` | `wealth_omni_wisdom` (mode=hysteresis) | 2026-06-03 |
| `wealth_synthesize` | `wealth_omni_wisdom` (mode=synthesize) | 2026-06-03 |
| `wealth_deal_frame` | `wealth_omni_wisdom` (mode=deal) | 2026-06-03 |

---

## Internal Engine Dependencies

Each public tool calls into internal "engine" functions:

```
wealth_conservation_capital → networth_state, snapshot_portfolio_tool, wealth_ledger_query, wealth_ledger_write
wealth_flow_liquidity       → cashflow_flow, growth_velocity, crisis_triage
wealth_gradient_price       → _gradient_spread, _gradient_pressure, _gradient_mispricing
wealth_entropy_risk         → emv_risk, audit_entropy, wealth_coupling_correlation (converted)
wealth_energy_productivity  → pi_efficiency, audit_entropy, npv_reward
wealth_time_discount        → npv_reward, irr_yield, payback_time, growth_velocity
wealth_inertia_leverage     → dscr_leverage
wealth_field_macro          → wealth_fx_rate, wealth_commodity_price, wealth_macro_indicator
wealth_signal_information   → wealth_evoi_compute, wealth_evoi_monte_carlo
wealth_game_coordination    → wealth_field_game, wealth_field_equilibrium, wealth_preference_rank
wealth_boundary_governance  → wealth_boundary_floors, wealth_boundary_policy
```

All internal engine functions are defined at module level in `monolith.py`.

---

## Target Split Structure

```
internal/
├── monolith.py              ← Import facade (re-exports from engines/)
├── engines/
│   ├── __init__.py
│   ├── conservation.py      ← Ω-WEALTH-01
│   ├── flow.py              ← Ω-WEALTH-02
│   ├── gradient.py          ← Ω-WEALTH-03
│   ├── entropy.py           ← Ω-WEALTH-04
│   ├── energy.py            ← Ω-WEALTH-05
│   ├── time.py              ← Ω-WEALTH-06
│   ├── inertia.py           ← Ω-WEALTH-07
│   ├── field.py             ← Ω-WEALTH-08
│   ├── signal.py            ← Ω-WEALTH-09
│   ├── game.py              ← Ω-WEALTH-10
│   ├── boundary.py          ← Ω-WEALTH-11
│   ├── registry.py          ← Ω-WEALTH-00
│   ├── omni_wisdom.py       ← Ω-WEALTH-OMNI
│   ├── agent_path.py        ← Ω-WEALTH-PATH
│   ├── verdict.py           ← Ω-WEALTH-VERDICT
│   ├── inequality.py        ← Ω-WEALTH-IEQ
│   └── survival.py          ← Ω-SURVIVAL
├── market_data.py           ← D3 (already separate)
├── personal_finance.py      ← D1 (already separate)
├── stock/                   ← D4 (already separate)
├── db_schema.py             ← already separate
├── kernel_math.py           ← already separate
└── ...
```

See `scripts/split_monolith.sh` for the extraction plan and `docs/SPLIT_PLAN.md` for the migration phases.
