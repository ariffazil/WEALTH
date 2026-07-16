#!/usr/bin/env python3
"""
Gold S/R Alert → Telegram SADO Group
Checks XAUUSD price against support/resistance levels.
If near S/R, generates chart + posts to SADO group.

Usage:
  python3 gold_alert.py              # normal run (silent if nothing)
  python3 gold_alert.py --force      # force alert regardless of S/R proximity
  python3 gold_alert.py --dry-run    # generate chart + message, don't post

Cron: */30 8-20 * * 1-5  (every 30 min, 8am-8pm MYT, Mon-Fri)
"""

import json
import os
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Load secrets from vault.env if not already loaded
if not os.environ.get("TELEGRAM_BOT_TOKEN"):
    vault_env = Path("/root/.secrets/vault.env")
    if vault_env.exists():
        for line in vault_env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key = key.removeprefix("export ").strip()
                val = val.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, val)

import requests
import yfinance as yf
import mplfinance as mpf
import matplotlib
matplotlib.use('Agg')  # headless
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

# ─── CONFIG ──────────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("GOLD_ALERT_CHAT_ID", "-1003815535761")  # SADO group
MCP_WEALTH_URL = "https://wealth.arif-fazil.com/mcp"

# S/R levels (from gold dashboard)
SR_LEVELS = [
    {"label": "S2", "price": 3980, "type": "support"},
    {"label": "S1", "price": 4020, "type": "support"},
    {"label": "R1", "price": 4100, "type": "resistance"},
    {"label": "R2", "price": 4150, "type": "resistance"},
]

# Thresholds
SR_PROXIMITY_PCT = 0.3    # within 0.3% of S/R = "near"
COOLDOWN_HOURS = 4         # don't re-alert same level within 4 hours
CONFIDENCE_MIN = 0.70      # minimum MCP confidence to alert

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
STATE_FILE = DATA_DIR / "gold_alert_state.json"
CHART_FILE = DATA_DIR / "gold_alert_chart.png"

# Timezone
MYT = timezone(timedelta(hours=8))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("gold_alert")


# ─── MCP: FETCH GOLD SNAPSHOT ────────────────────────────────────────────────

def fetch_gold_snapshot() -> dict:
    """Call WEALTH MCP capital_market(mode='gold', commodity='snapshot')."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "capital_market",
            "arguments": {"mode": "gold", "commodity": "snapshot"},
        },
        "id": 1,
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    resp = requests.post(MCP_WEALTH_URL, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"MCP error: {data['error']}")

    result = data.get("result", {})
    content = result.get("content", [])
    if content:
        text_item = next((c for c in content if c.get("type") == "text"), None)
        if text_item and text_item.get("text"):
            envelope = json.loads(text_item["text"])
            return envelope.get("result", envelope)

    if "structuredContent" in result:
        return result["structuredContent"]

    return result


def extract_price(snapshot: dict) -> tuple[float, float, str]:
    """Extract (price_usd, change_pct, source) from MCP snapshot."""
    snap = snapshot.get("snapshot", {})
    xau = snap.get("XAU_USD", {})
    price = xau.get("value", 0)
    source = xau.get("source", "unknown")

    signals = snapshot.get("signals", [])
    daily_move = next((s for s in signals if s.get("signal_type") == "daily_move"), None)
    change_pct = daily_move.get("value", 0) if daily_move else 0

    confidence = snapshot.get("evidence_quality", "OBSERVED")
    conf_map = {"STRONG": 0.95, "MODERATE": 0.80, "WEAK": 0.60, "OBSERVED": 0.50}
    conf_score = conf_map.get(confidence, 0.50)

    return price, change_pct, source, conf_score


# ─── S/R PROXIMITY CHECK ─────────────────────────────────────────────────────

def check_sr_proximity(price: float) -> list[dict]:
    """Return list of S/R levels the price is near."""
    near = []
    for level in SR_LEVELS:
        pct_diff = abs(price - level["price"]) / level["price"] * 100
        if pct_diff <= SR_PROXIMITY_PCT:
            near.append({**level, "pct_diff": pct_diff, "price_now": price})
    return near


# ─── COOLDOWN ─────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_alerts": {}}


def save_state(state: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def is_in_cooldown(level_label: str, state: dict) -> bool:
    last = state.get("last_alerts", {}).get(level_label)
    if not last:
        return False
    last_time = datetime.fromisoformat(last)
    return datetime.now(MYT) - last_time < timedelta(hours=COOLDOWN_HOURS)


def mark_alerted(level_label: str, state: dict):
    state.setdefault("last_alerts", {})[level_label] = datetime.now(MYT).isoformat()
    save_state(state)


# ─── CHART GENERATION ────────────────────────────────────────────────────────

def generate_chart(price: float, sr_near: list[dict]) -> Path:
    """Generate candlestick chart with EMA + S/R + RSI using mplfinance."""
    # Fetch 5 days of 1h data
    ticker = yf.Ticker("GC=F")
    df = ticker.history(period="5d", interval="1h")

    if df.empty:
        log.warning("yfinance returned empty data, trying 1d interval")
        df = ticker.history(period="1mo", interval="1d")

    if df.empty:
        raise RuntimeError("Cannot fetch OHLC data from yfinance")

    # Calculate EMAs
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # Calculate RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Style
    mc = mpf.make_marketcolors(
        up='#22c55e', down='#ef4444',
        edge={'up': '#22c55e', 'down': '#ef4444'},
        wick={'up': '#22c55e', 'down': '#ef4444'},
        volume={'up': '#22c55e80', 'down': '#ef444480'},
    )
    style = mpf.make_mpf_style(
        marketcolors=mc,
        facecolor='#0a0a0f',
        edgecolor='#1a1a2e',
        gridcolor='#1a1a2e',
        gridstyle='--',
        rc={
            'font.family': 'monospace',
            'font.size': 9,
            'axes.labelcolor': '#a0a0b0',
            'xtick.color': '#a0a0b0',
            'ytick.color': '#a0a0b0',
        },
    )

    # S/R horizontal lines
    hlines = []
    hcolors = []
    for sr in SR_LEVELS:
        hlines.append(sr["price"])
        hcolors.append('#22c55e' if sr["type"] == "support" else '#ef4444')

    # Highlight near levels
    for sr in sr_near:
        idx = SR_LEVELS.index(sr) if sr in SR_LEVELS else -1
        if idx >= 0:
            hcolors[idx] = '#f59e0b'  # amber for near levels

    # EMA plots
    ema_plots = [
        mpf.make_addplot(df['EMA20'], color='#3b82f6', width=1.2, label='EMA20'),
        mpf.make_addplot(df['EMA50'], color='#a855f7', width=1.2, label='EMA50'),
    ]

    # RSI panel
    if 'RSI' in df.columns and df['RSI'].notna().any():
        rsi_colors = ['#22c55e' if v < 30 else '#ef4444' if v > 70 else '#6b7280' for v in df['RSI']]
        ema_plots.append(
            mpf.make_addplot(df['RSI'], panel=2, color='#eab308', width=1.0, ylabel='RSI')
        )
        # RSI overbought/oversold lines
        ema_plots.append(
            mpf.make_addplot(pd.Series(70, index=df.index), panel=2, color='#ef444440', linestyle='--', width=0.5)
        )
        ema_plots.append(
            mpf.make_addplot(pd.Series(30, index=df.index), panel=2, color='#22c55e40', linestyle='--', width=0.5)
        )

    # Generate chart
    fig, axes = mpf.plot(
        df,
        type='candle',
        style=style,
        addplot=ema_plots,
        hlines=dict(hlines=hlines, colors=hcolors, linestyle='--', linewidths=1.0),
        volume=True,
        volume_panel=1,
        figsize=(12, 7),
        tight_layout=True,
        returnfig=True,
        panel_ratios=(4, 1, 1.5),
    )

    # Title
    now_str = datetime.now(MYT).strftime("%Y-%m-%d %H:%M MYT")
    fig.suptitle(
        f"XAUUSD ${price:,.2f}  |  {now_str}",
        fontsize=14, color='#e0e0e0', fontweight='bold',
        x=0.02, ha='left', y=0.98,
    )

    # Legend
    axes[0].legend(
        ['EMA20', 'EMA50', 'S1:4020', 'R1:4100'],
        loc='upper left', fontsize=8,
        facecolor='#0a0a0f', edgecolor='#333',
        labelcolor='#e0e0e0',
    )

    CHART_FILE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHART_FILE, dpi=150, bbox_inches='tight', facecolor='#0a0a0f')
    plt.close(fig)

    log.info(f"Chart saved: {CHART_FILE}")
    return CHART_FILE


# ─── TELEGRAM SEND ───────────────────────────────────────────────────────────

def send_telegram_photo(photo_path: Path, caption: str) -> bool:
    """Send photo with caption to Telegram group."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as f:
        resp = requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML",
        }, files={"photo": f}, timeout=30)

    if resp.status_code == 200:
        log.info("Alert posted to SADO group ✓")
        return True
    else:
        log.error(f"Telegram error: {resp.status_code} {resp.text}")
        return False


def send_telegram_text(text: str) -> bool:
    """Send text message to Telegram group (fallback if chart fails)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }, timeout=15)

    if resp.status_code == 200:
        log.info("Text alert posted to SADO group ✓")
        return True
    else:
        log.error(f"Telegram error: {resp.status_code} {resp.text}")
        return False


# ─── ALERT MESSAGE ───────────────────────────────────────────────────────────

def format_alert_message(
    price: float,
    change_pct: float,
    source: str,
    conf_score: float,
    sr_near: list[dict],
) -> str:
    """Format the alert message for Telegram."""
    now_str = datetime.now(MYT).strftime("%a %d %b %H:%M MYT")

    # Direction arrow
    arrow = "🟢" if change_pct >= 0 else "🔴"
    change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"

    # Near levels text
    level_lines = []
    for sr in sr_near:
        dist = abs(price - sr["price"])
        direction = "above" if price > sr["price"] else "below"
        level_lines.append(
            f"  {'🟢' if sr['type'] == 'support' else '🔴'} "
            f"<b>{sr['label']}</b> ${sr['price']:,.0f} "
            f"(${dist:.0f} {direction})"
        )

    # Bias based on position relative to S/R
    if any(sr["type"] == "support" for sr in sr_near):
        bias = "⚡ POTENTIAL BUY SETUP — Near Support"
    elif any(sr["type"] == "resistance" for sr in sr_near):
        bias = "⚠️ POTENTIAL SELL SETUP — Near Resistance"
    else:
        bias = "📊 MONITORING"

    # Confidence tier
    if conf_score >= 0.90:
        conf_tier = "STRONG"
    elif conf_score >= 0.75:
        conf_tier = "MODERATE"
    else:
        conf_tier = "WEAK"

    msg = f"""<b>🥇 GOLD S/R ALERT</b> | {now_str}

{arrow} <b>XAUUSD ${price:,.2f}</b> ({change_str})
📡 Source: {source} | Confidence: {conf_tier}

<b>📍 Near Levels:</b>
{chr(10).join(level_lines)}

<b>{bias}</b>

<i>Kau decide, kau execute. F13 Active. 🫡</i>"""

    return msg


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gold S/R Alert → Telegram SADO")
    parser.add_argument("--force", action="store_true", help="Force alert regardless of S/R proximity")
    parser.add_argument("--dry-run", action="store_true", help="Generate chart + message, don't post")
    parser.add_argument("--price-override", type=float, help="Override price for testing")
    args = parser.parse_args()

    log.info("Gold alert check starting...")

    # 1. Fetch price from WEALTH MCP
    try:
        snapshot = fetch_gold_snapshot()
        price, change_pct, source, conf_score = extract_price(snapshot)
        log.info(f"Price: ${price:,.2f} | Δ: {change_pct:+.2f}% | Source: {source} | Conf: {conf_score:.2f}")
    except Exception as e:
        log.error(f"MCP fetch failed: {e}")
        # Try yfinance fallback
        try:
            ticker = yf.Ticker("GC=F")
            info = ticker.fast_info
            price = info.last_price
            change_pct = 0
            source = "yfinance:fallback"
            conf_score = 0.70
            log.info(f"Fallback price: ${price:,.2f}")
        except Exception as e2:
            log.error(f"yfinance fallback also failed: {e2}")
            sys.exit(1)

    if args.price_override:
        price = args.price_override
        log.info(f"Price overridden: ${price:,.2f}")

    # 2. Check S/R proximity
    sr_near = check_sr_proximity(price)

    if not sr_near and not args.force:
        log.info("Price not near any S/R level. Silent. ✓")
        sys.exit(0)

    if args.force and not sr_near:
        log.info("--force: generating alert anyway (not near S/R)")
        sr_near = [{"label": "FORCE", "price": price, "type": "test", "pct_diff": 0}]

    # 3. Check cooldown
    state = load_state()
    alert_levels = [sr for sr in sr_near if not is_in_cooldown(sr["label"], state)]

    if not alert_levels and not args.force:
        log.info("All near levels in cooldown. Silent. ✓")
        sys.exit(0)

    if args.force:
        alert_levels = sr_near

    log.info(f"Alert triggered! Near levels: {[sr['label'] for sr in alert_levels]}")

    # 4. Generate chart
    try:
        chart_path = generate_chart(price, alert_levels)
    except Exception as e:
        log.error(f"Chart generation failed: {e}")
        chart_path = None

    # 5. Format message
    msg = format_alert_message(price, change_pct, source, conf_score, alert_levels)

    # 6. Send
    if args.dry_run:
        log.info("DRY RUN — not posting to Telegram")
        print("\n--- MESSAGE ---")
        print(msg)
        print(f"--- CHART: {chart_path} ---")
        sys.exit(0)

    if not TELEGRAM_BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    if chart_path and chart_path.exists():
        success = send_telegram_photo(chart_path, msg)
    else:
        log.warning("No chart available, sending text only")
        success = send_telegram_text(msg)

    if success:
        for sr in alert_levels:
            mark_alerted(sr["label"], state)
        log.info("Alert sent + state updated ✓")
    else:
        log.error("Alert send failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
