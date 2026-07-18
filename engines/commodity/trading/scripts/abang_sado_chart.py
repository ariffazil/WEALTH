#!/usr/bin/env python3
"""
XAUUSD H4 Professional Candlestick Chart — ABANG SADO UDIN
Dark-theme OANDA-style trading chart with full trade setup annotations.
Uses matplotlib + Rectangle patches (NO mplfinance).
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ── Color palette ──────────────────────────────────────────────
BG        = '#0d1117'
PANEL     = '#161b22'
GOLD      = '#f0a500'
GREEN     = '#3fb950'
RED       = '#f85149'
CYAN      = '#58a6ff'
ORANGE    = '#ffa657'
TEXT      = '#e6edf3'
DIM       = '#8b949e'
GRID      = '#21262d'

# ── Trade setup ────────────────────────────────────────────────
SELL_LIMIT = 4099.99
TP1        = 4000.00
SL         = 4130.00
CURRENT    = 4060.00

# ── Fetch data ─────────────────────────────────────────────────
print("Fetching XAUUSD (GC=F) data...")
ticker = yf.Ticker("GC=F")
df = ticker.history(period="30d", interval="1h")

if df.empty:
    print("1h data empty, trying 1d...")
    df = ticker.history(period="60d", interval="1d")

print(f"  Got {len(df)} bars, interval used")

# ── EMA calculation ────────────────────────────────────────────
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

df['EMA20'] = ema(df['Close'], 20)
df['EMA50'] = ema(df['Close'], 50)

# ── RSI calculation ────────────────────────────────────────────
def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

df['RSI'] = calc_rsi(df['Close'], 14)

# ── Zoom to last 14 days ───────────────────────────────────────
cutoff = df.index[-1] - pd.Timedelta(days=14)
df_zoom = df[df.index >= cutoff].copy()
df_zoom = df_zoom.reset_index()

# Use integer x-axis for cleaner candlestick spacing
n = len(df_zoom)
x = np.arange(n)

# ── Find swing highs for trendline ─────────────────────────────
# Identify local maxima
swing_highs = []
for i in range(2, n-2):
    if (df_zoom['High'].iloc[i] > df_zoom['High'].iloc[i-1] and 
        df_zoom['High'].iloc[i] > df_zoom['High'].iloc[i-2] and
        df_zoom['High'].iloc[i] > df_zoom['High'].iloc[i+1] and
        df_zoom['High'].iloc[i] > df_zoom['High'].iloc[i+2]):
        swing_highs.append(i)

# If not enough swing highs, use top N highest points
if len(swing_highs) < 2:
    top_indices = df_zoom['High'].nlargest(5).index.tolist()
    swing_highs = sorted(top_indices[:3])

# Pick first and last swing high for trendline
if len(swing_highs) >= 2:
    sh_x = [swing_highs[0], swing_highs[-1]]
    sh_y = [df_zoom['High'].iloc[swing_highs[0]], df_zoom['High'].iloc[swing_highs[-1]]]
else:
    sh_x = [0, n-1]
    sh_y = [df_zoom['High'].max(), df_zoom['High'].max()]

# Extend trendline forward
slope = (sh_y[1] - sh_y[0]) / (sh_x[1] - sh_x[0]) if sh_x[1] != sh_x[0] else 0
trend_x = [sh_x[0], n + 8]
trend_y = [sh_y[0], sh_y[0] + slope * (n + 8 - sh_x[0])]

# ── Support / Resistance levels ────────────────────────────────
# Use recent price action to find levels
recent_high = df_zoom['High'].max()
recent_low = df_zoom['Low'].min()
price_range = recent_high - recent_low

support_levels = [recent_low, recent_low + price_range * 0.25]
resistance_levels = [recent_high - price_range * 0.15, recent_high]

# ── Figure setup ────────────────────────────────────────────────
fig = plt.figure(figsize=(14.0, 8.5), facecolor=BG, dpi=150)

# Main chart: 75% height, RSI: 20% height, gap between
ax_main = fig.add_axes([0.08, 0.22, 0.78, 0.62], facecolor=PANEL)
ax_rsi  = fig.add_axes([0.08, 0.08, 0.78, 0.14], facecolor=PANEL, sharex=ax_main)

# ── Draw candlesticks ──────────────────────────────────────────
body_width = 0.55
wick_width = 0.08

for i in range(n):
    o = df_zoom['Open'].iloc[i]
    c = df_zoom['Close'].iloc[i]
    h = df_zoom['High'].iloc[i]
    l = df_zoom['Low'].iloc[i]
    
    if c >= o:  # Bullish
        color = GREEN
        body_bottom = o
        body_height = c - o
    else:  # Bearish
        color = RED
        body_bottom = c
        body_height = o - c
    
    # Wick
    ax_main.add_patch(plt.Rectangle(
        (x[i] - wick_width/2, l), wick_width, h - l,
        facecolor=color, edgecolor=color, linewidth=0.5, zorder=2
    ))
    # Body
    bh = max(body_height, price_range * 0.003)  # minimum visible height
    ax_main.add_patch(plt.Rectangle(
        (x[i] - body_width/2, body_bottom), body_width, bh,
        facecolor=color, edgecolor=color, linewidth=0.5, zorder=3
    ))

# ── EMA overlays ────────────────────────────────────────────────
ax_main.plot(x, df_zoom['EMA20'].values, color=CYAN, linewidth=1.2, alpha=0.85, label='EMA 20', zorder=4)
ax_main.plot(x, df_zoom['EMA50'].values, color=ORANGE, linewidth=1.2, alpha=0.85, label='EMA 50', zorder=4)

# ── Shaded zones ────────────────────────────────────────────────
# SELL zone (entry to SL) — light red
ax_main.axhspan(SELL_LIMIT, SL, facecolor=RED, alpha=0.08, zorder=0)
# PROFIT zone (TP to entry) — light green  
ax_main.axhspan(TP1, SELL_LIMIT, facecolor=GREEN, alpha=0.06, zorder=0)

# ── Trade levels ────────────────────────────────────────────────
# SELL LIMIT
ax_main.axhline(y=SELL_LIMIT, color=RED, linewidth=2.5, linestyle='-', zorder=6)
ax_main.text(n + 0.5, SELL_LIMIT, f'  SELL LIMIT @ ${SELL_LIMIT:,.2f} (0.5 lot)',
             color=RED, fontsize=13, fontweight='bold', va='center', ha='left',
             fontfamily='monospace', zorder=10,
             bbox=dict(boxstyle='round,pad=0.3', facecolor=BG, edgecolor=RED, alpha=0.9))

# TP1
ax_main.axhline(y=TP1, color=GREEN, linewidth=2.2, linestyle='--', zorder=6)
ax_main.text(n + 0.5, TP1, f'  TP1 @ ${TP1:,.0f}',
             color=GREEN, fontsize=13, fontweight='bold', va='center', ha='left',
             fontfamily='monospace', zorder=10,
             bbox=dict(boxstyle='round,pad=0.3', facecolor=BG, edgecolor=GREEN, alpha=0.9))

# SL
ax_main.axhline(y=SL, color=RED, linewidth=2.2, linestyle='--', zorder=6)
ax_main.text(n + 0.5, SL, f'  SL @ ${SL:,.0f}',
             color=RED, fontsize=13, fontweight='bold', va='center', ha='left',
             fontfamily='monospace', zorder=10,
             bbox=dict(boxstyle='round,pad=0.3', facecolor=BG, edgecolor=RED, alpha=0.9))

# ── Bearish trendline ───────────────────────────────────────────
ax_main.plot(trend_x, trend_y, color=RED, linewidth=1.8, linestyle='-', alpha=0.7, zorder=5)
# Arrow at end
ax_main.annotate('', xy=(n+4, sh_y[0] + slope * (n+4 - sh_x[0])),
                 xytext=(n+2, sh_y[0] + slope * (n+2 - sh_x[0])),
                 arrowprops=dict(arrowstyle='->', color=RED, lw=2), zorder=5)

# ── Current price marker ────────────────────────────────────────
ax_main.axhline(y=CURRENT, color=GOLD, linewidth=1.0, linestyle=':', alpha=0.5, zorder=4)
# Big gold label on right
ax_main.text(n + 0.5, CURRENT, f'  ${CURRENT:,.2f}',
             color=GOLD, fontsize=15, fontweight='bold', va='center', ha='left',
             fontfamily='monospace', zorder=10,
             bbox=dict(boxstyle='round,pad=0.3', facecolor=GOLD, edgecolor=GOLD, alpha=0.15))

# ── Support / Resistance lines ──────────────────────────────────
for sl in support_levels:
    ax_main.axhline(y=sl, color=GREEN, linewidth=0.8, linestyle='--', alpha=0.35, zorder=1)
for rl in resistance_levels:
    if abs(rl - SELL_LIMIT) > 15 and abs(rl - SL) > 15:
        ax_main.axhline(y=rl, color=RED, linewidth=0.8, linestyle='--', alpha=0.35, zorder=1)

# ── RSI panel ───────────────────────────────────────────────────
rsi_vals = df_zoom['RSI'].values
ax_rsi.plot(x, rsi_vals, color=CYAN, linewidth=1.2, zorder=3)
ax_rsi.axhline(y=70, color=RED, linewidth=0.6, linestyle='--', alpha=0.5)
ax_rsi.axhline(y=30, color=GREEN, linewidth=0.6, linestyle='--', alpha=0.5)
ax_rsi.axhline(y=50, color=DIM, linewidth=0.4, linestyle=':', alpha=0.3)

# Overbought/oversold shading
ax_rsi.axhspan(70, 100, facecolor=RED, alpha=0.05, zorder=0)
ax_rsi.axhspan(0, 30, facecolor=GREEN, alpha=0.05, zorder=0)

ax_rsi.fill_between(x, rsi_vals, 50, where=(rsi_vals > 50), 
                     color=CYAN, alpha=0.08, interpolate=True)
ax_rsi.fill_between(x, rsi_vals, 50, where=(rsi_vals < 50), 
                     color=CYAN, alpha=0.08, interpolate=True)

ax_rsi.set_ylim(15, 85)
ax_rsi.set_ylabel('RSI(14)', color=DIM, fontsize=10, fontfamily='monospace')
ax_rsi.tick_params(colors=DIM, labelsize=8)
for spine in ax_rsi.spines.values():
    spine.set_color(GRID)
ax_rsi.grid(axis='y', color=GRID, linewidth=0.3, alpha=0.5)

# RSI zone labels
ax_rsi.text(n - 1, 72, 'OB 70', color=RED, fontsize=8, alpha=0.6, ha='right', fontfamily='monospace')
ax_rsi.text(n - 1, 28, 'OS 30', color=GREEN, fontsize=8, alpha=0.6, ha='right', fontfamily='monospace')

# ── X-axis date labels ──────────────────────────────────────────
# Show dates at intervals
tick_positions = []
tick_labels = []
step = max(1, n // 10)
for i in range(0, n, step):
    tick_positions.append(x[i])
    dt = df_zoom['Date'].iloc[i] if 'Date' in df_zoom.columns else df_zoom.index[i]
    if hasattr(dt, 'strftime'):
        tick_labels.append(dt.strftime('%b %d'))
    else:
        tick_labels.append(str(dt)[:10])

ax_main.set_xticks(tick_positions)
ax_main.set_xticklabels([])  # Hide x labels on main chart
ax_rsi.set_xticks(tick_positions)
ax_rsi.set_xticklabels(tick_labels, color=DIM, fontsize=8, fontfamily='monospace', rotation=30)

# ── Y-axis styling ──────────────────────────────────────────────
ax_main.yaxis.tick_right()
ax_main.yaxis.set_label_position('right')
ax_main.tick_params(colors=DIM, labelsize=9)
ax_main.yaxis.set_major_formatter(plt.FormatStrFormatter('$%.0f'))
for spine in ax_main.spines.values():
    spine.set_color(GRID)
ax_main.grid(axis='y', color=GRID, linewidth=0.3, alpha=0.4)
ax_main.grid(axis='x', color=GRID, linewidth=0.2, alpha=0.2)

# Price range padding
price_min = min(TP1, df_zoom['Low'].min()) - 20
price_max = max(SL, df_zoom['High'].max()) + 20
ax_main.set_ylim(price_min, price_max)
ax_main.set_xlim(-1, n + 12)

# ── Title ───────────────────────────────────────────────────────
from datetime import timezone, timedelta as td
myt = timezone(td(hours=8))
now_myt = datetime.now(myt)
timestamp = now_myt.strftime('%Y-%m-%d %H:%M MYT')

fig.text(0.5, 0.96, 'XAUUSD H4 — ABANG SADO UDIN', 
         color=GOLD, fontsize=18, fontweight='bold', ha='center',
         fontfamily='monospace', transform=fig.transFigure)

fig.text(0.5, 0.935, f'Trade Setup Analysis  •  {timestamp}',
         color=DIM, fontsize=10, ha='center',
         fontfamily='monospace', transform=fig.transFigure)

# ── Legend (EMA) ────────────────────────────────────────────────
legend_elements = [
    Line2D([0], [0], color=CYAN, linewidth=1.5, label='EMA 20'),
    Line2D([0], [0], color=ORANGE, linewidth=1.5, label='EMA 50'),
]
leg = ax_main.legend(handles=legend_elements, loc='upper left', fontsize=9,
                     frameon=True, fancybox=True, framealpha=0.8,
                     facecolor=PANEL, edgecolor=GRID, labelcolor=TEXT)
leg.get_frame().set_zorder(20)

# ── Bottom info bar ─────────────────────────────────────────────
risk = SL - SELL_LIMIT   # $30.01
reward = SELL_LIMIT - TP1  # $99.99
rr_ratio = reward / risk

info_text = (
    f"ENTRY: ${SELL_LIMIT:,.2f}  •  TP1: ${TP1:,.0f}  •  SL: ${SL:,.0f}  •  "
    f"RISK: ${risk:,.0f}  •  REWARD: ${reward:,.0f}  •  "
    f"R:R = 1:{rr_ratio:.1f}  •  "
    f"Lot: 0.5  •  Confluence: EMA reject + bearish trendline + resistance zone"
)

fig.text(0.5, 0.025, info_text,
         color=DIM, fontsize=8.5, ha='center',
         fontfamily='monospace', transform=fig.transFigure,
         bbox=dict(boxstyle='round,pad=0.4', facecolor=PANEL, edgecolor=GOLD, 
                   alpha=0.85, linewidth=1.2))

# ── Gold accent border ──────────────────────────────────────────
border = mpatches.FancyBboxPatch(
    (0.01, 0.01), 0.98, 0.98,
    boxstyle="round,pad=0.01",
    facecolor='none',
    edgecolor=GOLD,
    linewidth=1.5,
    transform=fig.transFigure,
    clip_on=False,
    zorder=50
)
fig.patches.append(border)

# Inner subtle border
inner_border = mpatches.FancyBboxPatch(
    (0.025, 0.02), 0.95, 0.955,
    boxstyle="round,pad=0.008",
    facecolor='none',
    edgecolor=GOLD,
    linewidth=0.5,
    alpha=0.3,
    transform=fig.transFigure,
    clip_on=False,
    zorder=50
)
fig.patches.append(inner_border)

# ── Save ────────────────────────────────────────────────────────
output_path = '/var/arifos/artifacts/outbox/2026-07-14/abang-sado-trade-setup.pdf'
fig.savefig(output_path, format='pdf', facecolor=BG, edgecolor='none',
            bbox_inches='tight', dpi=150)
plt.close(fig)

print(f"\n✅ Chart saved to: {output_path}")
print(f"   R:R ratio: 1:{rr_ratio:.1f}")
print(f"   Risk: ${risk:,.2f} | Reward: ${reward:,.2f}")
print(f"   Bars plotted: {n}")
