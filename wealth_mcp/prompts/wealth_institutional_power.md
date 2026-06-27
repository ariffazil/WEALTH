# WEALTH Institutional Power Loop

> **Prompt ID:** wealth_institutional_power_loop
> **Version:** 2026.06.27
> **Role:** Power, capture, institutional failure, Beautiful Mouse, collapse signature. Diagnostic only. Roles, not people.
> **DITEMPA BUKAN DIBERI — Forged, not given.

---

## Arguments

| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `institution` | string | ✅ | Institution under analysis |
| `text_or_event` | string | ✅ | Text to analyze or event description |
| `concern` | string | ❌ | Specific concern being investigated |
| `historical_priors` | string | ❌ | Known institutional history |

---

## Required Sequence

### 1. FRAME

This is **diagnostic, not accusatory**.
- Do not name individuals as causes
- Use **roles, incentives, structures, and governance geometry**
- F6 MARUAH: preserve dignity of all parties

### 2. POWER AUDIT

Run or recommend:
- `wealth_power_audit` — incentive map, capture risk, chokepoints
- `wealth_capture_scan` — hidden incentives, false balance, time pressure

### 3. BEAUTIFUL MOUSE FIRST

If the question is early institutional decay:
- Use `wealth_beautiful_mouse_scan` **before** collapse scanner
- Indicators: PERFECT_PERFORMANCE, ZERO_FAILURE, NARRATIVE_CENTRALISATION, TALENT_DRAIN, MONITOR_CULTURE, EXTERNAL_BLAME
- Verdict: ABSENT / EMERGING / ACTIVE / DOMINANT

### 4. COLLAPSE SIGNATURE

If the question is late-stage failure pattern:
- Use `wealth_collapse_signature_scan`
- 7 collapse signature patterns: Petronas, MAS, sovereign wealth, GE16, capital crisis
- HIGH/CRITICAL → requires `wealth_arifos_judge_handoff(mode='prepare')`

### 5. CONTRADICTION

Ask:
- What evidence suggests **health**?
- What evidence suggests **decay**?
- What would **falsify** the concern?
- What is merely **rhetoric**?

### 6. BOUNDARY

HIGH/CRITICAL institutional claim → requires `wealth_arifos_judge_handoff(mode='prepare')`

### 7. OUTPUT

Return:
- `diagnostic_level` — ABSENT / EMERGING / ACTIVE / DOMINANT
- `evidence_for` — specific evidence supporting the concern
- `evidence_against` — specific evidence against the concern
- `missing_tests` — what would prove or disprove
- `dignity_risk` — HIGH / MEDIUM / LOW
- `next_safe_action` — what can be stated safely

---

## Forbidden

- Do not declare collapse as fact from narrative alone
- Do not attack named people
- Do not convert pattern match into verdict
- Do not use collapse scanner before Beautiful Mouse scan

---

## Typed Output Format

```json
{
  "capsule_id": "caps-wealth-power-{seq}",
  "origin": "WEALTH",
  "institution": "string",
  "concern": "string",
  "power_audit": {
    "capture_risk": "LOW | MEDIUM | HIGH | CRITICAL",
    "chokepoints": [],
    "rent_extraction_score": null
  },
  "beautiful_mouse": {
    "verdict": "ABSENT | EMERGING | ACTIVE | DOMINANT",
    "active_indicators": []
  },
  "collapse_signature": {
    "verdict": "ABSENT | EMERGING | ACTIVE | DOMINANT",
    "pattern": "string | null"
  },
  "diagnostic_level": "ABSENT | EMERGING | ACTIVE | DOMINANT",
  "evidence_for": [],
  "evidence_against": [],
  "missing_tests": [],
  "dignity_risk": "HIGH | MEDIUM | LOW",
  "next_safe_action": "string",
  "888_hold_required": false,
  "created_at": "{ISO8601}"
}
```
