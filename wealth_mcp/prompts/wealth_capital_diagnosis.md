# WEALTH Capital Diagnosis Loop

> **Prompt ID:** wealth_capital_diagnosis_loop
> **Version:** 2026.06.27
> **Role:** Diagnose capital health across conservation, flow, survival, value, and Malaysian-specific duties.
> **DITEMPA BUKAN DIBERI — Forged, not given.

---

## Arguments

| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `case` | string | ✅ | Capital case to diagnose |
| `scale` | string | ❌ | `personal` (default) or `project` or `institutional` |
| `numbers_available` | string | ❌ | Available financial data |
| `horizon` | string | ❌ | Time horizon for the analysis |

---

## Required Sequence

### 1. CONSERVATION

What assets, liabilities, reserves, and obligations exist?

- Use `wealth_conservation_check` for institutional
- Use `wealth_personal_finance(mode='net_worth')` for personal

### 2. FLOW

What income, expenses, burn, or cashflow exists?

- Use `wealth_flow_check` for institutional
- Use `wealth_personal_finance(mode='summary')` for personal

### 3. SURVIVAL

How long can the system survive under current burn?

- Use `wealth_runway_check`
- Use `wealth_personal_finance(mode='runway')` for personal

### 4. VALUE

If this is a project or deal, compute:
- NPV via `wealth_compute_npv`
- IRR via `wealth_compute_irr`
- EMV via `wealth_compute_emv` if scenarios exist

### 5. MALAYSIAN DUTIES

If personal Malaysian wealth is involved, check:
- **EPF readiness** — `wealth_personal_finance(mode='epf')`
- **zakat** if wealth is above nisab — `wealth_personal_finance(mode='zakat')`

### 6. OUTPUT

Return:
- `capital_health` — healthy / marginal / distressed / unknown
- `weakest_number` — the binding constraint
- `missing_data` — what is needed
- `downside_case` — worst credible case
- `next_safe_action` — what can be done now

---

## Forbidden

- Do not recommend moving money
- Do not say "financially safe" without downside and uncertainty
- Do not use precise decimals when evidence is weak

---

## Typed Output Format

```json
{
  "capsule_id": "caps-wealth-capital-{seq}",
  "origin": "WEALTH",
  "diagnosis": {
    "conservation": { "assets": [], "liabilities": [], "net_worth": null },
    "flow": { "income": [], "expenses": [], "burn_rate": null },
    "survival_months": null,
    "value": { "npv": null, "irr": null, "emv": null },
    "malaysian_duties": { "epf_ready": null, "zakat_liable": null }
  },
  "capital_health": "healthy | marginal | distressed | unknown",
  "weakest_number": "string",
  "missing_data": [],
  "downside_case": "string",
  "next_safe_action": "string",
  "created_at": "{ISO8601}"
}
```
