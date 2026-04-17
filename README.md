# WEALTH — Capital Intelligence

**Organism Role:** Economic truth lane for arifOS  
**Constitutional Authority:** `ariffazil/arifOS`

WEALTH is the capital-allocation engine in the organism. It prices reward, survival, entropy, leverage, dignity, coordination, and policy constraints so capital decisions can be evaluated before arifOS applies the final constitutional judgment.

## Repo source of truth

This repository currently exposes **two MCP surfaces**:

| Surface | File | Role | Current scope |
|---|---|---|---|
| **Canonical valuation kernel** | `server.py` | Main packaged WEALTH MCP server | **29 tools + 2 resources** |
| **Civilizational domain demo** | `mcp/server.py` | Secondary FastMCP surface for domain-specific demos | **6 tools + 3 resources** |

The packaged runtime, `package.json` scripts, `fastmcp.json`, `Dockerfile`, and `mcp.json` all target the **root `server.py`** kernel. `mcp/server.py` is supplemental, not the primary deployment surface.

## Canonical kernel surface (`server.py`)

The main WEALTH kernel currently groups into these operational families:

1. **Valuation and reward:** `wealth_npv_reward`, `wealth_irr_yield`, `wealth_pi_efficiency`, `wealth_emv_risk`, `wealth_payback_time`, `wealth_growth_velocity`, `wealth_monte_carlo_forecast`
2. **State and decision:** `wealth_networth_state`, `wealth_cashflow_flow`, `wealth_score_kernel`, `wealth_personal_decision`, `wealth_agent_budget`
3. **Crisis and coordination:** `wealth_crisis_triage`, `wealth_civilization_stewardship`, `wealth_coordination_equilibrium`, `wealth_game_theory_solve`
4. **Sense / ingest:** `wealth_ingest_fetch`, `wealth_ingest_snapshot`, `wealth_ingest_sources`, `wealth_ingest_health`, `wealth_ingest_vintage`, `wealth_ingest_reconcile`
5. **Governance and policy:** `wealth_audit_entropy`, `wealth_dscr_leverage`, `wealth_check_floors`, `wealth_policy_audit`, `wealth_init`
6. **Vault persistence:** `wealth_record_transaction`, `wealth_snapshot_portfolio`

Resources:

- `wealth://doctrine/valuation`
- `wealth://dimensions/definitions`

## Civilizational demo surface (`mcp/server.py`)

The smaller FastMCP surface is a domain demo for markets, energy, food, and GEOX-linked prospect economics:

- `wealth_evaluate_prospect`
- `markets_analyze_ticker`
- `markets_portfolio_stress_test`
- `energy_crisis_assess`
- `energy_shortage_predict`
- `food_security_index`

Resources:

- `market://{ticker}/fundamentals`
- `energy://{region}/realtime-mix`
- `food://global/prices`

## Architecture notes

- **`server.py` is the packaged truth surface.** If docs disagree with it, `server.py` wins.
- **`mcp/server.py` is a secondary surface.** It extends WEALTH into domain demos without replacing the canonical valuation kernel.
- **`registry.json` remains the canonical 11-band organism map**, not an exhaustive runtime tool list. The live root kernel is a larger operational superset.

## Repo layout

| Path | Purpose |
|---|---|
| `server.py` | Canonical WEALTH MCP kernel |
| `mcp/server.py` | Civilizational FastMCP demo server |
| `host/` | Shared runtime logic, governance, coordination, ingestion, and wealth primitives |
| `docs/` | Operational specifications and acceptance docs |
| `canon/` | Canonical 11-artifact knowledge spine |
| `wiki/` | Architecture notes and evolution log |
| `tests/` | Existing Node test suite |

## Running WEALTH

```bash
cd /root/WEALTH
npm test
python server.py
python mcp/server.py
```

## Economic invariants

- **Objective Function:** Maximize `Peace² × ΔKnowledge / (ΔEntropy × ΔCapital)` under constitutional bounds.
- **WEALTH qualifies; arifOS judges.** WEALTH produces capital truth and policy evidence, while arifOS retains final constitutional permission.
- **No black-box capital signals.** Pricing, entropy, and dignity signals must remain inspectable and tagged with epistemic humility where required.

---

## Epistemic Integrity Pipeline

**Audit Reference:** Session 2026-04-18
**Purpose:** Formalize probabilistic input schema, detect portfolio correlation risk, integrate EVOI calculations.

### Overview

WEALTH now requires **probabilistic inputs from GEOX**, not collapsed scalars. This preserves the posterior structure across the GEOX → WEALTH handoff — the entire epistemic content survives instead of being destroyed in transit.

### Schema Validation (`host/epistemic/schema_validator.py`)

WEALTH **rejects single-value volumetrics** from GEOX. Required input schema:

```json
{
  "prospect_id": "string",
  "stoiip": {"p10": float, "p50": float, "p90": float, "unit": "MMbbl"},
  "pos": float,
  "integrity_score": float,
  "model_lineage_hash": "string",
  "posterior_breadth": float
}
```

**Refusal triggers:**
- `integrity_score < 0.3` → `EPISTEMIC_HOLD`, do not pass to capital allocation
- Scalar-only stoiip (e.g., `{"stoiip": 45.2}`) → REJECTED
- Missing required fields → REJECTED

### Portfolio Correlation Guard (`host/epistemic/correlation_guard.py`)

Tracks `model_lineage_hash` across all prospects. If ≥3 prospects share the same lineage hash:

```
{"systemic_risk": true, "action": "HOLD — correlated model bias detected"}
```

This prevents the correlation catastrophe where one flawed AI interpretation influences 10 wells simultaneously.

### EVOI Calculator (`host/epistemic/evoi.py`) — WIP

```python
compute_evoi(
    prior_pos: float,
    posterior_pos: float,
    well_cost_musd: float,
    p50_value_musd: float
) -> {"evoi_musd": float, "drill_recommendation": str}
```

**EVOI = E[V | with_info] - E[V | without_info]**

Before drilling, compute whether acquiring more seismic is worth it. Sometimes the best decision is: Do not drill. Acquire data.

### Integrity Score Gating

| Integrity Score | Classification | Action |
|---------------|---------------|--------|
| < 0.3 | **AUTO_HOLD** | Do NOT pass to capital allocation |
| 0.3 – 0.6 | **PLAUSIBLE** | Pass with warning |
| > 0.6 | **CLAIM** | Pass to capital allocation normally |

### System-Level Coupling

| Before Fix | After Fix |
|-----------|-----------|
| GEOX produces scalar → WEALTH receives scalar | GEOX produces posterior → WEALTH reasons over posterior |
| Uncertainty destroyed at handoff | Uncertainty preserved end-to-end |
| Portfolio bias undetected | Correlation guard flags systemic lineage risk |
| No epistemic audit trail | model_lineage_hash + integrity_score on every output |
| Single NPV to board | P10/P50/P90 + integrity score + correlation risk to board |

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
