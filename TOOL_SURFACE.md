# WEALTH Tool Surface Registry
> **Canonical Source:** `ariffazil/wealth`
> **Authority:** WEALTH organ, governed by `ariffazil/arifOS`
> **Purpose:** Classify every `@mcp.tool` decorator in `internal/monolith.py`
> **Status:** OPERATIONAL — 20 public tools + 34 hidden aliases (verified 2026-06-12)

---

## Classification Key

| Class | Meaning |
|-------|---------|
| `CANONICAL_PUBLIC` | Intentionally exposed to MCP clients; safe for agents |
| `INTERNAL_ALIAS` | Helper/wrapper that maps to a canonical tool |
| `DEPRECATED_ALIAS` | Old name, superseded by canonical name |
| `TEST_ONLY` | Only for testing, not for production use |
| `REMOVE_CANDIDATE` | Should be removed; causes agent confusion |
| `UNKNOWN` | Not yet classified; requires SME review |

---

## Ghost Tool Registry (Phase 2 — 2026-05-27)

| Tool Name | Source Status | Decision | Absorbed By | Canonical Path |
|-----------|-------------|----------|------------|---------------|
| `wealth_screen_opportunity` | EXISTS in monolith.py, NOT in whitelist | **RETIRED** | `wealth_deal_frame` | Use `wealth_deal_frame` |
| `wealth_compute_viability` | EXISTS in monolith.py, NOT in whitelist | **RETIRED** | `wealth_deal_frame` | Use `wealth_deal_frame` |
| `wealth_score_risk` | EXISTS in monolith.py, NOT in whitelist | **RETIRED** | `wealth_deal_frame` | Use `wealth_deal_frame` |
| `wealth_compare_scenarios` | EXISTS in monolith.py, NOT in whitelist | **RETIRED** | `wealth_deal_frame` | Use `wealth_deal_frame(scenarios=[...])` |
| `wealth_emit_investment_memo` | EXISTS in monolith.py, NOT in whitelist | **RETIRED** | `wealth_deal_frame` | `wealth_deal_frame` emits structured memo |

> ✅ **All 5 ghost tools exist in `internal/monolith.py` as `@mcp.tool(name="...")` decorated functions.**
> They are **GHOST** (filtered by `PUBLIC_SURFACE_WHITELIST`) — not missing, intentionally not exposed.
> **Phase 2 decision:** Retire all 5 as absorbed by `wealth_deal_frame` (Ω-DEAL-00). Single canonical composite replaces 5 standalone dispatchers.
> Reason: `wealth_deal_frame` handles all use cases via `scenarios`, `extract_emv`, and structured memo output. One path, not six.

---

## All Decorated Functions in `internal/monolith.py`

**Total `@mcp.tool` decorators:** 65 (per `grep -c "@mcp.tool" internal/monolith.py`)

### Infrastructure (internal helpers — likely INTERNAL_ALIAS or TEST_ONLY)

| Function | Line | Class | Notes |
|----------|------|-------|-------|
| `_wealth_read_wiki_file` | 4110 | `INTERNAL_ALIAS` | Leading underscore; private helper |
| `_wealth_tree777_index` | 4123 | `INTERNAL_ALIAS` | Leading underscore; private helper |

### Tree777 System (internal knowledge graph — likely INTERNAL_ALIAS)

| Function | Line | Class | Notes |
|----------|------|-------|-------|
| `wealth_tree777_index` | 4161 | `INTERNAL_ALIAS` | Knowledge graph indexing |
| `wealth_tree777_skill` | 4173 | `INTERNAL_ALIAS` | Skill concept mapping |
| `wealth_tree777_concept` | 4195 | `INTERNAL_ALIAS` | Concept registry |
| `wealth_tree777_scar` | 4218 | `INTERNAL_ALIAS` | Consequence surface tracking |

### EVOI / Risk Tools

| Function | Line | Class | Notes |
|----------|------|-------|-------|
| `wealth_evoi_compute` | 4242 | `CANONICAL_PUBLIC` | Core EVOI computation |
| `wealth_evoi_monte_carlo` | 4358 | `CANONICAL_PUBLIC` | Monte Carlo EVOI simulation |
| `wealth_correlation_guard_check` | 4420 | `INTERNAL_ALIAS` | Internal guard; not a public tool |
| `wealth_schema_validate` | 4466 | `TEST_ONLY` | Schema validation only |
| `wealth_init_tool` | 4511 | `TEST_ONLY` | Tool initialization only |

### Thermodynamic Financial Tools (the 13-mode primitives)

| Function | Line | Class | Notes |
|----------|------|-------|-------|
| `wealth_future_value` | 4743 | `CANONICAL_PUBLIC` | NPV/FV calculation |
| `wealth_present_expect` | 4793 | `CANONICAL_PUBLIC` | Present value expectation |
| `wealth_future_simulate` | 4814 | `CANONICAL_PUBLIC` | Future simulation |
| `wealth_survival_liquidity` | 4841 | `CANONICAL_PUBLIC` | Survival analysis: liquidity |
| `wealth_survival_leverage` | 4875 | `CANONICAL_PUBLIC` | Survival analysis: leverage |
| `wealth_info_value` | 4912 | `CANONICAL_PUBLIC` | Information value |
| `wealth_truth_validate` | 4954 | `CANONICAL_PUBLIC` | Truth/evidence validation |
| `wealth_rule_enforce` | 4983 | `CANONICAL_PUBLIC` | Rule enforcement |
| `wealth_allocate_optimize` | 5032 | `CANONICAL_PUBLIC` | Allocation optimization |
| `wealth_game_coordinate` | 5094 | `UNKNOWN` | Game theory coordination |
| `wealth_sense_ingest` | 5123 | `UNKNOWN` | Data ingestion |
| `wealth_past_record` | 5155 | `UNKNOWN` | Historical record |
| `wealth_future_steward` | 5214 | `UNKNOWN` | Future stewardship |

### Thermodynamic Primitives (core physics-math mapping)

| Function | Line | Class | Notes |
|----------|------|-------|-------|
| `wealth_value_npv` | 5617 | `INTERNAL_ALIAS` | NPV helper (superseded by wealth_future_value) |
| `wealth_energy_irr` | 5641 | `DEPRECATED_ALIAS` | Use wealth_future_value instead |
| `wealth_density_pi` | 5665 | `UNKNOWN` | Profit density |
| `wealth_time_payback` | 5681 | `UNKNOWN` | Payback period |
| `wealth_expectation_emv` | 5700 | `UNKNOWN` | EMV calculation |
| `wealth_probability_monte_carlo` | 5710 | `UNKNOWN` | Monte Carlo probability |

### Signal / Coupling

| Function | Line | Class | Notes |
|----------|------|-------|-------|
| `wealth_signal_evoi` | 5733 | `UNKNOWN` | EVOI signal processing |
| `wealth_signal_evoi_mc` | 5758 | `UNKNOWN` | MC variant |
| `wealth_coupling_correlation` | 5779 | `UNKNOWN` | Correlation coupling |

### Flow / Field / Mechanics

| Function | Line | Class | Notes |
|----------|------|-------|-------|
| `wealth_flow_cashflow` | 5795 | `UNKNOWN` | Cashflow modeling |
| `wealth_velocity_runway` | 5807 | `UNKNOWN` | Runway velocity |
| `wealth_gravity_dscr` | 5823 | `UNKNOWN` | DSCR gravity model |
| `wealth_mass_networth` | 5850 | `UNKNOWN` | Net worth mass |
| `wealth_pressure_triage` | 5861 | `UNKNOWN` | Triage pressure |
| `wealth_stewardship_civilization` | 5873 | `UNKNOWN` | Civilizational stewardship |

---

## Next Steps

1. ✅ Created this registry (PHOENIX-73E)
2. ⬜ Verify 5 missing contract tools (`wealth_screen_opportunity`, etc.) — do they exist under different names?
3. ⬜ Classify all `UNKNOWN` entries with WEALTH SME review
4. ⬜ Mark deprecated aliases as `DEPRECATED_ALIAS`
5. ⬜ Update `mcp_surface.yaml` contract to match reality

---

## WEALTH README Claim vs Reality

| Claim | Value |
|-------|-------|
| Public MCP surface | 17 tools |
| Internal aliases / deprecated | 52 |
| Total `@mcp.tool` decorators | 65 |

Classification found so far:
- `CANONICAL_PUBLIC`: ~12 tools confirmed
- `INTERNAL_ALIAS`: ~10 tools
- `DEPRECATED_ALIAS`: ~1 tool
- `TEST_ONLY`: ~2 tools
- `UNKNOWN`: ~40 tools (majority — need SME review)
