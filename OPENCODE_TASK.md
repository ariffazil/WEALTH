You are a coding agent working in `/tmp/wealth-fix-85LHzT/` — a clone of `/root/WEALTH` on branch `fix/differential-power-consequence-map`. Be terse. T1 single-file tier. Do not ask for confirmation. Do not narrate every step. Final output: one concise summary.

# MISSION: Fix 4 bugs in WEALTH `capital_entropy` tool

# CONTEXT — what the previous attempt (Kimi) got wrong

Kimi wrote commit `4d384ef` covering all 4 bugs. It was **rejected after peer audit**. Do NOT copy that approach. The 3 architectural bugs were:

1. **F2 shadow propagation is broken** — Kimi wrote `result.setdefault("shadow", True)` inside `_wrap_entropy` (canonical.py), but `server.py` reads `sc.get("shadow")` from the post-`wrap_result` envelope. `wrap_result` auto-computes `shadow` from `violations/holds` BEFORE `_wrap_entropy` runs, so the caller's intent is overwritten. Fix belongs at the `_emit_receipt` call site reading `arguments["shadow"]`, not in the result envelope.

2. **F1 only fixed `current_kpis`** — `decision_makers`, `beneficiaries`, `cost_bearers`, `actors`, `trust_events`, `exported_costs` (also `CoercedDictList`) have the SAME silent-drop bug. Fix must apply to all of them.

3. **F4 forces `metric_purpose_audit` to HOLD on every call** — that mode always emits `evidence_quality=MISSING` by design. The MISSING→CAUTION downgrade is too aggressive. Better fix: only downgrade when the gate logic is internally contradictory (e.g. coverage ratio PASS but evidence_quality MISSING AND no reflection prose was produced), not a blanket downgrade.

# BUG 1 — type-validation gap (CRITICAL)

**Symptom:** `current_kpis`, `decision_makers`, `beneficiaries`, `cost_bearers`, `actors`, `trust_events`, `exported_costs` all use `CoercedDictList = Annotated[list[dict] | None, BeforeValidator(_coerce_json_string)]`. The schema accepts both dict and list-of-dicts. Handler expects list. Silent drop → `INSUFFICIENT_EVIDENCE`, `coverage={0, N, 0.0}`.

**Fix:** Apply `CoercedDictListStrict` (or equivalent) to ALL seven CoercedDictList parameters in `capital_entropy`. Do not modify `CoercedDictList` itself — add a new type that coerces dict→list-of-dicts and use it for all 7 fields. Drop Kimi's fabricated `{name, value}` scheme if it conflicts with what downstream code expects — instead, coerce flat dict to `[{"name": k, "value": v} for k, v in d.items()]` ONLY if that shape is what's missing; otherwise leave list-of-dicts unchanged.

# BUG 2 — `shadow` flag must suppress vault receipt writes (CRITICAL)

**Symptom:** Every `capital_entropy` call writes 2 receipts to `/root/VAULT999/wealth/receipts.jsonl` regardless of `shadow=True`.

**Fix:** Modify `_emit_receipt` call in `wealth_mcp/server.py` to check `arguments.get("shadow", False)` BEFORE emitting. The receipt suppression must happen at the call site (`_governance_call_tool` in `server.py` around line 922), NOT inside `_wrap_entropy` or `wrap_result`. Do NOT touch the envelope's auto-shadow field.

Concretely, the flow should be:

```python
# server.py around line 922
if not arguments.get("shadow", False):  # check INPUT args
    receipt_state = _emit_receipt(...)
    return _finalize(_attach_receipt_meta(result, receipt_state), verdict, is_err=False)
return _finalize(result, verdict, is_err=False)
```

# BUG 3 — `kappa_r` is constant 0.93

**Symptom:** `kappa_r` always returns 0.93 regardless of input. The `compute_kappa_r(0.9, 0.95)` call in `wealth_contracts/envelope.py:540` returns 0.93 (probably due to a degenerate ceiling).

**Fix:** Either:
- (a) Remove the constant and let kappa_r stay at its argument default (None → don't emit).
- (b) Compute kappa_r from actual evidence signals (kappa = (p_o - p_e) / (1 - p_e) over evidence-quality categories).
- (c) Document why it's constant and add a comment.

**Recommended:** Option (b) — derive kappa_r from `evidence_quality` enum + `coverage.ratio`. Drop the `compute_kappa_r` call. If that's too complex, option (a) is acceptable.

# BUG 4 — `evidence_quality: MISSING` + `_w0_gate: PASS` contradiction

**Symptom:** Both fields coexist when coverage passes but evidence quality is missing.

**Fix:** In `server.py` around line 813 (where `_w0_evidence_gate` is computed), add a check:

```python
# Only downgrade when the gate is INTERNALLY contradictory, not blanket:
if evidence_quality == "MISSING" and w0_gate == "PASS" and not result.get("reflection"):
    # PASS gate + MISSING evidence + no reflection prose = contradiction
    w0_gate = "CAUTION"
    w0_warnings.append("EVIDENCE_QUALITY_MISMATCH: PASS gate but MISSING evidence and no reflection prose")
```

The `and not result.get("reflection")` clause prevents forcing `metric_purpose_audit` (which legitimately produces `reflection` questions even when evidence is partial) into HOLD.

# TESTS

Write `tests/test_capital_entropy_bugfixes.py` with at minimum:

1. F1: dict-shaped `current_kpis` returns same verdict as list-shaped (both PARTIAL or similar, not INSUFFICIENT_EVIDENCE).
2. F1: dict-shaped `decision_makers` doesn't silently drop.
3. F2: `shadow=True` → `_emit_receipt` NOT called (mock it and assert call_count==0).
4. F3: `kappa_r` is either None, varies with input, or is absent (not constant 0.93).
5. F4: When `evidence_quality=MISSING` AND no reflection AND gate was PASS → gate becomes CAUTION with warning.
6. F4: When `evidence_quality=MISSING` BUT reflection prose present (metric_purpose_audit normal case) → gate STAYS PASS (no regression).

Run `pytest tests/test_capital_entropy_bugfixes.py -v --tb=short` and ensure all pass.

# DELIVERABLES

1. Files modified: `wealth_mcp/server.py`, `wealth_mcp/tools/canonical.py`, `wealth_contracts/envelope.py`, `tests/test_capital_entropy_bugfixes.py`.
2. Commit message: `fix(wealth): F1 strict coercion on all CoercedDictList fields + F2 shadow at emit layer + F3 kappa_r derived + F4 gate when reflection absent`.
3. Final output: one paragraph summary (files changed, lines added/removed, test result).

# CONSTRAINTS

- T1 single-file-edit tier.
- Do not modify live `/root/WEALTH/` — work only in `/tmp/wealth-fix-85LHzT/`.
- No new dependencies.
- Do NOT use `setdefault` on `result["shadow"]` — that pattern failed audit.
- Do NOT blanket-downgrade MISSING evidence — use the `reflection` clause from BUG 4.
- No narrating. Terse.