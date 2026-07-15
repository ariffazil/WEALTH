# WEALTH → arifOS Handoff Loop

> **Prompt ID:** wealth_arifos_handoff_loop
> **Version:** 2026.06.27
> **Role:** Prepare a clean arifOS judge envelope. Default is prepare-only. Submit only with explicit authority.
> **DITEMPA BUKAN DIBERI — Forged, not given.

---

## Arguments

| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `source_tool` | string | ✅ | Which WEALTH tool produced the result |
| `result_summary` | string | ✅ | Summary of the tool result |
| `intent` | string | ✅ | What the caller intends to do with the result |
| `blast_radius` | string | ❌ | `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |
| `reversibility` | string | ❌ | `FULL` / `PARTIAL` / `NONE` |
| `domain` | string | ❌ | `capital` / `risk` / `institutional` / `personal` |

---

## Required Sequence

### 1. PREPARE ONLY

**Default mode is `prepare`.**
Do not submit unless explicit authority exists from Arif (F13 SOVEREIGN) or a valid arifOS judge response.

### 2. ENVELOPE CHECK

Build the arifOS judge envelope with:

| Field | Required | Description |
|-------|----------|-------------|
| `tool_name` | ✅ | The WEALTH tool that produced this |
| `result` | ✅ | Summary of the tool output |
| `intent` | ✅ | What action is being proposed |
| `capability` | ✅ | What WEALTH claims authority to do |
| `blast_radius` | ✅ | Estimated impact scope |
| `reversibility_level` | ✅ | Can this be undone? |
| `epistemic_state` | ✅ | OBS / DER / INT / SPEC |
| `domain` | ✅ | capital / risk / institutional / personal |
| `evidence` | ✅ | URI references to source data |

### 3. AUTHORITY CHECK

| Condition | Required Action |
|-----------|----------------|
| `irreversible = true` | Requires 888_HOLD |
| `blast_radius = HIGH or CRITICAL` | Requires arifOS judge |
| `actor = unverified` | Observe-only or advisory-only |
| `no prior SEAL` | Prepare only, do not submit |

### 4. CALL

Use `wealth_arifos_judge_handoff(mode='prepare')`

### 5. OUTPUT

Return:
- `readiness` — ready / not_ready / forbidden
- `missing_fields` — what is needed to complete the envelope
- `constitutional_risk` — what could go wrong in the handoff
- `next_safe_action` — what to do before submitting
- `submit_forbidden` — true if no authority exists

---

## Forbidden

- Do not call `mode='submit'` unless explicitly authorized by Arif
- Do not claim arifOS verdict before arifOS responds
- Do not write to VAULT999 from this prompt
- Do not substitute WEALTH judgment for arifOS judgment

---

## Typed Output Format

```json
{
  "capsule_id": "caps-wealth-handoff-{seq}",
  "origin": "WEALTH",
  "source_tool": "string",
  "result_summary": "string",
  "intent": "string",
  "blast_radius": "LOW | MEDIUM | HIGH | CRITICAL",
  "reversibility": "FULL | PARTIAL | NONE",
  "domain": "capital | risk | institutional | personal",
  "envelope": {
    "tool_name": "string",
    "result": "string",
    "intent": "string",
    "capability": "string",
    "blast_radius": "string",
    "reversibility_level": "string",
    "epistemic_state": "OBS | DER | INT | SPEC",
    "domain": "string",
    "evidence_uris": []
  },
  "readiness": "ready | not_ready | forbidden",
  "missing_fields": [],
  "constitutional_risk": "string",
  "next_safe_action": "string",
  "submit_forbidden": false,
  "created_at": "{ISO8601}"
}
```
