<!-- SOT-MANIFEST
owner: ariffazil/wealth
last_verified: 2026-06-12
valid_from: 2026-06-12
valid_until: 2026-07-12
confidence: high
scope: /
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

1. **Dual runtime** — Python (`internal/monolith.py`, 48 tools) and JS (`src/`, legacy kernel) both exist. Python is canonical; JS is legacy. JS should be deprecated or removed.
2. **A-FORGE reimplementation** — `A-FORGE/src/tools/WealthTools.ts` reimplements WEALTH-domain logic (ROI, EMV, portfolio optimize). Should delegate to WEALTH MCP instead.
3. **License divergence** — `pyproject.toml` declares `PROPRIETARY` but `package.json` declares `AGPL-3.0`. One license must be canonical.

## Canonical Tool Surface (Live)

18 tools exposed on port 8082:
`wealth_health_check`, `wealth_conservation_capital`, `wealth_flow_liquidity`, `wealth_gradient_price`, `wealth_entropy_risk`, `wealth_energy_productivity`, `wealth_time_discount`, `wealth_inertia_leverage`, `wealth_field_macro`, `wealth_signal_information`, `wealth_game_coordination`, `wealth_boundary_governance`, `wealth_hysteresis_ledger`, `wealth_system_registry_status`, `wealth_synthesize`, `wealth_role_scarcity_risk`, `wealth_inequality_kernel`

## Canonical Surfaces

- **MCP Server:** FastMCP (`python internal/monolith.py`)
- **Test:** `pytest tests/` (Python) + `node --test tests/*.test.js` (JS legacy)
- **Docker:** `docker build -t wealth .`
