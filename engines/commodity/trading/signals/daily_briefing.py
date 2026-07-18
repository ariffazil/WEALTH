"""
Daily Briefing Generator — XAUUSD.
Morning briefing for Arif before London open.

Usage:
    from signals.daily_briefing import generate_briefing, format_briefing_telegram
"""

from datetime import datetime
from typing import Dict
from signals.engine import generate_signal, SignalGenerator
from signals.gold_feed import get_gold_price, get_gold_session_info
from signals.technical import analyze_gold
from signals.gold_feed import get_gold_candles
from signals.macro import get_macro_signals
from signals.journal import get_stats, log_signal
import json


def generate_briefing() -> Dict:
    """
    Generate comprehensive morning briefing.
    Run at 8am MYT (00:00 UTC) before London open.
    """
    briefing = {
        "timestamp": datetime.now().isoformat(),
        "title": "XAUUSD Morning Briefing",
    }

    # 1. Current price
    price_data = get_gold_price()
    briefing["price"] = price_data

    # 2. Session info
    session = get_gold_session_info()
    briefing["session"] = session

    # 3. Technical analysis
    candles = get_gold_candles("1h", 100)
    if candles and len(candles) >= 60:
        tech = analyze_gold(candles)
        briefing["technical"] = tech
    else:
        briefing["technical"] = {"error": "Insufficient data"}

    # 4. Macro signals
    macro = get_macro_signals()
    briefing["macro"] = macro

    # 5. Generate signal
    signal = generate_signal()
    briefing["signal"] = signal

    # 6. Log signal if it exists
    if signal.get("signal") != "NO_SIGNAL":
        logged = log_signal(signal)
        briefing["logged_signal_id"] = logged.get("id")

    # 7. Recent performance
    stats = get_stats(days=7)
    briefing["weekly_stats"] = stats

    return briefing


def format_briefing_telegram(briefing: Dict) -> str:
    """
    Format briefing for Telegram (mobile-readable).
    """
    lines = []

    # Header
    lines.append("☀️ XAUUSD MORNING BRIEFING")
    lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M MYT')}")
    lines.append("")

    # Price
    price = briefing.get("price", {})
    if "error" not in price:
        change_emoji = "🟢" if price.get("change", 0) >= 0 else "🔴"
        lines.append(f"💰 GOLD: ${price['price']:,.2f} {change_emoji} {price.get('change', 0):+.2f} ({price.get('change_pct', 0):+.2f}%)")
    else:
        lines.append(f"💰 GOLD: Price unavailable")
    lines.append("")

    # Session
    session = briefing.get("session", {})
    session_emoji = {"LONDON": "🇬🇧", "NEW_YORK": "🇺🇸", "ASIAN": "🌏"}.get(session.get("session"), "⏰")
    lines.append(f"{session_emoji} Session: {session.get('session', 'unknown')}")
    lines.append("")

    # Technical
    tech = briefing.get("technical", {})
    if "error" not in tech:
        ema = tech.get("ema", {})
        rsi = tech.get("rsi", {})
        confluence = tech.get("confluence", {})

        lines.append("📊 TECHNICAL")
        lines.append(f"  EMA20: {ema.get('fast', '?')} | EMA50: {ema.get('slow', '?')}")
        lines.append(f"  Trend: {ema.get('trend', '?').upper()}")
        if ema.get("crossover", "none") != "none":
            lines.append(f"  ⚡ CROSSOVER: {ema['crossover'].upper()}")
        lines.append(f"  RSI: {rsi.get('value', '?')} ({rsi.get('signal', '?')})")
        if rsi.get("divergence", "none") != "none":
            lines.append(f"  ⚡ RSI DIVERGENCE: {rsi['divergence'].upper()}")

        # S/R
        sr = tech.get("support_resistance", {})
        support = sr.get("nearest_support")
        resistance = sr.get("nearest_resistance")
        if support:
            lines.append(f"  Support: {support['level']} ({support['strength']:.0%})")
        if resistance:
            lines.append(f"  Resistance: {resistance['level']} ({resistance['strength']:.0%})")

        # Patterns
        patterns = tech.get("candle_patterns", [])
        if patterns:
            pattern_str = ", ".join([p["pattern"] for p in patterns])
            lines.append(f"  Patterns: {pattern_str}")

        lines.append(f"  Confluence: {confluence.get('score', 0):.0%} ({confluence.get('direction', '?').upper()})")
    lines.append("")

    # Macro
    macro = briefing.get("macro", {})
    macro_analysis = macro.get("macro", {}).get("analysis", {})
    if macro_analysis:
        lines.append("🌍 MACRO")
        bias = macro_analysis.get("macro_bias", "unknown")
        bias_emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(bias, "❓")
        lines.append(f"  Bias: {bias.upper()} {bias_emoji}")

        for f in macro_analysis.get("bullish_factors", []):
            lines.append(f"  ↑ {f}")
        for f in macro_analysis.get("bearish_factors", []):
            lines.append(f"  ↓ {f}")

        # Calendar
        calendar = macro.get("calendar", {})
        next_event = calendar.get("next_event")
        if next_event:
            lines.append(f"  📅 Next: {next_event['event']} ({next_event['days_until']}d)")
            lines.append(f"     Risk: {calendar.get('risk_level', '?')}")
    lines.append("")

    # Signal
    signal = briefing.get("signal", {})
    if signal.get("signal") == "NO_SIGNAL":
        lines.append("🚫 SIGNAL: NO TRADE TODAY")
        lines.append(f"  Reason: {signal.get('reason', 'unknown')}")
    else:
        signal_emoji = {"BUY": "🟢 BUY", "SELL": "🔴 SELL"}.get(signal.get("signal"), "❓")
        lines.append(f"📈 SIGNAL: {signal_emoji}")
        lines.append(f"  Entry: {signal.get('entry', '?')}")
        lines.append(f"  SL: {signal.get('stop_loss', '?')}")
        lines.append(f"  TP: {signal.get('take_profit', '?')}")
        lines.append(f"  RR: 1:{signal.get('risk_reward', '?')}")
        lines.append(f"  Confidence: {signal.get('confidence', 0):.0%}")
        lines.append(f"  Session: {signal.get('session', '?')}")
        lines.append("")
        lines.append("📝 REASONING:")
        lines.append(signal.get("reasoning", "No reasoning available"))
    lines.append("")

    # Weekly stats
    stats = briefing.get("weekly_stats", {})
    if stats.get("total_signals", 0) > 0:
        lines.append("📊 WEEKLY STATS")
        lines.append(f"  Signals: {stats.get('total_signals', 0)}")
        lines.append(f"  Win Rate: {stats.get('win_rate', 0)}%")
        lines.append(f"  Avg RR: {stats.get('avg_rr', 0)}")
        lines.append(f"  P&L: {stats.get('total_pnl_pips', 0):+.2f} pips")
        lines.append(f"  {stats.get('calibration_note', '')}")
    lines.append("")

    # Footer
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("Phase 1: AI signal, you execute")
    lines.append("Constitutional governance active (F1-F13)")
    lines.append("DITEMPA BUKAN DIBERI — 999 SEAL ALIVE")

    return "\n".join(lines)


def format_briefing_simple(briefing: Dict) -> str:
    """
    Ultra-simple briefing for quick reading.
    """
    price = briefing.get("price", {})
    signal = briefing.get("signal", {})

    lines = []
    lines.append(f"XAUUSD ${price.get('price', '?'):,.2f}")

    if signal.get("signal") == "NO_SIGNAL":
        lines.append(f"No signal — {signal.get('reason', 'unknown')[:50]}")
    else:
        lines.append(f"{signal.get('signal')} @ {signal.get('entry')}")
        lines.append(f"SL: {signal.get('stop_loss')} | TP: {signal.get('take_profit')}")
        lines.append(f"RR: 1:{signal.get('risk_reward')} | Conf: {signal.get('confidence', 0):.0%}")

    return "\n".join(lines)


# Quick test
if __name__ == "__main__":
    print("=== Daily Briefing Test ===")
    briefing = generate_briefing()
    print(format_briefing_telegram(briefing))
