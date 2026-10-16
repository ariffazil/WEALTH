# Research roadmap — NOT current performance claims
> **Moved from README.md** during the AGENTIC-README-DOCTRINE v1 restructure, 2026-10-16.
> Everything on this page is **planned or deferred research**, not demonstrated capability.
> Source archive: `docs/archive/README-2026-10-16-pre-doctrine.md`.

## CHRON × WEALTH — the prediction → outcome → calibration loop

```
WEALTH predicts   capital consequence / probability / risk band / falsifier
CHRON records     what WEALTH believed / when / using what evidence
Reality occurs
CHRON verifies    vs predicted
WEALTH recalibrates
HERMES checks    narrative distortion
arifOS governs    future use
```

This gives Prediction → Outcome → Calibration → ImprovedCapitalModel rather than endless
investment commentary. **Status: deferred** — no forecast calibration has been published.

## Historical collapse replay — discipline required

Replay historical financial collapses using only information available before the collapse.
The proposed benchmark requires:

- `case` (e.g., 2008 GFC, 1997 Asian crisis)
- `cutoff_date` with **mechanically enforced evidence cutoffs** — a recorded source
  allowlist, contamination tests and negative controls. (The stronger phrase "cryptographic
  exclusion" is reserved for when an actual commitment/hash/signature mechanism exists and
  is documented — it does not yet.)
- `allowed_sources` (only what was available before cutoff)
- `forbidden_future_sources` (regression test against contamination)
- `predicted_signal`, `actual_failure`
- `false_positive_controls` (firms that looked bad but survived)
- `score`

The proper test is `Model(E_{t<collapse}) → RiskSignal_t` with all post-cutoff evidence
excluded mechanically. Without negative controls, the demonstration collapses into
`FailedCompany → FindWarningSigns`, which is much easier. CHRON's prediction ledger is the
substrate for this benchmark. **Status: not implemented, not published.**

## P1 execution checklist (dated record)

This packet (P1, 2026-09-21) executed 4 of 7 items specified by the sovereign; the rest are deferred:

- ✅ **1** Fix session-envelope interface so arifOS → WEALTH works end-to-end without losing identity/authority.
- ✅ **2** Declare the Ω00–Ω12 surface canonical; move old `capital_*` names into an explicit compatibility layer.
- ✅ **3** Remove constitutional verdict ownership from `wealth_synthesize`; make its output explicitly advisory/domain-level.
- ⏭ **4** Repin and test the `capital_polix` schema drift (done in FEDERATION-CONVERGENCE-P0).
- ✅ **5** Make freshness/provenance mandatory on every market/macro output.
- 📋 **6** CHRON-linked forecast calibration before claiming predictive superiority (deferred).
- 📋 **7** Historical-collapse replay as a proper pre-cutoff benchmark with negative controls (deferred).
