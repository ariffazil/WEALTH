#!/usr/bin/env python3
"""
XAUUSD Price Alert with Chart Screenshot
Checks if price is near S/R levels, generates chart, outputs for Telegram delivery.

Usage:
  python3 sado_alert.py --check     # Check and alert if triggered
  python3 sado_alert.py --force     # Force alert regardless
"""

import json
import sys
import os
import warnings
warnings.filterwarnings('ignore')

os.environ['MPLCONFIGDIR'] = '/tmp/.mpl'

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')


import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from datetime import datetime, timedelta, timezone
from pathlib import Path

MYT = timezone(timedelta(hours=8))
CONFIG_PATH = Path(__file__).parent.parent / "config" / "trading_spec.json"
OUTPUT_DIR = Path("/tmp")

# ── COLORS ──────────────────────────────────────────────────────
BG = '#0d1117'
PANEL = '#161b22'
GOLD = '#f0a500'
GREEN = '#3fb950'
RED = '#f85149'
CYAN = '#58a6ff'
ORANGE = '#ffa657'
TEXT = '#e6edf3'
DIM = '#8b949e'
BORDER = '#30363d'

# ── DATA FETCH ──────────────────────────────────────────────────
def fetch_data():
    """Fetch XAUUSD H1 data."""
    ticker = yf.Ticker("GC=F")
    df = ticker.history(period="30d", interval="1h")
    if df.empty:
        ticker = yf.Ticker("XAUUSD=X")
        df = ticker.history(period="30d", interval="1h")
    return df

def calc_indicators(df):
    """Calculate EMA, RSI, S/R."""
    df['ema20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # S/R levels (pivot method)
    high = df['High'].tail(14).max()
    low = df['Low'].tail(14).min()
    close = df['Close'].iloc[-1]
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    r2 = pivot + (high - low)
    s1 = 2 * pivot - high
    s2 = pivot - (high - low)

    # Additional S/R from recent pivots
    highs = df['High'].rolling(10, center=True).max().dropna().unique()
    lows = df['Low'].rolling(10, center=True).min().dropna().unique()

    resistance = sorted([r for r in highs if r > close], reverse=False)[:3]
    support = sorted([s for s in lows if s < close], reverse=True)[:3]

    # If not enough levels from pivots, use calculated
    if len(resistance) < 2:
        resistance = sorted([r1, r2])[:2]
    if len(support) < 2:
        support = sorted([s1, s2], reverse=True)[:2]

    return df, {
        'support': [round(s, 2) for s in support],
        'resistance': [round(r, 2) for r in resistance],
        'pivot': round(pivot, 2)
    }

def check_alert(df, levels, threshold_pct=0.3):
    """Check if price is near any S/R level."""
    price = df['Close'].iloc[-1]
    alerts = []

    for s in levels['support']:
        dist_pct = abs(price - s) / price * 100
        if dist_pct < threshold_pct:
            alerts.append(f"Near SUPPORT ${s} ({dist_pct:.2f}% away)")

    for r in levels['resistance']:
        dist_pct = abs(price - r) / price * 100
        if dist_pct < threshold_pct:
            alerts.append(f"Near RESISTANCE ${r} ({dist_pct:.2f}% away)")

    # RSI extreme
    rsi = df['rsi'].iloc[-1]
    if rsi > 70:
        alerts.append(f"RSI OVERBOUGHT at {rsi:.1f}")
    elif rsi < 30:
        alerts.append(f"RSI OVERSOLD at {rsi:.1f}")

    # EMA cross
    ema20 = df['ema20'].iloc[-1]
    ema50 = df['ema50'].iloc[-1]
    prev_ema20 = df['ema20'].iloc[-2]
    prev_ema50 = df['ema50'].iloc[-2]

    if prev_ema20 < prev_ema50 and ema20 > ema50:
        alerts.append("EMA BULLISH CROSSOVER just happened!")
    elif prev_ema20 > prev_ema50 and ema20 < ema50:
        alerts.append("EMA BEARISH CROSSOVER just happened!")

    return alerts

def generate_chart(df, levels, alerts):
    """Generate dark-theme chart image for Telegram."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8),
                                     gridspec_kw={'height_ratios': [3, 1]},
                                     facecolor=BG)

    # Last 48 hours
    recent = df.tail(48).copy()
    recent = recent.reset_index()

    # Main chart
    ax1.set_facecolor(BG)
    for i, row in recent.iterrows():
        color = GREEN if row['Close'] >= row['Open'] else RED
        # Body
        body_bottom = min(row['Open'], row['Close'])
        body_height = abs(row['Close'] - row['Open'])
        if body_height < 0.1:
            body_height = 0.1
        rect = Rectangle((i - 0.3, body_bottom), 0.6, body_height,
                         facecolor=color if row['Close'] < row['Open'] else 'none',
                         edgecolor=color, linewidth=1)
        ax1.add_patch(rect)
        # Wicks
        ax1.plot([i, i], [row['Low'], body_bottom], color=color, linewidth=0.8)
        ax1.plot([i, i], [body_bottom + body_height, row['High']], color=color, linewidth=0.8)

    # EMA lines
    ema20_vals = recent['ema20'].values
    ema50_vals = recent['ema50'].values
    ax1.plot(range(len(recent)), ema20_vals, color=CYAN, linewidth=1.2, label='EMA20', alpha=0.9)
    ax1.plot(range(len(recent)), ema50_vals, color=ORANGE, linewidth=1.2, label='EMA50', alpha=0.9)

    # S/R lines
    price = df['Close'].iloc[-1]
    for s in levels['support']:
        ax1.axhline(y=s, color=GREEN, linestyle='--', linewidth=0.8, alpha=0.7)
        ax1.text(len(recent)-1, s, f'  S USD{s}', color=GREEN, fontsize=9,
                va='bottom', fontweight='bold')
    for r in levels['resistance']:
        ax1.axhline(y=r, color=RED, linestyle='--', linewidth=0.8, alpha=0.7)
        ax1.text(len(recent)-1, r, f'  R USD{r}', color=RED, fontsize=9,
                va='top', fontweight='bold')

    # Current price line
    ax1.axhline(y=price, color=GOLD, linewidth=1.5, alpha=0.8)
    ax1.text(len(recent)-1, price, f'  USD{price:.2f}', color=GOLD, fontsize=12,
            va='center', fontweight='bold', bbox=dict(boxstyle='round,pad=0.3',
            facecolor=BG, edgecolor=GOLD, alpha=0.9))

    # Formatting
    ax1.set_title(f'XAUUSD H1 — ABANG SADO ALERT', color=GOLD, fontsize=16,
                  fontweight='bold', pad=15)
    ax1.legend(loc='upper left', fontsize=9, facecolor=PANEL, edgecolor=BORDER,
              labelcolor=TEXT)
    ax1.tick_params(colors=DIM, labelsize=8)
    ax1.grid(True, alpha=0.1, color=BORDER)
    ax1.set_ylabel('Price (USD)', color=DIM, fontsize=10)

    # X-axis labels (time)
    tick_positions = list(range(0, len(recent), max(1, len(recent)//8)))
    tick_labels = []
    for pos in tick_positions:
        if pos < len(recent):
            ts = recent.iloc[pos].get('Date', recent.iloc[pos].get('Datetime', ''))
            if hasattr(ts, 'strftime'):
                tick_labels.append(ts.strftime('%d %H:%M'))
            else:
                tick_labels.append(str(pos))
        else:
            tick_labels.append('')
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, color=DIM, fontsize=8)

    # RSI panel
    ax2.set_facecolor(BG)
    rsi_vals = recent['rsi'].values
    ax2.plot(range(len(recent)), rsi_vals, color=GOLD, linewidth=1.5)
    ax2.axhline(y=70, color=RED, linestyle='--', linewidth=0.5, alpha=0.5)
    ax2.axhline(y=30, color=GREEN, linestyle='--', linewidth=0.5, alpha=0.5)
    ax2.axhline(y=50, color=DIM, linestyle='--', linewidth=0.3, alpha=0.3)
    ax2.fill_between(range(len(recent)), 70, 100, alpha=0.05, color=RED)
    ax2.fill_between(range(len(recent)), 0, 30, alpha=0.05, color=GREEN)
    ax2.set_ylim(20, 80)
    ax2.set_ylabel('RSI(14)', color=DIM, fontsize=10)
    ax2.tick_params(colors=DIM, labelsize=8)
    ax2.grid(True, alpha=0.1, color=BORDER)
    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels(tick_labels, color=DIM, fontsize=8)

    # Current RSI label
    current_rsi = rsi_vals[-1]
    ax2.text(len(recent)-1, current_rsi, f' {current_rsi:.1f}', color=GOLD,
            fontsize=11, fontweight='bold', va='center')

    # Alert text at bottom
    alert_text = " | ".join(alerts) if alerts else "No alerts"
    alert_text = alert_text.replace("$", "USD")
    fig.text(0.5, 0.01, alert_text, ha='center', fontsize=11, color=GOLD,
            fontweight='bold', style='italic',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=PANEL, edgecolor=GOLD, alpha=0.9))

    # Timestamp
    now = datetime.now(MYT)
    fig.text(0.98, 0.01, f'{now.strftime("%d %b %Y %I:%M %p")} MYT', ha='right',
            fontsize=8, color=DIM)

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    output_path = OUTPUT_DIR / 'sado_alert_chart.png'
    fig.savefig(output_path, dpi=150, facecolor=BG, bbox_inches='tight', pad_inches=0.3)
    plt.close()

    return str(output_path)

def format_alert_message(price, levels, alerts, rsi, ema20, ema50):
    """Format Telegram alert message."""
    now = datetime.now(MYT)
    lines = []

    lines.append("**XAUUSD ALERT**")
    lines.append(f"{now.strftime('%d %b %Y, %I:%M %p')} MYT")
    lines.append("")
    lines.append(f"Price: **${price:.2f}**")
    lines.append(f"RSI: {rsi:.1f}")
    lines.append(f"EMA20: ${ema20:.2f} | EMA50: ${ema50:.2f}")
    ema_status = "BULLISH" if ema20 > ema50 else "BEARISH"
    lines.append(f"Trend: **{ema_status}**")
    lines.append("")

    for a in alerts:
        lines.append(f"**[!] {a}**")

    lines.append("")
    lines.append(f"Support: {', '.join(['$'+str(s) for s in levels['support']])}")
    lines.append(f"Resistance: {', '.join(['$'+str(r) for r in levels['resistance']])}")
    lines.append("")
    lines.append("Chart attached. Kau decide, kau execute. 🫡")

    return "\n".join(lines)

# ── MAIN ────────────────────────────────────────────────────────
def main():
    force = '--force' in sys.argv

    # Fetch data
    df = fetch_data()
    if df.empty:
        print("ERROR: Cannot fetch data", file=sys.stderr)
        sys.exit(1)

    # Calculate indicators
    df, levels = calc_indicators(df)

    # Check alerts
    alerts = check_alert(df, levels)

    if not alerts and not force:
        # No alert triggered, output nothing (silent)
        sys.exit(0)

    # Generate chart
    price = df['Close'].iloc[-1]
    rsi = df['rsi'].iloc[-1]
    ema20 = df['ema20'].iloc[-1]
    ema50 = df['ema50'].iloc[-1]

    chart_path = generate_chart(df, levels, alerts)
    message = format_alert_message(price, levels, alerts, rsi, ema20, ema50)

    # Output for cron delivery
    output = {
        "alert": True,
        "message": message,
        "chart_path": chart_path,
        "price": round(price, 2),
        "rsi": round(rsi, 1),
        "alerts": alerts
    }

    print(json.dumps(output))

if __name__ == '__main__':
    main()
