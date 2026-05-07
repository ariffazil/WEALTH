# WEALTH MCP — Architecture Refactor Blueprint

**Status:** DESIGN APPROVED — Pending Implementation
**Author:** Arif Fazil + Hermes ASI
**Date:** 2026-05-07
**DITETPA BUKAN DIBERI — Forged, Not Given

---

## 1. Problem Statement

WEALTH MCP currently exposes **50 tools** via a single `@mcp.tool()` decorator layer and a `V2_CANONICAL_MAP` that aliases 32 v1 functions to v2 names. The result:

- **Category impurity:** tools, orchestration wrappers, and prompts all dumped as `@mcp.tool()`
- **Naming noise:** `wealth_reason_npv`, `wealth_survival_cashflow`, `wealth_mind_evoi` — mixed semantic layers
- **Duplication:** `wealth_npv_reward` and `wealth_reason_npv` are aliases for the same function
- **Zero prompts:** all reasoning workflows are forced into tool form
- **Zero resources:** schemas, formulas, policy docs live only in docstrings

The fix is not "fewer tools." The fix is **correct MCP primitive allocation:**
tool = action. prompt = reasoning path. resource = knowledge/state.

---

## 2. Physics ↔ Economics Ontology

WEALTH's core metaphor: economics is to capital what physics is to matter. This is a **disciplined analogy**, not literal ontology.

### 2.1 Dimension Map

| Physics concept | Economic analogue | WEALTH domain |
|---|---|---|
| Mass | Net worth / accumulated capital | `mass` |
| Energy | Return potential / capacity to do economic work | `energy` |
| Flow | Cash movement / metabolic liquidity | `flow` |
| Velocity | Compounding rate / growth trajectory | `velocity` |
| Gravity | Debt burden / fixed obligations pulling down | `gravity` |
| Pressure | Liquidity stress / survival compression | `pressure` |
| Entropy | Uncertainty / noise / decision degradation | `entropy` |
| Signal | Information value / low-noise evidence | `signal` |
| Field | Multi-agent incentives / game equilibrium | `field` |
| Boundary | Governance constraints / floors | `boundary` |
| Sensor | Data intake / market measurement | `sensor` |
| Ledger | Immutable record / conserved state | `ledger` |
| Density | Concentration ratio / efficiency | `density` |
| Time | Payback horizon / recovery period | `time` |

### 2.2 Naming Convention

```
wealth_<dimension>_<operation>
```

- `wealth` = MCP namespace
- `<dimension>` = physics-inspired economic abstraction
- `<operation>` = what the tool does

**Examples:**
- `wealth_value_npv` — value dimension, NPV operation
- `wealth_energy_irr` — energy dimension, IRR operation
- `wealth_mass_networth` — mass dimension, net worth operation
- `wealth_flow_cashflow` — flow dimension, cash flow operation
- `wealth_gravity_dscr` — gravity dimension, DSCR operation
- `wealth_entropy_audit` — entropy dimension, audit operation
- `wealth_signal_evoi` — signal dimension, EVOI operation
- `wealth_field_game` — field dimension, game theory operation
- `wealth_sensor_fetch` — sensor dimension, data fetch operation
- `wealth_ledger_write` — ledger dimension, write operation

---

## 3. Current Tool Inventory (50 tools)

### 3.1 Registered via `@mcp.tool()` decorators (16 direct)

These are the umbrella/orchestration tools — the ones flagged for demotion:

| Current name | Line | Type | Action |
|---|---|---|---|
| `mcp_health_check` | 540 | tool | ✅ KEEP — transport health |
| `wealth_future_value` | 3659 | umbrella | ❌ DEMOTE to `wealth_appraise_project` prompt |
| `wealth_present_expect` | 3687 | umbrella | ❌ DEMOTE to `wealth_expectation_emv` prompt |
| `wealth_future_simulate` | 3702 | umbrella | ❌ DEMOTE to `wealth_run_monte_carlo` prompt |
| `wealth_survival_liquidity` | 3727 | umbrella | ❌ DEMOTE — modes to atomic tools |
| `wealth_survival_leverage` | 3757 | umbrella | ❌ DEMOTE — modes to atomic tools |
| `wealth_info_value` | 3783 | umbrella | ❌ DEMOTE to `wealth_run_evoi` prompt |
| `wealth_truth_validate` | 3823 | umbrella | ❌ DEMOTE to `wealth_measurement_validate` prompt |
| `wealth_rule_enforce` | 3846 | umbrella | ❌ DEMOTE to `wealth_boundary_enforce` prompt |
| `wealth_allocate_optimize` | 3893 | umbrella | ❌ DEMOTE to `wealth_allocate_optimal` prompt |
| `wealth_game_coordinate` | 3951 | umbrella | ❌ DEMOTE to `wealth_coordinate_agents` prompt |
| `wealth_sense_ingest` | 3974 | umbrella | ❌ DEMOTE to `wealth_ingest_data` prompt |
| `wealth_past_record` | 4004 | umbrella | ❌ DEMOTE to `wealth_record_event` prompt |
| `wealth_future_steward` | 4064 | umbrella | ❌ DEMOTE to `wealth_steward_long_horizon` prompt |
| `vault_write` | 4097 | tool | ✅ KEEP — ledger append (irreversible write) |
| `vault_query` | 4158 | tool | ✅ KEEP — ledger read |

### 3.2 Registered via `V2_CANONICAL_MAP` (32 atomic tools)

These are the actual computational primitives — most are already correctly designed:

| Current name | Maps to | Dimension | Action |
|---|---|---|---|
| `wealth_sense_fetch` | `wealth_ingest_fetch` | `sensor` | ✅ KEEP |
| `wealth_sense_snapshot` | `wealth_ingest_snapshot` | `sensor` | ✅ KEEP |
| `wealth_sense_reconcile` | `wealth_ingest_reconcile` | `sensor` | ✅ KEEP |
| `wealth_sense_health` | `wealth_ingest_health` | `sensor` | ✅ KEEP |
| `wealth_sense_vintage` | `wealth_ingest_vintage` | `sensor` | ✅ KEEP |
| `wealth_sense_sources` | `wealth_ingest_sources` | `sensor` | ✅ KEEP |
| `wealth_mind_emv` | `wealth_emv_risk` | `expectation` | ⚠️ RENAME → `wealth_expectation_emv` |
| `wealth_mind_monte_carlo` | `wealth_monte_carlo_forecast` | `probability` | ⚠️ RENAME → `wealth_probability_monte_carlo` |
| `wealth_mind_correlation` | `wealth_correlation_guard_check` | `coupling` | ⚠️ RENAME → `wealth_coupling_correlation` |
| `wealth_mind_evoi` | `wealth_evoi_compute` | `signal` | ⚠️ RENAME → `wealth_signal_evoi` |
| `wealth_mind_evoi_mc` | `wealth_evoi_monte_carlo` | `signal` | ⚠️ RENAME → `wealth_signal_evoi_mc` |
| `wealth_mind_schema` | `wealth_schema_validate` | `measurement` | ⚠️ RENAME → `wealth_measurement_schema` |
| `wealth_survival_dscr` | `wealth_dscr_leverage` | `gravity` | ⚠️ RENAME → `wealth_gravity_dscr` |
| `wealth_survival_networth` | `wealth_networth_state` | `mass` | ⚠️ RENAME → `wealth_mass_networth` |
| `wealth_survival_velocity` | `wealth_growth_velocity` | `velocity` | ⚠️ RENAME → `wealth_velocity_runway` |
| `wealth_survival_cashflow` | `wealth_cashflow_flow` | `flow` | ⚠️ RENAME → `wealth_flow_cashflow` |
| `wealth_survival_triage` | `wealth_crisis_triage` | `pressure` | ⚠️ RENAME → `wealth_pressure_triage` |
| `wealth_survival_civilization` | `wealth_civilization_stewardship` | `stewardship` | ⚠️ RENAME → `wealth_stewardship_civilization` |
| `wealth_reason_npv` | `wealth_npv_reward` | `value` | ✅ KEEP — rename `wealth_npv_reward` |
| `wealth_npv_reward` | `wealth_npv_reward` | `value` | ❌ RETIRE — duplicate alias |
| `wealth_reason_irr` | `wealth_irr_yield` | `energy` | ⚠️ RENAME → `wealth_energy_irr` |
| `wealth_reason_pi` | `wealth_pi_efficiency` | `density` | ⚠️ RENAME → `wealth_density_pi` |
| `wealth_reason_payback` | `wealth_payback_time` | `time` | ⚠️ RENAME → `wealth_time_payback` |
| `wealth_reason_equilibrium` | `wealth_coordination_equilibrium` | `field` | ⚠️ RENAME → `wealth_field_equilibrium` |
| `wealth_reason_game` | `wealth_game_theory_solve` | `field` | ⚠️ RENAME → `wealth_field_game` |
| `wealth_reason_personal` | `wealth_personal_decision` | `preference` | ⚠️ RENAME → `wealth_preference_rank` |
| `wealth_reason_agent` | `wealth_agent_budget` | `agent` | ⚠️ RENAME → `wealth_agent_path` |
| `wealth_judge_kernel` | `wealth_score_kernel` | `governance` | ⚠️ RENAME → `wealth_governance_verdict` |
| `wealth_judge_floors` | `wealth_check_floors` | `boundary` | ⚠️ RENAME → `wealth_boundary_floors` |
| `wealth_judge_policy` | `wealth_policy_audit` | `boundary` | ⚠️ RENAME → `wealth_boundary_policy` |
| `wealth_judge_entropy` | `wealth_audit_entropy` | `entropy` | ⚠️ RENAME → `wealth_entropy_audit` |
| `wealth_vault_init` | `wealth_init` | `ledger` | ✅ KEEP — rename in ledger group |
| `wealth_vault_record` | `wealth_record_transaction` | `ledger` | ✅ KEEP |
| `wealth_vault_snapshot` | `wealth_snapshot_portfolio` | `ledger` | ✅ KEEP |

---

## 4. Target Architecture

### 4.1 Final Registry Shape

```
WEALTH MCP
├── tools/       (32 atomic executables)
├── prompts/     (8 reasoning workflows)
└── resources/   (20+ stable knowledge items)
```

### 4.2 Target Tools: 32

Organized by physics dimension:

#### Transport (1)
| New name | Operation | Description |
|---|---|---|
| `mcp_health_check` | health | Universal transport health |

#### Value / Energy (5)
| New name | Operation | Physics analogue |
|---|---|---|
| `wealth_value_npv` | npv | Potential energy discounted through time |
| `wealth_energy_irr` | irr | Internal return frequency / energy conversion rate |
| `wealth_density_pi` | pi | Capital concentration ratio |
| `wealth_time_payback` | payback | Recovery half-life |
| `wealth_expectation_emv` | emv | Probability-weighted expected state value |

#### Probability / Simulation (2)
| New name | Operation | Physics analogue |
|---|---|---|
| `wealth_probability_monte_carlo` | monte_carlo | Stochastic particle cloud simulation |
| `wealth_coupling_correlation` | correlation | Coupled-system correlation risk |

#### Signal / Information (2)
| New name | Operation | Physics analogue |
|---|---|---|
| `wealth_signal_evoi` | evoi | Value of information / signal quality |
| `wealth_signal_evoi_mc` | evoi_mc | Distributional EVOI via Monte Carlo |
| `wealth_measurement_schema` | schema | Measurement validity / schema integrity |

#### Flow / Velocity (2)
| New name | Operation | Physics analogue |
|---|---|---|
| `wealth_flow_cashflow` | cashflow | Cash movement / metabolic flow |
| `wealth_velocity_runway` | runway | Compounding trajectory / growth velocity |

#### Mass / Gravity / Pressure (3)
| New name | Operation | Physics analogue |
|---|---|---|
| `wealth_mass_networth` | networth | Accumulated capital / total economic mass |
| `wealth_gravity_dscr` | dscr | Debt burden / gravitational pull |
| `wealth_pressure_triage` | triage | Survival compression / pressure relief |

#### Entropy / Boundary / Governance (4)
| New name | Operation | Physics analogue |
|---|---|---|
| `wealth_entropy_audit` | audit | Decision noise / entropy measurement |
| `wealth_boundary_floors` | floors | F1–F13 governance floor constraints |
| `wealth_boundary_policy` | policy | Policy constraint audit |
| `wealth_governance_verdict` | verdict | Final allocation verdict engine |

#### Field / Coordination (3)
| New name | Operation | Physics analogue |
|---|---|---|
| `wealth_field_game` | game | Multi-agent game theory / incentive field |
| `wealth_field_equilibrium` | equilibrium | Stable state / Nash equilibrium |
| `wealth_preference_rank` | rank | Personal utility ranking |
| `wealth_agent_path` | path | Resource-constrained action path |

#### Sensor / Data (6)
| New name | Operation | Physics analogue |
|---|---|---|
| `wealth_sensor_fetch` | fetch | Market data measurement probe |
| `wealth_sensor_snapshot` | snapshot | Current state observation |
| `wealth_sensor_reconcile` | reconcile | Sensor divergence / divergence check |
| `wealth_sensor_health` | health | Data adapter health |
| `wealth_sensor_vintage` | vintage | Historical measurement state |
| `wealth_sensor_sources` | sources | Sensor inventory / source registry |

#### Ledger / Vault (5)
| New name | Operation | Physics analogue |
|---|---|---|
| `wealth_ledger_query` | query | Immutable record read |
| `wealth_ledger_write` | write | Irreversible state transition |
| `wealth_ledger_init` | init | Session boundary initialization |
| `wealth_ledger_record` | record | Structured transaction write |
| `wealth_ledger_snapshot` | snapshot | Structured computation snapshot |

---

### 4.3 Target Prompts: 8

Prompts are **reasoning rituals** — orchestration patterns that invoke multiple tools and return structured conclusions.

| New prompt name | Invokes | Use case |
|---|---|---|
| `wealth_appraise_project` | `wealth_value_npv`, `wealth_energy_irr`, `wealth_density_pi`, `wealth_time_payback`, `wealth_boundary_floors` | Full investment quality assessment |
| `wealth_run_survival_audit` | `wealth_flow_cashflow`, `wealth_gravity_dscr`, `wealth_mass_networth`, `wealth_pressure_triage` | Liquidity + leverage + solvency audit |
| `wealth_run_evoi` | `wealth_signal_evoi`, `wealth_signal_evoi_mc` | Information value analysis |
| `wealth_measurement_validate` | `wealth_measurement_schema`, `wealth_coupling_correlation`, `wealth_entropy_audit` | Data integrity + epistemic quality check |
| `wealth_judge_allocation` | `wealth_field_game`, `wealth_field_equilibrium`, `wealth_boundary_policy` | Multi-agent allocation judgment |
| `wealth_coordinate_agents` | `wealth_field_game`, `wealth_field_equilibrium`, `wealth_agent_path` | Agent coordination ritual |
| `wealth_steward_long_horizon` | `wealth_probability_monte_carlo`, `wealth_velocity_runway`, `wealth_stewardship_civilization` | Long-horizon civilization stewardship |
| `wealth_record_event` | `wealth_ledger_write`, `wealth_ledger_record`, `wealth_ledger_snapshot` | Governed event recording ritual |

**Prompt registration example:**

```python
@mcp.prompt(title="Appraise Investment Project", description="Run full NPV/IRR/PI/Payback + governance floors on a project proposal")
def wealth_appraise_project(
    project_name: str,
    initial_investment: float,
    cash_flows: list[float],
    discount_rate: float = 0.1,
    terminal_value: float = 0,
    reinvestment_rate: float = 0.1,
    scale_mode: str = "enterprise",
) -> str:
    return f"""Wealth MCP — Project Appraisal Ritual

Given: {project_name}
Investment: {initial_investment} | Rate: {discount_rate} | CFs: {cash_flows}

Step 1: wealth_value_npv
Step 2: wealth_energy_irr  
Step 3: wealth_density_pi
Step 4: wealth_time_payback
Step 5: wealth_boundary_floors

Synthesize a governed verdict: INVEST / HOLD / REJECT.
Arif Fazil is final authority. WEALTH is advisory only.
DITEMPA BUKAN DIBERI."""
```

---

### 4.4 Target Resources: 20+

Readable, stable context — schemas, policies, formulas, ontology, state.

#### Schemas
| Resource URI | Content |
|---|---|
| `wealth://schemas/prospect_metrics` | Input schema for prospect evaluation |
| `wealth://schemas/cashflow_project` | Cash flow projection schema |
| `wealth://schemas/portfolio` | Portfolio snapshot schema |
| `wealth://schemas/vault_event` | Vault event record schema |
| `wealth://schemas/governance_verdict` | Verdict envelope schema |

#### Formulas
| Resource URI | Content |
|---|---|
| `wealth://formulas/npv` | NPV formula + derivation |
| `wealth://formulas/irr` | IRR solving formula + Newton's method notes |
| `wealth://formulas/emv` | Expected Monetary Value formula |
| `wealth://formulas/evoi` | Expected Value of Information formula |
| `wealth://formulas/dscr` | Debt Service Coverage Ratio formula |
| `wealth://formulas/payback` | Payback period formula |
| `wealth://formulas/monte_carlo` | Monte Carlo simulation approach |

#### Policy / Governance
| Resource URI | Content |
|---|---|
| `wealth://policy/f1_f13_floors` | Full F1–F13 floor definitions |
| `wealth://policy/allocation_constraints` | Capital allocation constraints |
| `wealth://policy/vault_irreversibility` | VAULT999 irreversibility rules |
| `wealth://policy/final_authority_arif` | Statement: Arif Fazil is final authority |

#### Ontology
| Resource URI | Content |
|---|---|
| `wealth://ontology/physics_economics_map` | Physics ↔ Economics dimension table |
| `wealth://ontology/dimensions` | Full dimension definitions (mass, flow, entropy, etc.) |
| `wealth://ontology/verdict_labels` | VERDICT label taxonomy |

#### Vault
| Resource URI | Content |
|---|---|
| `wealth://vault/latest_seal` | Most recent VAULT999 seal event |
| `wealth://vault/session_state` | Current session boundary state |

#### Sources
| Resource URI | Content |
|---|---|
| `wealth://sources/adapter_status` | Live data adapter health matrix |

---

## 5. Implementation Plan

### Phase 1: Rename Tools (V2_CANONICAL_MAP rewrite)

**File:** `/root/WEALTH/internal/monolith.py`
**Scope:** Update `V2_CANONICAL_MAP` keys (v2 names only — v1 function names stay the same)
**Risk:** LOW — just dictionary key renaming

Steps:
1. Edit `V2_CANONICAL_MAP` keys to new `wealth_<dimension>_<operation>` names
2. Remove duplicate `wealth_npv_reward` entry
3. Update `_DANGER_MAP` in `tools_handler` to match new names
4. Update `if __name__ == "__main__"` alias block
5. Copy updated file to container: `docker cp internal/monolith.py wealth-organ:/app/internal/monolith.py`
6. Restart container

### Phase 2: Demote Umbrella Tools → Prompts

**File:** `/root/WEALTH/internal/monolith.py`
**Scope:** Replace 12 umbrella `@mcp.tool()` functions with `@mcp.prompt()` decorators
**Risk:** MEDIUM — changes function decorator type

The 12 demotions:

```python
# REPLACE @mcp.tool() WITH @mcp.prompt() FOR:
# wealth_future_value      → wealth_appraise_project (prompt)
# wealth_present_expect     → wealth_expectation_emv  (prompt) 
# wealth_future_simulate   → wealth_run_monte_carlo  (prompt)
# wealth_survival_liquidity → DEMOTE: modes handled by atomic tools
# wealth_survival_leverage  → DEMOTE: modes handled by atomic tools
# wealth_info_value        → wealth_run_evoi          (prompt)
# wealth_truth_validate    → wealth_measurement_validate (prompt)
# wealth_rule_enforce      → wealth_boundary_enforce  (prompt)
# wealth_allocate_optimize → wealth_allocate_optimal  (prompt)
# wealth_game_coordinate   → wealth_coordinate_agents (prompt)
# wealth_sense_ingest      → wealth_ingest_data       (prompt)
# wealth_past_record       → wealth_record_event      (prompt)
# wealth_future_steward    → wealth_steward_long_horizon (prompt)
```

**Note:** `wealth_survival_liquidity` and `wealth_survival_leverage` are fully demoted — their modes (`cashflow`→`wealth_flow_cashflow`, `velocity`→`wealth_velocity_runway`, `triage`→`wealth_pressure_triage`, `dscr`→`wealth_gravity_dscr`, `networth`→`wealth_mass_networth`) are already available as atomic tools.

### Phase 3: Register Resources

**File:** `/root/WEALTH/internal/monolith.py`
**Scope:** Add `@mcp.resource()` decorators for all 20+ resources
**Risk:** LOW — read-only additions

Resources are registered alongside existing `@mcp.resource()` decorators (already 7 exist at lines 3121–3233).

### Phase 4: Verify + Deploy

1. Copy updated `monolith.py` to container
2. Restart `wealth-organ`
3. `curl http://127.0.0.1:8082/mcp` → `tools/list` should show ~32 tools
4. `curl http://127.0.0.1:8082/mcp` → `prompts/list` should show ~8 prompts
5. `curl http://127.0.0.1:8082/mcp` → `resources/list` should show ~20 resources
6. Run `openclaw doctor --non-interactive` → WEALTH handshake should still pass
7. Git commit with message: `WEALTH MCP: physics-inspired naming + tools/prompts/resources restructure`

---

## 6. Count Summary

| Category | Before | After | Change |
|---|---|---|---|
| Tools | 50 | 32 | -18 (demotions) |
| Prompts | 0 | 8 | +8 (new) |
| Resources | 7 | 20+ | +13 (new) |
| Unique capabilities | 50 | ~60 | +10 (better coverage via prompts) |

**Net result:** Smaller, cleaner tool surface. Same economic intelligence depth. Better authority clarity.

---

## 7. Key Design Decisions

### 7.1 Why `wealth_npv_reward` is retired but `wealth_reason_npv` stays

`wealth_reason_npv` maps to `wealth_npv_reward` in the v1 function registry. The `V2_CANONICAL_MAP` has both:
```python
"wealth_reason_npv": "wealth_npv_reward",   # KEEP — canonical name
"wealth_npv_reward": "wealth_npv_reward",   # RETIRE — duplicate alias
```

The alias `"wealth_npv_reward": "wealth_npv_reward"` is redundant — a tool pointing to itself. It should be removed. `wealth_reason_npv` becomes `wealth_value_npv`.

### 7.2 Why `wealth_survival_liquidity` and `wealth_survival_leverage` demote cleanly

These two tools have `mode` parameters that branch to different computations:
- `wealth_survival_liquidity`: `cashflow`→`cashflow_flow`, `velocity`→`growth_velocity`, `triage`→`crisis_triage`
- `wealth_survival_leverage`: `dscr`→`dscr_leverage`, `networth`→`networth_state`

Each mode maps directly to an existing atomic tool. No functionality is lost. The umbrella tool is a pure routing wrapper.

### 7.3 Why `wealth_governance_verdict` is advisory only

The docstring must include: *"This tool produces a system verdict. Arif Fazil is the final authority. WEALTH is advisory only — it does not make sovereign decisions."*

This prevents `wealth_judge_kernel` / `wealth_governance_verdict` from being interpreted as a binding ruling.

### 7.4 Why FastMCP `prompt()` decorator is safe

FastMCP 3.2.4 fully supports `@mcp.prompt()`. The `render_prompt()` method generates the prompt string at runtime. Prompts are stateless — they generate guidance strings, not execute actions.

### 7.5 Why resources are safe

Resources are read-only. They never modify state, never call external APIs, never produce side effects. They are pure knowledge delivery.

---

## 8. Migration Compatibility

Old tool names must remain callable during a transition window:

```python
# In if __name__ == "__main__" block — add deprecated aliases
_migration_aliases = {
    "wealth_future_value": "wealth_appraise_project",
    "wealth_present_expect": "wealth_expectation_emv", 
    "wealth_survival_liquidity": "wealth_flow_cashflow",  # default mode
    "wealth_survival_leverage": "wealth_gravity_dscr",    # default mode
    "wealth_info_value": "wealth_signal_evoi",             # default mode
    "wealth_truth_validate": "wealth_measurement_validate",# default mode
    # ... etc
}
for old_name, new_name in _migration_aliases.items():
    try:
        mcp.tool(name=old_name)(_v1_funcs.get(new_name))
    except Exception:
        pass  # Silently skip if function not available
```

---

## 9. Final Naming Reference

### Complete rename table

| Old name | New name | Dimension | Type |
|---|---|---|---|
| `wealth_reason_npv` | `wealth_value_npv` | value | tool |
| `wealth_npv_reward` | ~~RETIRE~~ | value | duplicate |
| `wealth_reason_irr` | `wealth_energy_irr` | energy | tool |
| `wealth_reason_pi` | `wealth_density_pi` | density | tool |
| `wealth_reason_payback` | `wealth_time_payback` | time | tool |
| `wealth_mind_emv` | `wealth_expectation_emv` | expectation | tool |
| `wealth_mind_monte_carlo` | `wealth_probability_monte_carlo` | probability | tool |
| `wealth_mind_evoi` | `wealth_signal_evoi` | signal | tool |
| `wealth_mind_evoi_mc` | `wealth_signal_evoi_mc` | signal | tool |
| `wealth_mind_correlation` | `wealth_coupling_correlation` | coupling | tool |
| `wealth_mind_schema` | `wealth_measurement_schema` | measurement | tool |
| `wealth_survival_cashflow` | `wealth_flow_cashflow` | flow | tool |
| `wealth_survival_velocity` | `wealth_velocity_runway` | velocity | tool |
| `wealth_survival_dscr` | `wealth_gravity_dscr` | gravity | tool |
| `wealth_survival_networth` | `wealth_mass_networth` | mass | tool |
| `wealth_survival_triage` | `wealth_pressure_triage` | pressure | tool |
| `wealth_survival_civilization` | `wealth_stewardship_civilization` | stewardship | tool |
| `wealth_judge_entropy` | `wealth_entropy_audit` | entropy | tool |
| `wealth_judge_floors` | `wealth_boundary_floors` | boundary | tool |
| `wealth_judge_policy` | `wealth_boundary_policy` | boundary | tool |
| `wealth_judge_kernel` | `wealth_governance_verdict` | governance | tool |
| `wealth_reason_game` | `wealth_field_game` | field | tool |
| `wealth_reason_equilibrium` | `wealth_field_equilibrium` | field | tool |
| `wealth_reason_personal` | `wealth_preference_rank` | preference | tool |
| `wealth_reason_agent` | `wealth_agent_path` | agent | tool |
| `wealth_sense_fetch` | `wealth_sensor_fetch` | sensor | tool |
| `wealth_sense_snapshot` | `wealth_sensor_snapshot` | sensor | tool |
| `wealth_sense_reconcile` | `wealth_sensor_reconcile` | sensor | tool |
| `wealth_sense_health` | `wealth_sensor_health` | sensor | tool |
| `wealth_sense_vintage` | `wealth_sensor_vintage` | sensor | tool |
| `wealth_sense_sources` | `wealth_sensor_sources` | sensor | tool |
| `vault_query` | `wealth_ledger_query` | ledger | tool |
| `vault_write` | `wealth_ledger_write` | ledger | tool |
| `wealth_vault_init` | `wealth_ledger_init` | ledger | tool |
| `wealth_vault_record` | `wealth_ledger_record` | ledger | tool |
| `wealth_vault_snapshot` | `wealth_ledger_snapshot` | ledger | tool |
| `mcp_health_check` | `mcp_health_check` | transport | tool |
| `wealth_future_value` | `wealth_appraise_project` | orchestration | **PROMPT** |
| `wealth_present_expect` | `wealth_expectation_emv` | orchestration | **PROMPT** |
| `wealth_future_simulate` | `wealth_run_monte_carlo` | orchestration | **PROMPT** |
| `wealth_info_value` | `wealth_run_evoi` | orchestration | **PROMPT** |
| `wealth_truth_validate` | `wealth_measurement_validate` | orchestration | **PROMPT** |
| `wealth_rule_enforce` | `wealth_boundary_enforce` | orchestration | **PROMPT** |
| `wealth_allocate_optimize` | `wealth_allocate_optimal` | orchestration | **PROMPT** |
| `wealth_game_coordinate` | `wealth_coordinate_agents` | orchestration | **PROMPT** |
| `wealth_sense_ingest` | `wealth_ingest_data` | orchestration | **PROMPT** |
| `wealth_past_record` | `wealth_record_event` | orchestration | **PROMPT** |
| `wealth_future_steward` | `wealth_steward_long_horizon` | orchestration | **PROMPT** |
| `wealth_survival_liquidity` | DEMOTED | modes → atomic | **DEMOTED** |
| `wealth_survival_leverage` | DEMOTED | modes → atomic | **DEMOTED** |

---

## 10. Physics-Inspired Ontology Reference

```
WEALTH MCP — Dimension Atlas
═══════════════════════════════════════════════════════════════

DIMENSION     PHYSICS BASE    ECONOMIC FORM           UNIT
────────────────────────────────────────────────────────────────
mass          matter         net worth / capital      MYR / USD
energy        work capacity  return potential         % / MYR
flow          fluid dynamics cash movement           MYR/period
velocity      dv/dt          compounding rate         %/year
gravity       F = GMm/r²     debt burden / fixed cost MYR obligation
pressure      F/A            liquidity stress         ratio
entropy       S = k log W    uncertainty / noise      bits
signal        photon         information value        EVOI (MYR)
field         force field    multi-agent incentives   game solution
boundary      surface        governance floor         F1–F13
sensor        measurement    data intake              adapter
ledger        conservation   immutable record         VAULT999 event
density       ρ = m/V        capital concentration    PI ratio
time          t              horizon / recovery       periods

═══════════════════════════════════════════════════════════════
DITEMPA BUKAN DIBERI — Physics is sovereign. Economics routes.
```
