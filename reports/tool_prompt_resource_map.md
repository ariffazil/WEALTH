# WEALTH MCP — Tool / Prompt / Resource Map
**Date:** 2026-05-07
**REPO=WEALTH**

---

## 1. Tool → Prompt Routing

Each row shows: canonical tool → (orchestrated by) → prompt

| Tool | Dimension | Prompt(s) |
|------|-----------|-----------|
| `wealth_value_npv` | value | `wealth_appraise_project` |
| `wealth_energy_irr` | energy | `wealth_appraise_project` |
| `wealth_density_pi` | density | `wealth_appraise_project` |
| `wealth_time_payback` | time | `wealth_appraise_project` |
| `wealth_expectation_emv` | expectation | `wealth_opportunity_ranking` |
| `wealth_probability_monte_carlo` | probability | `wealth_run_information_audit` |
| `wealth_signal_evoi` | signal | `wealth_run_information_audit`, `wealth_opportunity_ranking` |
| `wealth_signal_evoi_mc` | signal | `wealth_run_information_audit` |
| `wealth_coupling_correlation` | coupling | `wealth_run_information_audit` |
| `wealth_flow_cashflow` | flow | `wealth_run_survival_audit`, `wealth_crisis_triage`, `wealth_diagnose_portfolio` |
| `wealth_velocity_runway` | velocity | `wealth_run_survival_audit`, `wealth_crisis_triage` |
| `wealth_gravity_dscr` | gravity | `wealth_run_survival_audit` |
| `wealth_mass_networth` | mass | `wealth_run_survival_audit`, `wealth_diagnose_portfolio` |
| `wealth_pressure_triage` | pressure | `wealth_run_survival_audit`, `wealth_crisis_triage` |
| `wealth_stewardship_civilization` | stewardship | `wealth_crisis_triage` |
| `wealth_entropy_audit` | entropy | `wealth_run_information_audit`, `wealth_diagnose_portfolio`, `wealth_opportunity_ranking`, `wealth_governance_full_audit` |
| `wealth_boundary_floors` | boundary | `wealth_appraise_project`, `wealth_judge_allocation`, `wealth_run_survival_audit`, `wealth_run_information_audit`, `wealth_diagnose_portfolio`, `wealth_record_governed_event`, `wealth_governance_full_audit` |
| `wealth_boundary_policy` | boundary | `wealth_judge_allocation`, `wealth_allocation_rebalance`, `wealth_governance_full_audit` |
| `wealth_governance_verdict` | governance | `wealth_judge_allocation`, `wealth_allocation_rebalance` |
| `wealth_field_game` | field | `wealth_run_game_coordination` |
| `wealth_field_equilibrium` | field | `wealth_run_game_coordination` |
| `wealth_preference_rank` | preference | `wealth_run_game_coordination`, `wealth_allocation_rebalance` |
| `wealth_agent_path` | agent | `wealth_run_game_coordination` |
| `wealth_sensor_fetch` | sensor | `wealth_run_macro_snapshot` |
| `wealth_sensor_snapshot` | sensor | `wealth_run_macro_snapshot` |
| `wealth_sensor_reconcile` | sensor | `wealth_run_macro_snapshot` |
| `wealth_sensor_health` | sensor | `wealth_run_macro_snapshot` |
| `wealth_sensor_vintage` | sensor | `wealth_run_macro_snapshot` |
| `wealth_sensor_sources` | sensor | `wealth_run_macro_snapshot` |
| `wealth_ledger_query` | ledger | `wealth_record_governed_event` |
| `wealth_ledger_write` | ledger | `wealth_record_governed_event` |
| `wealth_ledger_init` | ledger | `wealth_record_governed_event` |
| `wealth_ledger_record` | ledger | `wealth_record_governed_event` |
| `wealth_ledger_snapshot` | ledger | `wealth_record_governed_event` |
| `wealth_measurement_schema` | measurement | `wealth_run_information_audit` |

---

## 2. Prompt → Tool Orchestration

| Prompt | Orchestrates (in sequence) |
|--------|---------------------------|
| `wealth_appraise_project` | `wealth_value_npv` → `wealth_energy_irr` → `wealth_density_pi` → `wealth_time_payback` → `wealth_boundary_floors` |
| `wealth_judge_allocation` | `wealth_governance_verdict` → `wealth_boundary_floors` → `wealth_boundary_policy` |
| `wealth_run_survival_audit` | `wealth_flow_cashflow` → `wealth_velocity_runway` → `wealth_gravity_dscr` → `wealth_mass_networth` → `wealth_pressure_triage` |
| `wealth_run_information_audit` | `wealth_signal_evoi` → `wealth_signal_evoi_mc` → `wealth_entropy_audit` → `wealth_measurement_schema` |
| `wealth_run_macro_snapshot` | `wealth_sensor_fetch` → `wealth_sensor_snapshot` → `wealth_sensor_reconcile` → `wealth_sensor_health` → `wealth_sensor_sources` |
| `wealth_run_game_coordination` | `wealth_field_game` → `wealth_field_equilibrium` → `wealth_preference_rank` → `wealth_agent_path` |
| `wealth_diagnose_portfolio` | `wealth_mass_networth` → `wealth_flow_cashflow` → `wealth_entropy_audit` → `wealth_boundary_floors` |
| `wealth_crisis_triage` | `wealth_pressure_triage` → `wealth_flow_cashflow` → `wealth_velocity_runway` |
| `wealth_opportunity_ranking` | `wealth_expectation_emv` → `wealth_signal_evoi` → `wealth_entropy_audit` |
| `wealth_allocation_rebalance` | `wealth_governance_verdict` → `wealth_preference_rank` → `wealth_boundary_policy` |
| `wealth_governance_full_audit` | `wealth_boundary_floors` → `wealth_boundary_policy` → `wealth_entropy_audit` |
| `wealth_record_governed_event` | `wealth_ledger_record` → `wealth_ledger_snapshot` → `wealth_boundary_floors` |

---

## 3. Resource Consumption by Tool/Prompt

### 3.1 Resources Read by Tools

| Resource URI | Read By |
|-------------|---------|
| `wealth://schemas/prospect_metrics` | `wealth_measurement_schema` |
| `wealth://schemas/cashflow_project` | `wealth_flow_cashflow`, `wealth_run_survival_audit` |
| `wealth://schemas/portfolio` | `wealth_mass_networth`, `wealth_diagnose_portfolio` |
| `wealth://schemas/vault_event` | `wealth_ledger_record`, `wealth_ledger_snapshot` |
| `wealth://schemas/governance_verdict` | `wealth_governance_verdict` |
| `wealth://policy/f1_f13_floors` | `wealth_boundary_floors` |
| `wealth://policy/allocation_constraints` | `wealth_boundary_policy` |
| `wealth://policy/vault_irreversibility` | `wealth_ledger_write` |
| `wealth://policy/final_authority_arif` | All governance tools |
| `wealth://formulas/npv` | `wealth_value_npv` |
| `wealth://formulas/irr` | `wealth_energy_irr` |
| `wealth://formulas/emv` | `wealth_expectation_emv` |
| `wealth://formulas/evoi` | `wealth_signal_evoi`, `wealth_signal_evoi_mc` |
| `wealth://formulas/dscr` | `wealth_gravity_dscr` |
| `wealth://formulas/payback` | `wealth_time_payback` |
| `wealth://ontology/physics_economics_map` | All physics-named tools |
| `wealth://ontology/dimensions` | All physics-named tools |
| `wealth://ontology/verdict_labels` | `wealth_governance_verdict` |
| `wealth://vault/latest_seal` | `wealth_ledger_query`, `wealth_ledger_snapshot` |
| `wealth://vault/session_state` | `wealth_ledger_init` |
| `wealth://sources/adapter_status` | `wealth_sensor_sources`, `wealth_sensor_health` |

### 3.2 Prompts → Resource Read Dependency

| Prompt | Reads |
|--------|-------|
| `wealth_appraise_project` | `wealth://formulas/npv`, `wealth://formulas/irr`, `wealth://formulas/payback`, `wealth://policy/f1_f13_floors` |
| `wealth_judge_allocation` | `wealth://schemas/governance_verdict`, `wealth://policy/f1_f13_floors`, `wealth://policy/allocation_constraints` |
| `wealth_run_survival_audit` | `wealth://schemas/cashflow_project`, `wealth://schemas/portfolio`, `wealth://formulas/dscr` |
| `wealth_run_information_audit` | `wealth://schemas/prospect_metrics`, `wealth://formulas/evoi` |
| `wealth_run_macro_snapshot` | `wealth://sources/adapter_status` |
| `wealth_run_game_coordination` | `wealth://ontology/physics_economics_map` |
| `wealth_diagnose_portfolio` | `wealth://schemas/portfolio` |
| `wealth_crisis_triage` | `wealth://policy/vault_irreversibility` |
| `wealth_opportunity_ranking` | `wealth://formulas/emv`, `wealth://formulas/evoi` |
| `wealth_allocation_rebalance` | `wealth://policy/final_authority_arif` |
| `wealth_governance_full_audit` | `wealth://policy/f1_f13_floors` |
| `wealth_record_governed_event` | `wealth://schemas/vault_event`, `wealth://policy/vault_irreversibility`, `wealth://policy/final_authority_arif` |

---

**DITEMPA BUKAN DIBERI — Intelligence is forged, not given.**
