# WEALTH MCP — Ingestion Map

**Generated:** 2026-08-06 · Session SEAL-b3bbf8e9e1844adc · Actor ARIF (333-AGI)
**Purpose:** Per-field consumption analysis — which inputs MOVE which tools.
**Method:** Differential A/B testing with volatile-key stripping (see W-001).
**Dependency for:** W-003 (WealthEvidenceMiddleware), W-004 (three-valued scoring).
**Receipts:** `tests/fixtures/baseline/*.json` (4 fixtures), `tests/fixtures/w001_receipt.json` (differential results), live probe evidence at `:18082/mcp` session SEAL-b3bbf8e9e1844adc.

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ CONSUMED | Field produces observable output difference |
| 🟡 DEGRADED | Partially consumed or silently transformed |
| ❌ DEAD | Field has no effect on output |
| 💥 ERROR | Field crashes the tool |
| ⬜ UNPROBED | Not yet tested with differential pairs |

---

## 1. capital_primitive

| Mode | Field | Status | Evidence |
|------|-------|--------|----------|
| npv | cash_flows | ✅ CONSUMED | A=[300,400,500,600]→NPV+389, B=[50,50,50,50]→NPV-842 |
| npv | discount_rate | ✅ CONSUMED | Part of NPV formula |
| npv | mode | ✅ CONSUMED | Routes to npv engine |
| irr | — | ⬜ UNPROBED | |
| emv | — | ⬜ UNPROBED | |
| evoi | — | ⬜ UNPROBED | |
| mc | — | ⬜ UNPROBED | |
| kelly | — | ⬜ UNPROBED | |
| markowitz | — | ⬜ UNPROBED | |
| robust | — | ⬜ UNPROBED | |
| chance_constrained | — | ⬜ UNPROBED | |
| two_stage | — | ⬜ UNPROBED | |

**dead_field_count:** 0 (for npv) · **unprobed_modes:** 9

---

## 2. capital_health

| Mode | Field | Status | Evidence |
|------|-------|--------|----------|
| survival (personal_finance) | monthly_income_v | ✅ CONSUMED | 20000→+12k/mo, 3000→-2k/mo |
| survival (personal_finance) | monthly_expenses_v | ✅ CONSUMED | Affects net_monthly directly |
| survival (personal_finance) | liquid_assets | ✅ CONSUMED | Affects runway calculation |
| survival (personal_finance) | survival_submode | ✅ CONSUMED | Routes to personal_finance engine |
| survival (corporate_runway) | liquid_assets | ✅ CONSUMED | FIXED 2026-10-15: corporate branch computes runway from liquid_assets/monthly_burn; value reflected in output |
| survival (corporate_runway) | monthly_burn | ✅ CONSUMED | FIXED 2026-10-15: consumed by corporate branch; personal-finance-only fields now explicitly rejected (UNSUPPORTED_FIELDS) |
| survival (corporate_runway) | survival_submode | ✅ CONSUMED | FIXED 2026-10-15: resolved mode reflected in output (`mode`, `survival_submode` keys); no personal_finance downgrade |
| survival (sovereign_fiscal) | all | ✅ CONSUMED | FIXED (crash 2026-08-06 Loop 8; closure 2026-10-15): canonical 4-param payload → structured fiscal result with resolved-mode reflection; missing params → explicit MISSING_REQUIRED_PARAMS; real fixture `capital_health__survival__sovereign_fiscal.json` stored |
| conservation | — | ⬜ UNPROBED | |
| flow | — | ⬜ UNPROBED | |
| runway | — | ⬜ UNPROBED | |
| fiscal_breakeven | — | ⬜ UNPROBED | |
| confluence | — | ⬜ UNPROBED | |
| asymmetry | — | ⬜ UNPROBED | |

**dead_field_count:** 0 for the three audited defects (closed 2026-10-15; see below)
**critical_defects:**
- ~~corporate_runway silently downgraded to personal_finance~~ CLOSED 2026-10-15 — corporate branch live, resolved mode reflected, foreign fields explicitly rejected
- ~~sovereign_fiscal crashes at MCP schema layer (-32602)~~ CLOSED — crash fixed 2026-08-06 (Loop 8, commit 52ff13c); closure verified 2026-10-15 with canonical payload + real fixture
- apex authority gate: pass=false, actor=None despite supplied actor_id

---

## 3. capital_diagnose

| Mode | Field | Status | Evidence |
|------|-------|--------|----------|
| collapse_signature | domain_scope | ✅ CONSUMED | FIXED 2026-10-15: top-level domain_scope enters scenario chain (`profile._source_text`), corpus-prior selection (`priors_used`/`prior_comparison`), and output reflection (`domain_scope`, `domain_scope_resolved`). Unsupported scopes → UNSUPPORTED_DOMAIN_SCOPE. |
| collapse_signature | session_id | ✅ CONSUMED | Required for auth |
| petronas_vitals | (no args) | ✅ CONSUMED | Autonomous mode — reads IFR data internally. 9 tripwires, 3 layers, F2-audited. |
| sovereign_pulse | (no args) | ✅ CONSUMED | Alias for petronas_vitals. |
| petronas_phi | (no args) | ✅ CONSUMED | Alias for petronas_vitals. |
| stress_index | — | ⬜ UNPROBED | |
| governance_capacity | — | ⬜ UNPROBED | |
| cascade_model | — | ⬜ UNPROBED | |
| exploitation_detect | — | ⬜ UNPROBED | |
| beautiful_mouse | — | ⬜ UNPROBED | |
| capture_scan | — | ⬜ UNPROBED | |
| power_audit | — | ⬜ UNPROBED | |
| bid_surface | — | ⬜ UNPROBED | |
| optimize_mwc | — | ⬜ UNPROBED | |
| cadence_monitor | — | ⬜ UNPROBED | |
| crisis_reflex | — | ⬜ UNPROBED | |

**dead_field_count:** 0 (domain_scope on collapse_signature CLOSED 2026-10-15 — top-level param now wired into scenario chain + corpus-prior selection + output reflection; unsupported scopes rejected explicitly)
**undocumented_modes:** 3 (petronas_vitals, sovereign_pulse, petronas_phi — not in registry listing or error message)
**critical_defects:**
- ~~collapse_signature _source_text empty — ingestion pipeline broken~~ CLOSED 2026-10-15
- 12 modes advertised, 3 runtime-only modes invisible to discovery

---

## 4. capital_market

| Mode | Field | Status | Evidence |
|------|-------|--------|----------|
| fx | — | ⬜ UNPROBED | |
| commodity | — | ⬜ UNPROBED | |
| indicator | — | ⬜ UNPROBED | |
| stock | — | ⬜ UNPROBED | |
| gold | — | ⬜ UNPROBED | |
| oil | — | ⬜ UNPROBED | |
| gas | — | ⬜ UNPROBED | |

**dead_field_count:** unknown · **unprobed_modes:** 7

---

## 5. capital_ledger

| Mode | Field | Status | Evidence |
|------|-------|--------|----------|
| query | — | ⬜ UNPROBED | |
| write | — | ⬜ UNPROBED | (requires ack_irreversible) |

**dead_field_count:** unknown · **unprobed_modes:** 2

---

## 6. capital_registry

| Mode | Field | Status | Evidence |
|------|-------|--------|----------|
| status | — | ✅ CONSUMED | No material args needed. Returns organ health. |
| schema | — | ✅ CONSUMED | Returns full mode listing (missing 3 petronas_* modes). |
| domains | — | ⬜ UNPROBED | |
| health | — | ✅ CONSUMED | No material args needed. |

**dead_field_count:** 0 · **defects:** schema mode lists 12 diagnose modes, misses 3 runtime-only petronas_* modes

---

## 7. capital_entropy

| Mode | Field | Status | Evidence |
|------|-------|--------|----------|
| power_consequence_map | decision_makers | ✅ CONSUMED (FIXED) | Was DEAD — scores from list length only. NOW: authority, stake fields consumed. Version 2.0.0-differential-safe. |
| power_consequence_map | beneficiaries | ✅ CONSUMED (FIXED) | Was DEAD. NOW: benefit, share fields consumed. |
| power_consequence_map | cost_bearers | ✅ CONSUMED (FIXED) | Was DEAD. NOW: harm, exposure, exit, compensation consumed. |
| metric_purpose_audit | — | ⬜ UNPROBED | |
| responsibility_ledger | — | ⬜ UNPROBED | |
| trust_capital_decay | — | ⬜ UNPROBED | |
| coercive_order_cost | — | ⬜ UNPROBED | |
| entropy_externality | — | ⬜ UNPROBED | |

**dead_field_count:** 0 (was 9+, now FIXED for power_consequence_map)
**critical_fixes:**
- 🔧 power_consequence_map now reads actual input content. Scores move with payload.
- Differential test A/B: 0.722 vs 0.2708 power_concentration — materially different.
- KNOWN-RED resolved. This was the session's central defect class.

---

## 8. wealth_judge_handoff

| Mode | Field | Status | Evidence |
|------|-------|--------|----------|
| prepare | intent | ✅ CONSUMED | Reflected in result.intent |
| prepare | reversibility | ✅ CONSUMED | IRREVERSIBLE→HOLD verdict |
| prepare | blast_radius | ✅ CONSUMED | high→flagged |
| prepare | actor_id | ✅ CONSUMED | actor_cryptographically_verified: false |
| submit | — | ⬜ UNPROBED | |

**dead_field_count:** 0 · **warnings:** EMPTY_RESULT flagged but verdict correctly responds to reversibility input
**defect:** Unknown mode silently falls through to prepare-like behavior (no error on invalid mode)

---

## SUMMARY

| Tool | Modes Probed | Consumed | Degraded | Dead | Error | Unprobed |
|------|-------------|----------|----------|------|-------|----------|
| capital_primitive | 1/10 | 2 | 0 | 0 | 0 | 9 |
| capital_health | 2/7 (+3 submodes) | 4 | 3 | 0 | 1 | 5 |
| capital_diagnose | 4/15 | 3 | 0 | 1 | 0 | 11 |
| capital_market | 0/7 | 0 | 0 | 0 | 0 | 7 |
| capital_ledger | 0/2 | 0 | 0 | 0 | 0 | 2 |
| capital_registry | 4/4 | 4 | 0 | 0 | 0 | 0 |
| capital_entropy | 1/6 | 3 | 0 | 0 | 0 | 5 |
| wealth_judge_handoff | 1/2 | 4 | 0 | 0 | 0 | 1 |
| **TOTAL** | **17/53** | **20** | **3** | **1** | **1** | **40** |

**Critical defects blocking W-003 middleware — ALL THREE CLOSED 2026-10-15 (WEALTH_THREE_DEFECT_CLOSURE_20261014):**
1. ~~capital_health corporate_runway silent downgrade~~ → corporate branch consumes fields, mode reflected, foreign fields rejected
2. ~~capital_health sovereign_fiscal MCP_SCHEMA_VIOLATION~~ → structured responses; canonical payload fixture stored; unknown modes structured (never a bare raise)
3. ~~capital_diagnose collapse_signature domain_scope dead~~ → consumed end-to-end (source text + corpus prior + reflection); unsupported scope rejected
Middleware dead-field/crashing entries for these three removed the same day (defense structure retained).

**Fixed in this session:**
1. capital_entropy power_consequence_map — all 3 field groups now consumed (was: list-length-only)

**Receipt:** This document is the ingestion map receipt for W-002. It is the prerequisite for Prompt 3 (WealthEvidenceMiddleware).
