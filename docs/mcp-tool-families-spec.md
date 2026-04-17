# WEALTH MCP Tool Families — Current Repo SOT

> **Version:** v1.5.0  
> **Status:** ACTIVE REPO STATE  
> **Epistemic:** CLAIM  
> **DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**

---

## 1. Runtime split

WEALTH currently exposes two MCP surfaces in-repo:

| Surface | File | Purpose |
|---|---|---|
| Canonical valuation kernel | `server.py` | Main packaged WEALTH runtime |
| Civilizational demo surface | `mcp/server.py` | Secondary domain demo for markets / energy / food / prospect evaluation |

The rest of this document treats `server.py` as the primary operational surface and `mcp/server.py` as a narrower extension.

---

## 2. Canonical kernel families (`server.py`)

### 2.1 Valuation and reward
Tools:
- `wealth_npv_reward`
- `wealth_irr_yield`
- `wealth_pi_efficiency`
- `wealth_emv_risk`
- `wealth_payback_time`
- `wealth_growth_velocity`
- `wealth_monte_carlo_forecast`

Core question: **What is the reward profile once time, uncertainty, and compounding are made explicit?**

### 2.2 Structural load and survival
Tools:
- `wealth_dscr_leverage`
- `wealth_audit_entropy`

Core question: **Can the structure survive its own financing and cashflow noise?**

### 2.3 State and portfolio metabolism
Tools:
- `wealth_networth_state`
- `wealth_cashflow_flow`
- `wealth_score_kernel`
- `wealth_personal_decision`
- `wealth_agent_budget`

Core question: **What is the current financial state, and which choice is most defensible under constraints?**

### 2.4 Crisis, civilization, and coordination
Tools:
- `wealth_crisis_triage`
- `wealth_civilization_stewardship`
- `wealth_coordination_equilibrium`
- `wealth_game_theory_solve`

Core question: **How should capital be allocated when many actors, survival constraints, or long-horizon stewardship pressures interact?**

### 2.5 Sense / ingest
Tools:
- `wealth_ingest_fetch`
- `wealth_ingest_snapshot`
- `wealth_ingest_sources`
- `wealth_ingest_health`
- `wealth_ingest_vintage`
- `wealth_ingest_reconcile`

Core question: **What live or cached external signals are available, and how trustworthy are they right now?**

### 2.6 Governance and vault
Tools:
- `wealth_check_floors`
- `wealth_policy_audit`
- `wealth_record_transaction`
- `wealth_snapshot_portfolio`
- `wealth_init`

Resources:
- `wealth://doctrine/valuation`
- `wealth://dimensions/definitions`

Core question: **Is the allocation constitutionally acceptable, and how is the evidence anchored?**

---

## 3. Civilizational demo family (`mcp/server.py`)

This secondary server currently carries six domain-facing demo tools:

| Domain | Tools |
|---|---|
| Prospect economics | `wealth_evaluate_prospect` |
| Markets | `markets_analyze_ticker`, `markets_portfolio_stress_test` |
| Energy | `energy_crisis_assess`, `energy_shortage_predict` |
| Food | `food_security_index` |

Resources:

- `market://{ticker}/fundamentals`
- `energy://{region}/realtime-mix`
- `food://global/prices`

This surface is **real**, but it is **not** the packaged kernel used by `npm run mcp`.

---

## 4. Canonical 11-band map vs live runtime

`registry.json` still expresses the **canonical 11-band organism lattice**. That file is a conceptual lane map, not a complete live tool inventory.

Therefore:

- `registry.json` = canonical 11-band map
- `server.py` = packaged runtime truth
- `mcp/server.py` = secondary civilizational demo truth

If those ever conflict, prefer the runtime files.

---

## 5. Failure modes

| Failure | Symptom | Mitigation |
|---|---|---|
| Wrong server assumption | Operators wire `mcp/server.py` thinking it is the packaged kernel | Use `server.py` for packaged/runtime integrations |
| Stale family docs | Docs describe dotted namespaces not implemented in code | Derive tool families from actual `@mcp.tool` surfaces |
| Canon/runtime confusion | `registry.json` count differs from `server.py` tool count | Treat registry as canonical topology, not exhaustive runtime inventory |
| Demo promoted as kernel | Civilizational surface treated as full production valuation engine | Label `mcp/server.py` explicitly as supplemental |

---

*Spec v1.5.0 | Repo SOT aligned*
