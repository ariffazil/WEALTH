---
id: wealth-market-pulse
name: WEALTH Market Pulse
version: 1.0.0
description: Market and commodity observation via capital_market + capital_indicator. USE WHEN: 'gold price', 'XAUUSD context', 'FX MYR', 'oil price', 'RSI/EMA/MACD on a symbol'. Covers: capital_market (fx_commodity, stocks, indicators) → capital_indicator (ema/sma/rsi/macd/bb/psar/atr/adx pure numpy) → capital_entry_plan / capital_backtest for strategy surfaces. Iron rules: market data is OBS truth-class with timestamp staleness check; derived indicators are DER; trading SIGNALS are INT and require human confirm (F13) before any execution; backtests must state lookback + interval + initial capital assumptions.
owner: 333-AGI
risk_tier: medium
floor_scope: [F1, F2, F7, F11]
autonomy_tier: T1
organ_domain: wealth
forged: 2026-09-04
---

# WEALTH Market Pulse

Market and commodity observation via capital_market + capital_indicator. USE WHEN: 'gold price', 'XAUUSD context', 'FX MYR', 'oil price', 'RSI/EMA/MACD on a symbol'. Covers: capital_market (fx_commodity, stocks, indicators) → capital_indicator (ema/sma/rsi/macd/bb/psar/atr/adx pure numpy) → capital_entry_plan / capital_backtest for strategy surfaces. Iron rules: market data is OBS truth-class with timestamp staleness check; derived indicators are DER; trading SIGNALS are INT and require human confirm (F13) before any execution; backtests must state lookback + interval + initial capital assumptions.

## Provenance

Forged 2026-09-04 by 333-AGI (session SEAL-83defc585b5a4296) from live organ tool surfaces + FEDERATION_SKILL_PROFILE gap analysis. Source of truth: the organ MCP surface itself — when skill and tool surface disagree, the tool surface wins and this skill must be revised.
