#!/usr/bin/env python3
"""
XAUUSD H1 Signal Chart PDF — Mode D (Dark/OANDA-style)
For Abang Sado Udin's daily trading signals.

Dark background, gold accents, candlesticks with EMA overlays,
S/R levels, RSI panel, pattern markers, entry/SL/TP zones.

Usage:
  python3 xauusd_chart_pdf.py
  python3 xauusd_chart_pdf.py --output /path/to/chart.pdf
"""

import warnings
warnings.filterwarnings('ignore')

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import argparse

# ── COLORS ──────────────────────────────────────────────────────
BG = '#0d1117'
PANEL = '#161b22'
GRID = '#21262d'
TXT = '#c9d1d9'
GOLD = '#f0a500'
GOLD_DIM = '#b07800'
GREEN = '#3fb950'
RED = '#f85149'
BLUE = '#58a6ff'
ORANGE = '#d29922'
PURPLE = '#bc8cff'
BULL = '#2ea043'
BULL_W = '#238636'
BEAR = '#b62324'
BEAR_W = '#da3633'

MYT = timezone(timedelta(hours=8))


def fetch_gold_data(period="60d", interval="1h"):
    """Fetch XAUUSD from Yahoo Finance (GC=F)."""
    ticker = yf.Ticker("GC=F")
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        ticker = yf.Ticker("XAUUSD=X")
        df = ticker.history(period=period, interval=interval)
    return df


def calc_indicators(df):
    """Calculate EMA 20/50, RSI 14, candlestick patterns."""
    df['ema20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['Close'].ewm(span=50, adjust=False).mean()

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / loss))

    df['pattern'] = ''
    for i in range(1, len(df)):
        o, h, l, c = df.iloc[i][['Open', 'High', 'Low', 'Close']]
        po, ph, pl, pc = df.iloc[i-1][['Open', 'High', 'Low', 'Close']]
        body = abs(c - o)
        total = h - l
        if total == 0:
            continue
        uw = h - max(o, c)
        lw = min(o, c) - l
        if lw > 2*body and uw < body and c > o:
            df.iloc[i, df.columns.get_loc('pattern')] = 'H'
        elif uw > 2*body and lw < body and c < o:
            df.iloc[i, df.columns.get_loc('pattern')] = 'SS'
        elif c < o and pc > po and c < po and o > pc:
            df.iloc[i, df.columns.get_loc('pattern')] = 'BE'
        elif c > o and pc < po and c > po and o < pc:
            df.iloc[i, df.columns.get_loc('pattern')] = 'BEn'
    return df


def find_sr_levels(df_48, df_full):
    """Find S/R levels using pivot detection within visible range."""
    lo, hi = df_48['Low'].min(), df_48['High'].max()
    p_range = hi - lo

    # Pivot-based S/R on 48h data
    window = 12
    candidates = []
    for i in range(window, len(df_48)-window):
        if df_48['High'].iloc[i] == df_48['High'].iloc[i-window:i+window+1].max():
            candidates.append(('R', df_48['High'].iloc[i]))
        if df_48['Low'].iloc[i] == df_48['Low'].iloc[i-window:i+window+1].min():
            candidates.append(('S', df_48['Low'].iloc[i]))

    def cluster(levels, threshold=5.0):
        if not levels:
            return []
        levels = sorted(levels)
        clusters = [[levels[0]]]
        for v in levels[1:]:
            if v - clusters[-1][-1] < threshold:
                clusters[-1].append(v)
            else:
                clusters.append([v])
        return [round(np.mean(c), 2) for c in clusters]

    res = cluster([v for t, v in candidates if t == 'R'])
    sup = cluster([v for t, v in candidates if t == 'S'])

    # Fallback to full-data rolling pivots if insufficient
    if len(res) < 2:
        hf = df_full['High'].rolling(20, center=True).max().dropna().unique()
        res = sorted([round(v, 2) for v in hf if lo <= v <= hi+p_range], reverse=True)[:3]
    if len(sup) < 2:
        lf = df_full['Low'].rolling(20, center=True).min().dropna().unique()
        sup = sorted([round(v, 2) for v in lf if lo-p_range <= v <= hi])[:3]

    return res, sup


def detect_signal(df_48, res, sup):
    """Detect trading signal from EMA crossover + RSI + proximity to S/R."""
    price_now = df_48['Close'].iloc[-1]
    rsi_now = df_48['rsi'].iloc[-1]
    p_range = df_48['High'].max() - df_48['Low'].min()
    ema_bull = df_48['ema20'].iloc[-1] > df_48['ema50'].iloc[-1]

    signal = None
    if ema_bull and rsi_now < 70 and sup:
        ns = min(sup, key=lambda x: abs(x - price_now))
        signal = {
            'dir': 'LONG', 'entry': round(price_now, 2),
            'sl': round(ns - p_range*0.15, 2),
            'tp1': round(price_now + p_range*0.5, 2),
            'tp2': round(price_now + p_range*1.0, 2),
            'tp3': round(price_now + p_range*1.5, 2),
        }
    elif not ema_bull and rsi_now > 30 and res:
        nr = min(res, key=lambda x: abs(x - price_now))
        signal = {
            'dir': 'SHORT', 'entry': round(price_now, 2),
            'sl': round(nr + p_range*0.15, 2),
            'tp1': round(price_now - p_range*0.5, 2),
            'tp2': round(price_now - p_range*1.0, 2),
            'tp3': round(price_now - p_range*1.5, 2),
        }
    return signal


def render_chart(df_48, res, sup, signal, png_path):
    """Render the premium dark-mode candlestick chart."""
    now_myt = datetime.now(MYT)
    price_now = df_48['Close'].iloc[-1]
    rsi_now = df_48['rsi'].iloc[-1]
    lo, hi = df_48['Low'].min(), df_48['High'].max()
    p_range = hi - lo
    n = len(df_48)
    x = np.arange(n)

    ch = df_48['Close'].iloc[-1] - df_48['Close'].iloc[-2]
    pct = ch / df_48['Close'].iloc[-2] * 100
    cc = GREEN if ch >= 0 else RED
    ca = '▲' if ch >= 0 else '▼'

    fig = plt.figure(figsize=(16.54, 11.69), facecolor=BG)
    gs = GridSpec(3, 1, figure=fig, height_ratios=[5, 1.5, 0.3],
                  hspace=0.06, left=0.06, right=0.87, top=0.91, bottom=0.04)
    ax = fig.add_subplot(gs[0])
    ax_r = fig.add_subplot(gs[1], sharex=ax)
    ax_i = fig.add_subplot(gs[2])

    for a in [ax, ax_r, ax_i]:
        a.set_facecolor(PANEL)
        a.tick_params(colors=TXT, labelsize=8)
        for s in a.spines.values():
            s.set_color(GRID)

    # Candlesticks
    for i in range(n):
        o, h, l, c = df_48.iloc[i][['Open', 'High', 'Low', 'Close']]
        bull = c >= o
        col = BULL if bull else BEAR
        wcol = BULL_W if bull else BEAR_W
        ax.plot([x[i], x[i]], [l, h], color=wcol, linewidth=0.8, zorder=2)
        bh = max(abs(c - o), (h - l) * 0.02)
        ax.add_patch(Rectangle((x[i]-0.35, min(o, c)), 0.7, bh,
                                fc=col, ec=wcol, lw=0.5, zorder=3))
        pat = df_48.iloc[i].get('pattern', '')
        if pat == 'H':
            ax.annotate('H', xy=(x[i], h), xytext=(x[i], h+p_range*0.04),
                        fontsize=7, color=GOLD, ha='center', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.15', fc=BG, ec=GOLD, alpha=0.9))
        elif pat == 'SS':
            ax.annotate('SS', xy=(x[i], h), xytext=(x[i], h+p_range*0.04),
                        fontsize=7, color=RED, ha='center', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.15', fc=BG, ec=RED, alpha=0.9))
        elif pat == 'BE':
            ax.annotate('BE', xy=(x[i], l), xytext=(x[i], l-p_range*0.04),
                        fontsize=7, color=RED, ha='center', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.15', fc=BG, ec=RED, alpha=0.9))
        elif pat == 'BEn':
            ax.annotate('BEn', xy=(x[i], l), xytext=(x[i], l-p_range*0.04),
                        fontsize=7, color=GREEN, ha='center', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.15', fc=BG, ec=GREEN, alpha=0.9))

    # EMAs
    ax.plot(x, df_48['ema20'].values, color=BLUE, lw=1.5, label='EMA 20', zorder=4)
    ax.plot(x, df_48['ema50'].values, color=ORANGE, lw=1.5, label='EMA 50', zorder=4)

    # S/R lines
    for lvl in res:
        ax.axhline(y=lvl, color=RED, ls='--', lw=1.0, alpha=0.6, zorder=1)
        ax.text(n+0.5, lvl, f'R {lvl:,.2f}', fontsize=7.5, color=RED, va='center',
                fontfamily='monospace', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', fc=BG, ec=RED, alpha=0.85))
    for lvl in sup:
        ax.axhline(y=lvl, color=GREEN, ls='--', lw=1.0, alpha=0.6, zorder=1)
        ax.text(n+0.5, lvl, f'S {lvl:,.2f}', fontsize=7.5, color=GREEN, va='center',
                fontfamily='monospace', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', fc=BG, ec=GREEN, alpha=0.85))

    # Signal zones
    if signal:
        sc = GREEN if signal['dir'] == 'LONG' else RED
        ax.axhline(y=signal['entry'], color=GOLD, ls='-', lw=2.0, alpha=0.9, zorder=5)
        ax.text(-2, signal['entry'], f"ENTRY {signal['entry']:,.2f}", fontsize=8.5, color=GOLD,
                va='center', ha='right', fontweight='bold', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.25', fc=BG, ec=GOLD, alpha=0.9))
        ax.axhline(y=signal['sl'], color=RED, ls=':', lw=1.5, alpha=0.8, zorder=5)
        ax.text(-2, signal['sl'], f"SL {signal['sl']:,.2f}", fontsize=7.5, color=RED,
                va='center', ha='right', fontweight='bold', fontfamily='monospace')
        for tk in ['tp1', 'tp2', 'tp3']:
            ax.axhline(y=signal[tk], color=GREEN, ls=':', lw=1.0, alpha=0.6, zorder=5)
            ax.text(-2, signal[tk], f"{tk.upper()} {signal[tk]:,.2f}", fontsize=7, color=GREEN,
                    va='center', ha='right', fontfamily='monospace')
        ax.axhspan(signal['sl'], signal['entry'], alpha=0.08, color=sc, zorder=0)
        ax.axhspan(signal['entry'], signal['tp3'], alpha=0.04, color=GREEN, zorder=0)

    # Current price
    ax.axhline(y=price_now, color=GOLD, ls='-', lw=0.5, alpha=0.4, zorder=1)
    ax.text(n+2, price_now, f'● {price_now:,.2f}', fontsize=13, color=GOLD,
            va='center', fontweight='bold', fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.4', fc=BG, ec=GOLD, alpha=0.95))

    ax.set_xlim(-4, n+8)
    ax.set_ylim(lo - p_range*0.15, hi + p_range*0.35)
    ax.grid(True, color=GRID, alpha=0.3, lw=0.5)
    ax.set_ylabel('Price (USD)', color=TXT, fontsize=10, fontfamily='monospace')

    ticks = list(range(0, n, 4))
    labels = [df_48.index[i].strftime('%m/%d\n%H:%M') for i in ticks if i < n]
    ax.set_xticks(ticks)
    plt.setp(ax.get_xticklabels(), visible=False)

    ax.legend(loc='upper left', fontsize=8, facecolor=PANEL, edgecolor=GRID,
              labelcolor=TXT, framealpha=0.9)

    # RSI panel
    rsi_v = df_48['rsi'].values
    ax_r.fill_between(x, rsi_v, 50, where=(rsi_v >= 50), color=GREEN, alpha=0.15, interpolate=True)
    ax_r.fill_between(x, rsi_v, 50, where=(rsi_v < 50), color=RED, alpha=0.15, interpolate=True)
    ax_r.plot(x, rsi_v, color=PURPLE, lw=1.5, zorder=3)
    ax_r.axhline(y=70, color=RED, ls='--', lw=0.8, alpha=0.5)
    ax_r.axhline(y=30, color=GREEN, ls='--', lw=0.8, alpha=0.5)
    ax_r.axhline(y=50, color=TXT, ls=':', lw=0.5, alpha=0.3)
    ax_r.text(n+0.5, rsi_now, f'RSI {rsi_now:.1f}', fontsize=9, color=PURPLE,
              va='center', fontweight='bold', fontfamily='monospace',
              bbox=dict(boxstyle='round,pad=0.2', fc=BG, ec=PURPLE, alpha=0.9))
    ax_r.set_ylim(15, 85)
    ax_r.set_ylabel('RSI(14)', color=TXT, fontsize=9, fontfamily='monospace')
    ax_r.grid(True, color=GRID, alpha=0.3, lw=0.5)
    ax_r.set_yticks([30, 50, 70])
    ax_r.set_xticks(ticks)
    ax_r.set_xticklabels(labels, fontsize=6.5, color='#8b949e', fontfamily='monospace')

    # Info bar
    ax_i.set_xlim(0, 1)
    ax_i.set_ylim(0, 1)
    ax_i.axis('off')
    ema_st = 'BULLISH ▲' if df_48['ema20'].iloc[-1] > df_48['ema50'].iloc[-1] else 'BEARISH ▼'
    info = (f"EMA Cross: {ema_st}  │  RSI: {rsi_now:.1f}  │  "
            f"Range 48h: {lo:,.2f} – {hi:,.2f}  │  GC=F (Yahoo Finance)")
    if signal:
        info += f"  │  Signal: {signal['dir']} @ {signal['entry']:,.2f}"
    ax_i.text(0.0, 0.5, info, fontsize=7.5, color='#8b949e', va='center', fontfamily='monospace')

    # Title
    fig.text(0.06, 0.955, 'XAUUSD H1', fontsize=22, fontweight='bold', color=GOLD, fontfamily='monospace')
    fig.text(0.23, 0.955, '— Abang Sado Udin', fontsize=15, color=TXT, fontfamily='monospace')
    fig.text(0.06, 0.932, now_myt.strftime('%Y-%m-%d %H:%M MYT'), fontsize=10, color='#8b949e', fontfamily='monospace')
    fig.text(0.87, 0.95, f'{price_now:,.2f}', fontsize=28, fontweight='bold', color=GOLD,
             ha='right', fontfamily='monospace')
    fig.text(0.87, 0.928, f'{ca} {abs(ch):.2f} ({pct:+.2f}%)', fontsize=12, color=cc,
             ha='right', fontfamily='monospace')

    plt.savefig(png_path, dpi=150, facecolor=BG, bbox_inches='tight', pad_inches=0.3)
    plt.close()


def create_pdf(png_path, pdf_path):
    """Wrap chart PNG into landscape A4 PDF with gold accents."""
    now_myt = datetime.now(MYT)
    c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
    w, h = landscape(A4)

    c.setFillColor(HexColor(BG))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    c.setStrokeColor(HexColor(GOLD))
    c.setLineWidth(2)
    c.line(20, h-15, w-20, h-15)

    c.drawImage(png_path, 20, 25, width=w-40, height=h-55,
                preserveAspectRatio=True, anchor='c')

    c.setFillColor(HexColor('#8b949e'))
    c.setFont('Courier', 7)
    c.drawString(20, 10,
                 f'Generated: {now_myt.strftime("%Y-%m-%d %H:%M:%S MYT")}  │  '
                 f'Abang Sado Udin Trading Signals  │  XAUUSD H1')

    c.setStrokeColor(HexColor(GOLD_DIM))
    c.setLineWidth(1)
    c.line(20, 20, w-20, 20)

    c.save()


def main():
    parser = argparse.ArgumentParser(description='XAUUSD H1 Signal Chart PDF')
    parser.add_argument('--output', '-o', default='/var/arifos/artifacts/outbox/2026-07-14/xauusd_signal_chart.pdf')
    args = parser.parse_args()

    pdf_path = Path(args.output)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = '/tmp/xauusd_chart_render.png'

    print("📡 Fetching XAUUSD data (GC=F, 60d, 1h)...")
    df = fetch_gold_data()
    if df.empty:
        print("❌ Failed to fetch data")
        sys.exit(1)
    print(f"✅ Got {len(df)} candles")

    df = calc_indicators(df)
    df_48 = df.tail(48).copy()

    res, sup = find_sr_levels(df_48, df)
    print(f"📊 Support: {sup}")
    print(f"📊 Resistance: {res}")

    signal = detect_signal(df_48, res, sup)
    if signal:
        print(f"🎯 Signal: {signal['dir']} @ {signal['entry']}")
    else:
        print("ℹ️  No active signal")

    print("🎨 Rendering chart...")
    render_chart(df_48, res, sup, signal, png_path)

    print("📄 Generating PDF...")
    create_pdf(png_path, str(pdf_path))

    Path(png_path).unlink(missing_ok=True)

    print(f"✅ PDF saved: {pdf_path}")
    print(f"   Price: {df_48['Close'].iloc[-1]:,.2f}")
    print(f"   RSI:   {df_48['rsi'].iloc[-1]:.1f}")


if __name__ == '__main__':
    main()
