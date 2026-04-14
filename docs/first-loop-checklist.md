# First Governed Loop — Acceptance Test Checklist

> **Target:** One sovereign loan decision, end-to-end, from state → control → VAULT999.  
> **Epistemic:** ESTIMATE  
> **Status:** Phase A Exit Gate  
> **DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**

---

## Pre-Flight

- [ ] `node --version` ≥ 22
- [ ] `WEALTH/data/vault999.jsonl` exists and is append-only
- [ ] `WEALTH/scripts/run-first-loop.js` is present and executable
- [ ] No missing `host/kernel/*.js` files block imports (use inline stubs if necessary)

---

## Step-by-Step Verification

### 1. State — Market Snapshot
- [ ] Tool `wealth.state.marketsnapshot` returns `rf_curve`, `erp`, `capital_temperature`
- [ ] All outputs tagged `ESTIMATE`
- [ ] Request includes `envelope_id`

### 2. Risk — Capital Allocation
- [ ] Tool `wealth.risk.capitalallocation` returns `economic_capital`, `risk_budgets`, `liquidity_buffer`
- [ ] No bucket breaches `maruah_drawdown_floor` (default 0.6)
- [ ] If breach detected, chain routes to `wealth.control.gate888` before pricing

### 3. Price — Exergy Cost
- [ ] Tool `wealth.price.exergycost` returns `exergy_mj_per_unit`, `entropy_cost_per_unit`
- [ ] Values are non-negative and finite

### 4. Justice — Maruah Score
- [ ] Tool `wealth.justice.maruahscore` returns `maruah_score` ∈ [0,1]
- [ ] `maruah_band` is one of: `SOVEREIGN`, `STABLE`, `FLOOR`, `AMBER`, `RED`
- [ ] `incidence_map` identifies who bears cost / receives benefit

### 5. Price — capitalx
- [ ] Tool `wealth.price.capitalx` returns `r_adj` ≥ 0
- [ ] `adjustments` object contains full breakdown: `entropy_penalty`, `peace_discount`, `maruah_discount`, `trust_discount`, `civ_discount`
- [ ] `uncertainty_band` array has exactly 2 elements
- [ ] If `wealth_basis` + `defects` provided, `deltaCiv` is promoted via basis formula
- [ ] Monotonicity check: if `dS` or `shadow` increased, `r_adj` did not decrease

### 6. Flow — Scenario NPV
- [ ] Tool `wealth.flow.scenarionpv` returns `npv_distribution`, `irr`, `payback_years`
- [ ] Discounting uses `r_adj` from step 5, not naive WACC
- [ ] Any scenario with `Peace² < 1.0` or `ΔS > 0` (unheld) is downgraded to `VOID`

### 7. Control — Gate 888
- [ ] Tool `wealth.control.gate888` returns `hold_triggered`, `recommendation`, `repricing_hints`
- [ ] Trigger conditions evaluated:
  - [ ] `maruah < 0.4` → `888-HOLD`
  - [ ] `reversible === false && !human_confirmed` → `888-HOLD`
  - [ ] `entropy_budget_remaining < 0` → `VOID`
- [ ] `upstream_signal` string is present for telemetry back to arifOS/GEOX

### 8. Seal — VAULT999
- [ ] Final VAULT999 entry appended to `data/vault999.jsonl`
- [ ] Entry contains:
  - [ ] `event` type (e.g. `SOVEREIGN_LOAN_DECISION`)
  - [ ] `envelope_id`
  - [ ] `verdict` (`SEALED`, `888-HOLD`, or `VOID`)
  - [ ] `witness`: `{ human, ai, earth }`
  - [ ] `telemetry` block with `dS`, `peace2`, `r_adj`, `maruah`, `delta_bps`
  - [ ] `integrity_hash` (SHA-256 prefix)
  - [ ] `epoch` (ISO8601, non-decreasing)

---

## Failure-Mode Acceptance

| Failure | Expected Behavior | Pass/Fail |
|---|---|---|
| Missing `envelope_id` | F3 SABAR returned; tool refuses execution | |
| Rate inversion (`r_adj` drops while `dS` rises) | F12 hard block; output rejected; anomaly logged | |
| Justice bypass (maruah omitted) | F6 VOID; capital flow blocked | |
| Black-box pricing (missing `adjustments`) | Epistemic forced to `UNKNOWN`; warning issued | |
| Orphan control (gate888 before price/justice) | Rejected; prerequisite seals required | |

---

## Delta-bps Capture (for Δbps_proven path)

- [ ] Classical `r` computed and recorded
- [ ] `wealth.price.capitalx` `r_adj` computed and recorded
- [ ] `delta_bps` = `(r_classical - r_adj) * 10,000` is stored in VAULT999
- [ ] Decision rationale from `gate888` is stored alongside

---

## Sign-Off

Once all boxes are checked and VAULT999 contains at least one clean `SEALED` sovereign loan record:

**Phase A Framework:** ✅ Validated  
**Next move:** Select first *real* transaction for Δbps_proven.

---

*Checklist v1.0.0 | 999 SEAL ALIVE*
