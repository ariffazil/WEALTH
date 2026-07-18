#!/usr/bin/env python3
"""
GOLD SIGNAL ENGINE — Abang Sado Udin
Phase 1: Signal companion, not executor.

Fetches XAUUSD data, calculates EMA 20/50, S/R levels, RSI,
candlestick patterns, and generates trading signals with
confluence validation (≥2 indicators required).

F3 WITNESS: Single-indicator signal = breach, rejected.
F2 TRUTH: All signals labeled with evidence.
F7 HUMILITY: "No signal" is a valid output.

Usage:
  python3 gold_engine.py              # Generate current signal
  python3 gold_engine.py --briefing   # Daily briefing format
  python3 gold_engine.py --backtest   # Backtest last 30 days
"""

import json
import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import yfinance as yf
import pandas as pd
import numpy as np

# ── CONFIG ──────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent.parent / "config" / "trading_spec.json"
JOURNAL_PATH = Path(__file__).parent.parent / "journal" / "signals.jsonl"

MYT = timezone(timedelta(hours=8))
UTC = timezone.utc

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

# ── DATA FETCH ──────────────────────────────────────────────────
def fetch_gold_data(period="60d", interval="1h"):
    """Fetch XAUUSD from Yahoo Finance."""
    ticker = yf.Ticker("GC=F")  # Gold futures
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        # Fallback: try XAUUSD=X
        ticker = yf.Ticker("XAUUSD=X")
        df = ticker.history(period=period, interval=interval)
    return df

def fetch_macro():
    """Fetch DXY and 10Y yields."""
    macro = {}
    try:
        dxy = yf.Ticker("DX-Y.NYB").history(period="5d", interval="1d")
        if not dxy.empty:
            macro['dxy'] = round(dxy['Close'].iloc[-1], 2)
            macro['dxy_change'] = round(
                (dxy['Close'].iloc[-1] - dxy['Close'].iloc[-2]) / dxy['Close'].iloc[-2] * 100, 2
            ) if len(dxy) > 1 else 0
    except:
        macro['dxy'] = None
        macro['dxy_change'] = None

    try:
        tnx = yf.Ticker("^TNX").history(period="5d", interval="1d")
        if not tnx.empty:
            macro['us10y'] = round(tnx['Close'].iloc[-1], 3)
    except:
        macro['us10y'] = None

    return macro

# ── TECHNICAL ANALYSIS ──────────────────────────────────────────
def calc_ema(df, fast=20, slow=50):
    """Calculate EMA crossover signals."""
    df['ema_fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
    df['ema_cross'] = 0
    df.loc[df['ema_fast'] > df['ema_slow'], 'ema_cross'] = 1   # Bullish
    df.loc[df['ema_fast'] < df['ema_slow'], 'ema_cross'] = -1  # Bearish
    # Detect crossover
    df['ema_cross_signal'] = df['ema_cross'].diff()
    return df

def calc_rsi(df, period=14):
    """Calculate RSI."""
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def calc_rsi_divergence(df, lookback=20):
    """Detect RSI divergence (bullish/bearish)."""
    df['rsi_divergence'] = 0
    if len(df) < lookback:
        return df

    recent = df.tail(lookback)

    # Bullish divergence: price lower low, RSI higher low
    price_low_idx = recent['Close'].idxmin()
    rsi_at_low = recent.loc[price_low_idx, 'rsi']

    # Check if current RSI is higher than RSI at price low
    current_rsi = recent['rsi'].iloc[-1]
    current_price = recent['Close'].iloc[-1]
    price_at_rsi_low = recent.loc[recent['rsi'].idxmin(), 'Close']

    if current_price < price_at_rsi_low and current_rsi > recent['rsi'].min():
        df.loc[df.index[-1], 'rsi_divergence'] = 1  # Bullish divergence
    elif current_price > price_at_rsi_low and current_rsi < recent['rsi'].max():
        df.loc[df.index[-1], 'rsi_divergence'] = -1  # Bearish divergence

    return df

def find_support_resistance(df, window=20, num_levels=3):
    """Find S/R levels from recent pivots."""
    highs = df['High'].rolling(window=window, center=True).max()
    lows = df['Low'].rolling(window=window, center=True).min()

    # Get unique resistance levels (recent highs)
    resistance_levels = sorted(highs.dropna().unique(), reverse=True)[:num_levels]
    # Get unique support levels (recent lows)
    support_levels = sorted(lows.dropna().unique())[:num_levels]

    return {
        'resistance': [round(r, 2) for r in resistance_levels],
        'support': [round(s, 2) for s in support_levels]
    }

def detect_candle_patterns(df):
    """Detect key candlestick patterns."""
    df['candle_pattern'] = ''

    for i in range(1, len(df)):
        o, h, l, c = df.iloc[i][['Open', 'High', 'Low', 'Close']]
        prev_o, prev_h, prev_l, prev_c = df.iloc[i-1][['Open', 'High', 'Low', 'Close']]

        body = abs(c - o)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        total_range = h - l

        if total_range == 0:
            continue

        # Hammer (bullish reversal)
        if lower_wick > 2 * body and upper_wick < body and c > o:
            df.iloc[i, df.columns.get_loc('candle_pattern')] = 'HAMMER'

        # Shooting star (bearish reversal)
        elif upper_wick > 2 * body and lower_wick < body and c < o:
            df.iloc[i, df.columns.get_loc('candle_pattern')] = 'SHOOTING_STAR'

        # Bullish engulfing
        elif c > o and prev_c < prev_o and c > prev_o and o < prev_c:
            df.iloc[i, df.columns.get_loc('candle_pattern')] = 'BULL_ENGULFING'

        # Bearish engulfing
        elif c < o and prev_c > prev_o and c < prev_o and o > prev_c:
            df.iloc[i, df.columns.get_loc('candle_pattern')] = 'BEAR_ENGULFING'

        # Doji
        elif body < total_range * 0.1:
            df.iloc[i, df.columns.get_loc('candle_pattern')] = 'DOJI'

    return df

# ── SESSION & TIME FILTERS ──────────────────────────────────────
def is_valid_session(config):
    """Check if current time is in allowed session (London/NY)."""
    now_utc = datetime.now(UTC)
    current_time = now_utc.strftime("%H:%M")

    london_start = config['sessions']['london_open_utc']
    london_end = config['sessions']['london_close_utc']
    ny_start = config['sessions']['ny_open_utc']
    ny_end = config['sessions']['ny_close_utc']

    in_london = london_start <= current_time <= london_end
    in_ny = ny_start <= current_time <= ny_end

    if in_london:
        return True, "LONDON"
    elif in_ny:
        return True, "NEWYORK"
    else:
        return False, "ASIAN/BLOCKED"

def is_news_window(config):
    """Check if we're in a high-impact news window."""
    # TODO: integrate economic calendar API
    # For now, return False — manual calendar check
    return False, None

# ── SIGNAL GENERATION ───────────────────────────────────────────
def generate_signal(df, sr_levels, config):
    """Generate trading signal with confluence check."""
    if len(df) < 50:
        return None, "Insufficient data"

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = round(latest['Close'], 2)
    ema_fast = round(latest['ema_fast'], 2)
    ema_slow = round(latest['ema_slow'], 2)
    rsi = round(latest['rsi'], 1)
    pattern = latest['candle_pattern']
    rsi_div = latest['rsi_divergence']
    ema_cross = latest['ema_cross']
    ema_cross_sig = latest['ema_cross_signal']

    # Collect confluence signals
    signals = []
    reasons = []

    # 1. EMA crossover
    if ema_cross == 1:
        signals.append('EMA_BULLISH')
        reasons.append(f"EMA20 ({ema_fast}) > EMA50 ({ema_slow})")
    elif ema_cross == -1:
        signals.append('EMA_BEARISH')
        reasons.append(f"EMA20 ({ema_fast}) < EMA50 ({ema_slow})")

    # Fresh crossover is stronger
    if ema_cross_sig == 2:
        signals.append('EMA_CROSS_BULL')
        reasons.append("EMA bullish crossover just occurred")
    elif ema_cross_sig == -2:
        signals.append('EMA_CROSS_BEAR')
        reasons.append("EMA bearish crossover just occurred")

    # 2. S/R proximity
    for level in sr_levels['support']:
        if abs(price - level) / price < 0.002:  # Within 0.2%
            signals.append('NEAR_SUPPORT')
            reasons.append(f"Price near support {level}")
            break

    for level in sr_levels['resistance']:
        if abs(price - level) / price < 0.002:
            signals.append('NEAR_RESISTANCE')
            reasons.append(f"Price near resistance {level}")
            break

    # 3. Candlestick pattern
    if pattern in ['HAMMER', 'BULL_ENGULFING']:
        signals.append('CANDLE_BULLISH')
        reasons.append(f"Candle pattern: {pattern}")
    elif pattern in ['SHOOTING_STAR', 'BEAR_ENGULFING']:
        signals.append('CANDLE_BEARISH')
        reasons.append(f"Candle pattern: {pattern}")

    # 4. RSI divergence
    if rsi_div == 1:
        signals.append('RSI_BULL_DIV')
        reasons.append("RSI bullish divergence")
    elif rsi_div == -1:
        signals.append('RSI_BEAR_DIV')
        reasons.append("RSI bearish divergence")

    # RSI overbought/oversold
    if rsi > 70:
        signals.append('RSI_OVERBOUGHT')
        reasons.append(f"RSI {rsi} — overbought")
    elif rsi < 30:
        signals.append('RSI_OVERSOLD')
        reasons.append(f"RSI {rsi} — oversold")

    # ── CONFLUENCE CHECK (F3: ≥2 required) ──
    bull_signals = [s for s in signals if 'BULL' in s or 'SUPPORT' in s or 'OVERSOLD' in s]
    bear_signals = [s for s in signals if 'BEAR' in s or 'RESISTANCE' in s or 'OVERBOUGHT' in s]

    min_confluence = config['confluence_rules']['required']

    signal_type = None
    confidence = 0

    if len(bull_signals) >= min_confluence:
        signal_type = 'LONG'
        confidence = min(len(bull_signals) / 4, 0.9)  # Cap at 0.9 (F7)
    elif len(bear_signals) >= min_confluence:
        signal_type = 'SHORT'
        confidence = min(len(bear_signals) / 4, 0.9)

    # Calculate SL/TP
    atr = df['High'].tail(14).sub(df['Low'].tail(14)).mean()
    rr_min = config['risk']['min_rr_ratio']

    entry = price
    if signal_type == 'LONG':
        sl = round(entry - atr * 1.5, 2)
        tp = round(entry + (entry - sl) * rr_min, 2)
    elif signal_type == 'SHORT':
        sl = round(entry + atr * 1.5, 2)
        tp = round(entry - (sl - entry) * rr_min, 2)
    else:
        sl = None
        tp = None

    result = {
        'timestamp': datetime.now(MYT).isoformat(),
        'price': price,
        'signal': signal_type or 'NO_SIGNAL',
        'confidence': round(confidence, 2),
        'entry': entry,
        'sl': sl,
        'tp': tp,
        'rr_ratio': rr_min if signal_type else None,
        'ema_fast': ema_fast,
        'ema_slow': ema_slow,
        'ema_trend': 'BULLISH' if ema_cross == 1 else 'BEARISH' if ema_cross == -1 else 'NEUTRAL',
        'rsi': rsi,
        'rsi_divergence': 'BULLISH' if rsi_div == 1 else 'BEARISH' if rsi_div == -1 else 'NONE',
        'candle_pattern': pattern or 'NONE',
        'support_levels': sr_levels['support'],
        'resistance_levels': sr_levels['resistance'],
        'confluence_count': max(len(bull_signals), len(bear_signals)),
        'confluence_signals': bull_signals if signal_type == 'LONG' else bear_signals if signal_type == 'SHORT' else [],
        'reasons': reasons,
        'all_signals': signals
    }

    return result, None

# ── BRIEFING FORMAT ─────────────────────────────────────────────
def format_briefing(signal, macro, session_ok, session_name):
    """Format signal as daily briefing for Telegram."""
    now = datetime.now(MYT)
    lines = []

    lines.append(f"**GOLD SIGNAL — {now.strftime('%d %b %Y, %I:%M %p')} MYT**")
    lines.append("")

    # Session check
    if not session_ok:
        lines.append(f"SESSION: {session_name} — Outside trading hours")
        lines.append("Wait for London/NY session.")
        return "\n".join(lines)

    lines.append(f"SESSION: {session_name}")
    lines.append(f"PRICE: ${signal['price']}")
    lines.append("")

    # Signal
    if signal['signal'] == 'NO_SIGNAL':
        lines.append("SIGNAL: **NO TRADE**")
        lines.append(f"Confluence: {signal['confluence_count']}/4 (need ≥2)")
        lines.append("")
        lines.append("What I see:")
        for r in signal['reasons'][:3]:
            lines.append(f"  • {r}")
    else:
        emoji = "LONG" if signal['signal'] == 'LONG' else "SHORT"
        lines.append(f"SIGNAL: **{emoji}**")
        lines.append(f"Confidence: {signal['confidence']*100:.0f}%")
        lines.append(f"Confluence: {signal['confluence_count']}/4 — {', '.join(signal['confluence_signals'])}")
        lines.append("")
        lines.append(f"Entry: ${signal['entry']}")
        lines.append(f"Stop Loss: ${signal['sl']}")
        lines.append(f"Take Profit: ${signal['tp']}")
        lines.append(f"R:R = 1:{signal['rr_ratio']}")
        lines.append("")
        lines.append("Reasoning:")
        for r in signal['reasons']:
            lines.append(f"  • {r}")

    # Macro context
    if macro:
        lines.append("")
        lines.append("MACRO:")
        if macro.get('dxy'):
            dxy_dir = "+" if macro['dxy_change'] > 0 else ""
            lines.append(f"  DXY: {macro['dxy']} ({dxy_dir}{macro['dxy_change']}%)")
        if macro.get('us10y'):
            lines.append(f"  US 10Y: {macro['us10y']}%")

    # Levels
    lines.append("")
    lines.append(f"Support: {', '.join(['$'+str(s) for s in signal['support_levels']])}")
    lines.append(f"Resistance: {', '.join(['$'+str(r) for r in signal['resistance_levels']])}")

    # Disclaimer
    lines.append("")
    lines.append("---")
    lines.append("AI companion signal. Kau decide, kau execute.")

    return "\n".join(lines)

# ── JOURNAL ─────────────────────────────────────────────────────
def log_signal(signal):
    """Append signal to journal."""
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL_PATH, 'a') as f:
        f.write(json.dumps(signal) + "\n")

# ── MAIN ────────────────────────────────────────────────────────
def main():
    config = load_config()
    briefing_mode = '--briefing' in sys.argv

    # Step 1: Fetch gold data
    print("Fetching XAUUSD data...", file=sys.stderr)
    df = fetch_gold_data(period="60d", interval="1h")
    if df.empty:
        print("ERROR: Cannot fetch gold data", file=sys.stderr)
        sys.exit(1)

    # Step 2: Calculate indicators
    df = calc_ema(df, config['style']['ema_fast'], config['style']['ema_slow'])
    df = calc_rsi(df, config['style']['rsi_period'])
    df = calc_rsi_divergence(df)
    df = detect_candle_patterns(df)

    # Step 3: Find S/R levels
    sr_levels = find_support_resistance(df)

    # Step 4: Check session
    session_ok, session_name = is_valid_session(config)

    # Step 5: Check news window
    news_active, news_event = is_news_window(config)

    # Step 6: Generate signal
    signal, error = generate_signal(df, sr_levels, config)
    if error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

    # Step 7: Fetch macro
    macro = fetch_macro()

    # Step 8: Log
    log_signal(signal)

    # Step 9: Output
    if briefing_mode:
        print(format_briefing(signal, macro, session_ok, session_name))
    else:
        print(json.dumps(signal, indent=2))

if __name__ == '__main__':
    main()
