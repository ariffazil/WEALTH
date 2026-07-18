#!/usr/bin/env python3
"""
XAUUSD PRICE ALERT — Abang Sado Udin
Monitors gold price for notable events and generates
Telegram-ready alerts when conditions are met.

Checks:
  1. Price near key S/R levels (within 0.3%)
  2. EMA20/EMA50 crossover (just happened)
  3. RSI crossed 30 or 70 (extreme zones)
  4. Candlestick pattern just formed

Outputs Telegram-ready text if alertable, empty if nothing notable.
Designed for cron job every 30 min during London/NY sessions.

Usage:
  python3 price_alert.py --check
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

MYT = timezone(timedelta(hours=8))
UTC = timezone.utc

ALERT_THRESHOLD_SR = 0.003  # 0.3% proximity to S/R
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


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


def fetch_gold_data(period="60d", interval="1h"):
    """Fetch XAUUSD from Yahoo Finance (same as gold_engine.py)."""
    ticker = yf.Ticker("GC=F")
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        ticker = yf.Ticker("XAUUSD=X")
        df = ticker.history(period=period, interval=interval)
    return df


def calc_ema(df, fast=20, slow=50):
    """Calculate EMA crossover signals."""
    df['ema_fast'] = df['Close'].ewm(span=fast, adjust=False).mean()
    df['ema_slow'] = df['Close'].ewm(span=slow, adjust=False).mean()
    df['ema_cross'] = 0
    df.loc[df['ema_fast'] > df['ema_slow'], 'ema_cross'] = 1
    df.loc[df['ema_fast'] < df['ema_slow'], 'ema_cross'] = -1
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


def find_support_resistance(df, window=20, num_levels=3):
    """Find S/R levels from recent pivots."""
    highs = df['High'].rolling(window=window, center=True).max()
    lows = df['Low'].rolling(window=window, center=True).min()

    resistance_levels = sorted(highs.dropna().unique(), reverse=True)[:num_levels]
    support_levels = sorted(lows.dropna().unique())[:num_levels]

    return {
        'resistance': [round(r, 2) for r in resistance_levels],
        'support': [round(s, 2) for s in support_levels]
    }


def detect_candle_patterns(df):
    """Detect key candlestick patterns (last 2 candles only)."""
    df['candle_pattern'] = ''
    for i in range(max(1, len(df) - 2), len(df)):
        o, h, l, c = df.iloc[i][['Open', 'High', 'Low', 'Close']]
        prev_o, prev_h, prev_l, prev_c = df.iloc[i-1][['Open', 'High', 'Low', 'Close']]

        body = abs(c - o)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        total_range = h - l

        if total_range == 0:
            continue

        if lower_wick > 2 * body and upper_wick < body and c > o:
            df.iloc[i, df.columns.get_loc('candle_pattern')] = 'HAMMER'
        elif upper_wick > 2 * body and lower_wick < body and c < o:
            df.iloc[i, df.columns.get_loc('candle_pattern')] = 'SHOOTING_STAR'
        elif c > o and prev_c < prev_o and c > prev_o and o < prev_c:
            df.iloc[i, df.columns.get_loc('candle_pattern')] = 'BULL_ENGULFING'
        elif c < o and prev_c > prev_o and c < prev_o and o > prev_c:
            df.iloc[i, df.columns.get_loc('candle_pattern')] = 'BEAR_ENGULFING'
        elif body < total_range * 0.1:
            df.iloc[i, df.columns.get_loc('candle_pattern')] = 'DOJI'

    return df


def check_alerts(df, sr_levels, config):
    """Run all alert checks. Returns list of alert strings."""
    if len(df) < 50:
        return []

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    price = round(latest['Close'], 2)
    rsi = round(latest['rsi'], 1)
    rsi_prev = round(prev['rsi'], 1) if not pd.isna(prev['rsi']) else rsi
    ema_fast = round(latest['ema_fast'], 2)
    ema_slow = round(latest['ema_slow'], 2)
    ema_cross_sig = latest['ema_cross_signal']
    pattern = latest['candle_pattern']

    alerts = []

    # 1. S/R proximity (within 0.3%)
    for level in sr_levels['resistance']:
        dist_pct = abs(price - level) / price
        if dist_pct < ALERT_THRESHOLD_SR:
            alerts.append(f"[!] Near resistance ${level:,.2f} ({dist_pct*100:.1f}% away)")
            break

    for level in sr_levels['support']:
        dist_pct = abs(price - level) / price
        if dist_pct < ALERT_THRESHOLD_SR:
            alerts.append(f"[!] Near support ${level:,.2f} ({dist_pct*100:.1f}% away)")
            break

    # 2. EMA crossover (just happened: diff == 2 means bullish cross, -2 bearish)
    if ema_cross_sig == 2:
        alerts.append(f"[!] EMA bullish crossover — EMA20 ({ema_fast}) crossed above EMA50 ({ema_slow})")
    elif ema_cross_sig == -2:
        alerts.append(f"[!] EMA bearish crossover — EMA20 ({ema_fast}) crossed below EMA50 ({ema_slow})")

    # 3. RSI crossing 30 or 70
    if rsi_prev < RSI_OVERBOUGHT and rsi >= RSI_OVERBOUGHT:
        alerts.append(f"[!] RSI crossed into overbought — now {rsi}")
    elif rsi_prev > RSI_OVERSOLD and rsi <= RSI_OVERSOLD:
        alerts.append(f"[!] RSI crossed into oversold — now {rsi}")
    elif rsi > RSI_OVERBOUGHT:
        alerts.append(f"[!] RSI overbought at {rsi}")
    elif rsi < RSI_OVERSOLD:
        alerts.append(f"[!] RSI oversold at {rsi}")

    # 4. Candlestick pattern just formed
    if pattern in ('HAMMER', 'BULL_ENGULFING'):
        alerts.append(f"[!] Bullish candle pattern: {pattern}")
    elif pattern in ('SHOOTING_STAR', 'BEAR_ENGULFING'):
        alerts.append(f"[!] Bearish candle pattern: {pattern}")
    elif pattern == 'DOJI':
        alerts.append(f"[!] Doji formed — indecision, watch next candle")

    return alerts


def format_alert(price, session_name, alerts):
    """Format Telegram-ready alert message."""
    now = datetime.now(MYT)
    lines = [
        f"**XAUUSD ALERT** — {now.strftime('%d %b %Y, %I:%M %p')} MYT",
        f"Session: {session_name}",
        f"Price: ${price:,.2f}",
        "",
    ]
    for a in alerts:
        lines.append(a)
    lines.append("")
    lines.append("---")
    lines.append("AI companion alert. Kau decide, kau execute.")
    return "\n".join(lines)


def main():
    if '--check' not in sys.argv:
        print("Usage: python3 price_alert.py --check", file=sys.stderr)
        sys.exit(1)

    config = load_config()

    # Session check — skip silently outside trading hours
    session_ok, session_name = is_valid_session(config)
    if not session_ok:
        # Empty output — cron won't deliver anything
        sys.exit(0)

    # Fetch data
    df = fetch_gold_data(period="60d", interval="1h")
    if df.empty:
        print("ERROR: Cannot fetch XAUUSD data", file=sys.stderr)
        sys.exit(1)

    # Calculate indicators
    df = calc_ema(df, config['style']['ema_fast'], config['style']['ema_slow'])
    df = calc_rsi(df, config['style']['rsi_period'])
    df = detect_candle_patterns(df)
    sr_levels = find_support_resistance(df)

    # Run alert checks
    alerts = check_alerts(df, sr_levels, config)

    # Output: empty if nothing notable (cron won't deliver)
    if not alerts:
        sys.exit(0)

    price = round(df.iloc[-1]['Close'], 2)
    print(format_alert(price, session_name, alerts))


if __name__ == '__main__':
    main()
