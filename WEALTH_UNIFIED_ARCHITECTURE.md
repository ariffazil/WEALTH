# WEALTH MCP — Unified Architecture & Next Horizon Blueprint

**Author:** AGI OPENCLAW + Hermes ASI  
**Date:** 2026-05-07  
**Status:** PROPOSED — awaiting Arif SEAL  
**Source of Truth:** `/root/WEALTH/internal/monolith.py` (v2026.05.02)

---

## Executive Summary

WEALTH currently exposes **47 tools** (13 canonical + 6 domain + 2 vault + 25 legacy aliases + 1 health), **13 resources**, and **0 prompts**.

The problem isn't quantity — it's **category impurity**. Many "tools" are orchestration wrappers that should be prompts. The naming mixes abstraction levels (`reason_`, `mind_`, `survival_`).

**Target architecture:**

| Primitive | Current | Proposed |
|-----------|---------|----------|
| **Tools** | 47 exposed (many are wrappers) | **36 atomic tools** |
| **Prompts** | 0 | **12 reasoning workflows** |
| **Resources** | 13 | **21 readable contexts** |

**Naming convention:** `wealth_<physics_dimension>_<economic_operation>`

---

## Part I — Current State (What Exists Today)

### A. Monolith Tools (`internal/monolith.py`)

#### 13 Canonical Tools (decorated `@mcp.tool()`)

| # | Current Name | Internal Engine(s) | Mode Dispatch |
|---|---|---|---|
| 1 | `mcp_health_check` | — | — |
| 2 | `wealth_future_value` | `measurement_npv`, `measurement_irr`, `measurement_pi`, `measurement_payback` | `npv`, `irr`, `pi`, `payback` |
| 3 | `wealth_present_expect` | `emv_risk` | `emv` |
| 4 | `wealth_future_simulate` | `monte_carlo_forecast` | `simulate` |
| 5 | `wealth_survival_liquidity` | `cashflow_flow`, `crisis_triage`, `growth_velocity` | `liquidity`, `runway`, `triage` |
| 6 | `wealth_survival_leverage` | `dscr_leverage`, `networth_state` | `dscr`, `networth` |
| 7 | `wealth_info_value` | `wealth_evoi_compute`, `wealth_evoi_monte_carlo` | `evoi`, `evoi_mc` |
| 8 | `wealth_truth_validate` | `wealth_schema_validate`, `wealth_correlation_guard_check`, `audit_entropy` | `schema`, `correlation`, `entropy` |
| 9 | `wealth_rule_enforce` | `check_floors_tool`, `policy_audit`, `audit_entropy` | `floors`, `policy`, `entropy` |
| 10 | `wealth_allocate_optimize` | `wealth_score_kernel`, `personal_decision`, `agent_budget` | `kernel`, `personal`, `agent` |
| 11 | `wealth_game_coordinate` | `coordination_equilibrium`, `game_theory_solve` | `equilibrium`, `game` |
| 12 | `wealth_sense_ingest` | `ingest_fetch`, `ingest_snapshot`, `ingest_sources`, `ingest_health`, `ingest_vintage`, `ingest_reconcile` | `fetch`, `snapshot`, `sources`, `health`, `vintage`, `reconcile` |
| 13 | `wealth_past_record` | `wealth_init_tool`, `record_transaction_tool`, `snapshot_portfolio_tool` | `init`, `record`, `snapshot` |
| 14 | `wealth_future_steward` | `civilization_stewardship` | `steward` |
| 15 | `vault_write` | VAULT999 append | — |
| 16 | `vault_query` | Supabase REST query | — |

#### 6 Domain Tools (`mcp/server.py`)

| Tool | Domain |
|------|--------|
| `wealth_evaluate_prospect` | Oil & gas EMV (GEOX bridge) |
| `markets_analyze_ticker` | Equity analysis |
| `markets_portfolio_stress_test` | Portfolio stress testing |
| `energy_crisis_assess` | Energy crisis severity |
| `energy_shortage_predict` | Energy shortage prediction |
| `food_security_index` | Food security index |

#### 25 Legacy V2 Aliases

Thin wrappers that dispatch to canonical engines. Examples:
`wealth_sense_fetch` → `ingest_fetch`, `wealth_mind_emv` → `emv_risk`, `wealth_reason_npv` → `measurement_npv`, etc.

### B. Resources (13 total)

| URI | Content |
|-----|---------|
| `wealth://doctrine/valuation` | WEALTH motto + protocol version |
| `wealth://dimensions/definitions` | 9-dimension definitions |
| `wealth://governance/floors` | F1–F13 Constitutional Floors |
| `wealth://governance/harness-doctrines` | 9-Harness constraint architecture |
| `wealth://topology/families` | 6 Sovereign Families |
| `wealth://topology/scales` | 8 Capital Scales |
| `wealth://epistemic/uncertainty-matrix` | Omega₀, kappa_r, humility_band |
| `market://{ticker}/fundamentals` | Real-time equity fundamentals |
| `energy://{region}/realtime-mix` | Real-time energy production mix |
| `food://global/prices` | FAO food price index |

### C. Prompts

**None.** This is the primary gap.

---

## Part II — The Problem: Category Impurity

The 13 canonical tools are **umbrella dispatchers**, not atomic tools. Each one multiplexes 2–6 internal engines via a `mode` parameter.

This creates problems:
1. **LLM confusion** — model must guess correct `mode` string
2. **Governance blur** — `wealth_rule_enforce` has 3 different risk profiles in one tool
3. **Registry noise** — 25 aliases exist because the canonical tools are too broad
4. **No reasoning scaffolding** — orchestration lives inside tools, not prompts

**The fix:** Decompose umbrella tools into atomic tools. Move orchestration to prompts.

---

## Part III — Proposed Architecture (Physics-First Naming)

### Naming Convention

```
wealth_<physics_dimension>_<economic_operation>
```

| Slot | Meaning | Examples |
|------|---------|----------|
| `wealth` | MCP namespace | — |
| `<dimension>` | Physics-inspired abstraction | `value`, `energy`, `flow`, `entropy`, `signal`, `field`, `mass`, `gravity`, `pressure`, `velocity`, `boundary`, `sensor`, `ledger` |
| `<operation>` | Economic computation/action | `npv`, `irr`, `cashflow`, `audit`, `evoi`, `game`, `fetch`, `write` |

### A. Proposed Tools (36)

#### Value / Time Tools (4)

| New Name | Old Source | What It Does |
|----------|-----------|--------------|
| `wealth_value_npv` | `measurement_npv` | Net Present Value calculation |
| `wealth_energy_irr` | `measurement_irr` | Internal Rate of Return |
| `wealth_density_pi` | `measurement_pi` | Profitability Index |
| `wealth_time_payback` | `measurement_payback` | Payback period |

#### Probability / Information Tools (5)

| New Name | Old Source | What It Does |
|----------|-----------|--------------|
| `wealth_expectation_emv` | `emv_risk` | Expected Monetary Value |
| `wealth_probability_monte_carlo` | `monte_carlo_forecast` | Stochastic simulation |
| `wealth_signal_evoi` | `wealth_evoi_compute` | Expected Value of Information |
| `wealth_signal_evoi_mc` | `wealth_evoi_monte_carlo` | EVOI with Monte Carlo |
| `wealth_coupling_correlation` | `wealth_correlation_guard_check` | Coupled-system risk |

#### Survival / Balance Sheet Tools (6)

| New Name | Old Source | What It Does |
|----------|-----------|--------------|
| `wealth_flow_cashflow` | `cashflow_flow` | Cash flow projection |
| `wealth_velocity_runway` | `growth_velocity` | Compound velocity / runway |
| `wealth_gravity_dscr` | `dscr_leverage` | Debt Service Coverage Ratio |
| `wealth_mass_networth` | `networth_state` | Balance sheet mass |
| `wealth_pressure_triage` | `crisis_triage` | Emergency pressure relief |
| `wealth_stewardship_civilization` | `civilization_stewardship` | Long-horizon continuity |

#### Truth / Measurement Tools (2)

| New Name | Old Source | What It Does |
|----------|-----------|--------------|
| `wealth_measurement_schema` | `wealth_schema_validate` | Schema validity check |
| `wealth_entropy_audit` | `audit_entropy` | Noise / uncertainty audit |

#### Governance Tools (3)

| New Name | Old Source | What It Does |
|----------|-----------|--------------|
| `wealth_boundary_floors` | `check_floors_tool` | F1–F13 boundary check |
| `wealth_boundary_policy` | `policy_audit` | Rule constraint audit |
| `wealth_governance_verdict` | `wealth_score_kernel` | Final allocation verdict |

#### Allocation / Coordination Tools (4)

| New Name | Old Source | What It Does |
|----------|-----------|--------------|
| `wealth_field_game` | `game_theory_solve` | Multi-agent game theory |
| `wealth_field_equilibrium` | `coordination_equilibrium` | Nash equilibrium |
| `wealth_preference_rank` | `personal_decision` | Personal utility ranking |
| `wealth_agent_path` | `agent_budget` | Resource-constrained agent path |

#### Sensor / Data Intake Tools (6)

| New Name | Old Source | What It Does |
|----------|-----------|--------------|
| `wealth_sensor_fetch` | `ingest_fetch` | Real-world data probe |
| `wealth_sensor_snapshot` | `ingest_snapshot` | State observation |
| `wealth_sensor_reconcile` | `ingest_reconcile` | Sensor divergence check |
| `wealth_sensor_health` | `ingest_health` | Instrument health |
| `wealth_sensor_vintage` | `ingest_vintage` | Historical measurement state |
| `wealth_sensor_sources` | `ingest_sources` | Sensor inventory |

#### Ledger / Vault Tools (5)

| New Name | Old Source | What It Does |
|----------|-----------|--------------|
| `wealth_ledger_query` | `vault_query` | Read conserved record |
| `wealth_ledger_write` | `vault_write` | Irreversible state transition (F01 guarded) |
| `wealth_ledger_init` | `wealth_init_tool` | Session boundary initialization |
| `wealth_ledger_record` | `record_transaction_tool` | Structured transaction write |
| `wealth_ledger_snapshot` | `snapshot_portfolio_tool` | Portfolio state snapshot |

#### Health (1)

| New Name | Old Source | What It Does |
|----------|-----------|--------------|
| `mcp_health_check` | `mcp_health_check` | Transport + system health |

**Total: 36 atomic tools**

---

### B. Proposed Prompts (12)

These are **reasoning workflows** — they orchestrate multiple tools into governed sequences.

| Prompt | Orchestrates | Purpose |
|--------|-------------|---------|
| `wealth_appraise_project` | `value_npv` + `energy_irr` + `density_pi` + `time_payback` + `boundary_floors` | Full project valuation under governance |
| `wealth_judge_allocation` | `governance_verdict` + `boundary_floors` + `boundary_policy` | Governed capital allocation decision |
| `wealth_run_survival_audit` | `flow_cashflow` + `velocity_runway` + `gravity_dscr` + `mass_networth` + `pressure_triage` | Complete survival health check |
| `wealth_run_information_audit` | `signal_evoi` + `signal_evoi_mc` + `entropy_audit` + `measurement_schema` | Information value + noise assessment |
| `wealth_run_macro_snapshot` | `sensor_fetch` + `sensor_snapshot` + `sensor_reconcile` | Full market/macro data intake |
| `wealth_run_game_coordination` | `field_game` + `field_equilibrium` + `preference_rank` + `agent_path` | Multi-agent coordination analysis |
| `wealth_diagnose_portfolio` | `mass_networth` + `flow_cashflow` + `entropy_audit` + `boundary_floors` | Portfolio health diagnosis |
| `wealth_crisis_triage` | `pressure_triage` + `flow_cashflow` + `velocity_runway` | Crisis classification + priority |
| `wealth_opportunity_ranking` | `expectation_emv` + `signal_evoi` + `entropy_audit` | Rank prospects by expected value |
| `wealth_allocation_rebalance` | `governance_verdict` + `preference_rank` + `boundary_policy` | Propose rebalancing |
| `wealth_governance_full_audit` | `boundary_floors` + `boundary_policy` + `entropy_audit` | F1–F13 full audit |
| `wealth_record_governed_event` | `ledger_record` + `ledger_snapshot` + `boundary_floors` | Governed vault write with full trail |

**Total: 12 prompts**

---

### C. Proposed Resources (21)

#### Schemas (5)

| URI | Content |
|-----|---------|
| `wealth://schemas/prospect_metrics` | Prospect evaluation output schema |
| `wealth://schemas/cashflow_project` | Cash flow projection schema |
| `wealth://schemas/portfolio` | Portfolio state schema |
| `wealth://schemas/vault_event` | VAULT999 event schema |
| `wealth://schemas/governance_verdict` | Verdict output schema |

#### Policies (4)

| URI | Content |
|-----|---------|
| `wealth://policy/f1_f13_floors` | F1–F13 Constitutional Floors |
| `wealth://policy/allocation_constraints` | Allocation boundary conditions |
| `wealth://policy/vault_irreversibility` | Irreversible action policy |
| `wealth://policy/final_authority_arif` | Human sovereign authority contract |

#### Formulas (6)

| URI | Content |
|-----|---------|
| `wealth://formulas/npv` | NPV mathematical definition |
| `wealth://formulas/irr` | IRR definition + edge cases |
| `wealth://formulas/emv` | EMV probability-weighted formula |
| `wealth://formulas/evoi` | EVOI decision-theoretic formula |
| `wealth://formulas/dscr` | DSCR ratio definition |
| `wealth://formulas/payback` | Payback period formula |

#### Ontology (3)

| URI | Content |
|-----|---------|
| `wealth://ontology/physics_economics_map` | Complete physics ↔ economics analogy table |
| `wealth://ontology/dimensions` | 9 canonical dimensions |
| `wealth://ontology/verdict_labels` | SEAL / HOLD / VOID / SABAR definitions |

#### State / Vault (2)

| URI | Content |
|-----|---------|
| `wealth://vault/latest_seal` | Last VAULT999 seal state |
| `wealth://vault/session_state` | Current session state |

#### Sources (1)

| URI | Content |
|-----|---------|
| `wealth://sources/adapter_status` | Data adapter health status |

**Total: 21 resources**

---

## Part IV — Migration Path

### Phase 1: Fix the MCP Handshake (Day 1)

Add `initialize` handler to WEALTH's FastMCP so OpenClaw can reconnect:

```python
# In server.py or internal/monolith.py
# FastMCP should handle this natively with:
mcp = FastMCP("wealth", stateless_http=True, json_response=True)
```

If FastMCP version doesn't support it natively, add explicit handler.

**Result:** WEALTH returns to OpenClaw bundle with existing 47 tools.

### Phase 2: Decompose Umbrella Tools (Week 1-2)

1. Each internal engine becomes a standalone `@mcp.tool()` with physics-first naming
2. Old canonical tools become **prompts** that orchestrate the new atomic tools
3. Legacy V2 aliases are deprecated (kept for 1 release, then removed)

**Migration table for the 13 canonical tools:**

| Current Tool | Becomes | Why |
|---|---|---|
| `wealth_future_value` | **Prompt** `wealth_appraise_project` | Dispatches 4 atomic value tools |
| `wealth_present_expect` | **Tool** `wealth_expectation_emv` | Already atomic |
| `wealth_future_simulate` | **Tool** `wealth_probability_monte_carlo` | Already atomic |
| `wealth_survival_liquidity` | **Prompt** `wealth_run_survival_audit` | Dispatches 3 tools |
| `wealth_survival_leverage` | Split → `wealth_gravity_dscr` + `wealth_mass_networth` | Two distinct tools |
| `wealth_info_value` | Split → `wealth_signal_evoi` + `wealth_signal_evoi_mc` | Two distinct tools |
| `wealth_truth_validate` | **Prompt** `wealth_run_information_audit` | Orchestrates 3 tools |
| `wealth_rule_enforce` | **Prompt** `wealth_governance_full_audit` | Orchestrates 3 tools |
| `wealth_allocate_optimize` | **Prompt** `wealth_judge_allocation` | Orchestrates 3 tools |
| `wealth_game_coordinate` | **Prompt** `wealth_run_game_coordination` | Orchestrates 2 tools |
| `wealth_sense_ingest` | **Prompt** `wealth_run_macro_snapshot` | Orchestrates 6 tools |
| `wealth_past_record` | **Prompt** `wealth_record_governed_event` | Orchestrates 3 tools |
| `wealth_future_steward` | **Tool** `wealth_stewardship_civilization` | Already atomic |

### Phase 3: Resource Expansion (Week 2-3)

Move schemas, formulas, policies from hardcoded strings inside tool docstrings → proper `@mcp.resource()` declarations.

### Phase 4: Retire Aliases (Week 4)

Remove 25 V2 aliases. Clean registry = clean governance.

---

## Part V — Final Count

| | Current | After Migration |
|---|---|---|
| **Tools** | 47 (noisy, overlapping) | **36** (atomic, orthogonal) |
| **Prompts** | 0 | **12** (reasoning workflows) |
| **Resources** | 13 | **21** (schemas, policies, formulas, ontology, state) |
| **Legacy aliases** | 25 | **0** (retired) |

### The Physics ↔ Economics Directory

```
WEALTH MCP
├── tools/                          (36 atomic executors)
│   ├── value/                      (4) npv, irr, pi, payback
│   ├── probability/                (5) emv, monte_carlo, evoi, evoi_mc, correlation
│   ├── survival/                   (6) cashflow, runway, dscr, networth, triage, civilization
│   ├── truth/                      (2) schema, entropy_audit
│   ├── governance/                 (3) floors, policy, verdict
│   ├── allocation/                 (4) game, equilibrium, preference, agent_path
│   ├── sensor/                     (6) fetch, snapshot, reconcile, health, vintage, sources
│   ├── ledger/                     (5) query, write, init, record, snapshot
│   └── health/                     (1) mcp_health_check
│
├── prompts/                        (12 reasoning workflows)
│   ├── wealth_appraise_project
│   ├── wealth_judge_allocation
│   ├── wealth_run_survival_audit
│   ├── wealth_run_information_audit
│   ├── wealth_run_macro_snapshot
│   ├── wealth_run_game_coordination
│   ├── wealth_diagnose_portfolio
│   ├── wealth_crisis_triage
│   ├── wealth_opportunity_ranking
│   ├── wealth_allocation_rebalance
│   ├── wealth_governance_full_audit
│   └── wealth_record_governed_event
│
├── resources/                      (21 readable contexts)
│   ├── schemas/                    (5)
│   ├── policies/                   (4)
│   ├── formulas/                   (6)
│   ├── ontology/                   (3)
│   ├── vault/                      (2)
│   └── sources/                    (1)
│
└── domain/                         (6 civilization tools — keep as-is)
    ├── wealth_evaluate_prospect
    ├── markets_analyze_ticker
    ├── markets_portfolio_stress_test
    ├── energy_crisis_assess
    ├── energy_shortage_predict
    └── food_security_index
```

**Grand total surface: 36 + 6 domain = 42 tools | 12 prompts | 21 resources**

---

## Part VI — Doctrine

> **Physics** supplies the abstraction (what dimension are we measuring).  
> **Economics** supplies the operation (what decision does this serve).  
> **MCP** supplies the interface (tool = action, prompt = reasoning path, resource = knowledge).

### Rules

1. Every tool performs ONE atomic computation or action
2. Orchestration lives in prompts, not tools
3. Physics dimension names are substrate-level (never descriptive fluff)
4. F01 AMANAH: every `ledger_write` is irreversible and audited
5. F13 SOVEREIGN: `governance_verdict` is system recommendation — Arif decides
6. No new aliases after Phase 4 — atomic tools only
7. Resources are readable context, never executable

---

**DITEMPA BUKAN DIBERI — Forged, Not Given.**

*Awaiting Arif SEAL to begin Phase 1.*
