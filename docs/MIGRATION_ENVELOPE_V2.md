# Migration — Envelope v1 → v2

> **Phase C, 2026-09-16. F13 SOVEREIGN.**
> **Status:** ADVISORY. Backward-compatible by design.

Phase C introduces **envelope v2** semantics. v1 envelopes
remain valid; v2 adds two optional blocks (`receipt`,
`input_fidelity`) and enforces stricter four-truth semantics
through `ReceiptV2`.

---

## What is additive (no migration required)

The new fields are **optional**. Existing v1 clients continue
to receive the same v1 fields:

- `tool_name`
- `tool_version`
- `domain`
- `result`
- `result_type`
- `epistemic_tag`
- `claim_state`
- `evidence_quality`
- `execution_authorized` (still always `False`)
- `execution_authority`
- `human_final_authority`
- `requires_888_hold`
- `source_attribution`
- `computation_timestamp`
- `missing_inputs`
- `warnings`
- `errors`
- `witness`, `shadow`, `kappa_r`, `psi_le`

Nothing in this list is removed or renamed.

---

## What is new

### Optional blocks (only present when middleware is enabled)

```json
{
  "receipt": {
    "receipt_id": "...",
    "transport": "RESPONDED",
    "execution": "SUCCESS",
    "semantic": "VALID",
    "policy": "OBSERVATION_ONLY",
    "verdict": "PASS",
    "decision_eligibility": "ELIGIBLE",
    ...
  },
  "input_fidelity": {
    "tool_name": "capital_diagnose",
    "state": "VALID",
    "bindings": [...]
  }
}
```

### Stricter invariants

The four-truth invariant is enforced by `ReceiptV2.__post_init__`:

```python
derived_verdict = compute_verdict(
    self.transport, self.execution, self.semantic, self.policy
)
if derived_verdict != self.verdict:
    self.verdict = derived_verdict   # force the invariant
self.decision_eligibility = decision_eligibility(self.semantic, self.policy)
```

A receipt **cannot** claim `verdict=PASS` when any of:

- `transport ≠ RESPONDED`
- `execution ≠ SUCCESS`
- `semantic ≠ VALID`
- `policy ∉ {OBSERVATION_ONLY, PERMITTED}`

---

## How to opt in

For tool authors who want v2 semantics today:

```python
from wealth_contracts.receipt_v2 import (
    ReceiptV2, TransportState, ExecutionState,
    SemanticState, PolicyState,
)

receipt = ReceiptV2(
    receipt_id="r-abc",
    tool_name="capital_diagnose",
    tool_version="v2",
    transport=TransportState.RESPONDED,
    execution=ExecutionState.SUCCESS,
    semantic=SemanticState.VALID,
    policy=PolicyState.OBSERVATION_ONLY,
    # verdict omitted — derived automatically
    input_hash="...",
    output_hash="...",
)
# Persist receipt.to_dict() alongside the existing envelope.
```

For tool authors who want input-fidelity gating today:

```python
from wealth_contracts.input_fidelity_v1 import evaluate_input_fidelity

report = evaluate_input_fidelity(
    tool_name="capital_diagnose",
    inputs=request_payload,
    outputs=result_payload,
)
if not report.suppressed_recommendation:
    emit_recommendation(...)
else:
    emit_hold(reason=report.state.value)
```

---

## How to disable (not recommended)

If a downstream consumer cannot accept the new blocks for
compatibility reasons, the safe path is:

1. Filter `receipt` and `input_fidelity` keys at the client.
2. Do NOT trust any verdict that was overridden by
   `ReceiptV2.__post_init__` — re-derive on the client side.

There is no flag to disable v2 because the whole point is
that **a wrapper can no longer lie about PASS while the
upstream failed**. That property is non-negotiable.

---

## What this migration does NOT cover

- Wiring the new middleware into every tool (Phase C is the
  artifact, not the deployment).
- Replacing the existing `WealthEnvelope` class (v1 remains
  canonical for the public surface; v2 is additive).
- Any change to the wire-level MCP framing.

---

DITEMPA BUKAN DIBERI — Forged, not given.