#!/usr/bin/env python3
"""
XAUUSD Professional Chart Generator — WEALTH Dashboard Grade
Matplotlib-powered, fast, high-res PNG for Telegram.

Usage:
  python3 chart_pro.py                          # Auto signal
  python3 chart_pro.py --signal SHORT --entry 4055 --sl 4076 --tp 4027
  python3 chart_pro.py --force                  # Force generate even without signal
"""

import json
import sys
import warnings
warnings.filterwarnings('ignore')

import os
os.environ['MPLCONFIGDIR'] = '/tmp/.mpl'

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
from datetime import datetime, timedelta, timezone
from pathlib import Path

MYT = timezone(timedelta(hours=8))

# ── COLORS ──────────────────────────────────────────────────────
BG = '#0d1117'
PANEL = '#161b22'
GOLD = '#f0a500'
GREEN = '#3fb950'
RED = '#f85149'
CYAN = '#58a6ff'
ORANGE = '#ffa657'
PURPLE = '#bc8cff'
TEXT = '#e6edf3'
DIM = '#8b949e'
BORDER = '#30363d'

plt.rcParams.update({
    'figure.facecolor': BG,
    'axes.facecolor': BG,
    'text.color': TEXT,
    'axes.labelcolor': DIM,
    'xtick.color': DIM,
    'ytick.color': DIM,
    'axes.edgecolor': BORDER,
    'grid.color': BORDER,
    'grid.alpha': 0.3,
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# ── DATA ────────────────────────────────────────────────────────
def fetch_data(period="30d", interval="1h"):
    ticker = yf.Ticker("GC=F")
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        ticker = yf.Ticker("XAUUSD=X")
        df = ticker.history(period=period, interval=interval)
    return df

def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def find_sr_levels(df, n=3):
    price = df['Close'].iloc[-1]
    w = 20
    highs = df['High'].rolling(w, center=True).max().dropna().unique()
    lows = df['Low'].rolling(w, center=True).min().dropna().unique()
    resistance = sorted([r for r in highs if r > price * 0.999])[:n]
    support = sorted([s for s in lows if s < price * 1.001], reverse=True)[:n]
    if len(resistance) < 2:
        h, l = df['High'].tail(14).max(), df['Low'].tail(14).min()
        p = (h + l + price) / 3
        resistance = [p + (h - l), 2*p - l][:n]
    if len(support) < 2:
        h, l = df['High'].tail(14).max(), df['Low'].tail(14).min()
        p = (h + l + price) / 3
        support = [2*p - h, p - (h - l)][:n]
    return {
        'support': sorted([round(s, 2) for s in support], reverse=True)[:n],
        'resistance': sorted([round(r, 2) for r in resistance])[:n]
    }

def get_bias(df):
    e20, e50, e200 = df['ema20'].iloc[-1], df['ema50'].iloc[-1], df['ema200'].iloc[-1]
    rsi, price = df['rsi'].iloc[-1], df['Close'].iloc[-1]
    bull = sum([e20 > e50, e50 > e200, price > e20, rsi > 50])
    if bull >= 3: return 'BULLISH', GREEN, bull
    elif bull <= 1: return 'BEARISH', RED, 4 - bull
    return 'NEUTRAL', DIM, 2

# ── CHART ───────────────────────────────────────────────────────
def generate(df, signal=None, entry=None, sl=None, tp=None, out='/tmp/xauusd_chart.png'):
    recent = df.tail(72).copy().reset_index()
    time_col = 'Date' if 'Date' in recent.columns else 'Datetime' if 'Datetime' in recent.columns else recent.columns[0]

    price = df['Close'].iloc[-1]
    e20, e50, e200 = df['ema20'].iloc[-1], df['ema50'].iloc[-1], df['ema200'].iloc[-1]
    rsi = df['rsi'].iloc[-1]
    levels = find_sr_levels(df)
    bias, bias_col, conf = get_bias(df)
    now = datetime.now(MYT)

    # ── FIGURE ──
    fig = plt.figure(figsize=(14, 8.5))
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.05,
                          left=0.06, right=0.88, top=0.90, bottom=0.08)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)

    # ── CANDLESTICKS ──
    x = np.arange(len(recent))
    for i, row in recent.iterrows():
        o, h, l, c = row['Open'], row['High'], row['Low'], row['Close']
        color = GREEN if c >= o else RED
        # Body
        body_bot = min(o, c)
        body_h = max(abs(c - o), 0.3)
        edge = color if c < o else 'none'
        rect = Rectangle((i - 0.35, body_bot), 0.7, body_h,
                         facecolor=color if c < o else 'none',
                         edgecolor=color, linewidth=0.8)
        ax1.add_patch(rect)
        # Wicks
        ax1.plot([i, i], [l, body_bot], color=color, linewidth=0.6)
        ax1.plot([i, i], [body_bot + body_h, h], color=color, linewidth=0.6)

    # ── EMA LINES ──
    ax1.plot(x, recent['ema20'].values, color=CYAN, linewidth=1.3, label=f'EMA20 ${e20:.0f}', alpha=0.9)
    ax1.plot(x, recent['ema50'].values, color=ORANGE, linewidth=1.3, label=f'EMA50 ${e50:.0f}', alpha=0.9)
    ax1.plot(x, recent['ema200'].values, color=PURPLE, linewidth=1.5, linestyle=':', label=f'EMA200 ${e200:.0f}', alpha=0.8)

    # ── S/R LEVELS (max 3-4, clean) ──
    for s in levels['support'][:2]:
        ax1.axhline(y=s, color=GREEN, linestyle='--', linewidth=0.8, alpha=0.6)
        ax1.text(len(recent)-0.5, s, f'  S ${s}', color=GREEN, fontsize=10,
                va='bottom', fontweight='bold')
    for r in levels['resistance'][:2]:
        ax1.axhline(y=r, color=RED, linestyle='--', linewidth=0.8, alpha=0.6)
        ax1.text(len(recent)-0.5, r, f'  R ${r}', color=RED, fontsize=10,
                va='top', fontweight='bold')

    # ── SIGNAL OVERLAY ──
    if entry and sl and tp:
        # Zones
        if signal == 'SHORT':
            ax1.fill_between(x, tp, sl, alpha=0.06, color=GREEN, label='Profit Zone')
            ax1.fill_between(x, entry, sl, alpha=0.06, color=RED, label='Risk Zone')
        elif signal == 'LONG':
            ax1.fill_between(x, sl, tp, alpha=0.06, color=GREEN)
            ax1.fill_between(x, sl, entry, alpha=0.06, color=RED)

        # Entry
        ax1.axhline(y=entry, color=GOLD, linewidth=2.5, alpha=0.9)
        ax1.text(0, entry, f'  ENTRY ${entry}  ', color=BG, fontsize=11,
                fontweight='bold', va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=GOLD, edgecolor=GOLD, alpha=0.95))

        # SL
        ax1.axhline(y=sl, color=RED, linewidth=1.5, linestyle='--', alpha=0.7)
        ax1.text(0, sl, f'  SL ${sl}  ', color='#fff', fontsize=10,
                fontweight='bold', va='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=RED, edgecolor=RED, alpha=0.9))

        # TP
        ax1.axhline(y=tp, color=GREEN, linewidth=1.5, linestyle='--', alpha=0.7)
        ax1.text(0, tp, f'  TP ${tp}  ', color=BG, fontsize=10,
                fontweight='bold', va='center',
                bbox=dict(boxstyle='round,pad=0.2', facecolor=GREEN, edgecolor=GREEN, alpha=0.9))

    # ── CURRENT PRICE LINE ──
    ax1.axhline(y=price, color=GOLD, linewidth=1.5, alpha=0.7)
    ax1.text(len(recent)-0.5, price, f'  ${price:.2f}', color=BG, fontsize=13,
            fontweight='bold', va='center',
            bbox=dict(boxstyle='round,pad=0.4', facecolor=GOLD, edgecolor=GOLD, alpha=0.95))

    # ── FORMATTING ──
    ax1.set_title('')
    ax1.legend(loc='upper left', fontsize=9, facecolor=PANEL, edgecolor=BORDER,
              labelcolor=TEXT, framealpha=0.9)
    ax1.grid(True, alpha=0.15)
    ax1.tick_params(labelsize=8)

    # X-axis labels
    tick_pos = list(range(0, len(recent), max(1, len(recent)//8)))
    tick_labels = []
    for p in tick_pos:
        if p < len(recent):
            ts = recent.iloc[p][time_col]
            tick_labels.append(ts.strftime('%d %H:%M') if hasattr(ts, 'strftime') else str(p))
        else:
            tick_labels.append('')
    ax1.set_xticks(tick_pos)
    ax1.set_xticklabels([])  # Hide x labels on top chart

    # ── RSI PANEL ──
    rsi_vals = recent['rsi'].values
    ax2.plot(x, rsi_vals, color=GOLD, linewidth=1.5)
    ax2.fill_between(x, 30, rsi_vals, where=(rsi_vals > 70), alpha=0.1, color=RED)
    ax2.fill_between(x, rsi_vals, 70, where=(rsi_vals < 30), alpha=0.1, color=GREEN)
    ax2.axhline(y=70, color=RED, linestyle='--', linewidth=0.5, alpha=0.5)
    ax2.axhline(y=30, color=GREEN, linestyle='--', linewidth=0.5, alpha=0.5)
    ax2.axhline(y=50, color=DIM, linestyle=':', linewidth=0.3, alpha=0.3)
    ax2.set_ylim(20, 80)
    ax2.set_ylabel('RSI(14)', fontsize=9, color=DIM)
    ax2.grid(True, alpha=0.15)
    ax2.set_xticks(tick_pos)
    ax2.set_xticklabels(tick_labels, fontsize=8, color=DIM)

    # RSI label
    rsi_color = RED if rsi > 70 else GREEN if rsi < 30 else GOLD
    ax2.text(len(recent)-0.5, rsi, f' {rsi:.1f}', color=BG, fontsize=11,
            fontweight='bold', va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=rsi_color, edgecolor=rsi_color))

    # ── HEADER ──
    # Title
    fig.text(0.06, 0.95, 'XAUUSD H1', color=GOLD, fontsize=22, fontweight='bold')
    fig.text(0.22, 0.95, ' — ABANG SADO ALERT', color=DIM, fontsize=14)

    # Bias pill
    fig.text(0.45, 0.95, f' {bias} ', color=BG, fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=bias_col, edgecolor=bias_col))

    # Price
    fig.text(0.57, 0.95, f'${price:.2f}', color=GOLD, fontsize=20, fontweight='bold')

    # Confidence
    conf_pct = conf * 25
    fig.text(0.73, 0.95, f'{conf_pct:.0f}% conf', color=DIM, fontsize=12)

    # EMA legend
    fig.text(0.84, 0.95, f'EMA20 ${e20:.0f}', color=CYAN, fontsize=9)
    fig.text(0.84, 0.93, f'EMA50 ${e50:.0f}', color=ORANGE, fontsize=9)
    fig.text(0.84, 0.91, f'EMA200 ${e200:.0f}', color=PURPLE, fontsize=9)

    # ── BOTTOM BANNER ──
    verdict_parts = []
    if bias == 'BULLISH':
        verdict_parts.append('Trend bullish — EMA alignment up')
    elif bias == 'BEARISH':
        verdict_parts.append('Trend bearish — price below EMAs')
    else:
        verdict_parts.append('Consolidation — no clear direction')

    if rsi > 70: verdict_parts.append(f'RSI overbought ({rsi:.0f})')
    elif rsi < 30: verdict_parts.append(f'RSI oversold ({rsi:.0f})')

    if signal and entry:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr = reward / risk if risk > 0 else 0
        verdict_parts.append(f'{signal} @ ${entry} | SL ${sl} | TP ${tp} | R:R 1:{rr:.1f}')

    verdict = '  |  '.join(verdict_parts)
    fig.text(0.06, 0.025, verdict, color=TEXT, fontsize=10)
    fig.text(0.94, 0.025, 'Kau decide, kau execute. F13 Active', color=GOLD,
            fontsize=10, fontweight='bold', ha='right')
    fig.text(0.5, 0.005, f'{now.strftime("%d %b %Y, %I:%M %p")} MYT  |  WEALTH SOT  |  arifOS',
            color=DIM, fontsize=8, ha='center')

    # ── SAVE ──
    fig.savefig(out, dpi=180, facecolor=BG, bbox_inches='tight', pad_inches=0.3)
    plt.close()

    meta = {
        'path': out, 'price': round(price, 2), 'bias': bias,
        'confidence': conf_pct, 'rsi': round(rsi, 1),
        'ema20': round(e20, 2), 'ema50': round(e50, 2), 'ema200': round(e200, 2),
        'support': levels['support'], 'resistance': levels['resistance'],
        'signal': signal, 'entry': entry, 'sl': sl, 'tp': tp
    }
    return meta

# ── MAIN ────────────────────────────────────────────────────────
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--signal', choices=['LONG', 'SHORT'])
    parser.add_argument('--entry', type=float)
    parser.add_argument('--sl', type=float)
    parser.add_argument('--tp', type=float)
    parser.add_argument('--output', default='/tmp/xauusd_chart.png')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    df = fetch_data()
    if df.empty:
        print("ERROR: No data", file=sys.stderr); sys.exit(1)

    df['ema20'] = calc_ema(df['Close'], 20)
    df['ema50'] = calc_ema(df['Close'], 50)
    df['ema200'] = calc_ema(df['Close'], 200)
    df['rsi'] = calc_rsi(df['Close'])

    # Auto-detect signal if not provided
    if not args.signal:
        bias, _, _ = get_bias(df)
        rsi_val = df['rsi'].iloc[-1]
        if bias == 'BEARISH' and rsi_val > 60:
            args.signal = 'SHORT'
        elif bias == 'BULLISH' and rsi_val < 40:
            args.signal = 'LONG'

    meta = generate(df, signal=args.signal, entry=args.entry,
                   sl=args.sl, tp=args.tp, out=args.output)

    if args.json:
        import numpy as _np
        class _NpEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (_np.integer,)): return int(obj)
                if isinstance(obj, (_np.floating,)): return float(obj)
                if isinstance(obj, _np.ndarray): return obj.tolist()
                return super().default(obj)
        print(json.dumps(meta, indent=2, cls=_NpEncoder))
    else:
        print(f"OK: {args.output} | ${meta['price']} | {meta['bias']} | RSI {meta['rsi']}")
