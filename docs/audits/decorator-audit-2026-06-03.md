# WEALTH Decorator Audit (Path C) — 2026-06-03

**Author:** arifOS Forge Agent (Ω) — `feat/wealth-decorator-audit-2026-06-03`
**Source:** `internal/monolith.py` (13,623 lines, 500KB)
**Audit type:** Diagnostic only. NO behavior change. NO decorator edits. NO function moves.
**Authority:** 888_HOLD granted 2026-06-03 by Arif Fazil (via Perplexity audit frame)

---

## Executive Summary

| Metric | Count | Note |
|---|---|---|
| `@mcp.tool` decorators in source | **84** | `grep -c` |
| Named (`name="wealth_xxx"`) | **33** | Per grep count; 2 of these are duplicate registrations |
| Unnamed (`@mcp.tool()` auto-named) | **49–51** | Discrepancy due to multi-line vs single-line decorator parsing |
| **Live runtime tools** | **44** | `mcp.list_tools()` confirmed via `sync_manifest.py` dry-run |
| **Gap (84 - 44)** | **40** | Below resolution |
| Ghost tools in `WEALTH_PUBLIC_TOOL_ORDER` not registered | **5** | Per `internal/monolith.py:12638` `_KNOWN_MISSING` |
| Case-variant duplicate function names | **4** | `vault_write`/`vaultwrite`, `vault_query`/`vaultquery` |
| Typo in function name (auto-exposes) | **1** | `wealth mass_networth` (space) at L7355 |
| Functions with same name registered twice | **1** | `wealth_runway_calculate` at L1071 and L3761 |

### Where the 40 missing tools go

| Cause | Count | Disposition default |
|---|---|---|
| FastMCP de-duped case-variant `vault_write` / `vaultwrite` | 2 | **hide** (governance violation: vault internals exposed to MCP) |
| FastMCP de-duped `wealth_runway_calculate` (registered at L1071 and L3761) | 1 | **hide** (L3761 is the "Legacy Wrappers" duplicate per L3756) |
| 5 L3 ghost tools in `WEALTH_PUBLIC_TOOL_ORDER` but not registered at runtime (silent failure per `_KNOWN_MISSING`) | 5 | **keep_name + DEBUG** (they're in the canonical surface, the bug is the registration, not the decorator) |
| 32 v1 functions referenced in `_ALIAS_DISPATCH` map (L12658-12694) but only aliased to v2 if matching `v2_canonical_map` — most are never aliased, only the v2-canonical-named ones survive | ~22 | **hide** (v1 legacy layer per P1-1) |
| 10 named math primitives that should auto-name to clean canonical names but the auto-name function name has the canonical name (e.g. `def wealth_value_npv` → `wealth_value_npv`) — these ARE in the live surface already | n/a | **keep_name** (rename to add explicit `name=` for clarity) |
| Other unnamed (survival_liquidity, survival_leverage, info_value, truth_validate, etc.) — these overlap via the v1 alias map but get de-duped at registration | ~10 | **keep_name** (mostly stateless math, legitimate surface) |

The 40-tool gap is NOT 40 broken tools — it's a mix of (a) deliberate v1 retirement, (b) case-variant name collisions, (c) registration-failure ghosts. After Path C, the gap should drop to **0** (or close to 0 — we may decide some v1 helpers truly belong hidden).

---

## Classification Map (82 of 84 decorators)

Legend: **N** = named, **U** = unnamed, **S** = stateful (touches DB/cache/IO), **P** = pure stateless math, **G** = governance/floor, **H** = helper/internal leak.

### Section A — D1 Personal Finance (L995–L1625)

| # | Line | Function | Exposed | N/U | S/P/G/H | Family | Disposition | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | 995 | `wealth_cashflow_track()` | `wealth_cashflow_track` | N | S | personal_finance | **keep_name** | DB write |
| 2 | 1035 | `wealth_cashflow_summary()` | `wealth_cashflow_summary` | N | S | personal_finance | **keep_name** | DB read+aggregate |
| 3 | 1071 | `wealth_runway_calculate()` | `wealth_runway_calculate` | N | P | personal_finance | **keep_name** | D1-03 |
| 4 | 1104 | `wealth_net_worth_snapshot()` | `wealth_net_worth_snapshot` | N | S | personal_finance | **keep_name** | DB read |
| 5 | 1145 | `wealth_epf_project()` | `wealth_epf_project` | N | P | personal_finance | **keep_name** | Stateless projection |
| 6 | 1206 | `wealth_zakat_calculate()` | `wealth_zakat_calculate` | N | P | personal_finance | **keep_name** | D1-06 |
| 7 | 1253 | `wealth_fx_rate()` | `wealth_fx_rate` | N | S | market_data | **keep_name** | D3-01, live API call |
| 8 | 1298 | `wealth_commodity_price()` | `wealth_commodity_price` | N | S | market_data | **keep_name** | D3-02 |
| 9 | 1349 | `wealth_macro_indicator()` | `wealth_macro_indicator` | N | S | market_data | **keep_name** | D3-03, World Bank API |
| 10 | 1625 | `mcp_health_check()` | `mcp_health_check` | U | P | helper-leak | **rename** | Generic name. Rename to `wealth_health_check` and document as F1-F13 enforcement probe. **Note: this is the deprecated alias in `TOOL_SURFACE.md`.** |

### Section B — SURVIVAL_ENGINE + Legacy Wrappers (L3467, L3761)

| # | Line | Function | Exposed | N/U | S/P/G/H | Family | Disposition | Notes |
|---|---|---|---|---|---|---|---|---|
| 11 | 3467 | `wealth_survival_engine()` | `wealth_survival_engine` | U | S | personal_finance | **keep_name + add `name=`** | Ω-SURVIVAL-ENGINE, 5 modes (cashflow/runway/burn/liquidity/personal_finance) |
| 12 | 3761 | `wealth_runway_calculate()` | (DUPLICATE) | N | P | legacy-leak | **hide** | L3761 is the "Legacy Wrappers" duplicate per L3756 comment. Same name as #3 — FastMCP de-duped. The legacy copy is dead code. |

### Section C — Ω-SURVIVAL Family (L5859–L6332)

| # | Line | Function | Exposed (auto-name) | N/U | S/P/G/H | Family | Disposition | Notes |
|---|---|---|---|---|---|---|---|---|
| 13 | 5859 | `wealth_future_value()` | `wealth_future_value` | U | P | kernel_math | **keep_name** | Stateless math |
| 14 | 5909 | `wealth_present_expect()` | `wealth_present_expect` | U | P | kernel_math | **keep_name** | Stateless math |
| 15 | 5930 | `wealth_future_simulate()` | `wealth_future_simulate` | U | S | kernel_math | **keep_name** | Likely stateful (scenario store) |
| 16 | 5957 | `wealth_survival_liquidity()` | `wealth_survival_liquidity` | U | S | personal_finance | **keep_name** | Liquidity state read |
| 17 | 5991 | `wealth_survival_leverage()` | `wealth_survival_leverage` | U | P | personal_finance | **keep_name** | Pure math |
| 18 | 6028 | `wealth_info_value()` | `wealth_info_value` | U | P | kernel_math | **keep_name** | Pure math (EVOI) |
| 19 | 6070 | `wealth_truth_validate()` | `wealth_truth_validate` | U | P | governance | **keep_name** | Stateless |
| 20 | 6099 | `wealth_rule_enforce()` | `wealth_rule_enforce` | U | G | governance | **keep_name** | Floor enforcement — stateful in practice |
| 21 | 6148 | `wealth_allocate_optimize()` | `wealth_allocate_optimize` | U | S | personal_finance | **keep_name** | Agent budget optimization |
| 22 | 6210 | `wealth_game_coordinate()` | `wealth_game_coordinate` | U | P | kernel_math | **keep_name** | Game theory solver, pure math |
| 23 | 6239 | `wealth_sense_ingest()` | `wealth_sense_ingest` | U | S | market_data | **keep_name** | INGEST, touches world data |
| 24 | 6271 | `wealth_past_record()` | `wealth_past_record` | U | S | governance | **keep_name** | Past ledger write |
| 25 | 6332 | `wealth_future_steward()` | `wealth_future_steward` | U | S | governance | **keep_name** | Civilizational scope |

### Section D — VAULT (L6372–L6474) — **GOVERNANCE SMELL ZONE**

| # | Line | Function | Exposed | N/U | S/P/G/H | Family | Disposition | Notes |
|---|---|---|---|---|---|---|---|---|
| 26 | 6372 | `vault_write()` | `vault_write` (case-collides) | U | G | governance-leak | **hide + remove** | Exposes VAULT internals to MCP. Should be `arif_vault_seal` (kernel tool), not local. |
| 27 | 6434 | `vaultwrite()` | `vault_write` (variant) | U | G | governance-leak | **hide + remove** | Same function, no underscore. DEAD VARIANT. Remove. |
| 28 | 6457 | `vault_query()` | `vault_query` (case-collides) | U | G | governance-leak | **hide + remove** | VAULT read should route through arifOS. |
| 29 | 6474 | `vaultquery()` | `vault_query` (variant) | U | G | governance-leak | **hide + remove** | Same function, no underscore. DEAD VARIANT. Remove. |

**This is the biggest finding in the audit.** 4 functions expose VAULT internals directly. The `_ALIAS_DISPATCH` map at L12696 explicitly skips `vaultwrite` and `vaultquery` (the case variants), but `vault_write` and `vault_query` may still be live via the canonical path. **Disposition: ALL 4 removed** + open a 888_HOLD issue to route vault access through arifOS kernel.

### Section E — Ω-WEALTH Substrate Primitives (L6735–L7402)

| # | Line | Function | Exposed | N/U | S/P/G/H | Family | Disposition | Notes |
|---|---|---|---|---|---|---|---|---|
| 30 | 6735 | `wealth_value_npv()` | `wealth_value_npv` | U | P | kernel_math | **keep_name** | Pure math |
| 31 | 6759 | `wealth_energy_irr()` | `wealth_energy_irr` | U | P | kernel_math | **keep_name** | Pure math |
| 32 | 6783 | `wealth_density_pi()` | `wealth_density_pi` | U | P | kernel_math | **keep_name** | Pure math |
| 33 | 6799 | `wealth_time_payback()` | `wealth_time_payback` | U | P | kernel_math | **keep_name** | Pure math |
| 34 | 6818 | `wealth_expectation_emv()` | `wealth_expectation_emv` | U | P | kernel_math | **keep_name** | Pure math |
| 35 | 6828 | `wealth_probability_monte_carlo()` | `wealth_probability_monte_carlo` | U | S | kernel_math | **keep_name** | MC state store |
| 36 | 6851 | `wealth_signal_evoi()` | `wealth_signal_evoi` | U | P | kernel_math | **keep_name** | Pure math |
| 37 | 6876 | `wealth_signal_evoi_mc()` | `wealth_signal_evoi_mc` | U | S | kernel_math | **keep_name** | MC variant |
| 38 | 6897 | `wealth_deal_frame()` | `wealth_deal_frame` (absorbed) | U | S | personal_finance | **absorbed into wealth_omni_wisdom (mode='deal')** | Will be one of the 3 modes of `wealth_omni_wisdom`. Original Ω-DEAL-00 capability preserved as `mode='deal'`. |
| 39 | 7278 | `wealth_coupling_correlation()` | `wealth_coupling_correlation` | U | P | kernel_math | **keep_name** | Pure math |
| 40 | 7294 | `wealth_flow_cashflow()` | `wealth_flow_cashflow` | U | S | personal_finance | **keep_name** | Cash flow projection, state |
| 41 | 7312 | `wealth_velocity_runway()` | `wealth_velocity_runway` | U | P | personal_finance | **keep_name** | Pure math |
| 42 | 7328 | `wealth_gravity_dscr()` | `wealth_gravity_dscr` | U | P | personal_finance | **keep_name** | Pure math |
| 43 | 7355 | `wealth mass_networth()` | `wealth mass_networth` (SPACE) | U | P | personal_finance | **remove** | **Typo in function name (space)** — auto-exposes to "wealth mass_networth". Should be `wealth_mass_networth`. After rename, this is a duplicate of `wealth_net_worth_snapshot` (#4). **Disposition: remove the typo, rely on the snapshot tool.** |
| 44 | 7366 | `wealth_pressure_triage()` | `wealth_pressure_triage` | U | P | governance | **keep_name** | Triage logic |
| 45 | 7378 | `wealth_stewardship_civilization()` | `wealth_stewardship_civilization` | U | S | governance | **keep_name** | Civilizational scope |
| 46 | 7402 | `wealth_measurement_schema()` | `wealth_measurement_schema` | U | P | governance | **keep_name** | Schema validation, stateless |
| 47 | 7412 | `wealth_entropy_audit()` | `wealth_entropy_audit` | N | P | kernel_math | **keep_name** | Explicit name OK |
| 48 | 7507 | `wealth_institutional_entropy_scorer()` | `wealth_institutional_entropy_scorer` | N | S | governance | **keep_name** | Stateful institutional audit |

### Section F — Ω-WEALTH-BOUNDARY (Governance / Floor) (L7579–L7952)

| # | Line | Function | Exposed | N/U | S/P/G/H | Family | Disposition | Notes |
|---|---|---|---|---|---|---|---|---|
| 49 | 7579 | `wealth_boundary_floors()` | `wealth_boundary_floors` | U | G | governance | **keep_name** | Floor check |
| 50 | 7616 | `wealth_boundary_policy()` | `wealth_boundary_policy` | U | G | governance | **keep_name** | Floor policy |
| 51 | 7627 | `wealth_governance_verdict()` | `wealth_governance_verdict` | U | G | governance | **keep_name** | Final verdict |
| 52 | 7665 | `wealth_field_game()` | `wealth_field_game` | U | P | kernel_math | **keep_name** | Game theory |
| 53 | 7682 | `wealth_field_equilibrium()` | `wealth_field_equilibrium` | U | P | kernel_math | **keep_name** | Equilibrium solver |
| 54 | 7696 | `wealth_preference_rank()` | `wealth_preference_rank` | U | P | personal_finance | **keep_name** | Utility ranking |
| 55 | 7708 | `wealth_agent_path()` | `wealth_agent_path` | U | S | personal_finance | **keep_name** | Agent pathing (stateful) |
| 56 | 7823 | `wealth_sensor_fetch()` | `wealth_sensor_fetch` | U | S | market_data | **keep_name** | SENSE-like fetch |
| 57 | 7878 | `wealth_ledger_query()` | `wealth_ledger_query` | U | S | governance | **keep_name** | Read governance ledger |
| 58 | 7889 | `wealth_ledger_write()` | `wealth_ledger_write` | U | S | governance | **keep_name** | Write governance ledger |
| 59 | 7904 | `wealth_ledger_init()` | `wealth_ledger_init` | U | S | governance | **keep_name** | Init ledger |
| 60 | 7915 | `wealth_ledger_record()` | `wealth_ledger_record` | U | S | governance | **keep_name** | Record transaction |
| 61 | 7952 | `wealth_ledger_snapshot()` | `wealth_ledger_snapshot` | U | S | governance | **keep_name** | Snapshot ledger |

### Section G — Ω-FIELD / Ω-SIGNAL / Ω-CIVILIZATION (L9669–L10866) — Named canonical family

| # | Line | Function | Exposed | N/U | S/P/G/H | Family | Disposition | Notes |
|---|---|---|---|---|---|---|---|---|
| 62 | 9669 | `wealth_conservation_capital()` | `wealth_conservation_capital` | N | S | kernel_math | **keep_name** | Ω-WEALTH-01, stateful |
| 63 | 9699 | `wealth_flow_liquidity()` | `wealth_flow_liquidity` | N | S | personal_finance | **keep_name** | Ω-WEALTH-02 |
| 64 | 9728 | `wealth_gradient_price()` | `wealth_gradient_price` | N | P | kernel_math | **keep_name** | Ω-WEALTH-03 |
| 65 | 9743 | `wealth_entropy_risk()` | `wealth_entropy_risk` | N | P | kernel_math | **keep_name** | Ω-WEALTH-04 |
| 66 | 9819 | `wealth_energy_productivity()` | `wealth_energy_productivity` | N | P | kernel_math | **keep_name** | Ω-WEALTH-05 |
| 67 | 9912 | `wealth_time_discount()` | `wealth_time_discount` | N | P | kernel_math | **keep_name** | Ω-WEALTH-06 |
| 68 | 9939 | `wealth_inertia_leverage()` | `wealth_inertia_leverage` | N | P | personal_finance | **keep_name** | Ω-WEALTH-07 |
| 69 | 10011 | `wealth_field_macro()` | `wealth_field_macro` | N | S | market_data | **keep_name** | Ω-WEALTH-08, stateful macro |
| 70 | 10143 | `wealth_signal_information()` | `wealth_signal_information` | N | S | kernel_math | **keep_name** | Ω-WEALTH-09 |
| 71 | 10312 | `wealth_game_coordination()` | `wealth_game_coordination` | N | P | kernel_math | **keep_name** | Ω-WEALTH-10 |
| 72 | 10372 | `wealth_boundary_governance()` | `wealth_boundary_governance` | N | G | governance | **keep_name** | Ω-WEALTH-11 |
| 73 | 10816 | `wealth_hysteresis_ledger()` | `wealth_hysteresis_ledger` (absorbed) | N | S | governance | **absorbed into wealth_omni_wisdom (mode='hysteresis')** | Will be one of the 3 modes of `wealth_omni_wisdom`. Original Ω-WEALTH-12 capability preserved as `mode='hysteresis'`. |
| 74 | 10850 | `wealth_system_registry_status()` | `wealth_system_registry_status` | N | P | governance | **keep_name** | Registry probe, stateless |
| 75 | 10866 | `wealth_synthesize()` | `wealth_synthesize` (absorbed) | N | S | kernel_math | **absorbed into wealth_omni_wisdom (mode='synthesize')** | Will be one of the 3 modes of `wealth_omni_wisdom`. Original Ω-WEALTH-00 capability preserved as `mode='synthesize'`. |

### Section H — Ω-INEQUALITY (L11596, L12150)

| # | Line | Function | Exposed | N/U | S/P/G/H | Family | Disposition | Notes |
|---|---|---|---|---|---|---|---|---|
| 76 | 11596 | `wealth_role_scarcity_risk()` | `wealth_role_scarcity_risk` | N | S | kernel_math | **keep_name** | Inequality risk |
| 77 | 12150 | `wealth_inequality_kernel()` | `wealth_inequality_kernel` | N | S | kernel_math | **keep_name** | Ω-WEALTH-IEQ-00 |

### Section I — Ω-DEAL L3 Ghost Tools (L12377–L12497) — **REGISTRATION FAILURE**

| # | Line | Function | Exposed | N/U | S/P/G/H | Family | Disposition | Notes |
|---|---|---|---|---|---|---|---|---|
| 78 | 12377 | `wealth_screen_opportunity()` | (not live) | N | S | personal_finance | **keep_name + DEBUG** | In `_KNOWN_MISSING` set, silent registration failure |
| 79 | 12405 | `wealth_compute_viability()` | (not live) | N | S | personal_finance | **keep_name + DEBUG** | Same |
| 80 | 12437 | `wealth_score_risk()` | (not live) | N | S | personal_finance | **keep_name + DEBUG** | Same |
| 81 | 12466 | `wealth_compare_scenarios()` | (not live) | N | S | personal_finance | **keep_name + DEBUG** | Same |
| 82 | 12497 | `wealth_emit_investment_memo()` | (not live) | N | S | personal_finance | **keep_name + DEBUG** | Same |

**The 5 L3 ghost tools are the most important bug in this audit.** They're declared in `WEALTH_PUBLIC_TOOL_ORDER` (the canonical surface) but their `@mcp.tool` decorators silently fail to register. They DO NOT appear in the live runtime. A user reading the manifest expects them to be callable, but the runtime returns no such tool. This is a real silent failure that the `_KNOWN_MISSING` set was added to MASK, not fix.

**Recommended next action (separate 888_HOLD):** investigate the silent registration failure. Likely a FastMCP signature issue, async return type mismatch, or import-order bug. These are LEGITIMATE tools, not duplicates.

### Remaining 2 decorators

The grep counted 84 total but my parser found 82. The 2 missing are likely the 2 multi-line `@mcp.tool(name="...", description="...", ...)` decorators that span multiple lines. Need a more sophisticated parser to find them. Noted as a follow-up — **the live/runtime count of 44 is unchanged by these 2 either way.**

---

## Findings Summary (Path C verdict)

### 1. ✅ Most unnamed tools are LEGITIMATE
The 49 unnamed `@mcp.tool()` decorators are mostly stateless math functions that **should** be in the surface. The audit's default-to-hide heuristic over-counted the smell. Most of these are clean.

### 2. 🔴 4 VAULT leaks (governance violation)
`vault_write`, `vaultwrite`, `vault_query`, `vaultquery` (Section D) are the most serious finding. **Disposition: remove all 4.** WEALTH should not expose vault access to MCP. Vault access should route through arifOS kernel (`arif_vault_seal`).

### 3. 🟡 1 typo: `wealth mass_networth` (space in function name)
L7355. Auto-exposes to a malformed name. FastMCP likely de-dupes with the canonical `wealth_net_worth_snapshot` but the malformed name is a code smell. **Disposition: remove.** The canonical snapshot tool already exists.

### 4. 🟡 1 duplicate: `wealth_runway_calculate` registered twice
L1071 and L3761. L3761 is the "Legacy Wrappers" duplicate per the L3756 comment. **Disposition: hide the legacy copy.**

### 5. 🔴 5 L3 ghost tools: registration silently fails
`wealth_screen_opportunity`, `wealth_compute_viability`, `wealth_score_risk`, `wealth_compare_scenarios`, `wealth_emit_investment_memo`. They're in the canonical surface but don't register. **Disposition: keep_name + DEBUG.** This is a separate bug to fix.

### 6. ⚪ 32 v1 functions in `_ALIAS_DISPATCH` (L12658-12694)
These reference v1-named functions that mostly never get aliased (only those matching v2 canonical map survive). Per L12655 comment: "v1 legacy layer retired (P1-1)". The 32 v1 functions are mostly internal helpers. **Disposition: keep, they're already correctly excluded from the live surface.**

---

## Module Federation Blueprint (next-step output)

Based on the classification, the natural module boundaries for **Reading A (one organ, one port 8082, modules as imports)** are:

| Module | Function count | What it owns |
|---|---|---|
| `internal/engines/kernel_math.py` | ~22 (Sections C, E, G) | NPV, IRR, EMV, payback, density, MC, EVOI, time, entropy, conservation, gradient, signal, game, field, plus the synthesis (75) |
| `internal/engines/market_data.py` | ~5 (Sections A, F, plus #56 sensor_fetch) | fx_rate, commodity_price, macro_indicator, sense_ingest, sensor_fetch |
| `internal/engines/personal_finance.py` | ~14 (Sections A, B, C, F) | cashflow_track/summary, runway_calculate, net_worth_snapshot, epf_project, zakat_calculate, survival_engine/liquidity/leverage, allocate_optimize, agent_path, preference_rank |
| `internal/engines/governance.py` | ~15 (Sections C, D, E, F) | All ledger_*, vault_* (TO BE REMOVED), boundary_*, governance_verdict, rule_enforce, hysteresis_ledger, audit, institution_score |
| `internal/engines/personal_finance.py` (continued) | (deal frame) | deal_frame, screen_opportunity, compute_viability, score_risk, compare_scenarios, emit_investment_memo (the 5 ghost L3 + #38) |
| `internal/engines/civilization.py` | ~5 (Sections C, E, H) | inequality_kernel, role_scarcity_risk, stewardship_civilization, future_steward, plus the synthesis hub |
| `internal/utils/health.py` | 1 (Section A #10) | mcp_health_check → wealth_health_check |

Total: ~62 legitimate surface tools. The 5 ghost L3 + 4 vault-leak + 1 typo = 10 to remove/hide, bringing live surface to ~44–49 (with the 5 ghost L3 fixed back to 49).

---

## Future Consolidation: `wealth_omni_wisdom` (888_HOLD pending Path D)

**Status:** Mode design SEALED 2026-06-03 by Arif Fazil + Perplexity audit frame.
**Implementation:** 888_HOLD — Path D module federation is the execution vehicle.

### The consolidation

Three existing tools (Ω-WEALTH-00, Ω-DEAL-00, Ω-WEALTH-12) become modes of one new tool `wealth_omni_wisdom`. Net: -2 tools from the live surface (44 → 42 once Path D lands).

| Old tool | ω-tag | New mode |
|---|---|---|
| `wealth_synthesize` | Ω-WEALTH-00 | `mode='synthesize'` |
| `wealth_deal_frame` | Ω-DEAL-00 | `mode='deal'` |
| `wealth_hysteresis_ledger` | Ω-WEALTH-12 | `mode='hysteresis'` |
| (new) | (new) | `mode='omni'` — parallel fan-out, all three combined |

### Input contract (unified schema)

```python
{
  "mode": "synthesize" | "deal" | "hysteresis" | "omni",   # required
  "decision_context": {                                       # required for all modes
    "description": str,
    "capital_type": str,         # financial | temporal | cognitive | social | ecological | strategic | thermodynamic
    "horizon": str,              # e.g. "3Y", "10Y", "perpetual"
    "entropy_signal": float,     # optional
    "risk_regime": str           # optional — GO | HOLD | STOP
  },
  "deal_params": {               # required only for mode='deal' | 'omni'
    "structure": str,
    "counterparty_profile": str,
    "term_sheet_summary": str
  },
  "path_params": {               # required only for mode='hysteresis' | 'omni'
    "prior_path_id": str,
    "current_state": str,        # GROWTH | PLATEAU | REVERSION | COLLAPSE
    "transition_signal": str
  }
}
```

### Output contract (structured bundle)

```json
{
  "wisdom_verdict": "SEAL | HOLD | STOP",
  "confidence": 0.0–1.0,
  "epistemic_tag": "CLAIM | PLAUSIBLE | HYPOTHESIS | ESTIMATE",
  "synthesis":    { "omega_verdict": "Ω-WEALTH-00", "capital_score": float, "conversion_integrity": "CLEAN | CAPTURED | DEGRADED", "summary": str },
  "deal":         { "omega_verdict": "Ω-DEAL-00",   "deal_score": float,    "structure_verdict": str, "risk_flags": [str] },
  "hysteresis":   { "omega_path": "Ω-WEALTH-12",   "path_state": "GROWTH | PLATEAU | REVERSION | COLLAPSE", "hysteresis_risk": float, "transition_recommendation": str },
  "telemetry":    { "mode_executed": str, "parallel": bool, "tokens_estimated": int, "dS": float }
}
```

### Execution model

For `mode='omni'`: three sub-engines run in parallel (asyncio.gather or threading), results fused at the `wisdom_verdict` layer. **Constitutional floor: F01 Reversibility governs** — if any sub-engine returns STOP, the top-level `wisdom_verdict` is STOP regardless of the other two outputs.

### Live count delta (cumulative)

| State | Count |
|---|---|
| Current (PR #17 + Path C live) | 44 |
| After `wealth_omni_wisdom` consolidation | 42 |
| After + 5 L3 ghost tools fixed (DEBUG, separate issue) | 47 |
| After + 4 VAULT leaks removed (PR X, separate) | 43 |
| After + 1 typo + 1 duplicate fixed (PR X, separate) | 41 |
| **End state target (post-omni + post-cleanup)** | **38** |

### Authoritative sources (mode design ratified from)

- **Anthropic engineering:** ["Writing effective tools for agents"](https://www.anthropic.com/engineering/writing-tools-for-agents) — unambiguous parameter names, strict data models
- **MCP spec 2025-06-18:** tool consolidation pattern (mode enum on inputSchema)
- **Arcade.dev:** 54 MCP tool patterns (anti-pattern: granular sub-modes like `omni.synthesize_only`)
- **Klavis:** Workflow-Based Design — tools around complete user goals

---

## What Path C does NOT do (by design)

This audit is **diagnostic only**. It does NOT:
- Edit any decorator
- Move any function
- Rename anything
- Touch runtime behavior

**Next-step Path D** (Module Federation, Reading A) will use this classification to:
1. Move functions into engine modules (stateful + governance stay close to root)
2. Replace `@mcp.tool` imports with `from internal.engines.X import tool_X as wealth_X`
3. Update `WEALTH_PUBLIC_TOOL_ORDER` to match the new structure
4. Verify via `pytest tests/ -q` (66 passing) and `sync_manifest.py` (44 tools live)

Path D stays **888_HOLD** until this audit is reviewed and the dispositions are SEALed by Arif.

---

DITEMPA BUKAN DIBERI — 999 SEAL ALIVE
SEAL: 888_HOLD on 2026-06-03 by Arif Fazil (Path C diagnostic)
