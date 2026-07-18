#!/usr/bin/env python3
"""Test the full XAUUSD signal stack."""
import sys
sys.path.insert(0, "/root/trading")

print("=== XAUUSD Signal Stack Test ===")
print()

# Test 1: Gold price feed
print("1. Gold Price Feed...")
from signals.gold_feed import get_gold_price, get_gold_session_info
price = get_gold_price()
print(f"   Price: {price}")
session = get_gold_session_info()
print(f"   Session: {session}")
print()

# Test 2: Technical analysis
print("2. Technical Analysis...")
from signals.technical import analyze_gold
from signals.gold_feed import get_gold_candles
candles = get_gold_candles("1h", 100)
if candles:
    print(f"   Candles loaded: {len(candles)}")
    tech = analyze_gold(candles)
    ema = tech.get("ema", {})
    rsi = tech.get("rsi", {})
    conf = tech.get("confluence", {})
    print(f"   EMA20: {ema.get('fast')}")
    print(f"   EMA50: {ema.get('slow')}")
    print(f"   RSI: {rsi.get('value')}")
    print(f"   Trend: {ema.get('trend')}")
    print(f"   Confluence: {conf.get('direction')} ({conf.get('score')})")
    sr = tech.get("support_resistance", {})
    if sr.get("nearest_support"):
        print(f"   Nearest Support: {sr['nearest_support']['level']}")
    if sr.get("nearest_resistance"):
        print(f"   Nearest Resistance: {sr['nearest_resistance']['level']}")
else:
    print("   ERROR: No candle data")
print()

# Test 3: Macro signals
print("3. Macro Signals...")
from signals.macro import get_macro_signals
macro = get_macro_signals()
analysis = macro.get("macro", {}).get("analysis", {})
print(f"   Macro Bias: {analysis.get('macro_bias')}")
print(f"   Bull factors: {analysis.get('bull_score')}")
print(f"   Bear factors: {analysis.get('bear_score')}")
calendar = macro.get("calendar", {})
print(f"   Calendar Risk: {calendar.get('risk_level')}")
if calendar.get("next_event"):
    evt = calendar["next_event"]
    print(f"   Next Event: {evt['event']} ({evt['days_until']}d)")
print()

# Test 4: Signal generation
print("4. Signal Generation...")
from signals.engine import generate_signal
signal = generate_signal()
print(f"   Signal: {signal.get('signal')}")
if signal.get("signal") != "NO_SIGNAL":
    print(f"   Direction: {signal.get('direction')}")
    print(f"   Entry: {signal.get('entry')}")
    print(f"   SL: {signal.get('stop_loss')}")
    print(f"   TP: {signal.get('take_profit')}")
    print(f"   RR: 1:{signal.get('risk_reward')}")
    print(f"   Confidence: {signal.get('confidence')}")
    print(f"   Confluence: {signal.get('confluence_score')}")
else:
    print(f"   Reason: {signal.get('reason')}")
print()

# Test 5: Journal
print("5. Journal...")
from signals.journal import get_stats
stats = get_stats()
print(f"   Total signals logged: {stats.get('total_signals', 0)}")
print()

# Test 6: Briefing
print("6. Daily Briefing...")
from signals.daily_briefing import generate_briefing, format_briefing_simple
briefing = generate_briefing()
simple = format_briefing_simple(briefing)
print(simple)
print()

print("=== STACK OPERATIONAL ===")
