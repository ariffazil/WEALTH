#!/usr/bin/env python3
"""
Hermes Hourly Market Scan — XAUUSD
Mon-Fri: 00:00–20:00 UTC (08:00–04:00 MYT+1)
Covers: Asian(session 00-08 UTC) → London(08-16 UTC) → NY morning(13:30-20:00 UTC)
Output: /root/trading/logs/hourly_{YYYYMMDD_HH}.json
Site update: /var/www/html/gold/api/signal_v2.json
"""

import sys
import json
import os
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────
ROOT       = Path("/root/trading")
LOG_DIR    = ROOT / "logs"
OUT_DIR    = ROOT / "cron"
LOG_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

# ── logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "hourly_scan.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("hermes.hourly")

# ── Telegram config ──────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    "8410138119:AAEeKmJ8VTx8dzV8l76auY9QL17xyMgHMLM"
)
TELEGRAM_CHAT_ID   = "-1003753855708"   # AAA group
TELEGRAM_API_URL   = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# ── WEALTH MCP bridge ────────────────────────────────────────────────────────
WEALTH_MCP = "https://wealth.arif-fazil.com/mcp"

def call_wealth_mcp(tool: str, params: dict) -> dict:
    """Call WEALTH MCP tool via HTTPS POST. Returns parsed result dict."""
    import urllib.request, urllib.error
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": params}
    }).encode()
    req = urllib.request.Request(
        WEALTH_MCP,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read())
        # MCP result is double-wrapped: result.content[0].text → JSON envelope
        inner_text = raw.get("result", {}).get("content", [{}])[0].get("text", "{}")
        inner = json.loads(inner_text)
        return inner
    except urllib.error.URLError as e:
        log.error("WEALTH MCP unreachable: %s", e)
        return {"error": str(e)}

# ── Market hours check ───────────────────────────────────────────────────────
def is_trading_hours() -> bool:
    """
    Mon-Fri, 00:00–20:00 UTC (= 08:00–04:00 MYT+1).
    Covers: Asian(00-08 UTC) → London(08-16 UTC) → NY morning(13:30-20:00 UTC).
    """
    utc = datetime.now(timezone.utc)
    if utc.weekday() >= 5:          # Sat/Sun
        return False
    return 0 <= utc.hour <= 20

def get_session_label(utc_hour: int) -> str:
    if 0 <= utc_hour < 8:
        return "ASIAN"
    elif 8 <= utc_hour < 13:
        return "LONDON"
    elif 13 <= utc_hour < 20:
        return "NY_OPEN"
    else:
        return "NY_CLOSE"

# ── Core fetch ───────────────────────────────────────────────────────────────
def fetch_market_data() -> dict:
    """Fetch XAUUSD snapshot from WEALTH MCP. Returns parsed inner envelope."""
    log.info("Fetching XAUUSD data from WEALTH MCP …")
    return call_wealth_mcp("capital_market", {
        "mode":       "gold",
        "commodity":  "snapshot",
    })

def compute_signal_v2(wealth_data: dict, regime_data: dict) -> dict:
    """
    Build signal_v2 dict from WEALTH MCP responses.
    wealth_data is already the parsed inner envelope (post content[0].text unwrap).
    Path: wealth_data → result → snapshot → XAU_USD.value
    """
    utc_now  = datetime.now(timezone.utc)
    utc_hour = utc_now.hour
    session  = get_session_label(utc_hour)

    # Extract price — path: result.snapshot.XAU_USD.value
    price_val = 0.0
    try:
        result_block = wealth_data.get("result", {})
        snapshot     = result_block.get("snapshot", {})
        xau_usd     = snapshot.get("XAU_USD", {})
        price_val    = xau_usd.get("value", 0.0) or price_val
        log.info("XAU/USD extracted: $%.2f", price_val)
    except Exception as e:
        log.warning("Price extraction error: %s", e)

    # Direction from regime
    regime_val    = regime_data.get("regime", "NEUTRAL")
    direction_map = {
        "UPTREND":  "LONG",
        "DOWNTREND":"SHORT",
        "NEUTRAL":  "FLAT",
    }
    direction = direction_map.get(regime_val, "FLAT")

    return {
        "signal": {
            "direction":       direction,
            "strength":        regime_val,
            "confidence":      0.70,
            "entry_price":     round(price_val, 2) if price_val else 0.0,
            "stop_loss":       0.0,
            "take_profit_1":   0.0,
            "take_profit_2":   0.0,
            "rr_ratio":        0.0,
            "confluence_score": 0.0,
            "suggested_lot":   0.01,
            "risk_amount":     0,
            "verdict":         "SABAR" if direction == "FLAT" else "HOLD",
            "judge_reason":    f"Hourly scan [{session}] — {regime_val}. Awaiting confluence.",
            "scan_type":       "hourly",
            "session":         session,
        },
        "regime": {
            "regime":    regime_val,
            "confidence": 0.70,
            "price":     round(price_val, 2) if price_val else 0.0,
            "ema_20":    0.0,
            "ema_50":    0.0,
            "ema_200":   0.0,
            "rsi":       0.0,
        },
        "zones": {
            "buy_zone":  {"price": 0.0, "strength": 0},
            "sell_zone": {"price": 0.0, "strength": 0},
        },
        "confluence_factors": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# ── Site update ──────────────────────────────────────────────────────────────
SITE_API = Path("/var/www/html/gold/api/signal_v2.json")

def update_site(signal_v2: dict) -> None:
    """Write signal_v2 JSON to gold site API directory."""
    try:
        SITE_API.write_text(json.dumps(signal_v2, indent=2))
        log.info("Site updated: %s", SITE_API)
    except Exception as e:
        log.error("Site update failed: %s", e)

# ── Telegram helpers ─────────────────────────────────────────────────────────
def _telegram_send_text(text: str, parse_mode: str = "Markdown") -> bool:
    """
    Send text directly via Telegram Bot API (bypasses hermes-a2a).
    Returns True on success, False on failure.
    """
    try:
        resp = requests.post(
            TELEGRAM_API_URL,
            json={
                "chat_id":    TELEGRAM_CHAT_ID,
                "text":       text,
                "parse_mode": parse_mode,
            },
            timeout=15,
        )
        payload = resp.json()
        if payload.get("ok"):
            log.info("Telegram Bot API: message sent successfully")
            return True
        else:
            log.warning(
                "Telegram Bot API error: %s",
                payload.get("description", payload),
            )
            return False
    except Exception as e:
        log.warning("Telegram Bot API call failed: %s", e)
        return False

def _a2a_broadcast(text: str) -> None:
    """
    Broadcast via hermes-a2a bridge on port 18001 (A-FLOW srv1642546).
    FALLBACK ONLY — used when hermes-a2a is reachable.
    """
    import socket
    try:
        msg = json.dumps({"type": "broadcast", "text": text})
        with socket.create_connection(("127.0.0.1", 18001), timeout=5) as s:
            s.sendall(msg.encode() + b"\n")
        log.info("A2A broadcast sent")
    except Exception as e:
        log.warning("A2A broadcast failed: %s", e)

# ── Telegram alert ────────────────────────────────────────────────────────────
def send_telegram_alert(signal_v2: dict) -> None:
    """
    Send hourly scan summary to Telegram.
    Priority: Telegram Bot API (direct) → A2A bridge (fallback).
    """
    sig   = signal_v2["signal"]
    reg   = signal_v2["regime"]
    price = reg.get("price", 0)
    direction = sig["direction"]
    session   = sig["session"]
    verdict   = sig["verdict"]

    text = (
        f"🕐 *Hermes Hourly Scan*\n"
        f"`{datetime.now().strftime('%Y-%m-%d %H:%M MYT')}`\n\n"
        f"📊 Session: `{session}`\n"
        f"💰 XAUUSD: `${price:.2f}`\n"
        f"📐 Regime: `{reg['regime']}`\n"
        f"🎯 Direction: `{direction}`\n"
        f"⚖️ Verdict: `{verdict}`\n"
        f"📈 Confidence: `{sig['confidence']:.0%}`\n\n"
        f"`{sig['judge_reason']}`"
    )

    # Try direct Telegram Bot API first
    direct_ok = _telegram_send_text(text)

    # Fallback to A2A bridge if direct failed
    if not direct_ok:
        log.info("Falling back to A2A bridge …")
        _a2a_broadcast(text)

# ── On-demand signal sender (callable by skill) ─────────────────────────────
def send_signal_on_demand(
    direction: str,
    regime: str,
    price: float,
    session: str,
    verdict: str = "HOLD",
    confidence: float = 0.70,
    judge_reason: str = "",
    extra_text: str = "",
) -> dict:
    """
    Send a trading signal to Telegram on demand (e.g. from a skill).

    Args:
        direction:    LONG / SHORT / FLAT
        regime:       UPTREND / DOWNTREND / NEUTRAL
        price:        current XAUUSD price
        session:      ASIAN / LONDON / NY_OPEN / NY_CLOSE
        verdict:      HOLD / SABAR / EXECUTE / etc.
        confidence:   0.0–1.0
        judge_reason: free-text reason from the judge
        extra_text:   optional additional message appended after signal block

    Returns:
        dict with keys: ok (bool), method (str), chat_id (str), message_id (int or None)
    """
    emoji_dir = {"LONG": "🟢", "SHORT": "🔴", "FLAT": "⚪"}.get(direction, "⚪")

    text = (
        f"🚨 *Trading Signal (On-Demand)*\n"
        f"`{datetime.now().strftime('%Y-%m-%d %H:%M MYT')}`\n\n"
        f"{emoji_dir} Direction: `{direction}`\n"
        f"📐 Regime: `{regime}`\n"
        f"💰 Price: `${price:.2f}`\n"
        f"📊 Session: `{session}`\n"
        f"⚖️ Verdict: `{verdict}`\n"
        f"📈 Confidence: `{confidence:.0%}`\n"
    )

    if judge_reason:
        text += f"\n📋 Reason: `{judge_reason}`\n"

    if extra_text:
        text += f"\n{extra_text}\n"

    # Try direct Telegram Bot API first
    if _telegram_send_text(text):
        return {"ok": True, "method": "telegram_bot_api", "chat_id": TELEGRAM_CHAT_ID}

    # Fallback to A2A bridge
    try:
        _a2a_broadcast(text)
        return {"ok": True, "method": "a2a_bridge", "chat_id": TELEGRAM_CHAT_ID}
    except Exception as e:
        log.error("Both Telegram and A2A failed: %s", e)
        return {"ok": False, "method": "none", "error": str(e)}

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    log.info("═" * 50)
    log.info("Hermes Hourly Scan — START")

    utc_now   = datetime.now(timezone.utc)
    utc_hour  = utc_now.hour
    session   = get_session_label(utc_hour)
    log.info("Session: %s  UTC hour: %d", session, utc_hour)

    if not is_trading_hours():
        log.info("Outside trading hours — skipping fetch.")
        print("OUT_OF_HOURS")
        return

    # ── fetch ────────────────────────────────────────────────────────────────
    market_data = fetch_market_data()
    regime_data = {"regime": "NEUTRAL"}

    # Extract regime + price from market data
    # wealth_data = inner envelope → result.snapshot
    try:
        snapshot = market_data.get("result", {}).get("snapshot", {})
        xau      = snapshot.get("XAU_USD", {})
        price    = xau.get("value", 0.0)
        signals  = market_data.get("result", {}).get("signals", [])
        # Derive regime from signals: look for regime_label
        regime_raw = "NEUTRAL"
        for s in signals:
            if s.get("regime_label") in ("active",):
                regime_raw = "NEUTRAL"  # "active" in daily_move = caution, not a trend
                break
        regime_data = {"regime": regime_raw, "price": price}
        log.info("Regime: %s  Price: %.2f", regime_raw, price)
    except Exception as e:
        log.warning("Regime extraction error: %s", e)

    # ── compute ─────────────────────────────────────────────────────────────
    signal_v2 = compute_signal_v2(market_data, regime_data)

    # ── save log ────────────────────────────────────────────────────────────
    ts_str    = utc_now.strftime("%Y%m%d_%H")
    out_file  = OUT_DIR / f"hourly_{ts_str}.json"
    out_file.write_text(json.dumps(signal_v2, indent=2))
    log.info("Saved: %s", out_file)

    # ── update site ────────────────────────────────────────────────────────
    update_site(signal_v2)

    # ── Telegram alert ─────────────────────────────────────────────────────
    send_telegram_alert(signal_v2)

    log.info("Hermes Hourly Scan — DONE  price=%s direction=%s verdict=%s",
             regime_data.get("price"), signal_v2["signal"]["direction"],
             signal_v2["signal"]["verdict"])
    print("OK")

if __name__ == "__main__":
    main()
