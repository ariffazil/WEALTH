# arifOS Trading Intelligence System

> **SCANNER → SIGNAL → RISK → JUDGE → EXECUTE → TRACK → ALERT**
> Agentic intelligence for XAUUSD. Built by arifOS federation for ARIF (F13 SOVEREIGN).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    arifOS TRADING SYSTEM                        │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ SCANNER  │→ │ SIGNAL   │→ │   RISK   │→ │   JUDGE      │   │
│  │ (111)    │  │ (333)    │  │ (WEALTH) │  │ (arifOS 888) │   │
│  │          │  │          │  │          │  │              │   │
│  │ • EMA    │  │ • Conf-  │  │ • Kelly  │  │ • F1 AMANAH  │   │
│  │ • RSI    │  │   luce   │  │ • Daily  │  │ • F2 TRUTH   │   │
│  │ • MACD   │  │   Score  │  │   Loss   │  │ • F7 HUMILITY│   │
│  │ • ATR    │  │ • Dir-   │  │ • Max DD │  │ • F11 AUDIT  │   │
│  │ • S/R    │  │   ection │  │ • Pos    │  │ • F13 SOV.   │   │
│  │ • Candle │  │ • Conf-  │  │   Limits │  │              │   │
│  │   Pattern│  │   idence │  │          │  │  VERDICT:    │   │
│  └──────────┘  └──────────┘  └──────────┘  │  PROCEED/    │   │
│                                             │  HOLD/       │   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  BLOCK/SABAR │   │
│  │ EXECUTE  │← │  TRACK   │← │  ALERT   │← └──────────────┘   │
│  │ (777)    │  │ (VAULT)  │  │ (DM/Voice)│                     │
│  │          │  │          │  │          │                      │
│  │ • Manual │  │ • Journal│  │ • Telegram│                     │
│  │ • MT5    │  │ • Learn  │  │ • Voice  │                     │
│  │ • Alert  │  │ • Stats  │  │   BM     │                     │
│  └──────────┘  └──────────┘  └──────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

## Components

| Module | Path | Purpose |
|--------|------|---------|
| **Config** | `core/config.py` | Single source of truth for all parameters |
| **Models** | `core/models.py` | OHLCV, Signal, Position, TradeRecord, RiskState |
| **Scanner** | `signals/scanner.py` | EMA, RSI, MACD, ATR, S/R, candle patterns |
| **Engine** | `signals/engine.py` | Multi-factor confluence scoring → Signal |
| **Data Feed** | `signals/data_feed.py` | yfinance, file, or manual price ingestion |
| **Position Sizer** | `risk/position_sizer.py` | Kelly Criterion + fixed-risk sizing |
| **Risk Manager** | `risk/manager.py` | Drawdown protection, daily limits, position caps |
| **Governance** | `governance/gate.py` | arifOS F1-F13 constitutional gate |
| **Orchestrator** | `main.py` | Wires everything together |

## Usage

```bash
# Test with sample data
python -m trading.main test

# Scan only (generates signal)
python -m trading.main scan --json

# Generate alert text
python -m trading.main alert

# System status
python -m trading.main status
```

## Signal Generation Logic

1. **Scan** — compute all indicators from OHLCV data
2. **Score** — each indicator produces a ConfluenceFactor (direction, weight, confidence)
3. **Aggregate** — BUY score vs SELL score. Winner must exceed min_confluence threshold
4. **Size** — Kelly Criterion + fixed-risk, conservative (quarter-Kelly for Syed)
5. **Judge** — arifOS constitutional floors (F1-F13). Can PROCEED, HOLD, BLOCK, or SABAR
6. **Alert** — human-readable text (BM for Syed, JSON for machines)

## Risk Rules

| Rule | Value | Floor |
|------|-------|-------|
| Max risk per trade | 1% of equity | F1 AMANAH |
| Max daily loss | 3% of equity | F1 AMANAH |
| Max drawdown | 10% of equity | F1 AMANAH |
| Max open positions | 3 | F1 AMANAH |
| Min RR ratio | 1:2 | F2 TRUTH |
| Confidence cap | 0.90 | F7 HUMILITY |
| Kelly fraction | 0.25 (quarter) | F7 HUMILITY |

## Cron Integration

This system replaces the existing `XAUUSD Price Alert` cron job with a governed pipeline:

```
Old: Scrape → Format → Send
New: Scan → Score → Size → Judge → Alert (with provenance)
```

## Status

- [x] Core engine (scanner + signal + risk + governance)
- [x] Position sizing (Kelly + fixed-risk)
- [x] Governance gate (arifOS constitutional)
- [x] Test pipeline (sample data)
- [ ] Real-time data feed (yfinance or MT5)
- [ ] Cron integration (replace existing alert)
- [ ] Backtesting framework
- [ ] Performance journal + learning
- [ ] Voice alerts (TTS in BM)
- [ ] Syed dashboard (arif-fazil.com/wealth/gold/)
