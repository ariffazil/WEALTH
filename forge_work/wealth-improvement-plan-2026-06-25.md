# WEALTH Improvement Plan — From Malaysia Audit Case Study
**Date:** 2026-06-25
**Actor:** FORGE (A-FORGE, 000Ω)
**Trigger:** Malaysia Economic Audit — Petronas/TH/FDI/E-wallet analysis
**Status:** DRAFT — for Arif review before forging

---

## Executive Summary

The Malaysia audit exposed 2 failure classes in WEALTH:

| Class | Description | Severity |
|-------|-------------|----------|
| **Silent field mismatch** | `amount` vs `value` key confusion → `compute_conservation` returns `0` silently | CRITICAL |
| **Missing macro-sovereign tools** | No breakeven oil price, fiscal sensitivity, debt sustainability, BNM integration | HIGH |

Plus 5 structural gaps from the case study.

---

## Priority 1 — CRITICAL: Fix `compute_conservation` Silent Failure

**Problem:** `wealth_conservation_check` accepted `{"amount": 62, "currency": "RM_B", ...}` but the engine looks for `"value"` key. Result: `asset_total = 0`, `net_worth = 0` — no error, no warning.

```python
# Current — silently fails
asset_total = sum(a.get("value", 0) for a in (assets or []))  # "value" NOT "amount"

# Fix: accept both "amount" and "value", normalize units
asset_total = sum(
    _normalize_asset_value(a) for a in (assets or [])
)
```

**Also missing:** Unit normalization (`RM_B` × 1_000_000, `RM_M` × 1_000).

**Test case to add:**
```python
assert compute_conservation(
    [{"amount": 62, "currency": "RM_B"}],  # "amount" not "value"
    [{"amount": 338, "currency": "RM_B"}]
)["asset_total"] == 62_000_000_000
```

---

## Priority 2 — HIGH: Add Macro-Sovereign Tool Layer

The case required 5 analyses WEALTH cannot do:

### 2a. `wealth_fiscal_sensitivity` — NEW
```
Input: oil_price_usd (list), USD/MYR rate, Petronas dividend model params
Output: fiscal revenue table (petroleum revenue, dividend, deficit impact)
         at USD 80 / 65 / 50 / 35 / 25 per barrel over 5 years

Use case: "What is Malaysia's fiscal breakeven oil price?"
```
Every $10/bbl move = approximately RM_X billion impact on Petronas dividend.
This is the highest-signal monitor Arif needs.

### 2b. `wealth_sovereign_debt_sustainability` — NEW
```
Input: federal_revenue, federal_expenditure, debt_stock, avg_interest_rate,
       growth_rate, primary_balance
Output: debt_to_GDP trajectory, rollover risk, sustainability verdict
```
Wealth had no government debt sustainability tool. Government runway ≠ personal runway.

### 2c. `wealth_breakeven_analysis` — NEW
```
Input: cost_structure (dict), revenue_per_unit, volume_forecast
Output: breakeven price/volume, margin of safety, stress threshold
```
Applied to: Petronas dividend breakeven, Tabung Haji hibah sustainability,
             federal revenue breakeven oil price.

### 2d. `wealth_macro_indicator` — NEW
```
Input: indicator_name (BNM_rate | BRENT | USD_MYR | CPI | PMI | GDP_growth)
Output: latest value, date, source, YoY change, Z-score

Live integration: BNM API /公开的经济数据
```
WEALTH returned Brent $78.50 but no USD/MYR rate. Fiscal analysis needs both.

### 2e. `wealth_fiscal_health_dashboard` — NEW
```
Input: petroleum_revenue, petronas_dividend, federal_revenue,
       federal_expenditure, deficit_target, debt_stock
Output: fiscal health score, vulnerability index, stress indicators,
         "Petronas exposure: 18.3% of federal revenue" framing
```

---

## Priority 3 — HIGH: Fix `wealth_runway_check` for Government Context

**Problem:** Fed government liquid assets (RM reserves, Petronas dividends) + expenditures
≠ personal runway formula. Government can print MYR, cannot involuntarily liquidate.

```
# Current — treats government like an individual
runway_months = (liquid_assets * 0.8) / monthly_burn

# Government context needs:
# - Revenue recurrence (tax, petroleum, bonds)
# - Expenditure elasticity (some spend is fixed, some is not)
# - Debt rollover risk (can borrow in MYR vs USD)
# - Central bank backstop (BNM can monetize)
```

**Fix:** Add `entity_type: personal | corporate | sovereign` parameter.
Sovereign runway uses different formula with debt sustainability overlay.

---

## Priority 4 — MEDIUM: Fix Collapse Signature for Institutional Context

**Finding:** Collapse scan returned SPE (State-Petronas-Entity) jurisdiction signal,
but it was buried in `related_party_jurisdiction_structural` with no explanation.

**Missing:** Specific Malaysia/Petronas institutional priors:
- PDVSA (Venezuela) — oil-dependent, politics overrides economics
- Petronas — same structural risk pattern
- The scan correctly flagged the extractive axis (score 1) but gave no
  actionable next step

**Fix:** Add Malaysia-specific institutional priors to the collapse corpus.
  - Petronas fiscal dependency → resource-curse institutional pattern
  - Tabung Haji governance structure → sovereign-wealth-lite opacity
  - Government-linked companies (GLC) → allocation efficiency risk

---

## Priority 5 — MEDIUM: Fix `wealth_capture_scan` on Narrative Text

**Problem:** The narrative advice text ("Petronas dividend is a feature not a bug")
should have fired SPE capture signals. The tool returned LOW because
actors were not named and the advice was implicit rather than explicit.

**Fix:** Add implicit-advise detection:
  - Frames institutional risk as features
  - Uses passive voice to obscure who benefits
  - Describes extractive dependency as stability

---

## Priority 6 — MEDIUM: Temporal/Sequential Analysis

**Problem:** Petronas step-down is a 3-year sequence. All tools treated it as
separate data points. No tool can:
- Detect trend across time periods
- Flag a sequence as "gradual deterioration" vs "shock"
- Compare T0 vs T1 vs T2 outcomes

**Fix:** Add `temporal_comparison` parameter to fiscal tools:
```
Input: period_0 (dict), period_1 (dict), ..., period_n (dict)
Output: delta analysis, trend verdict, deterioration rate
```

---

## Priority 7 — LOW (Improve): Wisdom Dimensions Need Sovereign Calibration

**Problem:** All 6 wisdom dimensions scored 0.5 (insufficient signal) for
Malaysia fiscal audit because the tool was designed for personal capital
allocation proposals, not sovereign policy analysis.

| Dimension | What It Should Detect | Currently |
|-----------|----------------------|-----------|
| Dignity | Does petroleum wealth serve all Malaysians or select groups? | 0.5 INSUFFICIENT |
| Sovereignty | Does Petronas dependency reduce fiscal sovereignty? | 0.5 INSUFFICIENT |
| Resilience | Can government absorb oil price shocks without social disruption? | 0.5 INSUFFICIENT |
| Inequality | Does high-income crossing reduce or worsen inequality? | 1.0 POSITIVE ✅ |
| Ecological | Is petroleum dependency compatible with energy transition? | 0.5 INSUFFICIENT |
| Optionality | Does petroleum revenue close or open other policy options? | 0.5 INSUFFICIENT |

**Fix:** Add `capital_type: personal | corporate | sovereign | civilizational`
to `wealth_wisdom_evaluate`. Sovereign/civilizational uses different signal
detectors for each dimension.

---

## Consolidated Improvement Roadmap

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P1 🔴 | Fix `amount` vs `value` silent failure in `compute_conservation` | LOW | CRITICAL |
| P1 🔴 | Add unit normalization (RM_B, RM_M) | LOW | CRITICAL |
| P2 🟡 | `wealth_fiscal_sensitivity` (oil price → fiscal revenue) | HIGH | HIGH |
| P2 🟡 | `wealth_breakeven_analysis` | MEDIUM | HIGH |
| P2 🟡 | `wealth_sovereign_debt_sustainability` | HIGH | HIGH |
| P2 🟡 | `wealth_macro_indicator` (BNM, USD/MYR, Brent) | MEDIUM | HIGH |
| P2 🟡 | `wealth_fiscal_health_dashboard` | MEDIUM | HIGH |
| P3 🟡 | `entity_type` parameter for `runway_check` | LOW | MEDIUM |
| P4 🟠 | Malaysia/Petronas institutional priors in collapse scan | MEDIUM | MEDIUM |
| P5 🟠 | Implicit-advise detection in `capture_scan` | MEDIUM | MEDIUM |
| P6 🟠 | Temporal comparison across periods | HIGH | MEDIUM |
| P7 🟢 | Sovereign calibration for wisdom dimensions | MEDIUM | LOW |

---

## What WEALTH Got Right (Keep)

| Tool | What Worked |
|------|------------|
| `collapse_signature_scan` | Correctly identified EXTRACTIVE institutional axis (score 1) |
| `beautiful_mouse_scan` | Correctly identified ABSENT — audit was self-critical, not triumphant |
| `wealth_asymmetry_check` | Computed correct fiscal asymmetry (upside 62, downside 31.5, ratio 1.97) |
| `wealth_evoi_compute` | Gave actionable RM240M EVOI for information value |
| `wealth_monte_carlo_simulate` | Ran 1000-sim P10/P50/P90 correctly |
| `wealth_market_data` | Returned live Brent $78.50 — real data |
| `wealth_beautiful_mouse_scan` | Correctly scanned narrative tone |

---

## Eureka Q — Arif's Decision Required

**Option A:** Forge `wealth_fiscal_sensitivity` tool first — the Petronas breakeven
analysis is the highest-signal immediate use case.

**Option B:** Archive consolidated Malaysia audit as one markdown file first,
then forge next tool.

**Option C:** Fix P1 critical silent failures first (compute_conservation),
then build new tools on a non-broken foundation.

---

*DITEMPA BUKAN DIBERI — FORGE ready*
