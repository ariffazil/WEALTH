# WEALTH Epistemic Ladder

> **URI:** wealth://policy/epistemic-ladder
> **Version:** 2026.06.27
> **DITEMPA BUKAN DIBERI — Forged, not given.

---

## Evidence Grades

Every WEALTH claim must be labeled with one of four epistemic grades.

| Grade | Label | Definition | Confidence Ceiling |
|-------|-------|-----------|-------------------|
| **OBS** | Observed | Direct observation, official source, timestamped | 0.95 |
| **DER** | Derived | Computed from OBS with explicit methodology | 0.90 |
| **INT** | Interpreted | Inferred from multiple DER/INT with stated assumptions | 0.75 |
| **SPEC** | Speculation | Hypothesis, pattern match, or model output without full validation | 0.60 |

---

## Grade Application Rules

### OBS — Observed
- Source: BNM OpenAPI, Bursa filings, SEC EDGAR, IMF, World Bank, PETRONAS public reports
- Must include: timestamp or as-of-date, source class (P1/P2), URL or URI
- Never use precise decimals — use rounded values that reflect source resolution
- Example: `BNM FX rate USD/MYR = 4.7210 as of 2026-06-26 (OBS, P1, BNM OpenAPI)`

### DER — Derived
- Computed via `wealth_compute_npv`, `wealth_compute_irr`, `wealth_compute_emv`, etc.
- Must include: inputs with source URIs, methodology, assumptions stated explicitly
- Confidence ceiling 0.90 even with perfect inputs
- Example: `NPV = +RM42.1M (DER, inputs: OBS×3, discount_rate=10%, DER ceiling=0.90)`

### INT — Interpreted
- Domain expert judgment combining multiple DER/INT sources
- Must state: which evidence supports, which evidence contradicts, what assumptions are being made
- Confidence ceiling 0.75 — do not present as near-certain
- Example: `POS = 35% (INT, seismic leads support, well control sparse, INT ceiling=0.75)`

### SPEC — Speculation
- Model output, pattern match, counterfactual, or forecast
- Must be labeled SPEC explicitly, not mixed into DER/INT conclusions
- Confidence ceiling 0.60 — do not use SPEC in financial authorization paths without downgrade
- Example: `Future Brent scenario USD 95/bbl by Q4 2026 (SPEC, no formal model, SPEC ceiling=0.60)`

---

## Forbidden Grade Labels

- ❌ `CERTAIN` / `CONFIRMED` / `VERIFIED` — WEALTH never claims these
- ❌ No grade = DER by default — always label explicitly
- ❌ Mixing grades within a single conclusion — separate them

---

## Typed Output Annotation

Every typed artifact from WEALTH must include per-field epistemic grades:

```json
{
  "npv": {
    "value": 42100000,
    "unit": "RM",
    "grade": "DER",
    "inputs": ["obs:bnm_discount_rate", "der:capex_estimate", "obs:production_profile"],
    "confidence_ceiling": 0.90,
    "actual_confidence": 0.82
  }
}
```
