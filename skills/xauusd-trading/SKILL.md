---
id: xauusd-trading-stack
name: XAUUSD-trading-stack
version: 1.0.0-2026.07.14
description: >
  Federation-wide gold (XAUUSD) trading capability. Python stack, OANDA broker,
  backtesting, macro signals, RSI strategy. Every organ has a role.
owner: A-FORGE (execution) / WEALTH (intelligence) / arifOS (governance)
risk_tier: high
floor_scope: [F1, F2, F4, F5, F6, F7, F8, F9, F11, F13]
autonomy_tier: T3
trigger_phrases:
  - "trade gold"
  - "xauusd"
  - "gold trading"
  - "backtest gold"
  - "oanda"
  - "gold strategy"
  - "RSI gold"
dependencies:
  mcp_servers: [arifos, aforge, wealth, geox, well]
  skills: [ASI-cooling-ledger-rsi, wealth-collapse-signature]
  python_env: /root/trading/
  research: /root/XAUUSD_TRADING_RESEARCH.md
inputs:
  - market_data (OANDA / yfinance)
  - macro_signals (fredapi / GEOX)
  - human_readiness (WELL)
  - risk_limits (arifOS F1-F13)
outputs:
  - trade_signals
  - backtest_results
  - portfolio_metrics
  - sealed_trade_receipts (VAULT999)
capability_tier: fed-reasoning-heavy
ecology_state: WARM
---

# XAUUSD Trading Stack — Federation Skill

> **DITEMPA BUKAN DIBERI** — Gold is wealth. The stack is forged. Trade with governance.
> **This skill wires the entire federation to think about gold.**

## Quick Start (Any Agent)

```python
import sys
sys.path.insert(0, "/root/trading")
from quickstart import get_oanda_client, get_gold_price, run_backtest

# Check gold price now
price = get_gold_price()
print(f"XAUUSD: {price}")

# Connect to OANDA (needs credentials in config/oanda.env)
client = get_oanda_client()
```

## What Lives Where

| Path | Purpose |
|------|---------|
| `${TRADING_HOME:-/root/trading}/` | Python venv + all trading code |
| `${TRADING_HOME:-/root/trading}/bin/python3` | Python interpreter with all packages |
| `${TRADING_HOME:-/root/trading}/config/oanda.env` | OANDA credentials (NEVER commit) |
| `${TRADING_HOME:-/root/trading}/strategies/` | Backtrader strategies |
| `${TRADING_HOME:-/root/trading}/data/` | Cached market data |
| `${TRADING_HOME:-/root/trading}/logs/` | Trade logs |
| `/root/XAUUSD_TRADING_RESEARCH.md` | Full research brief |
| `${AAA_HOME:-/root/AAA}/prompts/XAUUSD_RSI_UPGRADE_v1.0.md` | RSI upgrade prompt |

## Installed Packages

| Package | Version | Purpose |
|---------|---------|---------|
| backtrader | 1.9.78 | Backtesting engine |
| TA-Lib | 0.7.0 | Technical analysis (RSI, MACD, BB, etc.) |
| pandas-ta | 0.4.71 | Pure-Python TA fallback |
| yfinance | 1.5.1 | Market data (GC=F for gold futures) |
| ccxt | 4.5.65 | Exchange connectivity |
| oandapyV20 | 0.7.2 | OANDA broker API |
| fredapi | 0.5.2 | Federal Reserve macro data |
| pandas | 3.0.3 | Data manipulation |
| numpy | 2.2.6 | Numerical computing |

## Organ Roles

| Organ | Role | Tool/Action |
|-------|------|-------------|
| **arifOS** | Govern | Approve/block trades, F1-F13 floor checks, seal receipts |
| **A-FORGE** | Execute | Run backtests, place orders, manage positions |
| **WEALTH** | Think | Position sizing, portfolio optimization, EMV, risk parity |
| **GEOX** | Sense | Commodity supply signals, macro regime detection |
| **WELL** | Guard | Human readiness gate — no manual trades if fatigued |
| **AAA** | Display | Cockpit dashboard, trade journal, P&L tearsheets |
| **VAULT999** | Record | Immutable trade receipts, sealed strategies |

## RSI Protocol (5 Phases)

Every trading session follows RSI:

1. **TRACE** — What did we observe? (market data, signals, decisions)
2. **DIAGNOSE** — What worked, what didn't? (backtest vs live, signal quality)
3. **REMEDIATE** — Fix the bottleneck (strategy tweak, risk adjustment, new signal)
4. **LEDGER** — Record the delta (append to cooling ledger)
5. **SEAL** — Lock learnings into VAULT999 (if significant)

## Safety Rails (F1-F13)

- **F1 AMANAH** — All trades start as paper/demo. Live trading requires explicit F13 approval.
- **F2 TRUTH** — No fabricated P&L. All backtest results come from real data.
- **F5 PEACE** — No leveraged positions > 10:1 without F13 approval.
- **F7 HUMILITY** — Surface uncertainty. "I don't know" is valid.
- **F9 ANTIHANTU** — No fake signals, no pump-and-dump, no manipulation.
- **F13 SOVEREIGN** — Arif has final say on all live trades.

## Agent Discovery

Any agent can find this skill via:
- Path: `/root/.agents/skills/XAUUSD-trading-stack/SKILL.md`
- Trigger phrases: "trade gold", "xauusd", "backtest", "oanda"
- Federation registry: `FEDERATED_SKILLS_REGISTRY_V3.yaml`

## For Hermes ASI

Hermes can use this skill to:
1. Run backtests via `${TRADING_HOME:-/root/trading}/bin/python3 strategies/xauusd_rsi_basic.py`
2. Fetch live prices via the quickstart module
3. Generate trade signals with RSI + macro overlay
4. Route trade approval through arifOS (F1-F13)
5. Seal successful strategies to VAULT999
6. Run RSI cycle at session end (cooling-ledger-rsi integration)
