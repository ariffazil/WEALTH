# WEALTH Valuation Kernel
> Physics > Narrative — Wealth must be forged, not given.

WEALTH is the **Sovereign Valuation Kernel** for the arifOS ecosystem. It provides high-precision financial evaluation, capital allocation math, and portfolio intelligence.

## Domain Boundaries
- **WEALTH**: Financial Valuation & Capital Allocation (NPV, IRR, Networth).
- **arifOS**: Sovereign Orchestration & Governance (Floors, Seals, Identity).
- **GEOX**: World-State & Exogenous Risk (Country Premia, Macro Signals).

## Tools Registry

### 💰 Capital & Project Evaluation (`wealth.capital.*`)
- `wealth.capital.npv`: Net Present Value (Absolute value creation).
- `wealth.capital.irr`: Internal Rate of Return (Efficiency).
- `wealth.capital.mirr`: Modified IRR (Reinvestment-adjusted).
- `wealth.capital.emv`: Expected Monetary Value (Risk-adjusted).
- `wealth.capital.pi`: Profitability Index (Capital efficiency).
- `wealth.capital.payback`: Standard/Discounted Payback period.
- `wealth.capital.eaa`: Equivalent Annual Annuity (Unequal lives).
- `wealth.capital.roi`: Return on Investment.
- `wealth.capital.audit`: Financial integrity & sign-change audit.
- `wealth.capital.score`: Risk-adjusted cost of capital engine.

### 📊 Personal & Portfolio Intelligence (`wealth.personal.*`)
- `wealth.personal.networth`: Multi-asset net worth with epistemic tags.
- `wealth.personal.cashflow`: Liquidity and runway analysis.
- `wealth.personal.growth`: Compound growth projections.
- `wealth.personal.runway`: Depletion estimates.

## Usage
Run the FastMCP server:
```bash
npm run fastmcp
```

Or via Docker:
```bash
docker build -t wealth-valuation .
docker run -p 8080:8080 wealth-valuation
```

---
*999 SEAL ALIVE*
