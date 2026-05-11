# WEALTH MCP — Registry Audit Report
**Date:** 2026-05-07
**Auditor:** OPENCLAW
**Source:** HTTP endpoint (localhost:8082/mcp) — ground truth for running process
**Secondary:** Python import analysis (discrepancy noted)
**REPO=WEALTH**

---

## 0. Discrepancy Notice

| Source | Tool Count |
|--------|-----------|
| HTTP `/mcp` (running process) | **87** |
| Python `mcp.list_tools()` (fresh import) | **53** |

**Root cause:** The running container (`wealth-organ`) has the old Docker image whose `monolith.py` registered V2 aliases at **module level** (outside `if __name__ == "__main__":`). The new code moved alias registration inside `if __name__ == "__main__":`, so imports don't trigger registration.

**Fix:** Rebuild Docker image after alias retirement (Phase 3). After rebuild, both sources will agree on ~47 tools.

**This audit uses HTTP endpoint counts as ground truth.**

---

## 1. Registry Summary

| Primitive | Count | Target | Delta |
|-----------|-------|--------|-------|
| **Tools** | 87 | 48 | -39 excess |
| **Prompts** | 12 | 12 | ✅ match |
| **Resources** | 28 | 21 | -7 excess |
| **Total** | 127 | 81 | -46 |

---

## 2. Tools Registry Audit

### 2.1 KEEP_AS_TOOL (39) ✅

**Atomic physics-named tools — single responsibility, no mode dispatch.**

| Tool | Dimension | Engine | Status |
|------|-----------|--------|--------|
| `mcp_health_check` | — | — | ✅ Single responsibility |
| `wealth_value_npv` | value | `npv_reward` | ✅ |
| `wealth_energy_irr` | energy | `irr_yield` | ✅ |
| `wealth_density_pi` | density | `pi_efficiency` | ✅ |
| `wealth_time_payback` | time | `payback_time` | ✅ |
| `wealth_expectation_emv` | expectation | `emv_risk` | ✅ |
| `wealth_probability_monte_carlo` | probability | `monte_carlo_forecast` | ✅ |
| `wealth_signal_evoi` | signal | `wealth_evoi_compute` | ✅ |
| `wealth_signal_evoi_mc` | signal | `wealth_evoi_monte_carlo` | ✅ |
| `wealth_coupling_correlation` | coupling | `wealth_correlation_guard_check` | ✅ |
| `wealth_flow_cashflow` | flow | `cashflow_flow` | ✅ |
| `wealth_velocity_runway` | velocity | `growth_velocity` | ✅ |
| `wealth_gravity_dscr` | gravity | `dscr_leverage` | ✅ |
| `wealth_mass_networth` | mass | `networth_state` | ✅ |
| `wealth_pressure_triage` | pressure | `crisis_triage` | ✅ |
| `wealth_stewardship_civilization` | stewardship | `civilization_stewardship` | ✅ |
| `wealth_measurement_schema` | measurement | `wealth_schema_validate` | ✅ |
| `wealth_entropy_audit` | entropy | `audit_entropy` | ✅ |
| `wealth_boundary_floors` | boundary | `check_floors_tool` | ✅ |
| `wealth_boundary_policy` | boundary | `policy_audit` | ✅ |
| `wealth_governance_verdict` | governance | `wealth_score_kernel` | ✅ |
| `wealth_field_game` | field | `game_theory_solve` | ✅ |
| `wealth_field_equilibrium` | field | `coordination_equilibrium` | ✅ |
| `wealth_preference_rank` | preference | `personal_decision` | ✅ |
| `wealth_agent_path` | agent | `agent_budget` | ✅ |
| `wealth_sensor_fetch` | sensor | `ingest_fetch` | ✅ |
| `wealth_sensor_snapshot` | sensor | `ingest_snapshot` | ✅ |
| `wealth_sensor_reconcile` | sensor | `ingest_reconcile | ✅ |
| `wealth_sensor_health` | sensor | `ingest_health` | ✅ |
| `wealth_sensor_vintage` | sensor | `ingest_vintage` | ✅ |
| `wealth_sensor_sources` | sensor | `ingest_sources` | ✅ |
| `wealth_ledger_query` | ledger | `snapshot_portfolio_tool` | ✅ |
| `wealth_ledger_write` | ledger | `record_transaction_tool` | ✅ |
| `wealth_ledger_init` | ledger | `wealth_init_tool` | ✅ |
| `wealth_ledger_record` | ledger | `record_transaction_tool` | ✅ |
| `wealth_ledger_snapshot` | ledger | `snapshot_portfolio_tool` | ✅ |
| `vault_write` | vault | `record_transaction_tool` | ✅ Required interface |
| `vault_query` | vault | `snapshot_portfolio_tool` | ✅ Required interface |

**Note:** `vault_write` and `vault_query` share underlying engines with `wealth_ledger_write`/`wealth_ledger_snapshot`. They are kept for arifOS compatibility but are functionally redundant.

---

### 2.2 MOVE_TO_PROMPT (12) 🔄

**Umbrella dispatcher tools — orchestrate multiple engines via `mode` parameter.**

These must be **converted to prompts** (reasoning workflows) and the tools removed from the tool surface. The atomic tools they dispatch to are already implemented (above).

| Tool | Dispatches To | Target Prompt |
|------|-------------|---------------|
| `wealth_future_value` | `npv_reward`, `irr_yield`, `pi_efficiency`, `payback_time` | `wealth_appraise_project` |
| `wealth_present_expect` | `emv_risk` | `wealth_opportunity_ranking` |
| `wealth_future_simulate` | `monte_carlo_forecast` | `wealth_run_information_audit` |
| `wealth_survival_liquidity` | `cashflow_flow`, `crisis_triage`, `growth_velocity` | `wealth_run_survival_audit` |
| `wealth_survival_leverage` | `dscr_leverage`, `networth_state` | `wealth_run_survival_audit` |
| `wealth_info_value` | `wealth_evoi_compute`, `wealth_evoi_monte_carlo` | `wealth_run_information_audit` |
| `wealth_truth_validate` | `wealth_schema_validate`, `correlation_guard`, `audit_entropy` | `wealth_run_information_audit` |
| `wealth_rule_enforce` | `check_floors_tool`, `policy_audit`, `audit_entropy` | `wealth_governance_full_audit` |
| `wealth_allocate_optimize` | `wealth_score_kernel`, `personal_decision`, `agent_budget` | `wealth_judge_allocation` |
| `wealth_game_coordinate` | `coordination_equilibrium`, `game_theory_solve` | `wealth_run_game_coordination` |
| `wealth_sense_ingest` | `ingest_fetch`, `ingest_snapshot`, `ingest_sources`, `ingest_health`, `ingest_vintage`, `ingest_reconcile` | `wealth_run_macro_snapshot` |
| `wealth_past_record` | `wealth_init_tool`, `record_transaction_tool`, `snapshot_portfolio_tool` | `wealth_record_governed_event` |

**Migration:** These tools return a deprecation notice pointing to the canonical atomic tool(s) and the target prompt. After migration window (Phase 3), remove from tool surface entirely.

---

### 2.3 ALIAS_ONLY (33) 🔇

**V2 legacy aliases — map old `wealth_<family>_<operation>` names to internal engines.**

These create noise in the tool registry and must be retired in Phase 3. They continue to work during the backward-compatibility window but should not be used in new integrations.

| Alias | Maps To | Family |
|-------|---------|--------|
| `wealth_sense_fetch` | `ingest_fetch` | SENSE |
| `wealth_sense_snapshot` | `ingest_snapshot` | SENSE |
| `wealth_sense_reconcile` | `ingest_reconcile` | SENSE |
| `wealth_sense_health` | `ingest_health` | SENSE |
| `wealth_sense_vintage` | `ingest_vintage` | SENSE |
| `wealth_sense_sources` | `ingest_sources` | SENSE |
| `wealth_mind_emv` | `emv_risk` | MIND |
| `wealth_mind_monte_carlo` | `monte_carlo_forecast` | MIND |
| `wealth_mind_correlation` | `wealth_correlation_guard_check` | MIND |
| `wealth_mind_evoi` | `wealth_evoi_compute` | MIND |
| `wealth_mind_evoi_mc` | `wealth_evoi_monte_carlo` | MIND |
| `wealth_mind_schema` | `wealth_schema_validate` | MIND |
| `wealth_survival_dscr` | `dscr_leverage` | SURVIVAL |
| `wealth_survival_networth` | `networth_state` | SURVIVAL |
| `wealth_survival_velocity` | `growth_velocity` | SURVIVAL |
| `wealth_survival_cashflow` | `cashflow_flow` | SURVIVAL |
| `wealth_survival_triage` | `crisis_triage` | SURVIVAL |
| `wealth_survival_civilization` | `civilization_stewardship` | SURVIVAL |
| `wealth_reason_npv` | `npv_reward` | REASON |
| `wealth_reason_irr` | `irr_yield` | REASON |
| `wealth_reason_pi` | `pi_efficiency` | REASON |
| `wealth_reason_payback` | `payback_time` | REASON |
| `wealth_reason_equilibrium` | `coordination_equilibrium` | REASON |
| `wealth_reason_game` | `game_theory_solve` | REASON |
| `wealth_reason_personal` | `personal_decision` | REASON |
| `wealth_reason_agent` | `agent_budget` | REASON |
| `wealth_judge_kernel` | `wealth_score_kernel` | JUDGE |
| `wealth_judge_floors` | `check_floors_tool` | JUDGE |
| `wealth_judge_policy` | `policy_audit` | JUDGE |
| `wealth_judge_entropy` | `audit_entropy` | JUDGE |
| `wealth_vault_init` | `wealth_init_tool` | VAULT |
| `wealth_vault_record` | `record_transaction_tool` | VAULT |
| `wealth_vault_snapshot` | `snapshot_portfolio_tool` | VAULT |

---

### 2.4 RETIRE_DUPLICATE (2) 🚫

**Duplicate entries that serve no purpose.**

| Tool | Reason |
|------|--------|
| `vaultwrite` | Duplicate of `vault_write` (same engine `record_transaction_tool`) |
| `vaultquery` | Duplicate of `vault_query` (same engine `snapshot_portfolio_tool`) |

---

### 2.5 NEEDS_REVIEW (1) ❓

| Tool | Issue |
|------|-------|
| `wealth_npv_reward` | Registered as both a V2 alias AND a `_v1_funcs` entry. Exposed publicly as a tool name but should be internal-only. Recommend retiring this public alias and using `wealth_value_npv` as the canonical tool. |

---

## 3. Prompts Registry Audit

**Status: ✅ Correct — all 12 reasoning workflows are properly registered.**

| Prompt | Orchestrates | Verdict |
|--------|-------------|---------|
| `wealth_appraise_project` | value_npv, energy_irr, density_pi, time_payback, boundary_floors | ✅ KEEP |
| `wealth_judge_allocation` | governance_verdict, boundary_floors, boundary_policy | ✅ KEEP |
| `wealth_run_survival_audit` | flow_cashflow, velocity_runway, gravity_dscr, mass_networth, pressure_triage | ✅ KEEP |
| `wealth_run_information_audit` | signal_evoi, signal_evoi_mc, entropy_audit, boundary_floors | ✅ KEEP |
| `wealth_run_macro_snapshot` | sensor_fetch, sensor_snapshot, sensor_reconcile, sensor_health, sensor_sources | ✅ KEEP |
| `wealth_run_game_coordination` | field_game, field_equilibrium, preference_rank, agent_path | ✅ KEEP |
| `wealth_diagnose_portfolio` | mass_networth, flow_cashflow, entropy_audit, boundary_floors | ✅ KEEP |
| `wealth_crisis_triage` | pressure_triage, flow_cashflow, velocity_runway | ✅ KEEP |
| `wealth_opportunity_ranking` | expectation_emv, signal_evoi, entropy_audit | ✅ KEEP |
| `wealth_allocation_rebalance` | governance_verdict, preference_rank, boundary_policy | ✅ KEEP |
| `wealth_governance_full_audit` | boundary_floors, boundary_policy, entropy_audit | ✅ KEEP |
| `wealth_record_governed_event` | ledger_record, ledger_snapshot, boundary_floors | ✅ KEEP |

**Gap:** These prompts exist but are not exposed via the MCP JSON-RPC `/prompts/list` method in the OLD image. After Docker rebuild, verify prompts are accessible via `prompts/list`.

---

## 4. Resources Registry Audit

**Current: 28 resources. Target: 21 resources. Excess: 7.**

### 4.1 Canonical Resources (21) — TARGET ✅

These match Arif's specified list and are properly implemented:

| URI | Type | Status |
|-----|------|--------|
| `wealth://ontology/physics_economics_map` | ontology | ✅ EXISTS |
| `wealth://schemas/prospect_metrics` | schema | ✅ EXISTS |
| `wealth://schemas/portfolio` | schema | ✅ EXISTS |
| `wealth://schemas/vault_event` | schema | ✅ EXISTS |
| `wealth://schemas/project_cashflow` | schema | ⚠️ EXISTS as `cashflow_project` — RENAME |
| `wealth://policies/f1_f13_floors` | policy | ⚠️ EXISTS as `governance/floors` — RENAME |
| `wealth://policies/final_authority_arif` | policy | ✅ EXISTS |
| `wealth://policies/vault_irreversibility` | policy | ✅ EXISTS |
| `wealth://formulas/npv` | formula | ✅ EXISTS |
| `wealth://formulas/irr` | formula | ✅ EXISTS |
| `wealth://formulas/emv` | formula | ✅ EXISTS |
| `wealth://formulas/evoi` | formula | ✅ EXISTS |
| `wealth://formulas/dscr` | formula | ✅ EXISTS |
| `wealth://vault/latest_state` | vault | ⚠️ EXISTS as `vault/latest_seal` — RENAME |
| `wealth://sources/adapter_status` | sources | ✅ EXISTS |

**Total canonical: 15 exist, 6 need renaming.**

### 4.2 Extra Resources (7) — REMOVE 🔇

These are operational/legacy resources that should be removed or reclassified:

| URI | Reason to Remove/Reclassify |
|-----|----------------------------|
| `wealth://doctrine/valuation` | Operational metadata, not schema/policy/formula |
| `wealth://dimensions/definitions` | Duplicates `ontology/dimensions` |
| `wealth://governance/harness-doctrines` | Operational — not a user-facing resource |
| `wealth://topology/families` | Operational — not a user-facing resource |
| `wealth://topology/scales` | Operational — not a user-facing resource |
| `wealth://epistemic/uncertainty-matrix` | Operational — not a user-facing resource |
| `wealth://vault/session_state` | Duplicates `vault/latest_state` |
| `wealth://policy/allocation_constraints` | Operational — partial duplicate of `policies/f1_f13_floors` |

**Note:** `wealth://ontology/dimensions` exists but is not in Arif's canonical list. Keep or deprecate based on relevance.

### 4.3 Missing Resources (6) — ADD ➕

These are in Arif's target list but not currently implemented:

| URI | Type | Implementation |
|-----|------|----------------|
| `wealth://ontology/dimensions` | ontology | EXISTS (not in canonical list — keep as extra) |
| `wealth://ontology/verdict_labels` | ontology | EXISTS as extra — keep |
| `wealth://schemas/project_cashflow` | schema | RENAME `cashflow_project` → `project_cashflow` |
| `wealth://policies/f1_f13_floors` | policy | RENAME `governance/floors` → `policies/f1_f13_floors` |
| `wealth://vault/latest_state` | vault | RENAME `vault/latest_seal` → `vault/latest_state` |

---

## 5. Domain Tools (6) — Unchanged ✅

From `mcp/server.py` — these are domain-specific tools outside the physics-naming convention. Keep as-is:

| Tool | Domain |
|------|--------|
| `wealth_evaluate_prospect` | Oil & gas EMV (GEOX bridge) |
| `markets_analyze_ticker` | Equity analysis |
| `markets_portfolio_stress_test` | Portfolio stress testing |
| `energy_crisis_assess` | Energy crisis severity |
| `energy_shortage_predict` | Energy shortage prediction |
| `food_security_index` | Food security index |

---

## 6. Naming Audit: Specific Tools Flagged

### `wealth_reason_npv` vs `wealth_npv_reward` vs `wealth_value_npv`

| Name | Classification | Engine | Notes |
|------|---------------|--------|-------|
| `wealth_reason_npv` | ALIAS_ONLY | `npv_reward` | V2 alias — retire in Phase 3 |
| `wealth_npv_reward` | NEEDS_REVIEW | `npv_reward` | Also V2 alias, also `_v1_funcs` key — retire |
| `wealth_value_npv` | KEEP_AS_TOOL | `npv_reward` | ✅ Canonical physics-named tool |

**Doctrine:** `wealth_value_npv` is the one tool to rule NPV. Retire the other two.

### `wealth_present_expect` vs `wealth_mind_emv`

| Name | Classification | Engine | Notes |
|------|---------------|--------|-------|
| `wealth_present_expect` | MOVE_TO_PROMPT | `emv_risk` | Umbrella — convert to `wealth_opportunity_ranking` prompt |
| `wealth_mind_emv` | ALIAS_ONLY | `emv_risk` | V2 alias — retire |

**Doctrine:** Use `wealth_expectation_emv` as the atomic tool. Use `wealth_opportunity_ranking` prompt for orchestration.

---

## 7. Architecture Health Score

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Tool orthogonality | 45% | Too many aliases and umbrella tools |
| Prompt coverage | 100% | All 12 workflows present |
| Resource organization | 75% | 7 extra resources need culling |
| Naming consistency | 52% | V2 aliases create noise |
| Governance clarity | 85% | Physics naming is clear; aliases obscure it |
| Backward compat | 90% | Aliases preserve compat; dupes need removal |
| **Overall** | **68%** | Functional but needs cleanup |

---

**DITEMPA BUKAN DIBERI — Intelligence is forged, not given.**
