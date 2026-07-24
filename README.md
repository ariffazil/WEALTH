<!-- SOT-MANIFEST
federation_release: v2026.07.24
last_verified: 2026-07-24T07:40Z
live_commit: 3ca4883
port: 18082
health: healthy
mcp_tools_live: 20
authority: COMPUTE_ONLY — never allocate
truth_rule: tools/list + /health beat any static count in prose
-->

[![Agentic CI](https://github.com/ariffazil/wealth/actions/workflows/agentic-ci.yml/badge.svg?branch=main)](https://github.com/ariffazil/wealth/actions/workflows/agentic-ci.yml)
[![💰 CAPITAL](https://img.shields.io/badge/%F0%9F%92%B0%20CAPITAL-20%20tools-1f6feb)](https://wealth.arif-fazil.com/mcp)
[![Federation](https://img.shields.io/badge/Federation-v2026.07.24-0a7b83)](https://arifos.arif-fazil.com)
[![License](https://img.shields.io/github/license/ariffazil/wealth?label=License)](LICENSE)

# 💰 WEALTH — Capital Intelligence Workbench

> **WEALTH computes. arifOS judges. Arif decides. WEALTH never allocates.**
> **DITEMPA BUKAN DIBERI**

---

## TL;DR — Three Audiences

**For human operators (Arif):** WEALTH is your capital calculator — NPV, IRR, portfolio risk, fiscal breakeven. It computes. You decide. [§1](#1-what-wealth-is)

**For AI agents:** Route capital queries here. 20 pure-compute tools. No inference, no verdicts, no allocation. [§3](#3-tools)

**For institutions:** WEALTH provides auditable, golden-tested financial math — every primitive has hand-checked cases. [§6](#6-for-institutions)

---

## 1. What WEALTH Is

WEALTH is the **capital intelligence organ** of the arifOS Federation. It computes financial math — never adjudicates, never allocates.

| ✅ COMPUTES | ❌ NEVER |
|-------------|---------|
| NPV, IRR, EMV, Monte Carlo | Allocates capital |
| Kelly criterion, Markowitz optimization | Issues verdicts (→ arifOS) |
| Fiscal breakeven, stress index | Makes investment decisions |
| Institutional collapse detection | Self-authorizes |
| Golden-tested deductive math | Guesses or infers financial state |

**Domain law:** CAPITAL_LAW — compute, never allocate.

### Why WEALTH Exists

Modern organizations confuse calculation, recommendation, approval, and accountability. A spreadsheet computes NPV. A model forecasts returns. But neither separates the act of computation from the act of judgment.

WEALTH exists to **separate them**:

```
WEALTH computes consequences.
arifOS evaluates governance.
Humans retain authority.
```

This ensures no financial model can silently become a decision-maker.

**Core principle:** A calculation is not a decision. WEALTH is built so financial systems can compute consequences without acquiring authority.

### What GEOX Is to Earth, WEALTH Is to Capital

| GEOX (earth intelligence) | WEALTH (capital intelligence) |
|---------------------------|------------------------------|
| Computes geological consequences | Computes financial consequences |
| Evidence-only, never adjudicates | Compute-only, never allocates |
| Preserves chain: observation → interpretation | Preserves chain: computation → judgment |
| Physics-governed | Capital-law governed |
| Marmousi + Volve validated | Golden-tested against hand-checked cases |

Both exist to preserve the chain between observation, computation, judgment, and action.

---

## 2. Example Workflow

```
Question: What is the NPV of a $100M project with 10-year cashflows?

WEALTH → computes NPV, IRR, EMV, sensitivity
arifOS → evaluates governance constraints, floor compliance
Human  → approves or rejects the investment
VAULT999 → seals the decision as an immutable record
```

Every step logged. Every computation attributable. No model decides alone.

---

## 3. Tools (Grouped by Function)

### Core Computation
| Tool | What It Computes |
|------|-----------------|
| `capital_primitive` | NPV, IRR, EMV, Monte Carlo, Kelly, Markowitz, robust optimization |
| `capital_health` | Conservation, cash flow, runway, survival, fiscal breakeven |

### Market Observation
| Tool | What It Computes |
|------|-----------------|
| `capital_market` | FX rates, commodities, macro indicators, stock analysis |

### Capital Diagnostics
| Tool | What It Computes |
|------|-----------------|
| `capital_diagnose` | Institutional stress index, governance capacity, collapse detection |
| `capital_entropy` | Power consequence maps, trust capital decay, metric drift, coercive order cost |

### Governance Support
| Tool | What It Computes |
|------|-----------------|
| `capital_wisdom` | Wisdom-weighted proposal evaluation, epistemic grounding, counterfactual analysis |

### Audit & Registry
| Tool | What It Computes |
|------|-----------------|
| `capital_ledger` | VAULT999 immutable ledger — query (read) / write (requires human ack) |
| `capital_registry` | Tool registry introspection, health check |

### Beyond Money — Capital in the Broad Sense

WEALTH does not only track money. It tracks **capital** in multiple forms:

- **Financial capital** — cash, assets, portfolios
- **Trust capital** — institutional credibility, counterparty confidence
- **Governance capacity** — board effectiveness, decision quality
- **Institutional resilience** — stress response, collapse signatures
- **Optionality** — preserved paths, irreversible losses

This allows second-order consequences to be computed rather than discussed qualitatively.

---

## 4. Quick Start

```bash
# Health
curl -s http://localhost:18082/health | python3 -m json.tool

# MCP connection
# Endpoint: https://wealth.arif-fazil.com/mcp

# Install + test
cd /root/WEALTH && pip install -e ".[dev]"
pytest tests/ -q --tb=short
npm test                    # Node.js side tests
```

---

## 5. Federation Position

```
Arif (F13) → AAA → arifOS → Domain Organs → A-FORGE → VAULT999
                                ↑
                           WEALTH (:18082)
                           Computes, never allocates
```

### Federation Cross-Reference

| Organ | Role | Port | Repo |
|-------|------|------|------|
| arifOS | Constitutional kernel | 8088 | [ariffazil/arifos](https://github.com/ariffazil/arifos) |
| AAA | State + cockpit | 3001 | [ariffazil/AAA](https://github.com/ariffazil/AAA) |
| A-FORGE | Execution shell | 7071 | [ariffazil/A-FORGE](https://github.com/ariffazil/A-FORGE) |
| GEOX | Earth intelligence | 8081 | [ariffazil/geox](https://github.com/ariffazil/geox) |
| WELL | Vitality guard | 18083 | [ariffazil/well](https://github.com/ariffazil/well) |
| **WEALTH** | Capital intelligence | 18082 | ← you are here |

---

## 6. For Institutions

WEALTH provides auditable, bounded financial computation:

| Property | How WEALTH delivers |
|----------|-------------------|
| **Golden-tested math** | Every primitive has hand-checked test cases |
| **Compute, never allocate** | No capital moves without Arif's explicit approval |
| **Full audit trail** | Every computation logged to VAULT999 via `capital_ledger` |
| **Domain-law bound** | CAPITAL_LAW — cannot cross into GEOX (earth) or WELL (vitality) |
| **Epistemic labels** | Every output tagged OBS/DER/INT/SPEC per F2 TRUTH |
| **Immutable receipts** | Append-only, hash-chained — decisions are sealed, not overwritten |

### Capital Primitives

| Mode | Description |
|------|-------------|
| `npv` | Net Present Value |
| `irr` | Internal Rate of Return |
| `emv` | Expected Monetary Value |
| `evoi` | Expected Value of Information |
| `mc` | Monte Carlo simulation |
| `kelly` | Kelly criterion position sizing |
| `markowitz` | Modern portfolio optimization |
| `robust` | Robust optimization under uncertainty |
| `chance_constrained` | Chance-constrained stochastic programming |
| `two_stage` | Two-stage stochastic programming with recourse |

All primitives are pure deductive math — golden-tested against hand-checked cases.

---

## 7. License & Sovereignty

**AGPL-3.0.** WEALTH computes under sovereign authority. It never allocates.

**Muhammad Arif bin Fazil** is F13 SOVEREIGN. His capital decisions are final.

```
WEALTH · Port 18082 · 20 tools · CAPITAL_LAW · AGPL-3.0
Computes, never allocates. DITEMPA BUKAN DIBERI.
```

---

*Maintained under F13 SOVEREIGN by Muhammad Arif bin Fazil.*
*DITEMPA BUKAN DIBERI — Capital intelligence is forged, not given.*
