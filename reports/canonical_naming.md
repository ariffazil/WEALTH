# WEALTH MCP — Canonical Naming Proposal
**Date:** 2026-05-07
**REPO=WEALTH**

---

## 1. Grammar

```
wealth_<dimension>_<operation>
```

| Slot | Valid Values | Meaning |
|------|-------------|---------|
| `dimension` | `value`, `energy`, `density`, `time`, `expectation`, `probability`, `signal`, `coupling`, `flow`, `velocity`, `gravity`, `mass`, `pressure`, `stewardship`, `entropy`, `measurement`, `boundary`, `governance`, `field`, `preference`, `agent`, `sensor`, `ledger` | Physics-inspired economic abstraction |
| `operation` | `npv`, `irr`, `pi`, `payback`, `emv`, `monte_carlo`, `evoi`, `evoi_mc`, `correlation`, `cashflow`, `runway`, `dscr`, `networth`, `triage`, `civilization`, `audit`, `floors`, `policy`, `verdict`, `game`, `equilibrium`, `rank`, `path`, `fetch`, `snapshot`, `reconcile`, `health`, `vintage`, `sources`, `query`, `write`, `init`, `record` | Economic computation or action |

---

## 2. Dimension → Operation Matrix

| Dimension | Operations | Tools |
|----------|-----------|-------|
| **value** | npv | `wealth_value_npv` |
| **energy** | irr | `wealth_energy_irr` |
| **density** | pi | `wealth_density_pi` |
| **time** | payback | `wealth_time_payback` |
| **expectation** | emv | `wealth_expectation_emv` |
| **probability** | monte_carlo | `wealth_probability_monte_carlo` |
| **signal** | evoi, evoi_mc | `wealth_signal_evoi`, `wealth_signal_evoi_mc` |
| **coupling** | correlation | `wealth_coupling_correlation` |
| **flow** | cashflow | `wealth_flow_cashflow` |
| **velocity** | runway | `wealth_velocity_runway` |
| **gravity** | dscr | `wealth_gravity_dscr` |
| **mass** | networth | `wealth_mass_networth` |
| **pressure** | triage | `wealth_pressure_triage` |
| **stewardship** | civilization | `wealth_stewardship_civilization` |
| **entropy** | audit | `wealth_entropy_audit` |
| **measurement** | schema | `wealth_measurement_schema` |
| **boundary** | floors, policy | `wealth_boundary_floors`, `wealth_boundary_policy` |
| **governance** | verdict | `wealth_governance_verdict` |
| **field** | game, equilibrium | `wealth_field_game`, `wealth_field_equilibrium` |
| **preference** | rank | `wealth_preference_rank` |
| **agent** | path | `wealth_agent_path` |
| **sensor** | fetch, snapshot, reconcile, health, vintage, sources | 6 tools |
| **ledger** | query, write, init, record, snapshot | 5 tools |

---

## 3. Forbidden Patterns

| Pattern | Example | Why Forbidden |
|---------|---------|---------------|
| `wealth_<verb>_<noun>` | `wealth_calculate_npv` | Use `<dimension>_<operation>` |
| `wealth_<family>_<verb>` | `wealth_reason_calculate` | Family names are internal |
| Mode dispatch in tool name | `wealth_future_value_mode` | One tool, one operation |
| CamelCase | `wealthValueNPV` | Always snake_case |
| Abbreviations beyond standard | `wealth_val_npv` | Use full words |
| Prefix without dimension | `wealth_npv` | Must have dimension slot |

---

## 4. Resource URI Grammar

```
wealth://<category>/<specific>
```

| Category | Examples |
|----------|---------|
| `schemas` | `prospect_metrics`, `project_cashflow`, `portfolio`, `vault_event`, `governance_verdict` |
| `policies` | `f1_f13_floors`, `allocation_constraints`, `vault_irreversibility`, `final_authority_arif` |
| `formulas` | `npv`, `irr`, `emv`, `evoi`, `dscr`, `payback` |
| `ontology` | `physics_economics_map`, `dimensions`, `verdict_labels` |
| `vault` | `latest_state`, `session_state` |
| `sources` | `adapter_status` |

---

## 5. Prompt Naming

```
wealth_<workflow_descriptor>
```

| Current | Proposed |
|---------|---------|
| `wealth_appraise_project` | `wealth_appraise_project` ✅ |
| `wealth_judge_allocation` | `wealth_judge_allocation` ✅ |
| `wealth_run_survival_audit` | `wealth_run_survival_audit` ✅ |
| `wealth_run_information_audit` | `wealth_run_information_audit` ✅ |
| `wealth_run_macro_snapshot` | `wealth_run_macro_snapshot` ✅ |
| `wealth_run_game_coordination` | `wealth_run_game_coordination` ✅ |
| `wealth_diagnose_portfolio` | `wealth_diagnose_portfolio` ✅ |
| `wealth_crisis_triage` | `wealth_crisis_triage` ✅ |
| `wealth_opportunity_ranking` | `wealth_opportunity_ranking` ✅ |
| `wealth_allocation_rebalance` | `wealth_allocation_rebalance` ✅ |
| `wealth_governance_full_audit` | `wealth_governance_full_audit` ✅ |
| `wealth_record_governed_event` | `wealth_record_governed_event` ✅ |

All 12 existing prompt names are already canonical. ✅

---

## 6. Migration Table: Old → Canonical

| Old Name | Canonical Name | Type |
|----------|---------------|------|
| `wealth_reason_npv` | `wealth_value_npv` | Alias |
| `wealth_npv_reward` | `wealth_value_npv` | Retire |
| `wealth_reason_irr` | `wealth_energy_irr` | Alias |
| `wealth_reason_pi` | `wealth_density_pi` | Alias |
| `wealth_reason_payback` | `wealth_time_payback` | Alias |
| `wealth_mind_emv` | `wealth_expectation_emv` | Alias |
| `wealth_mind_monte_carlo` | `wealth_probability_monte_carlo` | Alias |
| `wealth_mind_evoi` | `wealth_signal_evoi` | Alias |
| `wealth_mind_evoi_mc` | `wealth_signal_evoi_mc` | Alias |
| `wealth_mind_correlation` | `wealth_coupling_correlation` | Alias |
| `wealth_mind_schema` | `wealth_measurement_schema` | Alias |
| `wealth_survival_cashflow` | `wealth_flow_cashflow` | Alias |
| `wealth_survival_velocity` | `wealth_velocity_runway` | Alias |
| `wealth_survival_dscr` | `wealth_gravity_dscr` | Alias |
| `wealth_survival_networth` | `wealth_mass_networth` | Alias |
| `wealth_survival_triage` | `wealth_pressure_triage` | Alias |
| `wealth_survival_civilization` | `wealth_stewardship_civilization` | Alias |
| `wealth_judge_entropy` | `wealth_entropy_audit` | Alias |
| `wealth_judge_floors` | `wealth_boundary_floors` | Alias |
| `wealth_judge_policy` | `wealth_boundary_policy` | Alias |
| `wealth_judge_kernel` | `wealth_governance_verdict` | Alias |
| `wealth_reason_game` | `wealth_field_game` | Alias |
| `wealth_reason_equilibrium` | `wealth_field_equilibrium` | Alias |
| `wealth_reason_personal` | `wealth_preference_rank` | Alias |
| `wealth_reason_agent` | `wealth_agent_path` | Alias |
| `wealth_sense_fetch` | `wealth_sensor_fetch` | Alias |
| `wealth_sense_snapshot` | `wealth_sensor_snapshot` | Alias |
| `wealth_sense_reconcile` | `wealth_sensor_reconcile` | Alias |
| `wealth_sense_health` | `wealth_sensor_health` | Alias |
| `wealth_sense_vintage` | `wealth_sensor_vintage` | Alias |
| `wealth_sense_sources` | `wealth_sensor_sources` | Alias |
| `wealth_vault_init` | `wealth_ledger_init` | Alias |
| `wealth_vault_record` | `wealth_ledger_record` | Alias |
| `wealth_vault_snapshot` | `wealth_ledger_snapshot` | Alias |
| `vaultwrite` | `vault_write` | Retire duplicate |
| `vaultquery` | `vault_query` | Retire duplicate |

---

**DITEMPA BUKAN DIBERI — Intelligence is forged, not given.**
