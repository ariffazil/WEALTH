# WEALTH MCP — Next Horizon Full Blueprint (FINAL)

> **Version:** 2026.05.07-KANON-NEXT  
> **Author:** ARIF-Perplexity × Arif Fazil × Hermes ASI  
> **Status:** APPROVED — Awaiting Phase 0 Execution  
> **Source:** WEALTH_NEXT_HORIZON_BLUEPRINT_v2026.05.07.md + AAA conversation synthesis  
> **SEAL:** DITEMPA BUKAN DIBERI

---

## Executive Summary

WEALTH MCP is a **governed economic reasoning instrument** — not a calculator, not an actuator, not a bank. Its purpose is to reduce LLM hallucination, replace vague reasoning with epistemic computation, and present governed recommendations that Arif ratifies or vetoes under F13 sovereign authority.

The next horizon reshapes WEALTH into three orthogonal surfaces:
- **Tools (42 atomic):** one computation per tool, no orchestration inside.
- **Prompts (12 governed workflows):** reasoning sequences that call tools in constitutional order.
- **Resources (21 readable contexts):** schemas, formulas, policies, ontology, state — never executable.

Naming convention: `wealth_<physics_dimension>_<economic_operation>`

---

## Phase 0 — CRITICAL GAP ITEMS (Must Fix Before Any Rename)

| # | Gap Item | Fix | File | Status |
|---|---|---|---|---|
| G1 | `vaultwrite` MCP wrapper missing | Add `@mcp.tool(name="vaultwrite")` wired to `vaultsupabase.py`; F01 gate | `internal/monolith.py` | PENDING |
| G2 | `vaultquery` MCP wrapper missing | Add `@mcp.tool(name="vaultquery")` from Postgres/JSONL VAULT999 | `internal/monolith.py` | PENDING |
| G3 | Tri-Witness unwired in envelope | Import `TriWitness`, add `witness=None` param to `create_envelope`, wire `witness.to_dict()` | `internal/monolith.py` | PENDING |
| G4 | `shadow` boolean absent from envelope | Add `shadow = len(holds) > 0 or len(violations) > 0` inside `create_envelope` | `internal/monolith.py` | PENDING |

---

## Phase 1 — MCP Handshake Fix (COMPLETED)

Added `initialize` handler to `legacy_mcp_handler` in `internal/monolith.py`.

---

## Phase 2 — Decompose Umbrella Tools → Atomic Tools (Planned)

See Part IV of source document.

---

## Phase 3 — Promotes Resources (Planned)

Add `@mcp.resource()` for all 21 resources.

---

## Phase 4 — Retire Legacy Aliases (Planned)

Remove all 25 V2 aliases.

---

## Final Registry Target

```
WEALTH MCP
├── tools/          42 atomic executors
├── prompts/        12 governed reasoning workflows
└── resources/      21 readable contexts
```

---

## Identity Statement

> WEALTH MCP is a physics-inspired, mathematically grounded, code-executed governance instrument for economic decision support.
>
> Physics supplies the metaphor and constraint grammar.
> Economics supplies the human allocation domain.
> Math supplies formal calculation.
> Code supplies execution.
> Governance supplies judgment.
> Arif holds the veto. Always.

---

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
