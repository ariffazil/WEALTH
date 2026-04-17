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

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
