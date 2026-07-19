<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-18
valid_from: 2026-06-14
valid_until: 2026-08-17
confidence: high
scope: /root/WEALTH/BOUNDARY.md
-->

# BOUNDARY.md — WEALTH Capital Intelligence / Resource Thermodynamics

> **DITEMPA BUKAN DIBERI** — Forged, not given.

## Owns

- **Capital Stock Reality** — Asset/liability/reserve accounting, conservation capital scoring (Ω-WEALTH-01)
- **Liquidity Movement** — Cashflow analysis, burn rate, runway, survival scoring (Ω-WEALTH-02)
- **Price Pressure & Mispricing** — Gradient detection, spread analysis, market asymmetry (Ω-WEALTH-03)
- **Risk & Uncertainty** — Entropy audit, tail risk, return classification, Monte Carlo simulation (Ω-WEALTH-04)
- **Productivity & Efficiency** — IRR, NPV, energy productivity, capital efficiency (Ω-WEALTH-05)
- **Time Value** — Discount rates, payback, compounding, decay (Ω-WEALTH-06)
- **Leverage & Fragility** — DSCR, inertia stress, debt service coverage (Ω-WEALTH-07)
- **Macro Field** — Rates, FX, energy, carbon, regime snapshots (Ω-WEALTH-08)
- **Information Value** — EVOI, signal quality, evidence grading (Ω-WEALTH-09)
- **Game Theory** — Multi-agent coordination, bargaining, Nash approximation (Ω-WEALTH-10)
- **Governance & Legitimacy** — Boundary audits, maruah scoring, institutional drift (Ω-WEALTH-11)
- **Ledger & Memory** — Path dependence, sealed financial memory (Ω-WEALTH-12)
- **Synthesis** — Cross-dimensional capital intelligence verdict (Ω-WEALTH-00)
- **Inequality Kernel** — Role scarcity, conversion architecture, asymmetry mapping (Ω-WEALTH-IEQ)

## Does Not Own

- **Constitutional Law** — F1–F13 enforcement, verdict engine, seal authority (owned by arifOS)
- **Earth-Truth Modeling** — Geospatial, subsurface, prospect evaluation (owned by GEOX)
- **Operator Cockpit** — React dashboard, agent workspace UX (owned by AAA)
- **Deployment Orchestration** — Docker compose, release assembly, infrastructure (owned by A-FORGE)
- **MCP Schema Authority** — Canonical tool registry, governance contracts (owned by arifOS)
- **Web Search / Crawling** — General web search, URL fetch (owned by A-FORGE or sensing layer)

## Imports From

| Source | What | Interface |
|--------|------|-----------|
| **arifOS** | Constitutional constraints, floor enforcement, session tokens | MCP mesh, federation probe |
| **A-FORGE** | Deploy metadata, container runtime, build pipeline | GHCR image, compose manifests |
| **GEOX** — *planned* | Prospect volume estimates, resource quality data | MCP mesh (future) |
| **AAA** | Operator capital allocation intent, portfolio review requests | A2A mesh |

## Exports To

| Consumer | What | Interface |
|----------|------|-----------|
| **arifOS** | Capital viability verdicts, risk scores, decision memos | MCP tool calls, JSON artifacts |
| **AAA** | Decision memo viewer, portfolio dashboard data | HTTP API, static artifacts |
| **A-FORGE** | Docker image, build context | `ghcr.io/ariffazil/wealth:<sha>` |

## Known Boundary Violations (888 HOLD Queue)

1. **Dual runtime** — Python (`internal/monolith.py`, 26 public tools + 6 hidden aliases = 32 total decorated tools) and JS (`src/`, legacy kernel) both exist. Python is canonical; JS is legacy. JS should be deprecated or removed.
2. **A-FORGE reimplementation** — `A-FORGE/src/tools/WealthTools.ts` reimplements WEALTH-domain logic (ROI, EMV, portfolio optimize). Should delegate to WEALTH MCP instead.
3. **License divergence** — RESOLVED. `pyproject.toml` and `package.json` both declare `AGPL-3.0`.

## Canonical Tool Surface (Live)

26 public tools exposed on port 18082 (plus 6 hidden aliases; 32 total decorated tools):

`wealth_wisdom_evaluate`, `wealth_power_audit`, `wealth_capture_scan`, `wealth_compute_npv`, `wealth_compute_irr`, `wealth_conservation_check`, `wealth_flow_check`, `wealth_runway_check`, `wealth_compute_emv`, `wealth_compute_evoi`, `wealth_monte_carlo_simulate`, `wealth_confluence_check`, `wealth_asymmetry_check`, `wealth_stock_analysis`, `wealth_personal_finance`, `wealth_market_data`, `wealth_omni_wisdom`, `wealth_agent_path`, `wealth_vault_write`, `wealth_vault_query`, `wealth_boundary_governance`, `wealth_survival_engine`, `wealth_registry_status`, `wealth_collapse_signature_scan`, `wealth_beautiful_mouse_scan`, `wealth_judge_handoff`

> **Verified:** 32 `@mcp.tool` decorated names exposed via `tools/list` on port 18082 — 26 public tools + 6 backward-compat aliases.

## Canonical Surfaces

- **MCP Server:** FastMCP (`python internal/monolith.py`)
- **Test:** `pytest tests/` (Python) + `node --test tests/*.test.js` (JS legacy)
- **Docker:** `docker build -t wealth .`
