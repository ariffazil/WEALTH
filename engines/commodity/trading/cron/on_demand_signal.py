#!/usr/bin/env python3
"""
On-demand XAUUSD Signal Fetcher
Call: python3 /root/trading/cron/on_demand_signal.py
Returns: formatted signal as print() — safe for skill/exec capture
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

API_URL = "http://localhost:3456/api/gold/signal_v2"
TIMEOUT = 10  # seconds


def fetch_signal() -> dict:
    try:
        req = urllib.request.Request(API_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as e:
        return {"error": str(e)}


def format_signal(data: dict) -> str:
    if "error" in data:
        return f"⚠️ Signal engine unavailable: {data['error']}"

    sig   = data.get("signal", {})
    reg   = data.get("regime", {})
    zones = data.get("zones", {})
    ts    = data.get("timestamp", "")

    # Clean timestamp
    try:
        dt = datetime.fromisoformat(ts.replace("+08:00", "").replace("Z", ""))
        ts_str = dt.strftime("%Y-%m-%d %H:%M MYT")
    except Exception:
        ts_str = ts

    direction  = sig.get("direction", "UNKNOWN")
    verdict    = sig.get("verdict", "UNKNOWN")
    entry      = sig.get("entry_price", 0)
    sl         = sig.get("stop_loss", 0)
    tp1        = sig.get("take_profit_1", 0)
    tp2        = sig.get("take_profit_2", 0)
    confidence = sig.get("confidence", 0)
    judge      = sig.get("judge_reason", "")
    regime_val = reg.get("regime", "UNKNOWN")
    reg_conf   = reg.get("confidence", 0)
    price      = reg.get("price", 0)
    ema20      = reg.get("ema_20", 0)
    ema50      = reg.get("ema_50", 0)
    ema200     = reg.get("ema_200", 0)
    rsi        = reg.get("rsi", 0)
    buy_zone   = zones.get("buy_zone", {})
    sell_zone  = zones.get("sell_zone", {})
    buy_price  = buy_zone.get("price", 0)
    buy_str    = buy_zone.get("strength", 0)
    sell_price = sell_zone.get("price", 0)
    sell_str   = sell_zone.get("strength", 0)

    # Verdict emoji
    vemoji = {"HOLD": "⏸", "SABAR": "💤", "SEAL": "🔒", "BUY": "🟢", "SELL": "🔴"}.get(verdict, "⚖️")

    # Direction emoji
    demoji = {"LONG": "🟢", "SHORT": "🔴", "FLAT": "⚪", "SABAR": "💤"}.get(direction, "⚪")

    lines = [
        f"📊 *XAUUSD Signal*",
        f"🕐 `{ts_str}`",
        "",
        f"💰 Price: `${price:.2f}`",
        f"📐 Regime: `{regime_val}`",
        f"🎯 Direction: {demoji} `{direction}`",
        f"⚖️ Verdict: {vemoji} `{verdict}`",
        "",
        f"📈 Entry: `${entry:.2f}`",
        f"🛑 SL: `${sl:.2f}`",
        f"🎯 TP1: `${tp1:.2f}`",
        f"🎯 TP2: `${tp2:.2f}`",
        "",
        f"📊 Confidence: `{confidence:.0%}` (regime: `{reg_conf:.0%}`)",
        f"📉 RSI(14): `{rsi:.1f}`",
        f"📐 EMA20: `{ema20:.2f}` | EMA50: `{ema50:.2f}` | EMA200: `{ema200:.2f}`",
        "",
        f"💎 Buy Zone: `${buy_price:.2f}` (strength {buy_str})",
        f"💎 Sell Zone: `${sell_price:.2f}` (strength {sell_str})",
        "",
        f"_{judge}_",
    ]

    return "\n".join(lines)


def main():
    data = fetch_signal()
    print(format_signal(data))


if __name__ == "__main__":
    main()
