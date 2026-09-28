# Runtime Manifests — Phase C

> **Phase C, 2026-09-16. F13 SOVEREIGN.**

Five manifests separate **what source declares** from **what
the serving process can prove**. Public health status for a
tool derives from probe state — never from source declaration.

---

## The five manifests

### 1. `wealth://manifest/source`

What committed source declares. Generated from `git rev-parse
HEAD` plus the canonical tool list declared in code.

```python
from wealth_contracts.manifest_v1 import SourceManifest
m = SourceManifest.from_git(["capital_primitive", "capital_market"])
```

### 2. `wealth://manifest/build`

What was packaged into the running artifact. Generated from
the build digest and dependency lock digest.

### 3. `wealth://manifest/runtime`

What the **currently active process** registered. Must be
produced by introspection of the running server, not by static
declaration.

### 4. `wealth://manifest/public`

What an MCP client can actually discover today via live
`tools/list`, resource list, and prompt list. Must derive from
a live call — never from a cached YAML.

### 5. `wealth://manifest/probe`

What independently passed:

- cold import
- safe invocation
- output schema validation
- semantic invariant check
- sanitized error behavior
- receipt outcome

---

## Effective state

Every capability in the probe manifest carries an
`EffectiveState`:

```text
DECLARED        → schema present, never executed
IMPORTABLE      → cold-import succeeds
INVOKABLE       → safe invocation returns envelope
VALIDATED       → all 10 LAW-WEALTH-01 clauses pass
LIVE            → probe confirms in serving build
DEGRADED        → some clause now fails
HELD            → policy HOLD; arifOS review pending
UNAVAILABLE     → upstream or runtime dead
DEAD            → import or cold-start failed
```

---

## The lowest-state rule

**A tool's public health status is the lowest verified state
across the probe outcomes, never the best historical,
documentary, or static-prose state.**

```python
from wealth_contracts.manifest_v1 import aggregate_probe_state

worst_per_capability = aggregate_probe_state(probe_outcomes)
```

This is the constitutional guarantee against the 2026-09-16
defect pattern where the source manifest said "healthy" while
the runtime probe said "dead."

---

## Drift detection

A drift between source and runtime manifests is a HELD state
for the affected capabilities. Drift is computed as:

```text
missing = source_tools - runtime_tools
ghost   = runtime_tools - source_tools
```

- `missing` → capability was declared but never registered.
  Surfaced as DECLARED in the public manifest.
- `ghost`   → capability is live but never declared. Surfaced
  as a CONFLICTED anomaly in the probe manifest.

---

## Example usage

```python
from wealth_contracts.manifest_v1 import (
    ProbeManifest, ProbeOutcome, EffectiveState, aggregate_probe_state,
)
from wealth_contracts.runtime_probe_v1 import (
    cold_import, build_probe_manifest,
)

results = [
    cold_import("wealth_core.power.capture_detector"),
    cold_import("wealth_core.power.rent_extraction"),
    cold_import("wealth_core.power.opacity_scorer"),
]
manifest = build_probe_manifest(results)

# Public health surface
worst = aggregate_probe_state([r.outcome for r in results])
for cap, state in worst.items():
    print(f"{cap:40s} → {state.value}")
```

Expected output (when imports succeed):

```
wealth_core.power.capture_detector   → IMPORTABLE
wealth_core.power.rent_extraction    → IMPORTABLE
wealth_core.power.opacity_scorer     → IMPORTABLE
```

If any module fails to import, that capability reports DEAD
and the public surface reflects it.

---

## What this manifest contract does NOT cover

- Network-dependent probes (deliberately excluded; Phase C
  tests are deterministic and offline).
- Long-running live probes (deliberately excluded; live
  probes are an opt-in deployment-level concern).
- Cross-process state attestation (deliberately excluded; the
  manifest is a snapshot, not a verdict).

---

DITEMPA BUKAN DIBERI — Forged, not given.