# WEALTH Valuation Kernel (v1.3.1)
> Physics > Narrative — Capital must be forged, not given.

WEALTH is the **Sovereign Valuation Kernel** for the arifOS ecosystem. It provides high-precision financial evaluation and capital allocation math, mapped to fundamental physical dimensions.

## What's new in v1.3.1

- Hardened the finance kernel with explicit measurement rules for **NPV, EAA, IRR, MIRR, PI, EMV, payback, discounted payback, and DSCR**.
- Locked **JS↔Python parity** on canonical NPV, DSCR, and growth vectors.
- Removed the Python MCP server's runtime dependency on a `node` subprocess for core WEALTH tools.
- Added **confidence bands** for estimated/hypothesis inputs and escalated ambiguous IRR plus DSCR default stress to **`888-HOLD`**.

## 🛡️ Orthogonal Architecture
WEALTH is part of a 33-tool orthogonal lattice (3 organs × 11 tools).

| Organ | Role | Namespace |
| :--- | :--- | :--- |
| **arifOS** | Constitutional Governor | `arifos_*` |
| **WEALTH** | Capital Evaluation | `wealth_*` |
| **GEOX** | Earth Intelligence | `geox_*` |

## 🛠️ The Dimensional Forge (11 Tools)

| Tool Name | Dimension | Included Metrics |
| :--- | :--- | :--- |
| `wealth_npv_reward` | Reward | NPV, Terminal Value, EAA |
| `wealth_irr_yield` | Energy | IRR, MIRR, Potential |
| `wealth_pi_efficiency` | Energy | Profitability Index (Concentration) |
| `wealth_emv_risk` | Entropy | Expected Monetary Value (Probability) |
| `wealth_audit_entropy` | Entropy | Sign-change Audit, Sensitivity |
| `wealth_dscr_leverage` | Survival | Debt Service Coverage (Structural Load) |
| `wealth_payback_time` | Time | Recovery Velocity (Standard/Discounted) |
| `wealth_growth_velocity` | Velocity | Compounding + Mandatory Runway |
| `wealth_networth_state` | Mass | Portfolio Mass (Enforced Taxonomy) |
| `wealth_cashflow_flow` | Flow | Metabolic Liquidity (Monthly Flow) |
| `wealth_score_kernel` | Allocation | Mandatory Governance Signal Evaluation |

## 📜 Asset Taxonomy (Enforced)
To maintain mass integrity, `wealth_networth_state` accepts only:
`cash` | `equity` | `property` | `digital` | `debt` | `business`

## 🚀 Usage
### Local MCP server
```bash
npm run mcp
```

### Python entrypoint
Entrypoint: `server.py:mcp`

### Node validation suite
```bash
npm test
```

## Measurement doctrine

WEALTH measures **capital physics**, not total reality:

- **Observable state** — assets, liabilities, income, expenses, debt service
- **Derived finance metrics** — NPV, MIRR, PI, EMV, DSCR, payback, runway
- **Governed scored variables** — maruah, trust, entropy, deltaCiv

Anything without a source, unit, periodicity, transformation rule, or uncertainty band should be downgraded or refused rather than presented as a hard claim.

---
**999 SEAL ALIVE** — *Dimensional Integrity Sealed*
