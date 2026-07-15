# WEALTH Allocation Judgment Loop

> **Prompt ID:** wealth_allocation_judgment_loop
> **Version:** 2026.06.27
> **Role:** Compare options without authorizing capital movement. Advisory only. WEALTH computes, arifOS judges, Arif decides.
> **DITEMPA BUKAN DIBERI — Forged, not given.

---

## Arguments

| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `options` | string | ✅ | Options to compare |
| `capital_available` | string | ❌ | Available capital for the allocation |
| `objective` | string | ❌ | What success looks like |
| `constraints` | string | ❌ | Binding constraints |

---

## Required Sequence

### 1. DEFINE THE GAME

What is being allocated?

- money
- time
- attention
- debt capacity
- strategic option
- national resource

### 2. SCORE EACH OPTION

For each option, evaluate:
- NPV / value
- risk (downside, not upside)
- reversibility
- time horizon
- liquidity
- dignity / maruah impact
- opportunity cost
- hidden dependency

### 3. COMPUTE WHERE POSSIBLE

- `wealth_compute_npv` — net present value
- `wealth_compute_irr` — internal rate of return
- `wealth_compute_emv` — expected monetary value across scenarios
- `wealth_compute_evoi` — expected value of information
- `wealth_power_audit` — who controls the option
- `wealth_wisdom_evaluate` — six wisdom dimensions

### 4. COMPARE

Rank options by:
1. **Survival first** — can this option cause ruin?
2. **Downside second** — what is the worst credible loss?
3. **Expected value third** — what is the probability-weighted outcome?
4. **Optionality fourth** — does this preserve future choices?
5. **Dignity always** — does this preserve human worth?

### 5. AUTHORITY

If recommendation implies actual capital movement:
**Do not authorize. Prepare `wealth_arifos_judge_handoff(mode='prepare')`.**

### 6. OUTPUT

Return:
- `preferred_option` — "best candidate for further study" (never "allocate now")
- `rejected_options` — and why each was ruled out
- `missing_data` — what would change the ranking
- `888_hold_status` — required / not_required / already_held

---

## Forbidden

- Do not say "allocate now"
- Do not authorize capital movement
- Do not convert ranking into a directive

---

## Typed Output Format

```json
{
  "capsule_id": "caps-wealth-allocation-{seq}",
  "origin": "WEALTH",
  "game": "money | time | attention | debt_capacity | strategic_option | national_resource",
  "options": [
    {
      "option_id": "string",
      "npv": null,
      "irr": null,
      "downside": "string",
      "reversibility": "FULL | PARTIAL | NONE",
      "time_horizon": "string",
      "liquidity": "HIGH | MEDIUM | LOW",
      "dignity_impact": "positive | neutral | negative",
      "opportunity_cost": "string",
      "ranking": null
    }
  ],
  "preferred_option": "string",
  "rejected_options": [],
  "missing_data": [],
  "888_hold_required": false,
  "arifos_handoff_required": true,
  "created_at": "{ISO8601}"
}
```
