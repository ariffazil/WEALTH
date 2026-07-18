"""
Macro Signal Layer — XAUUSD context.
DXY, US 10Y Yield, Fed expectations, economic calendar.

Usage:
    from signals.macro import get_macro_signals, get_dxy, get_yields, get_calendar
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


# Tickers
DXY_TICKER = "DX-Y.NYB"  # US Dollar Index
US10Y_TICKER = "^TNX"     # 10-Year Treasury Yield
US2Y_TICKER = "^IRX"      # 13-Week Treasury Bill (proxy for short-term rates)
VIX_TICKER = "^VIX"       # Volatility Index


def get_dxy() -> Dict:
    """Get US Dollar Index (DXY) data."""
    try:
        ticker = yf.Ticker(DXY_TICKER)
        hist = ticker.history(period="5d")

        if hist.empty:
            return {"error": "Cannot fetch DXY"}

        current = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
        change = current - prev
        change_pct = (change / prev) * 100 if prev else 0

        # DXY trend (20-day)
        hist_20d = ticker.history(period="1mo")
        if not hist_20d.empty and len(hist_20d) >= 20:
            sma20 = float(hist_20d["Close"].tail(20).mean())
            trend = "bullish" if current > sma20 else "bearish"
        else:
            sma20 = None
            trend = "unknown"

        return {
            "value": round(current, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 3),
            "sma20": round(sma20, 2) if sma20 else None,
            "trend": trend,
            "gold_correlation": "inverse",  # DXY up = gold down typically
        }
    except Exception as e:
        return {"error": str(e)}


def get_yields() -> Dict:
    """Get US Treasury yields data."""
    try:
        # 10Y yield
        tnx = yf.Ticker(US10Y_TICKER)
        tnx_hist = tnx.history(period="5d")

        us10y = None
        if not tnx_hist.empty:
            us10y = float(tnx_hist["Close"].iloc[-1])

        # VIX
        vix = yf.Ticker(VIX_TICKER)
        vix_hist = vix.history(period="5d")

        vix_value = None
        if not vix_hist.empty:
            vix_value = float(vix_hist["Close"].iloc[-1])

        return {
            "us10y": round(us10y, 3) if us10y else None,
            "vix": round(vix_value, 2) if vix_value else None,
            "gold_impact": _assess_yield_impact(us10y, vix_value),
        }
    except Exception as e:
        return {"error": str(e)}


def _assess_yield_impact(us10y: Optional[float], vix: Optional[float]) -> str:
    """Assess how yields impact gold."""
    if us10y is None:
        return "unknown"

    # High real yields = bearish for gold
    # Low/negative real yields = bullish for gold
    if us10y > 4.5:
        return "bearish"  # High yields crush gold
    elif us10y > 4.0:
        return "mild_bearish"
    elif us10y < 3.0:
        return "bullish"  # Low yields support gold
    elif us10y < 3.5:
        return "mild_bullish"
    else:
        return "neutral"


def get_gold_macro_context() -> Dict:
    """
    Get comprehensive macro context for gold.
    Combines DXY, yields, VIX, and macro assessment.
    """
    dxy = get_dxy()
    yields = get_yields()

    # Macro bias
    bullish_factors = []
    bearish_factors = []
    neutral_factors = []

    # DXY analysis
    if "error" not in dxy:
        if dxy.get("trend") == "bearish":
            bullish_factors.append("DXY weakening — supports gold")
        elif dxy.get("trend") == "bullish":
            bearish_factors.append("DXY strengthening — pressures gold")
        else:
            neutral_factors.append("DXY neutral")

        if dxy.get("change_pct", 0) < -0.3:
            bullish_factors.append(f"DXY down {abs(dxy['change_pct']):.2f}% today")
        elif dxy.get("change_pct", 0) > 0.3:
            bearish_factors.append(f"DXY up {dxy['change_pct']:.2f}% today")

    # Yield analysis
    if "error" not in yields:
        impact = yields.get("gold_impact", "unknown")
        if "bullish" in impact:
            bullish_factors.append(f"US10Y at {yields.get('us10y')}% — {impact} for gold")
        elif "bearish" in impact:
            bearish_factors.append(f"US10Y at {yields.get('us10y')}% — {impact} for gold")
        else:
            neutral_factors.append(f"US10Y at {yields.get('us10y')}% — neutral")

        vix = yields.get("vix")
        if vix and vix > 25:
            bullish_factors.append(f"VIX elevated ({vix}) — risk-off supports gold")
        elif vix and vix < 15:
            neutral_factors.append(f"VIX low ({vix}) — risk-on, gold less demanded")

    # Overall macro bias
    bull_score = len(bullish_factors)
    bear_score = len(bearish_factors)

    if bull_score > bear_score + 1:
        macro_bias = "bullish"
    elif bear_score > bull_score + 1:
        macro_bias = "bearish"
    else:
        macro_bias = "neutral"

    return {
        "timestamp": datetime.now().isoformat(),
        "dxy": dxy,
        "yields": yields,
        "analysis": {
            "macro_bias": macro_bias,
            "bullish_factors": bullish_factors,
            "bearish_factors": bearish_factors,
            "neutral_factors": neutral_factors,
            "bull_score": bull_score,
            "bear_score": bear_score,
        },
    }


# Economic calendar (static — key dates for July/August 2026)
# Update monthly or integrate with investing.com API later
GOLD_CALENDAR_2026 = [
    # Format: (date, event, impact, gold_effect)
    ("2026-07-15", "US CPI", "HIGH", "CPI higher → USD up → gold down"),
    ("2026-07-29", "FOMC Decision", "HIGH", "Hawkish → USD up → gold down"),
    ("2026-07-30", "FOMC Press Conference", "HIGH", "Dovish → USD down → gold up"),
    ("2026-08-01", "US NFP", "HIGH", "Strong NFP → USD up → gold down"),
    ("2026-08-12", "US CPI", "HIGH", "CPI higher → USD up → gold down"),
    ("2026-08-26", "FOMC Decision", "HIGH", "Hawkish → USD up → gold down"),
]


def get_upcoming_events(days: int = 7) -> List[Dict]:
    """Get upcoming economic events that impact gold."""
    today = datetime.now().date()
    cutoff = today + timedelta(days=days)

    events = []
    for date_str, event, impact, gold_effect in GOLD_CALENDAR_2026:
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if today <= event_date <= cutoff:
            events.append({
                "date": date_str,
                "event": event,
                "impact": impact,
                "gold_effect": gold_effect,
                "days_until": (event_date - today).days,
            })

    return events


def get_macro_signals() -> Dict:
    """
    Get all macro signals for gold trading.
    Main entry point for macro layer.
    """
    context = get_gold_macro_context()
    calendar = get_upcoming_events(7)

    # Calendar risk
    high_impact_events = [e for e in calendar if e["impact"] == "HIGH"]
    calendar_risk = "HIGH" if len(high_impact_events) >= 2 else "MEDIUM" if high_impact_events else "LOW"

    return {
        "timestamp": datetime.now().isoformat(),
        "macro": context,
        "calendar": {
            "upcoming": calendar,
            "risk_level": calendar_risk,
            "next_event": calendar[0] if calendar else None,
        },
        "summary": _build_macro_summary(context, calendar),
    }


def _build_macro_summary(context: Dict, calendar: List[Dict]) -> str:
    """Build human-readable macro summary."""
    lines = []
    analysis = context.get("analysis", {})

    lines.append(f"Macro Bias: {analysis.get('macro_bias', 'unknown').upper()}")
    lines.append(f"Bull factors: {analysis.get('bull_score', 0)}")
    lines.append(f"Bear factors: {analysis.get('bear_score', 0)}")

    for f in analysis.get("bullish_factors", []):
        lines.append(f"  ↑ {f}")
    for f in analysis.get("bearish_factors", []):
        lines.append(f"  ↓ {f}")

    if calendar:
        lines.append(f"\nCalendar Risk: {calendar[0].get('event', 'none')} in {calendar[0].get('days_until', '?')} days")

    return "\n".join(lines)


# Quick test
if __name__ == "__main__":
    print("=== Macro Signals Test ===")
    signals = get_macro_signals()
    print(json.dumps(signals, indent=2, default=str))
