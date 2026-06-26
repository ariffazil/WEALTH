# WEALTH Ingest Guide

> **For any AI agent entering the WEALTH organ repository.**
> **Doctrine:** DITEMPA BUKAN DIBERI — Forged, Not Given.

---

## Step 1 — Load Reality (60s)

Read in this order:

1. **`CONTEXT.md`** — What is this organ, its live state, dependencies, known issues
2. **`WEALTH_SNAPSHOT.yaml`** — Current financial reality, machine-parseable, zero/null = uninitialized
3. **`FEDERATION_STATUS.md`** — How this organ relates to the 6 others in the federation

## Step 2 — Load Governance

Read:

4. **`BOUNDARY.md`** — What this organ may and may not own or do
5. **`888_ACTIVE.md`** — Pending sovereign decisions requiring Arif sign-off

## Step 3 — Load Intent

Read:

6. **`AGENTS.md`** — Constitutional rules, build/test/deploy commands, escalation paths
7. **`WEALTH_NEXT_HORIZON.md`** — Strategy, roadmap, upcoming features

## Step 4 — Load Code Surface (if building/modifying)

Read:

8. **`INVARIANTS.md`** — Immutable boundaries, ownership map, live port/history
9. **`internal/monolith.py`** — Canonical kernel (~655KB, 20 public + 34 hidden tools)
10. **`wealth_core/`** — Modular core (capital, collapse, game, governance, etc.)
11. **`contracts/`** — Tool contracts, capability manifest, schemas
12. **`reality_contracts/`** — Federation call graph, wire contracts, ISA map

---

## Constraints

- **EVIDENCE_ONLY** — WEALTH computes capital metrics but does not execute trades
- **Compute-only** — Never allocates capital, authorizes trades, or moves money
- **Evidence-tagged** — Every output carries epistemic band (CLAIM / PLAUSIBLE / HYPOTHESIS / ESTIMATE / UNKNOWN)
- **Kernel-gated** — Irreversible financial decisions require `arif_judge_deliberate → SEAL` from arifOS
- **Downside-honest** — Risk models surface worst-case, not just expected value
- **888_HOLD required** — Any irreversible financial action stages in `888_ACTIVE.md` before execution
- **Canonical server** — `internal/monolith.py` on port 18082 (live via `wealth-organ.service`)
- **Dual runtime** — Python canonical + Node.js legacy (`src/`)

---

## Ingestion Verification

After reading, verify you have context by answering:

1. What is the current financial reality? (from WEALTH_SNAPSHOT.yaml)
2. What organ boundaries apply? (from BOUNDARY.md)
3. Are there pending 888_HOLDs? (from 888_ACTIVE.md)
4. What is the canonical MCP surface? (from AGENTS.md or /health endpoint)

If any of these are unclear, re-read the corresponding file before proceeding.
