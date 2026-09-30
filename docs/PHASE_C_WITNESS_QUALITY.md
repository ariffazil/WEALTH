# Phase C — Witness Quality Floor

> **Branch:** `phase-c-witness-quality`
> **Status:** SHIPPED-LOCAL (PR-ready, no merge, no push)
> **Locked roadmap:** C → E → A → D → B

Phase C makes WEALTH incapable of silently promoting:

- a transport failure,
- a runtime failure,
- malformed output,
- stale or incomplete data,
- ignored or mis-keyed material input,
- a policy-held result,
- an unauthorized result

into PASS, OBSERVED, recommendation, publication eligibility,
or decision-eligible output.

---

## What this phase delivers

### 1. LAW-WEALTH-01 — Reality-Bound Capability Promotion

10 enforceable clauses. Machine-readable companion at
`schemas/law-wealth-01.yaml`. Enforcement code at
`wealth_contracts/law_wealth_01.py`.

### 2. Receipt v2 — Four-truth witness envelope

`wealth_contracts/receipt_v2.py`. The decisive invariant:

```
PASS <=> transport=RESPONDED
       AND execution=SUCCESS
       AND semantic=VALID
       AND policy IN {OBSERVATION_ONLY, PERMITTED}
```

Any receipt whose stored verdict disagrees with this
invariant is **forced to the correct value** at
`__post_init__`. No receipt can lie.

### 3. Input-fidelity gate

`wealth_contracts/input_fidelity_v1.py`. Material inputs
declared per-tool in `MATERIAL_INPUT_PATHS`. The gate detects:

- UNMAPPED_INPUT (typo'd key, the 2026-09-16 defect)
- UNCONSUMED_MATERIAL_INPUT
- PARTIAL_EVIDENCE
- INSUFFICIENT_DATA
- CONFLICTED
- VALID

Suppressed recommendation is the default for every non-VALID
state.

### 4. Five-manifest registry

`wealth_contracts/manifest_v1.py`. Separates DECLARATION from
PROOF:

| Manifest | What it answers |
|---|---|
| source | What does committed source declare? |
| build  | What was packaged into this artifact? |
| runtime | What did the active process register? |
| public | What can a client discover live? |
| probe  | What independently passed cold-import, safe invocation, schema validation, semantic invariants, and failure injection? |

Public health status is the **worst verified state**, never
the best. A declared-but-unimportable tool is DEAD, not healthy.

### 5. Read-only runtime probes

`wealth_contracts/runtime_probe_v1.py`. Safe probe argument
sets per tool. Probes NEVER invoke write/submit/publish/allocation
paths. They only exercise cold-import, envelope-shape detection,
and exception swallowing.

### 6. Wire contracts

- `schemas/receipt.v2.json` — JSON Schema 2020-12 for receipts
- `schemas/wealth-envelope.v2.json` — backward-compatible v1+v2
- `schemas/law-wealth-01.yaml` — machine-readable law

### 7. Tests

`tests/test_phase_c_witness_quality.py` — 32 tests, all green.
Covers the 14 mandatory fault-injection scenarios plus:

- LAW-WEALTH-01 evaluation gate
- Receipt invariant enforcement
- UNMEASURED sentinel arithmetic refusal
- Safe-invoke envelope detection
- Safe-invoke exception swallowing
- JSON Schema artifact validation
- YAML law artifact validation

---

## What this phase EXPLICITLY does NOT deliver

- Production deployment
- Service restart
- VAULT999 mutation
- Public-page update
- Phase E (market-state typing, oil-lane recovery)
- Phase A (POLIX v0.1)
- Phase D (Consequence Graph v1)
- Phase B (CIVX scenario shell)

These are sequential future work. Each depends on Phase C
shipping cleanly.

---

## Operational runbook

### Run unit tests

```bash
cd /root/WEALTH
python3 -m pytest tests/test_phase_c_witness_quality.py -v
```

Expected: 32 passed in < 1 second.

### Run mock integration tests

The Phase C tests are deterministic and require **no live
services, no credentials, no network access**. They can run on
any clean Python 3.13 environment.

### Run optional live read-only probes

Phase C does not enable live probes by default. To opt in
during deployment review:

```python
from wealth_contracts.runtime_probe_v1 import (
    cold_import, safe_invoke, build_probe_manifest,
)

results = [
    cold_import("wealth_core.power.capture_detector"),
    cold_import("wealth_core.power.rent_extraction"),
    # ... extend with all canonical tools
]
manifest = build_probe_manifest(results)
print(manifest.to_dict())
```

### Verify active runtime revision

```bash
cd /root/WEALTH
git rev-parse HEAD
git status
# Confirm: branch phase-c-witness-quality
# Confirm: dirty tree (2 modified files + .ua/) preserved
```

---

## Acceptance criteria — verified

- All required tests pass locally without credentials or live
  services. ✓
- Any failure condition produces FAIL / HOLD / UNMEASURED /
  UNAVAILABLE, never a false PASS / OBSERVED / recommendation. ✓
- `capital_diagnose` cannot convert missing / mis-keyed board
  data into zero NEDs or an emergency appointment recommendation. ✓
- Registry distinguishes declared capability from tested
  runtime state. ✓
- Every public tool has an envelope or a documented
  compatibility path. ✓
- No new write, submit, publish, allocation, or execution
  capability is introduced. ✓
- No source secret, server path, or trace internals leak in
  responses. ✓
- Existing compute-only / human-final-authority boundaries are
  preserved. ✓

---

## Remaining risks for Phase E

1. **Backtest cold-start import failure** — out of Phase C scope,
   must be repaired or marked UNAVAILABLE before Phase E ships.
2. **Oil-lane upstream availability** — must be probed and
   surfaced via the new freshness / decision-eligibility fields.
3. **Live deployment revision attestation** — needs a separate
   PR that integrates Phase C middleware into the serving build.

---

## PR description (draft)

```
Title: Phase C — Witness-Quality Floor (LAW-WEALTH-01 + receipt v2 + input-fidelity + five-manifest + probes)

Branch: phase-c-witness-quality
Base: main (preserves dirty working tree on main; this branch
       contains only new Phase C files)

Files added (new):
  wealth_contracts/law_wealth_01.py
  wealth_contracts/receipt_v2.py
  wealth_contracts/input_fidelity_v1.py
  wealth_contracts/manifest_v1.py
  wealth_contracts/runtime_probe_v1.py
  schemas/law-wealth-01.yaml
  schemas/receipt.v2.json
  schemas/wealth-envelope.v2.json
  tests/test_phase_c_witness_quality.py
  docs/LAW-WEALTH-01.md
  docs/PHASE_C_WITNESS_QUALITY.md
  docs/MIGRATION_ENVELOPE_V2.md
  docs/RUNTIME_MANIFESTS.md

Files NOT modified:
  (no edits to existing modules; dirty main working tree preserved)

Tests: 32 passed in <1s, no live services, no credentials.
Production writes: ZERO.
Service restarts: ZERO.
VAULT999 mutations: ZERO.

Closes: 2026-09-16 PETRONAS "0 independent NEDs" defect class
        (P1#1 claim_gate already shipped; Phase C adds the
        generalized input-fidelity gate that prevents the
        upstream pattern, not just the named-entity symptom).
```

---

DITEMPA BUKAN DIBERI — Forged, not given.