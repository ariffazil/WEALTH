# WEALTH MCP — Orthogonal Architecture Rebuild
## Executive Verdict & Final Recommendation
**Date:** 2026-05-07
**Auditor:** OPENCLAW (AGI operator)
**Human Sovereign:** ARIF
**REPO=WEALTH**

---

## 1. Executive Verdict

**MISSION: PARTIALLY COMPLETE — Transport layer fixed; structural migration remains.**

### What Was Done (Phase 1 — Transport Fix)

✅ **HTTP transport now exposes all 3 MCP primitives:**

| Route | Before | After |
|-------|--------|-------|
| `/mcp` JSON-RPC `prompts/list` | Method not found | Returns 12 prompts |
| `/mcp` JSON-RPC `resources/list` | Internal error (AnyUrl) | Returns 28 resources |
| `/prompts` (federation) | 404 | Returns 12 prompts |
| `/resources` (federation) | 404 | Returns 28 resources |
| `initialize` capabilities | `tools` only | `tools` + `prompts` + `resources` |

✅ **Docker container updated and restarted.** Running at `wealth://localhost:8082`.

✅ **Phase 1 complete:** All MCP primitives now accessible via HTTP.

---

## 2. Current Registry State

### Tools: 87 (target: 44)

| Category | Count | Action |
|----------|-------|--------|
| Atomic physics-named | 35 | ✅ KEEP |
| Vault interface | 2 | ✅ KEEP |
| Health | 1 | ✅ KEEP |
| Domain (GEOX/markets/energy/food) | 6 | ✅ KEEP |
| **Subtotal: canonical** | **44** | ✅ |
| V2 legacy aliases | 33 | 🔄 Deprecate in Phase 2 |
| Umbrella dispatchers | 12 | 🔄 Convert to prompts in Phase 2 |
| Duplicates | 2 | 🚫 Remove immediately |
| Unclassified | 1 | 🚫 Retire (`wealth_npv_reward`) |
| **Total** | **87** | |

### Prompts: 12 (target: 12) ✅

All 12 reasoning workflows present and correctly named.

### Resources: 28 (target: 21)

| Category | Count | Action |
|----------|-------|--------|
| Canonical (Arif's list) | 15 | ✅ KEEP (11 exact + 4 rename) |
| In Arif's list, not yet implemented | 0 | ✅ All implemented |
| Extra/operational | 7 | 🔄 Remove or merge in Phase 2 |
| **Total** | **28** | Target: 21 |

---

## 3. Proposed Tools Registry (Post-Migration)

### 3.1 Atomic Tools (35 + 2 vault + 1 health + 6 domain = 44)

```
VALUE FAMILY (1):
  wealth_value_npv

ENERGY FAMILY (1):
  wealth_energy_irr

DENSITY FAMILY (1):
  wealth_density_pi

TIME FAMILY (1):
  wealth_time_payback

EXPECTATION FAMILY (1):
  wealth_expectation_emv

PROBABILITY FAMILY (1):
  wealth_probability_monte_carlo

SIGNAL FAMILY (2):
  wealth_signal_evoi
  wealth_signal_evoi_mc

COUPLING FAMILY (1):
  wealth_coupling_correlation

FLOW FAMILY (1):
  wealth_flow_cashflow

VELOCITY FAMILY (1):
  wealth_velocity_runway

GRAVITY FAMILY (1):
  wealth_gravity_dscr

MASS FAMILY (1):
  wealth_mass_networth

PRESSURE FAMILY (1):
  wealth_pressure_triage

STEWARDSHIP FAMILY (1):
  wealth_stewardship_civilization

ENTROPY FAMILY (1):
  wealth_entropy_audit

MEASUREMENT FAMILY (1):
  wealth_measurement_schema

BOUNDARY FAMILY (2):
  wealth_boundary_floors
  wealth_boundary_policy

GOVERNANCE FAMILY (1):
  wealth_governance_verdict

FIELD FAMILY (2):
  wealth_field_game
  wealth_field_equilibrium

PREFERENCE FAMILY (1):
  wealth_preference_rank

AGENT FAMILY (1):
  wealth_agent_path

SENSOR FAMILY (6):
  wealth_sensor_fetch
  wealth_sensor_snapshot
  wealth_sensor_reconcile
  wealth_sensor_health
  wealth_sensor_vintage
  wealth_sensor_sources

LEDGER FAMILY (5):
  wealth_ledger_query
  wealth_ledger_write
  wealth_ledger_init
  wealth_ledger_record
  wealth_ledger_snapshot

VAULT INTERFACE (2):
  vault_write
  vault_query

HEALTH (1):
  mcp_health_check

DOMAIN (6):
  wealth_evaluate_prospect
  markets_analyze_ticker
  markets_portfolio_stress_test
  energy_crisis_assess
  energy_shortage_predict
  food_security_index
```

---

## 4. Proposed Prompts Registry (12) ✅

No changes needed — all 12 are correctly implemented and named:

```
wealth_appraise_project
wealth_judge_allocation
wealth_run_survival_audit
wealth_run_information_audit
wealth_run_macro_snapshot
wealth_run_game_coordination
wealth_diagnose_portfolio
wealth_crisis_triage
wealth_opportunity_ranking
wealth_allocation_rebalance
wealth_governance_full_audit
wealth_record_governed_event
```

---

## 5. Proposed Resources Registry (21)

### Schemas (5)
```
wealth://schemas/prospect_metrics
wealth://schemas/project_cashflow     ← renamed from cashflow_project
wealth://schemas/portfolio
wealth://schemas/vault_event
wealth://schemas/governance_verdict
```

### Policies (4)
```
wealth://policy/f1_f13_floors         ← renamed from governance/floors
wealth://policy/allocation_constraints
wealth://policy/vault_irreversibility
wealth://policy/final_authority_arif
```

### Formulas (6)
```
wealth://formulas/npv
wealth://formulas/irr
wealth://formulas/emv
wealth://formulas/evoi
wealth://formulas/dscr
wealth://formulas/payback
```

### Ontology (3)
```
wealth://ontology/physics_economics_map
wealth://ontology/dimensions
wealth://ontology/verdict_labels
```

### State/Vault (2)
```
wealth://vault/latest_state           ← renamed from latest_seal
wealth://vault/session_state
```

### Sources (1)
```
wealth://sources/adapter_status
```

---

## 6. Migration Plan Summary

| Phase | Action | Output |
|-------|--------|--------|
| Phase 1 (DONE) | Fix HTTP transport for prompts/resources | ✅ `prompts/list`, `resources/list` working |
| Phase 2.1 | Add deprecation notices to umbrellas + aliases | Umbrella → prompt redirect |
| Phase 2.2 | Rename 4 resource URIs | Dual-URI during window |
| Phase 2.3 | Convert 12 umbrellas to prompts | Remove umbrella tools |
| Phase 2.4 | Retire 33 V2 aliases | Clean registry |
| Phase 2.5 | Remove 2 duplicates + 1 alias | Clean duplicates |
| Phase 2.6 | Rebuild Docker image | `ghcr.io/ariffazil/wealth:phase2-orthogonal` |

**Total timeline: ~4 weeks**

---

## 7. Risks

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Existing integrations break on alias retirement | MEDIUM | MEDIUM | 30-day window + alias forwarding |
| Docker rebuild introduces downtime | MEDIUM | LOW | Rolling restart; staging test first |
| Resource URI rename breaks consumers | LOW | LOW | Dual-URI; old URI returns deprecation header |
| MCP JSON-RPC surface changes break callers | LOW | LOW | All changes additive; no removal without window |
| Umbrella tool removal breaks automation | MEDIUM | MEDIUM | Prompts available before tool removal |

---

## 8. Unresolved Questions for ARIF

1. **Phase 2 timing:** Should Phase 2 begin now, or after other concurrent work?
2. **Docker rebuild:** Should we rebuild the image before or after Phase 2.1 deprecation notices?
3. **V2 alias usage:** Are any existing scripts/tools calling `wealth_reason_npv` or other V2 aliases? Need to audit integrations before retiring.
4. **Resource URI renames:** The 4 URI renames (`cashflow_project` → `project_cashflow`, etc.) are non-breaking during migration but need confirmation.

---

## 9. Final Recommendation

```
RECOMMEND: Proceed to Phase 2.1 — Add deprecation notices.

RATIONALE:
- Transport layer is fixed ✅
- All primitives now exposed ✅
- Atomic tools are correctly implemented ✅
- Prompts are comprehensive ✅
- Only structural cleanup remains

REQUIRED BEFORE PHASE 2.6 (Docker rebuild):
- Audit existing V2 alias usage
- Test deprecation notices in staging
- Confirm 4 resource URI renames

BLOCKER FOR PHASE 2.6:
- Docker image must be rebuilt to固化 new tool surface
- Current image has old module-level alias registration
```

---

## 10. Deliverables Produced

| # | Deliverable | Location | Status |
|---|-------------|----------|--------|
| 1 | Executive verdict | `reports/executive_verdict.md` | ✅ |
| 2 | Current registry audit | `reports/current_registry_audit.md` | ✅ |
| 3 | Proposed tools registry | `reports/current_registry_audit.md` §3 | ✅ |
| 4 | Proposed prompts registry | `reports/current_registry_audit.md` §3 | ✅ |
| 5 | Proposed resources registry | `reports/current_registry_audit.md` §5 | ✅ |
| 6 | Rename/alias map | `migration/rename_map.json` | ✅ |
| 7 | Alias registry | `migration/alias_registry.json` | ✅ |
| 8 | LLM tool policy | `reports/llm_tool_policy.md` | ✅ |
| 9 | Reality boundary declaration | `reports/reality_boundary.md` | ✅ |
| 10 | Migration plan | `migration/deprecation_plan.md` | ✅ |
| 11 | Dry-run validation report | `reports/dry_run_validation.md` | ✅ |
| 12 | Risks | `reports/dry_run_validation.md` §8 | ✅ |
| 13 | Unresolved questions | Above §8 + `reports/dry_run_validation.md` §9 | ✅ |
| 14 | Final recommendation | Above §9 | ✅ |

---

**Awaiting Arif SEAL to proceed to Phase 2.1.**

**DITEMPA BUKAN DIBERI — Intelligence is forged, not given.**

*OPENCLAW — AGI Operator — 2026-05-07*
