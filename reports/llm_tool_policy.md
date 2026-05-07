# WEALTH MCP — LLM Tool Policy
**Date:** 2026-05-07
**Governance:** F1–F13 Constitutional Floors
**Final Authority:** ARIF (F13 SOVEREIGN)
**REPO=WEALTH**

---

## Preamble

WEALTH MCP is a governed economic reasoning engine. It exposes three MCP primitives: **tools** (executable), **prompts** (reasoning workflows), and **resources** (readable context). This policy governs how LLMs must interact with this surface.

Physics supplies the abstraction vocabulary. Economics supplies the domain meaning. Governance supplies the judgment boundary. ARIF supplies the sovereign decision.

---

## Part I — Primitive Classification

### Tools: Executable Operations

Tools perform atomic computations or actions. They do ONE thing.

**Examples:**
- `wealth_value_npv` → compute NPV
- `wealth_gravity_dscr` → compute DSCR
- `wealth_ledger_write` → write to VAULT999 (irreversible)
- `wealth_boundary_floors` → check F1–F13 compliance

**Rule:** One tool, one operation. No mode dispatching inside a tool.

### Prompts: Reasoning Workflows

Prompts orchestrate multiple tools into a governed sequence. They do NOT execute economics directly — they call tools.

**Examples:**
- `wealth_appraise_project` → orchestrates NPV + IRR + PI + Payback + Floor check
- `wealth_judge_allocation` → orchestrates verdict + floors + policy
- `wealth_crisis_triage` → orchestrates triage + cashflow + runway

**Rule:** Use prompts for orchestration. Use tools for execution.

### Resources: Readable Context

Resources are schemas, policies, formulas, ontology definitions, and state snapshots. They are NEVER executable.

**Examples:**
- `wealth://schemas/prospect_metrics` → input/output schema
- `wealth://policy/f1_f13_floors` → constitutional constraints
- `wealth://formulas/npv` → mathematical definition
- `wealth://ontology/physics_economics_map` → metaphor documentation

**Rule:** Read resources before calling tools. Validate against schemas.

---

## Part II — LLM MUST

### Schema Validation

```
BEFORE computing any valuation:
1. Read wealth://schemas/prospect_metrics
2. Read wealth://schemas/cashflow_project
3. Validate input structure matches schema
4. If schema invalid → return error, do not proceed
```

### Primitive Distinction

```
FOR any task:
- Need to compute something?           → Use a TOOL
- Need to run a multi-step workflow?    → Use a PROMPT
- Need reference/context/state?         → Use a RESOURCE
- Need to understand meaning/mapping?   → Use a RESOURCE (ontology)
```

### Prompt Orchestration

```
WHEN任务是 appraisal or allocation or audit:
1. Identify the correct prompt for the task
2. Call the prompt (it orchestrates the tools)
3. Present the combined result to ARIF
4. Do NOT manually chain tools — let the prompt do it
```

**Exception:** If the prompt does not cover your specific case, use individual atomic tools in sequence. Document your reasoning.

### Tool Usage for Execution

```
WHEN executing:
1. Select the most atomic tool for the operation
2. Validate inputs against the relevant schema resource
3. Execute with explicit parameters (no hidden state)
4. Return result with epistemic tag (CLAIM/PLAUSIBLE/ESTIMATE/HYPOTHESIS)
```

### ARIF as Final Authority

```
AFTER getting any system verdict (SEAL/QUALIFY/HOLD/VOID):
- Present the verdict as a recommendation
- Clearly state: "This is a system recommendation. Final decision rests with ARIF."
- Never claim the system has made a sovereign decision
- For irreversible actions (ledger_write): require explicit ARIF confirmation
```

---

## Part III — LLM MUST NOT

### Physics as Literal

```
NEVER claim:
- "The capital has mass" (it has net worth)
- "Cash flow has gravity" (it has debt burden)
- "The system has entropy" (it has uncertainty/noise)
- "Economic energy is thermodynamic energy"

DO say:
- "Net worth, modeled as mass in the capital structure"
- "Debt burden, analogous to gravitational pull"
- "Cash flow uncertainty, measured as entropy"
- "Return potential, analogous to energy in a physical system"
```

### Execution Without Substrate

```
NEVER claim the ability to:
- Move capital (WEALTH computes, banks execute)
- Place trades (WEALTH advises, brokers execute)
- Enforce policy (WEALTH audits, ARIF enforces)
- Make irreversible decisions (WEALTH recommends, ARIF decides)
```

### Silent Irreversible Actions

```
NEVER call these without explicit ARIF confirmation:
- wealth_ledger_write (irreversible vault write)
- vault_write (same)
- Any tool that appends to VAULT999

ALWAYS:
1. Explain what will be written
2. State the irreversibility
3. Wait for explicit confirmation
4. Then execute with ack_irreversible=True
```

### Prompt/Resource Confusion

```
NEVER treat a prompt as a tool:
- "Run wealth_appraise_project" → this IS correct (prompt)
- "wealth_appraise_project(initial_investment=...)" → this is WRONG (it's a prompt, not a tool with those params)

NEVER treat a resource as a tool:
- "Call wealth://formulas/npv" → this is WRONG (it's a resource, read it)
- "Compute NPV using wealth://formulas/npv" → CORRECT (read the formula, then use wealth_value_npv)
```

### System Verdicts as Sovereign

```
NEVER say:
- "WEALTH has approved this allocation"
- "The system has decided"
- "Capital will be moved"

ALWAYS say:
- "WEALTH recommends ACCEPT (SEAL verdict)"
- "System advisory: PI = 1.4, DSCR = 1.8 — F13 approval required"
- "Recommendation: present this to ARIF for sovereign decision"
```

---

## Part IV — Epistemic Discipline

### Tag Every Output

| Tag | Meaning |
|-----|---------|
| `CLAIM` | Verified against real data |
| `PLAUSIBLE` | Consistent with evidence, not fully verified |
| `ESTIMATE` | Based on models, significant uncertainty |
| `HYPOTHESIS` | Speculative, requires validation |
| `UNKNOWN` | Insufficient information |

### Confidence Bands

For scalar outputs (NPV, IRR, EMV), always provide:
- Point estimate
- Confidence band (width depends on epistemic tag)
- The epistemic tag itself

### Uncertainty Propagation

When chaining tools:
1. Propagate epistemic tags from inputs to outputs
2. If input is HYPOTHESIS, output cannot be CLAIM
3. If input is ESTIMATE, output is at best ESTIMATE

---

## Part V — Anti-Patterns (Forbidden)

| Anti-Pattern | Why Forbidden | Correct Approach |
|-------------|--------------|-----------------|
| `wealth_future_value(mode='npv')` | Umbrella tool with mode dispatch | Use `wealth_value_npv` directly |
| `wealth_sense_ingest(mode='fetch')` | Umbrella tool | Use `wealth_sensor_fetch` |
| Skipping schema validation | Risk of garbage-in-garbage-out | Always read `wealth://schemas/*` first |
| Claiming "capital has entropy" | Category error (physics ≠ economics) | "Capital uncertainty, modeled as entropy" |
| Executing `wealth_ledger_write` silently | F1 AMANAH violation | Always get ARIF confirmation first |
| Using V2 aliases in new code | Legacy, to be retired | Use canonical physics-named tools |
| Treating prompt as callable tool | Wrong MCP primitive | Call prompts via prompts/list + prompts/get |

---

## Part VI — Quick Reference

### Decision Tree: Which Primitive?

```
Is it a computation or action?
├── YES → Is it orchestrating multiple tools?
│   ├── YES → PROMPT
│   └── NO  → TOOL
└── NO  → Is it readable context?
    ├── YES → RESOURCE
    └── NO  → NOT IN WEALTH MCP
```

### Physics-Economics Mapping (Quick)

| Physics | Economics | Example |
|---------|-----------|---------|
| mass | net worth | `wealth_mass_networth` |
| flow | cash flow | `wealth_flow_cashflow` |
| gravity | debt burden | `wealth_gravity_dscr` |
| velocity | compounding | `wealth_velocity_runway` |
| pressure | liquidity stress | `wealth_pressure_triage` |
| entropy | uncertainty | `wealth_entropy_audit` |
| signal | information value | `wealth_signal_evoi` |
| energy | return potential | `wealth_energy_irr` |
| field | incentives/game theory | `wealth_field_game` |
| boundary | governance constraints | `wealth_boundary_floors` |
| sensor | data intake | `wealth_sensor_fetch` |
| ledger | conserved memory | `wealth_ledger_query` |

---

**DITEMPA BUKAN DIBERI — Intelligence is forged, not given.**

*Policy version 2026.05.07 — REPO=WEALTH — Author: OPENCLAW — Awaiting Arif SEAL*
