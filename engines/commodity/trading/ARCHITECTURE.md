# arifOS Trading Intelligence — Federation Architecture

> 3 patterns. Buy low, sell high. Risk/reward.
> Every organ has a job. No organ acts alone.

## The Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  🌍 GEOX        → Pattern detection (regime classification)        │
│  (111 observe)    Uptrend / Downtrend / Sideways                   │
│                   Swing highs/lows, S/R zones                       │
│                           ↓                                         │
│  🧠 arifOS      → Signal generation + governance                   │
│  (333 think)      Confluence scoring, F1-F13 floors                │
│  (888 judge)      Constitutional gate before execution             │
│                           ↓                                         │
│  💰 WEALTH       → Position sizing + risk management               │
│  (capital)        Kelly Criterion, drawdown limits                 │
│                   Daily loss cap, max positions                     │
│                           ↓                                         │
│  🔨 A-FORGE      → Order execution                                 │
│  (777 execute)    MT5 API, order management                        │
│                   Trailing stop, partial TP                         │
│                           ↓                                         │
│  ❤️ WELL         → Operator state check                            │
│  (wellness)       Is the human ready to trade?                     │
│                   Fatigue, stress, decision quality                 │
│                           ↓                                         │
│  📊 AAA          → Dashboard + alerts                              │
│  (display)        Cockpit, Telegram alerts                         │
│                   Voice notes in BM for Syed                        │
│                                                                     │
│  🔒 VAULT999    → Trade journal (immutable)                        │
│  (seal)           Every entry/exit recorded                        │
│                   Performance tracking                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Per-Organ Role

### GEOX (Pattern Detection)
- **What**: Compute market regime from OHLCV data
- **Tools**: EMA alignment, swing point detection, zone identification
- **Input**: Raw price data
- **Output**: MarketState (regime, zones, confidence)
- **Does NOT**: Generate signals, size positions, or execute

### arifOS (Signal + Governance)
- **What**: Generate trading signals and gate them through constitution
- **Tools**: `arif_think` (confluence scoring), `arif_judge` (constitutional gate)
- **Input**: MarketState from GEOX
- **Output**: Signal with verdict (PROCEED / HOLD / BLOCK / SABAR)
- **Does NOT**: Execute orders or manage positions

### WEALTH (Position Sizing + Risk)
- **What**: Calculate how much to risk and manage exposure
- **Tools**: `capital_primitive` (Kelly), risk state tracking
- **Input**: Signal from arifOS + account equity
- **Output**: Lot size, risk amount, position limits
- **Does NOT**: Place orders or detect patterns

### A-FORGE (Execution)
- **What**: Place and manage orders
- **Tools**: `forge_*` (MT5 API, order management)
- **Input**: Signal + sizing from WEALTH
- **Output**: Order confirmation, position tracking
- **Does NOT**: Generate signals or decide what to trade

### WELL (Operator State)
- **What**: Check if the human should be trading
- **Tools**: `well_assess_homeostasis`, `well_classify_state`
- **Input**: Operator biometrics, message patterns
- **Output**: Readiness score, decision quality assessment
- **Does NOT**: Trade or generate signals

### AAA (Display + Alerts)
- **What**: Show everything and alert the right people
- **Tools**: Dashboard, Telegram, voice
- **Input**: All outputs
- **Output**: Human-readable alerts, charts, voice notes
- **Does NOT**: Compute or execute

### VAULT999 (Journal)
- **What**: Record every trade immutably
- **Tools**: `arif_seal`
- **Input**: Trade records
- **Output**: Sealed receipts
- **Does NOT**: Modify or delete

## Data Flow

```
1. PRICE DATA → GEOX scans → "DOWNTREND, sell zone 4046"
2. GEOX → arifOS → "SELL signal, conf 79%, RR 1:2"
3. arifOS → WEALTH → "Risk $5, lot 0.01"
4. WEALTH → arifOS judge → "PROCEED (F1-F13 passed)"
5. arifOS → A-FORGE → "Execute SELL 0.01 @ 4036"
6. A-FORGE → MT5 → "Order placed, ticket #12345"
7. VAULT999 → "Sealed: SELL 0.01 @ 4036, SL 4060, TP 3983"
8. AAA → Telegram → "🔴 SELL signal. Entry 4036. SL 4060. TP 3983."
9. WELL → "Syed fatigue=LOW, decision_quality=GOOD"
```

## Cron Schedule

| Job | Schedule | What |
|-----|----------|------|
| Market Scan | Every 1H (London/NY sessions) | Full pipeline: scan → signal → alert |
| Position Monitor | Every 15min | Check open positions, trail stops |
| Daily Briefing | 8:00 AM MYT | Overnight moves, key levels, regime |
| Performance Review | Weekly | Trade journal analysis, stats |

## Backtesting

Every strategy change MUST be backtested before deployment:
1. Run on 2+ years of XAUUSD data (H1)
2. Minimum 100 trades
3. Win rate, avg RR, max drawdown, Sharpe ratio
4. If drawdown > 15% → strategy REJECTED
5. If Sharpe < 0.5 → strategy REJECTED

## Status

- [x] Regime detection (3 patterns)
- [x] Zone identification (S/R from swing points)
- [x] Signal engine v2 (simple truth)
- [x] Position sizing (Kelly + fixed-risk)
- [x] Governance gate (F1-F13)
- [ ] Backtest results (agents running)
- [ ] MT5 integration (A-FORGE)
- [ ] Cron automation
- [ ] WELL state check integration
- [ ] AAA dashboard
- [ ] VAULT999 trade journal
