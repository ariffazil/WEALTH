# WEALTH Risk + Downside Loop

> **Prompt ID:** wealth_risk_downside_loop
> **Version:** 2026.06.27
> **Role:** Force downside-first analysis before any expected-value claim. Stock pre-trade logic folded here.
> **DITEMPA BUKAN DIBERI — Forged, not given.

---

## Arguments

| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `decision` | string | ✅ | The decision or commitment under consideration |
| `scenarios` | string | ❌ | Scenario descriptions (base, upside, downside, ruin) |
| `evidence_quality` | string | ❌ | `strong` / `moderate` / `weak` / `unknown` |
| `irreversible` | string | ❌ | `true` or `false` |

---

## Required Sequence

### 1. DOWNSIDE FIRST

State the **worst credible loss** before the expected gain.
Do not lead with the upside.

### 2. SCENARIO MAP

Identify:
- **base case** — most likely outcome
- **upside case** — favorable scenario
- **downside case** — adverse scenario
- **ruin case** — catastrophic loss
- **missing scenario** — what scenario is conspicuously absent

### 3. COMPUTE

Use only if inputs exist:
- `wealth_compute_emv` — expected monetary value across scenarios
- `wealth_compute_evoi` — expected value of information
- `wealth_monte_carlo_simulate` — distribution of outcomes
- `wealth_asymmetry_check` — is the distribution skewed?
- `wealth_confluence_check` — are indicators measuring the same signal?

### 4. CONTRADICTION

Ask:
- Are indicators independent?
- Is confluence fake?
- Is one assumption carrying the whole thesis?
- **What evidence would reverse the conclusion?**

### 5. BOUNDARY

- If `irreversible=true` → prepare `wealth_arifos_judge_handoff(mode='prepare')`
- If downside is HIGH/CRITICAL → prepare `wealth_arifos_judge_handoff(mode='prepare')`
- Evidence quality `weak` → increase uncertainty bounds, do not sharpen

### 6. OUTPUT

Return:
- `risk_verdict` — LOW / MEDIUM / HIGH / CRITICAL
- `dominant_risk` — the single largest exposure
- `missing_data` — what would change the verdict
- `888_hold_required` — true/false

---

## Forbidden

- Do not hide downside behind expected value
- Do not use precise decimals when evidence quality is weak
- Do not present one scenario as certain

---

## Typed Output Format

```json
{
  "capsule_id": "caps-wealth-risk-{seq}",
  "origin": "WEALTH",
  "decision": "string",
  "scenario_map": {
    "base_case": "string",
    "upside_case": "string",
    "downside_case": "string",
    "ruin_case": "string",
    "missing_scenario": "string"
  },
  "emv": null,
  "evoi": null,
  "monte_carlo_pctl_5": null,
  "monte_carlo_pctl_95": null,
  "asymmetry_ratio": null,
  "risk_verdict": "LOW | MEDIUM | HIGH | CRITICAL",
  "dominant_risk": "string",
  "missing_data": [],
  "contradiction_flags": [],
  "888_hold_required": false,
  "created_at": "{ISO8601}"
}
```
