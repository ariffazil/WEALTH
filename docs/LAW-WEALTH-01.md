# LAW-WEALTH-01 — Reality-Bound Capability Promotion

> **Ratified 2026-09-16. F13 SOVEREIGN.**
> **Status:** ACTIVE.
> **Authority ceiling:** 555_COMPUTE_ONLY.

> **WEALTH computes. arifOS judges. Human decides.**
> No WEALTH capability may be promoted above SPECULATED
> unless it passes all 10 clauses below. Each clause is
> testable in CI; prose is not enforcement.

---

## Preamble

WEALTH is a compute organ. It exists to witness capital,
institutional, market, political-economic, and consequence
patterns. It does NOT authorize execution, allocation,
constitutional judgment, or final policy choice.

The 2026-09-16 incident — where a `capital_diagnose` engine
internally produced `"0 independent NEDs"` about PETRONAS and
that string reached a public page as observed fact — proved
that **the wrapper was recording PASS while the upstream call
had failed, while material input was ignored, while the engine
itself was not running, and while the public health surface
was green because the source schema was present.**

This law exists so that pattern can never repeat.

---

## The 10 clauses

### 1. Schema validity
**Inputs and outputs validate against declared contracts.**
A schema-present tool is not a working tool. JSON Schema 2020-12
is the wire contract; schema rejection at runtime is a
DEGRADED state.

### 2. Input fidelity
**Every material input is consumed and reflected in the output.**
A supplied material input that is unrecognized, ignored, or
unreflected is a blocking semantic failure. The 2026-09-16
`board_membrs` (typo) → `[]` → `"0 independent NEDs"` chain
is the canonical violation.

Enforcement: `wealth_contracts.input_fidelity_v1.evaluate_input_fidelity`.

### 3. Evidence binding
**Material claims carry source references or epistemic labels.**
A claim about a real-world fact without source attribution or
without ASSUMED / INTERPRETED / SPECULATED / UNMEASURED /
CONFLICTED labelling is rejected for promotion.

### 4. Temporal validity
**Current-state outputs require observation time, source,
freshness, and decision-eligibility state.** Stale data must
never produce a decision-eligible verdict.

### 5. Runtime proof
**A claimed capability requires an independent runtime probe.**
Public health status is the **worst verified state** of
source/build/runtime/public/probe — never the best.

### 6. Four-truth receipt
**A PASS verdict requires:**

```
PASS <=> transport == RESPONDED
       AND execution == SUCCESS
       AND semantic == VALID
       AND policy IN {OBSERVATION_ONLY, PERMITTED}
```

Any other combination yields DEGRADED, HOLD, or FAIL.
A receipt's stored verdict cannot override this invariant —
`ReceiptV2.__post_init__` re-derives and corrects.

### 7. Failure injection
**Controlled failure tests exist before promotion.**
The 14 mandatory scenarios in
`tests/test_phase_c_witness_quality.py` are the LAW §7
enforcement artifact. A capability without these tests cannot
be promoted above DECLARED.

### 8. Calibration
**Interpretive capabilities stay ≤ SPECULATED until calibrated.**
POLIX and CIVX (Phases A and B) are explicitly interpretive.
Until they have documented calibration cases, negative
controls, abstention conditions, and parameter provenance,
they remain research-grade.

### 9. Authority boundary
**WEALTH cannot self-authorize execution, capital allocation,
constitutional judgment, publication, or irreversible action.**
`execution_authorized=True` is a CONFLICTED state that
triggers arifOS escalation.

### 10. Named-entity discipline
**A public claim concerning a named institution or person
requires independently source-bound, time-bound,
contradiction-checked evidence.** Engine output is not a
source for claims about real named entities.

Enforcement: `wealth_contracts.claim_gate.evaluate` /
`evaluate_dict_result` (P1#1, 2026-09-16).

---

## Promotion states

```text
DECLARED        → schema present, never executed
IMPORTABLE      → cold-import succeeds
INVOKABLE       → safe invocation returns envelope
VALIDATED       → all 10 clauses pass
LIVE            → probe confirms in serving build
DEGRADED        → some clause now fails
HELD            → policy HOLD; arifOS review pending
UNAVAILABLE     → upstream or runtime dead
DEAD            → import or cold-start failed
```

A capability cannot move DOWN without reason. A capability
cannot move UP without all 10 clauses passing.

---

## Federation invariants preserved

- WEALTH computes; arifOS judges; Human decides.
- POLIX = bounded political-economy evidence, not public
  accusation.
- Capability promotion ≤ SPECULATED until all 10 clauses pass.
- No tool promotes its own conclusion into allocation or
  action.

---

## What this law explicitly does NOT cover

- Phase E (market-state typing, oil-lane recovery, backtest
  cold-start repair) — separate work item.
- Phase A (POLIX v0.1 schema + first evidence case) — depends
  on Phase C shipping.
- Phase D (Consequence Graph v1 prototype) — depends on
  Phase A.
- Phase B (CIVX scenario shell) — depends on Phase D.
- Production deployment, service restart, VAULT999 mutation,
  public-page update — all explicitly forbidden by Phase C.

---

## Related artifacts

- `wealth_contracts/law_wealth_01.py` — enforcement code
- `wealth_contracts/receipt_v2.py` — four-truth receipt
- `wealth_contracts/input_fidelity_v1.py` — input-fidelity gate
- `wealth_contracts/manifest_v1.py` — five-manifest registry
- `wealth_contracts/runtime_probe_v1.py` — read-only probes
- `schemas/law-wealth-01.yaml` — machine-readable companion
- `schemas/receipt.v2.json` — receipt wire contract
- `schemas/wealth-envelope.v2.json` — envelope wire contract
- `tests/test_phase_c_witness_quality.py` — LAW §7 enforcement
- `docs/PHASE_C_WITNESS_QUALITY.md` — Phase C overview
- `docs/MIGRATION_ENVELOPE_V2.md` — v1 → v2 migration
- `docs/RUNTIME_MANIFESTS.md` — manifest semantics

---

## Change log

- 2026-09-16 — LAW-WEALTH-01 ratified. Phase C witness-quality
  floor shipped as branch `phase-c-witness-quality`.

DITEMPA BUKAN DIBERI — Forged, not given.