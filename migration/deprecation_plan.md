# WEALTH MCP — Deprecation Plan
**Date:** 2026-05-07
**Phase:** Phase 2 — Umbrella Tool Migration
**REPO=WEALTH**

---

## Overview

WEALTH MCP has 3 categories of deprecated items:
1. **Umbrella tools (12)** — multi-engine dispatchers → convert to prompts
2. **V2 aliases (33)** — legacy naming → redirect to atomic tools
3. **Duplicate tools (2)** — `vaultwrite`, `vaultquery` → retire immediately

---

## Phase 2.1: Add Deprecation Notices (Week 1)

**Action:** Modify umbrella tools and V2 aliases to return deprecation notices.

### Umbrella Tool Deprecation

Each umbrella tool (`wealth_future_value`, `wealth_sense_ingest`, etc.) is modified to:
1. Return a structured deprecation notice with `redirect_to_prompt` and `redirect_to_tool` fields
2. Log the deprecation event to VAULT999
3. Still execute the underlying computation (backward compatibility)

```python
@mcp.tool(deprecated=True, deprecation_message="Use wealth_value_npv + wealth_appraise_project prompt instead")
def wealth_future_value(...):
    ...
```

### V2 Alias Deprecation

V2 aliases (`wealth_reason_npv`, `wealth_sense_fetch`, etc.) are modified to:
1. Return a structured redirect response with `canonical_name`
2. Log the alias usage for tracking
3. Forward to the canonical tool transparently (silent redirect)

---

## Phase 2.2: Resource URI Renames (Week 1)

**Action:** Add new resource URIs as aliases, mark old URIs as deprecated.

| Old URI | New URI | Action |
|---------|---------|--------|
| `wealth://schemas/cashflow_project` | `wealth://schemas/project_cashflow` | Add new, deprecate old |
| `wealth://governance/floors` | `wealth://policy/f1_f13_floors` | Add new, deprecate old |
| `wealth://vault/latest_seal` | `wealth://vault/latest_state` | Add new, deprecate old |

**Implementation:** Both old and new URIs work during migration. Old URI returns `X-Deprecated: true` header.

---

## Phase 2.3: Umbrella Tool → Prompt Conversion (Week 2)

**Action:** Convert 12 umbrella tools to prompts. Remove tool implementation.

The 12 umbrella tools are replaced by the 12 existing prompts:

| Umbrella Tool | Target Prompt |
|--------------|---------------|
| `wealth_future_value` | `wealth_appraise_project` |
| `wealth_present_expect` | `wealth_opportunity_ranking` |
| `wealth_future_simulate` | `wealth_run_information_audit` |
| `wealth_survival_liquidity` | `wealth_run_survival_audit` |
| `wealth_survival_leverage` | `wealth_run_survival_audit` |
| `wealth_info_value` | `wealth_run_information_audit` |
| `wealth_truth_validate` | `wealth_run_information_audit` |
| `wealth_rule_enforce` | `wealth_governance_full_audit` |
| `wealth_allocate_optimize` | `wealth_judge_allocation` |
| `wealth_game_coordinate` | `wealth_run_game_coordination` |
| `wealth_sense_ingest` | `wealth_run_macro_snapshot` |
| `wealth_past_record` | `wealth_record_governed_event` |

**Implementation:**
1. Keep the tool implementation but mark `deprecated=True`
2. Add docstring redirect to target prompt
3. After 30-day window: remove tool from registry

---

## Phase 2.4: V2 Alias Retirement (Week 3)

**Action:** Remove 33 V2 aliases from the tool registry.

After Phase 2.1, V2 aliases still forward to canonical tools. In Phase 2.4:
1. Remove `mcp.tool(name=v2_name)(...)` registrations
2. Update `V2_CANONICAL_MAP` documentation to mark all entries as `DEPRECATED`
3. Rebuild Docker image (fixes the module-level alias registration issue)

**V2 aliases to retire:**
```
wealth_sense_fetch, wealth_sense_snapshot, wealth_sense_reconcile,
wealth_sense_health, wealth_sense_vintage, wealth_sense_sources,
wealth_mind_emv, wealth_mind_monte_carlo, wealth_mind_correlation,
wealth_mind_evoi, wealth_mind_evoi_mc, wealth_mind_schema,
wealth_survival_dscr, wealth_survival_networth, wealth_survival_velocity,
wealth_survival_cashflow, wealth_survival_triage, wealth_survival_civilization,
wealth_reason_npv, wealth_reason_irr, wealth_reason_pi, wealth_reason_payback,
wealth_reason_equilibrium, wealth_reason_game, wealth_reason_personal,
wealth_reason_agent, wealth_judge_kernel, wealth_judge_floors,
wealth_judge_policy, wealth_judge_entropy, wealth_vault_init,
wealth_vault_record, wealth_vault_snapshot
```

---

## Phase 2.5: Duplicate Tool Retirement (Immediate)

**Action:** Remove `vaultwrite` and `vaultquery` from the tool registry.

These are exact duplicates of `vault_write` and `vault_query`. Remove their registrations immediately.

**Implementation:** Remove from `V2_CANONICAL_MAP` or add to skip list.

---

## Phase 2.6: Docker Image Rebuild (Week 4)

**Action:** Rebuild Docker image to固化 new tool surface.

The current Docker image (`ghcr.io/ariffazil/wealth:phase1-tools`) has:
- 87 tools exposed via HTTP
- Module-level alias registration (causing the 87-count discrepancy)

After Phase 2.4, rebuild with:
- 44 canonical tools
- 12 prompts
- 21 resources
- No V2 aliases
- Alias registration moved inside `if __name__ == "__main__":`

---

## Rollback Plan

If migration causes issues:

1. **Immediate rollback:** Revert Docker image to previous tag
2. **Alias rollback:** Add V2 aliases back to registration block
3. **Umbrella rollback:** Restore umbrella tool implementations
4. **Resource rollback:** Keep old resource URIs alongside new ones

---

## Communication Plan

| Day | Action |
|-----|--------|
| Day 1 | Announce migration window (30 days) in system log |
| Day 15 | Send midpoint reminder — identify any blockers |
| Day 28 | Pre-removal announcement |
| Day 30 | Execute Phase 2.4–2.6 (alias + umbrella retirement, rebuild) |

---

## Success Criteria

After Phase 2:
- `/tools/list` returns ≤ 48 tools (44 atomic + 2 vault + 1 health + 6 domain - duplicates removed)
- All 12 prompts accessible via `prompts/list`
- All 21 canonical resources present, old URIs return deprecation headers
- No V2 aliases in tool registry
- Docker image rebuilt, `mcp.list_tools()` and HTTP endpoint agree on count

---

**DITEMPA BUKAN DIBERI — Intelligence is forged, not given.**
