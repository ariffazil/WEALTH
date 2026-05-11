# WEALTH MCP — Orthogonal Architecture Rebuild
## SPEC v1.0 — DITEMPA BUKAN DIBERI

---

## 1. Concept & Vision

WEALTH MCP becomes a **governed economic intelligence substrate** where every primitive has one job:

| Primitive | Job |
|-----------|-----|
| **Tool** | Atomic computation or action — pure execution |
| **Prompt** | Governed reasoning workflow — orchestrates tools |
| **Resource** | Readable schema/policy/formula/state — stable knowledge |

Physics supplies the **analogy vocabulary** (mass, flow, gravity, entropy). Economics supplies the **domain meaning** (capital, cash flow, debt, uncertainty). Governance supplies the **judgment boundary** (F1–F13 floors, 888_JUDGE, VAULT999).

The mission: fix the category impurity where one tool did everything, and make the MCP surface **auditable, traceable, and human-sovereign** at every layer.

---

## 2. Architecture

### Target Surface (after rebuild)

```
WEALTH MCP
├── tools/              36 atomic + 6 domain = 42
├── prompts/            12 reasoning workflows
└── resources/          21 schemas/policies/formulas/ontology
```

### HTTP Transport Fix

Problem: FastMCP 3.2.4 streamable-http does not expose prompts/list or resources/list.

Fix: Add explicit HTTP routes in `server.py` that call the underlying FastMCP provider methods directly:

- `GET /prompts` → `mcp.list_prompts()` (async)
- `GET /resources` → `mcp.list_resources()` (async)
- `GET /resources/{uri}` → `mcp.read_resource(uri)` (async)

Also add `GET /health` and handle `initialize` request properly.

---

## 3. Tool Grammar

### Physics-First Naming Convention

```
wealth_<dimension>_<operation>
```

**Dimensions:** value, energy, density, time, expectation, probability, signal, coupling, flow, velocity, gravity, mass, pressure, stewardship, entropy, measurement, boundary, governance, field, preference, agent, sensor, ledger

**Operations:** npv, irr, pi, payback, emv, monte_carlo, evoi, evoi_mc, correlation, cashflow, runway, dscr, networth, triage, civilization, audit, floors, policy, verdict, game, equilibrium, rank, path, fetch, snapshot, reconcile, health, vintage, sources, query, write, init, record

### 36 Atomic Tools

| Tool | Dimension | Engine |
|------|-----------|--------|
| `wealth_value_npv` | value | `npv_reward` |
| `wealth_energy_irr` | energy | `irr_yield` |
| `wealth_density_pi` | density | `pi_efficiency` |
| `wealth_time_payback` | time | `payback_time` |
| `wealth_expectation_emv` | expectation | `emv_risk` |
| `wealth_probability_monte_carlo` | probability | `monte_carlo_forecast` |
| `wealth_signal_evoi` | signal | `wealth_evoi_compute` |
| `wealth_signal_evoi_mc` | signal | `wealth_evoi_monte_carlo` |
| `wealth_coupling_correlation` | coupling | `wealth_correlation_guard_check` |
| `wealth_flow_cashflow` | flow | `cashflow_flow` |
| `wealth_velocity_runway` | velocity | `growth_velocity` |
| `wealth_gravity_dscr` | gravity | `dscr_leverage` |
| `wealth_mass_networth` | mass | `networth_state` |
| `wealth_pressure_triage` | pressure | `crisis_triage` |
| `wealth_stewardship_civilization` | stewardship | `civilization_stewardship` |
| `wealth_entropy_audit` | entropy | `audit_entropy` |
| `wealth_boundary_floors` | boundary | `check_floors_tool` |
| `wealth_boundary_policy` | boundary | `policy_audit` |
| `wealth_governance_verdict` | governance | `wealth_score_kernel` |
| `wealth_field_game` | field | `game_theory_solve` |
| `wealth_field_equilibrium` | field | `coordination_equilibrium` |
| `wealth_preference_rank` | preference | `personal_decision` |
| `wealth_agent_path` | agent | `agent_budget` |
| `wealth_sensor_fetch` | sensor | `ingest_fetch` |
| `wealth_sensor_snapshot` | sensor | `ingest_snapshot` |
| `wealth_sensor_reconcile` | sensor | `ingest_reconcile` |
| `wealth_sensor_health` | sensor | `ingest_health` |
| `wealth_sensor_vintage` | sensor | `ingest_vintage` |
| `wealth_sensor_sources` | sensor | `ingest_sources` |
| `wealth_ledger_query` | ledger | `snapshot_portfolio_tool` |
| `wealth_ledger_write` | ledger | `record_transaction_tool` |
| `wealth_ledger_init` | ledger | `wealth_init_tool` |
| `wealth_ledger_record` | ledger | `record_transaction_tool` |
| `wealth_ledger_snapshot` | ledger | `snapshot_portfolio_tool` |
| `mcp_health_check` | — | — |

### 6 Domain Tools (unchanged)

From `mcp/server.py`:
`wealth_evaluate_prospect`, `markets_analyze_ticker`, `markets_portfolio_stress_test`, `energy_crisis_assess`, `energy_shortage_predict`, `food_security_index`

---

## 4. Prompts (12 Reasoning Workflows)

Each prompt is a governed reasoning scaffold. It:
- Orchestrates multiple atomic tools
- Reads relevant resources
- Produces bounded reasoning output
- Preserves Arif's authority at the end

| Prompt | Tools Orchestrated |
|--------|-------------------|
| `wealth_appraise_project` | value_npv, energy_irr, density_pi, time_payback, boundary_floors |
| `wealth_judge_allocation` | governance_verdict, boundary_floors, boundary_policy |
| `wealth_run_survival_audit` | flow_cashflow, velocity_runway, gravity_dscr, mass_networth, pressure_triage |
| `wealth_run_information_audit` | signal_evoi, signal_evoi_mc, entropy_audit, boundary_floors |
| `wealth_run_macro_snapshot` | sensor_fetch, sensor_snapshot, sensor_reconcile, sensor_health, sensor_sources |
| `wealth_run_game_coordination` | field_game, field_equilibrium, preference_rank, agent_path |
| `wealth_diagnose_portfolio` | mass_networth, flow_cashflow, entropy_audit, boundary_floors |
| `wealth_crisis_triage` | pressure_triage, flow_cashflow, velocity_runway |
| `wealth_opportunity_ranking` | expectation_emv, signal_evoi, entropy_audit |
| `wealth_allocation_rebalance` | governance_verdict, preference_rank, boundary_policy |
| `wealth_governance_full_audit` | boundary_floors, boundary_policy, entropy_audit |
| `wealth_record_governed_event` | ledger_record, ledger_snapshot, boundary_floors |

---

## 5. Resources (21 Readable Contexts)

### Schemas (5)
- `wealth://schemas/prospect_metrics`
- `wealth://schemas/cashflow_project`
- `wealth://schemas/portfolio`
- `wealth://schemas/vault_event`
- `wealth://schemas/governance_verdict`

### Policies (4)
- `wealth://policy/f1_f13_floors`
- `wealth://policy/allocation_constraints`
- `wealth://policy/vault_irreversibility`
- `wealth://policy/final_authority_arif`

### Formulas (6)
- `wealth://formulas/npv`
- `wealth://formulas/irr`
- `wealth://formulas/emv`
- `wealth://formulas/evoi`
- `wealth://formulas/dscr`
- `wealth://formulas/payback`

### Ontology (3)
- `wealth://ontology/physics_economics_map`
- `wealth://ontology/dimensions`
- `wealth://ontology/verdict_labels`

### State/Vault (2)
- `wealth://vault/latest_seal`
- `wealth://vault/session_state`

### Sources (1)
- `wealth://sources/adapter_status`

---

## 6. Migration Plan

### Phase 1: Fix HTTP Transport
Add explicit HTTP routes for prompts and resources in `server.py`.

### Phase 2: Deprecate Umbrella Tools
The 13 old canonical tools (`wealth_future_value`, `wealth_survival_liquidity`, etc.) become prompts. Their underlying engines are the atomic tools. The old tools return a deprecation notice pointing to the atomic tool + prompt.

### Phase 3: Retire V2 Aliases
Remove the 25 V2 aliases from the registration loop. Old names still work via redirects.

### Phase 4: Verify HTTP Surface
Test that `/mcp` JSON-RPC returns correct tools/prompts/resources counts.

---

## 7. Governance Rules

- F1 AMANAH: `wealth_ledger_write` requires `ack_irreversible=True`
- F13 SOVEREIGN: All verdicts are recommendations. Arif decides.
- No tool executes irreversible action without human confirmation
- Resources are readable only — never executable
- Prompts are reasoning scaffolds — they call tools, they don't execute economics

---

## 8. Success Criteria

After rebuild:
- `/tools/list` returns exactly 42 tools (36 atomic + 6 domain)
- `/prompts/list` returns exactly 12 prompts
- `/resources/list` returns exactly 21 resources
- No umbrella tool remains on the primary surface
- V2 aliases removed (backward compatibility via redirect)
- HTTP transport exposes all three primitives correctly
- All tools, prompts, resources preserve auditability and Arif's sovereignty

**DITEMPA BUKAN DIBERI — Forged, Not Given.**