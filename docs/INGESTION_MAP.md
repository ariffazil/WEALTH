# WEALTH INGESTION MAP
**Forged:** 2026-08-06 · **Source:** W-002 live probe via `_tool_fn()` direct calls
**Method:** `normalize(result)` → compare with/without field. Identical → DEAD.

## Summary

| Tool | Fields Tested | LIVE | DEAD | Dead Field Count |
|------|--------------|------|------|------------------|
| capital_health.conservation | assets, liabilities | 2 | 0 | 0 |
| capital_health.flow | income, expenses | 2 | 0 | 0 |
| capital_health.survival | survival_submode | 1 | 0 | 0 |
| capital_entropy.pcm | decision_makers, beneficiaries, cost_bearers, veto_holders | 4 | 0 | 0 |
| capital_diagnose.collapse_signature | payload.scenario (text) | 1 | 0 | 0 |
| capital_diagnose.stress_index | payload.financial_signals | ⚠️ conditional | ⚠️ conditional | see below |

## Detail

### capital_health — ALL LIVE
- `assets`: LIVE — changing asset amounts changes conservation output. ✅
- `liabilities`: LIVE — changing liability amounts changes conservation output. ✅
- `income`: LIVE — changing income amounts changes flow output. ✅
- `expenses`: LIVE — changing expense amounts changes flow output. ✅
- `survival_submode`: LIVE — `corporate_runway` vs `personal_finance` route to different paths. ✅
- **tool_name**: CORRECT — reports `capital_health` not `capital_market`. ✅

### capital_entropy.power_consequence_map — ALL LIVE
- `decision_makers` count: LIVE — adding/removing members changes `power_concentration`. ✅
- `beneficiaries` count: LIVE — adding/removing beneficiaries changes `benefit_concentration`. ✅
- `cost_bearers` count: LIVE — adding/removing bearers changes `harm_distance` + `consequence_gap`. ✅
- `veto_holders` presence: LIVE — adding veto holders changes `veto_concentration`. ✅

### capital_diagnose.collapse_signature — LIVE
- `payload.scenario` text: LIVE — "stable company" vs "Enron-like" produce different signals. ✅
  - Enron-like text: axis_1 (national_destiny_triumphalism) fires on "all-time high"
  - related_party signals fire on "off-balance-sheet" and "related-party"
  - But overall `risk_level: MINIMAL` — assessment is conservative to the point of blindness

### capital_diagnose.stress_index — CONDITIONAL
- `payload.financial_signals`: LIVE only for 7 recognized corporate field names
- **21 recognized fields across 5 dimensions:**
  - financial: profit_change_pct, revenue_change_pct, cost_cutting_announced, sovereign_extraction, cffo, fcf, gearing
  - governance: board_resignations_12m, company_secretaries_as_directors, avg_tenure_years, governance_separation_index
  - workforce: rightsizing_pct, voluntary_exits_pct, key_personnel_departures
  - legal: active_litigation_count, injunction_value_musd, regulatory_uncertainty_score
  - exploitation: counterparty_payment_freeze, interpleader_filed, competing_claims
- **Any field NOT in this vocabulary → silently dropped, counted as MISSING**
- **Fields present with aliases**: recognized via `_FIELD_ALIASES` mapping
- When 0/21 fields present → `risk_level: INSUFFICIENT_DATA` (correct downgrade)

### capital_diagnose (modes not yet tested)
- capture_scan: W0 flagged coverage=0.0 — likely same text-classifier pattern as collapse_signature
- power_audit: W0 flagged coverage=0.0 — likely same
- cadence_monitor: W0 flagged coverage=0.0 but tool works correctly (2/5 dims active)

### capital_market — NOT TESTED
- All 7 modes depend on live market data — differential/ingestion tests unstable

## Known Defects (from W-000 + W-002)

| # | Defect | Severity | Tools Affected |
|---|--------|----------|----------------|
| 1 | `stress_index` recognizes only 21 corporate field names — any other field silently dropped | HIGH | capital_diagnose |
| 2 | `collapse_signature` returns MINIMAL risk for Enron-description scenario | HIGH | capital_diagnose |
| 3 | `capture_scan` returns LOW risk for CFO-controlled entity language | HIGH | capital_diagnose |
| 4 | `petronas_vitals` crashes with MCP -32602 (output schema mismatch) | HIGH | capital_diagnose |
| 5 | W0 duplicates warnings in content sync path | LOW | all |
| 6 | `cadence_monitor` W0 false-positive — tool works but payload field name != result field name | LOW | capital_diagnose |

## Surprises (from W-002)

- **Prior report of `capital_health` returning `tool_name: capital_market` was stale or environmental** — live probe shows correct `tool_name: capital_health`. The fix may have already landed.
- **`capital_entropy.power_consequence_map` IS content-sensitive at the tool level** — all 4 tested fields are LIVE. The Holocaust backtest showed correct differentiation (Enron vs Berkshire payloads). The remaining defect is semantic (model vocabulary) not mechanical (dead fields).
