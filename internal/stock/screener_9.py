"""
WEALTH Stock Analysis — 9-Point Fundamentals + Technical Screener
══════════════════════════════════════════════════════════════════

The 9 criteria every Bursa stock must pass before entering Arif's watchlist:

FUNDAMENTAL (5 checks from klse-screener):
  1. PE Ratio     < 15        — Value check (not overpaying)
  2. ROE          > 10%       — Quality check (management creates value)
  3. Dividend Yield > 2%      — Income check (paid to wait)
  4. PB Ratio     < 2.0       — Asset check (not buying air)
  5. EPS          > 0         — Profitability (actually making money)

TECHNICAL (4 checks from yfinance history):
  6. Price > SMA50            — Uptrend (above medium-term average)
  7. RSI 30-70                — Not extreme (not overbought/oversold)
  8. MACD bullish             — Momentum (trend strength confirmed)
  9. Volume > 1M daily        — Liquidity (can exit cleanly)

Score: 0-9. 9/9 = textbook setup. 5/9 = needs more study. < 3/9 = skip.

DITEMPA BUKAN DIBERI — Screen on truth, not hope.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

# ─── Major Bursa Tickers (verified working) ───────────────────────────────

MAJOR_TICKERS = [
    "1155",  # MAYBANK
    "1295",  # PBBANK
    "3182",  # GENTING
    "4197",  # SIME DARBY
    "5183",  # PETRONAS CHEMICALS
    "5681",  # PETRONAS DAGANGAN
    "6033",  # PETRONAS ENERGY
    "6947",  # DIALOG
    "7113",  # TOP GLOVE
    "7277",  # KOSSAN
]


def run_screener_9() -> Dict[str, Any]:
    """Run the 9-point fundamentals + technical screener on major Bursa stocks.

    Returns ranked list: stocks that pass the most criteria first.
    """
    results: List[Dict[str, Any]] = []

    for ticker in MAJOR_TICKERS:
        try:
            score, details = _score_stock(ticker)
            if details:
                results.append(
                    {
                        "ticker": ticker,
                        "name": details.get("name", ticker),
                        "score": score,
                        "max_score": 9,
                        "checks": details.get("checks", {}),
                        "last_price": details.get("last_price"),
                        "pe": details.get("pe"),
                        "roe": details.get("roe"),
                        "dy": details.get("dy"),
                        "sector": details.get("sector", ""),
                    }
                )
            time.sleep(0.1)  # minimal rate limit
        except Exception:
            continue

    # Sort by score descending, then by ticker
    results.sort(key=lambda r: (-r["score"], r["ticker"]))

    # Verdicts
    strong = [r for r in results if r["score"] >= 7]
    study = [r for r in results if 4 <= r["score"] < 7]
    skip = [r for r in results if r["score"] < 4]

    return {
        "status": "OK",
        "verdict": "SAFE_TO_STUDY",
        "tool": "wealth_stock_analysis",
        "mode": "screener_9",
        "total_screened": len(results),
        "strong_buys": len(strong),
        "worth_studying": len(study),
        "skip": len(skip),
        "criteria": [
            {
                "id": 1,
                "name": "PE < 15",
                "type": "fundamental",
                "description": "Value check — not overpaying",
            },
            {
                "id": 2,
                "name": "ROE > 10%",
                "type": "fundamental",
                "description": "Quality — management creates value",
            },
            {
                "id": 3,
                "name": "Dividend Yield > 2%",
                "type": "fundamental",
                "description": "Income — paid to wait",
            },
            {
                "id": 4,
                "name": "PB < 2.0",
                "type": "fundamental",
                "description": "Asset — not buying air",
            },
            {
                "id": 5,
                "name": "EPS > 0",
                "type": "fundamental",
                "description": "Profitability — actually making money",
            },
            {
                "id": 6,
                "name": "Price > SMA50",
                "type": "technical",
                "description": "Uptrend — above medium-term average",
            },
            {
                "id": 7,
                "name": "RSI 30-70",
                "type": "technical",
                "description": "Not extreme — neither overbought nor oversold",
            },
            {
                "id": 8,
                "name": "MACD Bullish",
                "type": "technical",
                "description": "Momentum — trend strength confirmed",
            },
            {
                "id": 9,
                "name": "Volume > 1M",
                "type": "technical",
                "description": "Liquidity — can exit cleanly",
            },
        ],
        "results": results,
        "recommendation_only": True,
        "final_authority": "Arif",
        "note": "Screening only. NOT a buy/sell signal. Each stock needs individual TAC-9 + evidence card before acting.",
    }


def _score_stock(ticker: str) -> tuple:
    """Score a single Bursa stock across 9 criteria.

    Returns (score, details_dict).
    """
    score = 0
    checks: Dict[str, Any] = {}
    details: Dict[str, Any] = {"name": ticker, "checks": checks}

    # ── FUNDAMENTALS (from klse-screener) ──
    try:
        from klse_screener import get_klse_fundamentals, get_klse_intraday_stats

        fund = get_klse_fundamentals(ticker)
        if not fund:
            return 0, None

        name = fund.get("name", ticker)
        pe = _safe_float(fund.get("pe_ratio"))
        roe = _safe_float(fund.get("roe"))
        dy = _safe_float(fund.get("dividend_yield"))
        pb = _safe_float(fund.get("pb_ratio"))
        eps = _safe_float(fund.get("eps"))
        sector = fund.get("sector", "")

        details["name"] = name
        details["pe"] = pe
        details["roe"] = roe
        details["dy"] = dy
        details["pb"] = pb
        details["eps"] = eps
        details["sector"] = sector

        # 1. PE < 15
        if pe is not None and 0 < pe < 15:
            score += 1
            checks["1_PE"] = {"pass": True, "value": pe, "rule": "PE < 15"}
        else:
            checks["1_PE"] = {"pass": False, "value": pe, "rule": "PE < 15"}

        # 2. ROE > 10%
        if roe is not None and roe > 10:
            score += 1
            checks["2_ROE"] = {"pass": True, "value": roe, "rule": "ROE > 10%"}
        else:
            checks["2_ROE"] = {"pass": False, "value": roe, "rule": "ROE > 10%"}

        # 3. Dividend Yield > 2%
        if dy is not None and dy > 2:
            score += 1
            checks["3_DY"] = {"pass": True, "value": dy, "rule": "DY > 2%"}
        else:
            checks["3_DY"] = {"pass": False, "value": dy, "rule": "DY > 2%"}

        # 4. PB < 2.0
        if pb is not None and 0 < pb < 2.0:
            score += 1
            checks["4_PB"] = {"pass": True, "value": pb, "rule": "PB < 2.0"}
        else:
            checks["4_PB"] = {"pass": False, "value": pb, "rule": "PB < 2.0"}

        # 5. EPS > 0
        if eps is not None and eps > 0:
            score += 1
            checks["5_EPS"] = {"pass": True, "value": eps, "rule": "EPS > 0"}
        else:
            checks["5_EPS"] = {"pass": False, "value": eps, "rule": "EPS > 0"}

        # ── TECHNICAL (from yfinance) ──
        try:
            import yfinance as yf

            yt = yf.Ticker(f"{ticker}.KL")
            hist = yt.history(period="3mo")
            if not hist.empty:
                closes = [float(x) for x in hist["Close"].tolist()]
                volumes = [int(x) for x in hist["Volume"].tolist()]
                highs = [float(x) for x in hist["High"].tolist()]
                lows = [float(x) for x in hist["Low"].tolist()]

                last_price = closes[-1] if closes else None
                details["last_price"] = last_price

                # 6. Price > SMA50
                if len(closes) >= 50:
                    sma50 = sum(closes[-50:]) / 50
                    if last_price and last_price > sma50:
                        score += 1
                        checks["6_SMA50"] = {
                            "pass": True,
                            "value": f"{last_price:.2f} > {sma50:.2f}",
                            "rule": "Price > SMA50",
                        }
                    else:
                        checks["6_SMA50"] = {
                            "pass": False,
                            "value": f"{last_price:.2f} vs {sma50:.2f}",
                            "rule": "Price > SMA50",
                        }
                else:
                    checks["6_SMA50"] = {
                        "pass": False,
                        "value": "insufficient data",
                        "rule": "Price > SMA50",
                    }

                # 7. RSI 30-70
                rsi = _compute_rsi_14(closes)
                if rsi is not None and 30 <= rsi <= 70:
                    score += 1
                    checks["7_RSI"] = {"pass": True, "value": rsi, "rule": "RSI 30-70"}
                else:
                    checks["7_RSI"] = {"pass": False, "value": rsi, "rule": "RSI 30-70"}

                # 8. MACD Bullish
                macd_bullish = _macd_is_bullish(closes)
                if macd_bullish:
                    score += 1
                    checks["8_MACD"] = {
                        "pass": True,
                        "value": "bullish",
                        "rule": "MACD Bullish",
                    }
                else:
                    checks["8_MACD"] = {
                        "pass": False,
                        "value": "bearish/neutral",
                        "rule": "MACD Bullish",
                    }

                # 9. Volume > 1M daily
                avg_vol = sum(volumes[-20:]) / min(20, len(volumes)) if volumes else 0
                if avg_vol > 1_000_000:
                    score += 1
                    checks["9_VOLUME"] = {
                        "pass": True,
                        "value": f"{avg_vol / 1e6:.1f}M avg",
                        "rule": "Volume > 1M",
                    }
                else:
                    checks["9_VOLUME"] = {
                        "pass": False,
                        "value": f"{avg_vol / 1e3:.0f}K avg",
                        "rule": "Volume > 1M",
                    }

        except Exception:
            details["last_price"] = None
            for cid in ["6_SMA50", "7_RSI", "8_MACD", "9_VOLUME"]:
                checks[cid] = {
                    "pass": False,
                    "value": "yfinance unavailable",
                    "rule": checks.get(cid, {}).get("rule", "?"),
                }

    except ImportError:
        return 0, None

    return score, details


# ─── Mini Technical Helpers (self-contained, no heavy deps) ────────────────


def _safe_float(val) -> Optional[float]:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _compute_rsi_14(prices: List[float]) -> Optional[float]:
    """Compute RSI(14) — returns latest value only."""
    if len(prices) < 15:
        return None
    gains = []
    losses = []
    for i in range(1, 15):
        delta = prices[i] - prices[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains) / 14
    avg_loss = sum(losses) / 14
    for i in range(15, len(prices)):
        delta = prices[i] - prices[i - 1]
        gain = max(delta, 0)
        loss = max(-delta, 0)
        avg_gain = (avg_gain * 13 + gain) / 14
        avg_loss = (avg_loss * 13 + loss) / 14
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)


def _ema(prices: List[float], period: int) -> List[float]:
    """Exponential Moving Average."""
    if len(prices) < period:
        return []
    result = []
    multiplier = 2.0 / (period + 1)
    sma = sum(prices[:period]) / period
    result.append(sma)
    for i in range(period, len(prices)):
        ema_val = (prices[i] - result[-1]) * multiplier + result[-1]
        result.append(ema_val)
    return result


def _macd_is_bullish(prices: List[float]) -> bool:
    """Check if MACD is bullish (MACD line > signal line)."""
    if len(prices) < 35:
        return False
    ema12 = _ema(prices, 12)
    ema26 = _ema(prices, 26)
    macd_line = [e12 - e26 for e12, e26 in zip(ema12[-len(ema26) :], ema26)]
    signal = _ema(macd_line, 9)
    if len(signal) > 1:
        return macd_line[-1] > signal[-1]
    return False
