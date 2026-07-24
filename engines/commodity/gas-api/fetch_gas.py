#!/usr/bin/env python3
"""
XNATGAS Natural Gas Data Fetcher — WEALTH Organ
Fetches live gold data from yfinance, computes technical indicators,
generates trading signals. Called by Node.js API server.

Usage:
    python3 fetch_gold.py ticker
    python3 fetch_gold.py history --interval 1h --period 30d
    python3 fetch_gold.py signals
    python3 fetch_gold.py levels
    python3 fetch_gold.py macro

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import json
import sys
import os
import argparse
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ── Cache ────────────────────────────────────────────────────────
CACHE_DIR = Path("/tmp/gas_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 300  # 5 minutes

MYT = timezone(timedelta(hours=8))

ASSET_KEY = "gas"


def _cache_key(endpoint: str, **kwargs) -> Path:
    raw = f"{endpoint}_{json.dumps(kwargs, sort_keys=True)}"
    h = hashlib.md5(raw.encode()).hexdigest()[:12]
    return CACHE_DIR / f"{endpoint}_{h}.json"


def _read_cache(path: Path) -> dict | None:
    if not path.exists():
        return None
    age = datetime.now().timestamp() - path.stat().st_mtime
    if age > CACHE_TTL:
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _write_cache(path: Path, data: dict):
    try:
        path.write_text(json.dumps(data, default=str))
    except Exception:
        pass



def _read_stale(path: Path) -> dict | None:
    """Rate-limit fallback: serve expired cache rather than fail (F2: marked stale)."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        age = int(datetime.now().timestamp() - path.stat().st_mtime)
        data["stale"] = True
        data["stale_age_s"] = age
        return data
    except Exception:
        return None

# ── Data Fetch ───────────────────────────────────────────────────
def fetch_ohlcv(interval: str = "1h", period: str = "30d") -> pd.DataFrame:
    import yfinance as yf

    ticker = yf.Ticker("NG=F")
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        ticker = yf.Ticker("NATGAS=X")
        df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise ValueError("No gas data available from yfinance")

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.columns = ["open", "high", "low", "close", "volume"]
    df.index.name = "time"
    return df


# ── Technical Indicators ─────────────────────────────────────────
def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"].shift(1)
    tr = pd.concat([high - low, (high - close).abs(), (low - close).abs()], axis=1).max(
        axis=1
    )
    return tr.ewm(span=period, adjust=False).mean()


def find_support_resistance(df: pd.DataFrame, lookback: int = 50) -> dict:
    recent = df.tail(lookback).copy()
    highs = recent["high"].values
    lows = recent["low"].values
    close_now = recent["close"].iloc[-1]

    swing_highs = []
    swing_lows = []
    for i in range(2, len(recent) - 2):
        if (
            highs[i] > highs[i - 1]
            and highs[i] > highs[i - 2]
            and highs[i] > highs[i + 1]
            and highs[i] > highs[i + 2]
        ):
            swing_highs.append(highs[i])
        if (
            lows[i] < lows[i - 1]
            and lows[i] < lows[i - 2]
            and lows[i] < lows[i + 1]
            and lows[i] < lows[i + 2]
        ):
            swing_lows.append(lows[i])

    h = recent["high"].iloc[-1]
    l = recent["low"].iloc[-1]
    c = recent["close"].iloc[-1]
    pivot = (h + l + c) / 3
    r1 = 2 * pivot - l
    r2 = pivot + (h - l)
    s1 = 2 * pivot - h
    s2 = pivot - (h - l)

    resistance_raw = swing_highs + [r1, r2, pivot]
    support_raw = swing_lows + [s1, s2, pivot]

    resistance = sorted(set(round(r, 2) for r in resistance_raw if r > close_now))
    support = sorted(
        set(round(s, 2) for s in support_raw if s < close_now), reverse=True
    )

    return {
        "support": support[:3],
        "resistance": resistance[:3],
        "pivot": round(pivot, 2),
    }


def detect_divergence(price: pd.Series, rsi: pd.Series, lookback: int = 10) -> str:
    if len(price) < lookback * 2:
        return "NONE"
    recent_price = price.iloc[-lookback:]
    prev_price = price.iloc[-lookback * 2 : -lookback]
    recent_rsi = rsi.iloc[-lookback:]
    prev_rsi = rsi.iloc[-lookback * 2 : -lookback]
    if recent_price.max() > prev_price.max() and recent_rsi.max() < prev_rsi.max():
        return "BEARISH"
    if recent_price.min() < prev_price.min() and recent_rsi.min() > prev_rsi.min():
        return "BULLISH"
    return "NONE"


def detect_candle_pattern(df: pd.DataFrame) -> str:
    if len(df) < 3:
        return "NONE"
    last = df.iloc[-1]
    prev = df.iloc[-2]
    body = abs(last["close"] - last["open"])
    upper_wick = last["high"] - max(last["close"], last["open"])
    lower_wick = min(last["close"], last["open"]) - last["low"]

    if body < (last["high"] - last["low"]) * 0.1:
        return "DOJI"
    if lower_wick > body * 2 and upper_wick < body * 0.5:
        return "HAMMER"
    if upper_wick > body * 2 and lower_wick < body * 0.5:
        return "SHOOTING_STAR"
    if (
        prev["close"] < prev["open"]
        and last["close"] > last["open"]
        and last["close"] > prev["open"]
        and last["open"] < prev["close"]
    ):
        return "ENGULFING_BULL"
    if (
        prev["close"] > prev["open"]
        and last["close"] < last["open"]
        and last["close"] < prev["open"]
        and last["open"] > prev["close"]
    ):
        return "ENGULFING_BEAR"
    return "NONE"


# ── Signal Generation ────────────────────────────────────────────
def generate_signal(df: pd.DataFrame) -> dict:
    close = df["close"]
    ema20 = compute_ema(close, 20)
    ema50 = compute_ema(close, 50)
    ema200 = compute_ema(close, 200)
    rsi = compute_rsi(close, 14)
    atr = compute_atr(df, 14)

    price = round(float(close.iloc[-1]), 2)
    ema20_val = round(float(ema20.iloc[-1]), 2)
    ema50_val = round(float(ema50.iloc[-1]), 2)
    ema200_val = round(float(ema200.iloc[-1]), 2)
    rsi_val = round(float(rsi.iloc[-1]), 1)
    atr_val = round(float(atr.iloc[-1]), 2)

    ema_trend = "BULLISH" if ema20_val > ema50_val else "BEARISH"
    rsi_state = (
        "OVERBOUGHT" if rsi_val > 70 else ("OVERSOLD" if rsi_val < 30 else "NEUTRAL")
    )
    divergence = detect_divergence(close, rsi)
    pattern = detect_candle_pattern(df)
    sr = find_support_resistance(df)

    confluence = []
    reasons = []

    if ema_trend == "BEARISH":
        confluence.append("EMA_BEARISH")
        reasons.append(f"EMA20 ({ema20_val}) < EMA50 ({ema50_val})")
    if ema_trend == "BULLISH":
        confluence.append("EMA_BULLISH")
        reasons.append(f"EMA20 ({ema20_val}) > EMA50 ({ema50_val})")
    if rsi_state == "OVERBOUGHT":
        confluence.append("RSI_OVERBOUGHT")
        reasons.append(f"RSI {rsi_val} — overbought")
    if rsi_state == "OVERSOLD":
        confluence.append("RSI_OVERSOLD")
        reasons.append(f"RSI {rsi_val} — oversold")
    if divergence == "BEARISH":
        confluence.append("RSI_BEAR_DIV")
        reasons.append("RSI bearish divergence")
    elif divergence == "BULLISH":
        confluence.append("RSI_BULL_DIV")
        reasons.append("RSI bullish divergence")
    if pattern in ("ENGULFING_BEAR", "SHOOTING_STAR"):
        confluence.append(f"CANDLE_{pattern}")
        reasons.append(f"Candle: {pattern.lower()}")
    elif pattern in ("ENGULFING_BULL", "HAMMER"):
        confluence.append(f"CANDLE_{pattern}")
        reasons.append(f"Candle: {pattern.lower()}")

    if sr["resistance"]:
        nearest_res = sr["resistance"][0]
        if price > nearest_res * 0.998:
            confluence.append("NEAR_RESISTANCE")
            reasons.append(f"Near resistance ${nearest_res}")
    if sr["support"]:
        nearest_sup = sr["support"][0]
        if price < nearest_sup * 1.002:
            confluence.append("NEAR_SUPPORT")
            reasons.append(f"Near support ${nearest_sup}")

    bearish_score = sum(
        1
        for c in confluence
        if any(k in c for k in ["BEAR", "OVERBOUGHT", "RESISTANCE", "SHOOTING"])
    )
    bullish_score = sum(
        1
        for c in confluence
        if any(k in c for k in ["BULL", "OVERSOLD", "SUPPORT", "HAMMER"])
    )

    if bearish_score >= 2 and bearish_score > bullish_score:
        signal = "SHORT"
        confidence = min(0.5 + bearish_score * 0.1, 0.95)
        sl = round(price + atr_val * 1.5, 2)
        tp = round(price - atr_val * 2, 2)
    elif bullish_score >= 2 and bullish_score > bearish_score:
        signal = "LONG"
        confidence = min(0.5 + bullish_score * 0.1, 0.95)
        sl = round(price - atr_val * 1.5, 2)
        tp = round(price + atr_val * 2, 2)
    else:
        signal = "NEUTRAL"
        confidence = 0.3
        sl = round(price + atr_val * 1.5, 2)
        tp = round(price - atr_val * 1.5, 2)

    rr = round(abs(tp - price) / max(abs(sl - price), 0.01), 1)

    return {
        "price": price,
        "ema_fast": ema20_val,
        "ema_slow": ema50_val,
        "ema_trend": ema_trend,
        "ema200": ema200_val,
        "rsi": rsi_val,
        "rsi_state": rsi_state,
        "rsi_divergence": divergence,
        "candle_pattern": pattern,
        "atr": atr_val,
        "signal": signal,
        "confidence": round(confidence, 2),
        "entry": price,
        "sl": sl,
        "tp": tp,
        "rr_ratio": rr,
        "support_levels": sr["support"],
        "resistance_levels": sr["resistance"],
        "pivot": sr["pivot"],
        "confluence_count": len(confluence),
        "confluence_signals": confluence,
        "reasons": reasons,
        "all_signals": confluence,
    }


# ── Endpoint Handlers ────────────────────────────────────────────
def cmd_ticker(args):
    cache = _cache_key("ticker")
    cached = _read_cache(cache)
    if cached:
        return cached

    df = fetch_ohlcv(interval="1h", period="5d")
    sig = generate_signal(df)
    prev_close = float(df["close"].iloc[-2])
    change = round(sig["price"] - prev_close, 2)
    change_pct = round(change / prev_close * 100, 2)

    result = {
        "symbol": "XNATGAS",
        "price": sig["price"],
        "change": change,
        "changePct": change_pct,
        "rsi": sig["rsi"],
        "rsiState": sig["rsi_state"],
        "signal": sig["signal"],
        "confidence": sig["confidence"],
        "ema20": sig["ema_fast"],
        "ema50": sig["ema_slow"],
        "ema200": sig["ema200"],
        "emaTrend": sig["ema_trend"],
        "support": sig["support_levels"],
        "resistance": sig["resistance_levels"],
        "pivot": sig["pivot"],
        "timestamp": datetime.now(MYT).isoformat(),
    }
    _write_cache(cache, result)
    return result


def cmd_history(args):
    interval = args.get("interval", "1h")
    period = args.get("period", "30d")
    # Normalize shorthand to yfinance-valid periods (F2: fail loud otherwise)
    period = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "2Y": "2y"}.get(period, period)
    cache = _cache_key("history", interval=interval, period=period)
    cached = _read_cache(cache)
    if cached:
        return cached

    df = fetch_ohlcv(interval=interval, period=period)
    df["ema20"] = compute_ema(df["close"], 20)
    df["ema50"] = compute_ema(df["close"], 50)
    df["ema200"] = compute_ema(df["close"], 200)
    df["rsi"] = compute_rsi(df["close"], 14)

    candles = []
    for ts, row in df.iterrows():
        t = int(ts.timestamp())
        candles.append(
            {
                "time": t,
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(row["volume"]) if not np.isnan(row["volume"]) else 0,
            }
        )

    ema20_line = [
        {"time": int(ts.timestamp()), "value": round(float(row["ema20"]), 2)}
        for ts, row in df.iterrows()
    ]
    ema50_line = [
        {"time": int(ts.timestamp()), "value": round(float(row["ema50"]), 2)}
        for ts, row in df.iterrows()
    ]
    ema200_line = [
        {"time": int(ts.timestamp()), "value": round(float(row["ema200"]), 2)}
        for ts, row in df.iterrows()
    ]
    rsi_line = [
        {"time": int(ts.timestamp()), "value": round(float(row["rsi"]), 1)}
        for ts, row in df.iterrows()
    ]

    result = {
        "candles": candles,
        "ema20": ema20_line,
        "ema50": ema50_line,
        "ema200": ema200_line,
        "rsi": rsi_line,
        "interval": interval,
        "period": period,
        "count": len(candles),
    }
    _write_cache(cache, result)
    return result


def cmd_signals(args):
    cache = _cache_key("signals")
    cached = _read_cache(cache)
    if cached:
        return cached

    df = fetch_ohlcv(interval="1h", period="5d")
    sig = generate_signal(df)
    sig["timestamp"] = datetime.now(MYT).isoformat()
    result = {"signals": [sig]}
    _write_cache(cache, result)
    return result


def cmd_levels(args):
    cache = _cache_key("levels")
    cached = _read_cache(cache)
    if cached:
        return cached

    df = fetch_ohlcv(interval="1h", period="30d")
    sr_1h = find_support_resistance(df, lookback=50)
    sr_daily = sr_1h

    try:
        df_daily = fetch_ohlcv(interval="1d", period="3mo")
        sr_daily = find_support_resistance(df_daily, lookback=30)
    except Exception:
        pass

    result = {
        "support_1h": sr_1h["support"],
        "resistance_1h": sr_1h["resistance"],
        "support_daily": sr_daily["support"],
        "resistance_daily": sr_daily["resistance"],
        "pivot": sr_1h["pivot"],
        "timestamp": datetime.now(MYT).isoformat(),
    }
    _write_cache(cache, result)
    return result


def cmd_macro(args):
    cache = _cache_key("macro")
    cached = _read_cache(cache)
    if cached:
        return cached

    import yfinance as yf

    result = {"timestamp": datetime.now(MYT).isoformat()}

    for sym, key in [
        ("DX-Y.NYB", "dxy"),
        ("^VIX", "vix"),
        ("^TNX", "us10y"),
        ("SI=F", "silver"),
        ("MYR=X", "usmyr"),
    ]:
        try:
            t = yf.Ticker(sym)
            h = t.history(period="5d")
            if not h.empty:
                result[key] = round(
                    float(h["Close"].iloc[-1]), 2 if key != "us10y" else 3
                )
        except Exception:
            result[key] = None

    if result.get("silver"):
        ticker_data = cmd_ticker({})
        if ticker_data.get("price"):
            result["gold_silver_ratio"] = round(
                ticker_data["price"] / result["silver"], 1
            )

    _write_cache(cache, result)
    return result


# ── APEX Evaluation (from trading engine) ──────────────────────────
def cmd_apex(args):
    """APEX market evaluation: G = A · P · E · X · Φ"""
    cache = _cache_key("apex")
    cached = _read_cache(cache)
    if cached:
        return cached

    import sys

    sys.path.insert(0, "/root/WEALTH")
    from trading.core.config import get_config
    from trading.core.models import OHLCV
    from trading.signals.scanner import compute_indicators
    from trading.apex.apex_predictor import evaluate_market

    cfg = get_config()

    # Fetch multi-timeframe data
    df_1h = fetch_ohlcv("1h", "30d")
    df_4h = None
    df_1d = None

    try:
        df_4h_raw = fetch_ohlcv("1h", "60d")
        if not df_4h_raw.empty:
            df_4h = (
                df_4h_raw[["open", "high", "low", "close", "volume"]]
                .resample("4h")
                .agg(
                    {
                        "open": "first",
                        "high": "max",
                        "low": "min",
                        "close": "last",
                        "volume": "sum",
                    }
                )
                .dropna(subset=["open"])
            )
    except Exception:
        pass

    try:
        df_1d = fetch_ohlcv("1d", "1y")
    except Exception:
        pass

    def _df_to_ohlcv(df):
        candles = []
        for ts, row in df.iterrows():
            candles.append(
                OHLCV(
                    timestamp=ts.to_pydatetime()
                    if hasattr(ts, "to_pydatetime")
                    else datetime.now(MYT),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row.get("volume", 0))
                    if not np.isnan(row.get("volume", 0))
                    else 0,
                )
            )
        return candles

    candles_1h = _df_to_ohlcv(df_1h)
    candles_4h = _df_to_ohlcv(df_4h) if df_4h is not None and not df_4h.empty else []
    candles_1d = _df_to_ohlcv(df_1d) if df_1d is not None and not df_1d.empty else []

    # Compute indicators
    from trading.signals.scanner import atr as atr_calc

    ind = compute_indicators(candles_1h, cfg)
    atr_vals = atr_calc(candles_1h, 14)
    atr_val = atr_vals[-1] if atr_vals else 10.0
    atr_avg = sum(atr_vals[-20:]) / min(20, len(atr_vals)) if atr_vals else atr_val

    # APEX evaluate
    apex = evaluate_market(
        candles_1h=candles_1h,
        candles_4h=candles_4h if candles_4h else None,
        candles_1d=candles_1d if candles_1d else None,
        ema_20=ind.ema_20,
        ema_50=ind.ema_50,
        ema_200=ind.ema_200,
        atr_val=atr_val,
        atr_avg=atr_avg,
    )

    price = float(df_1h["close"].iloc[-1])

    result = {
        "apex": {
            "A": round(apex.A, 4),
            "P": round(apex.P, 4),
            "E": round(apex.E, 4),
            "X": round(apex.X, 4),
            "Phi": round(apex.Phi, 4),
        },
        "G": round(apex.G, 4),
        "C_dark": round(apex.C_dark, 4),
        "dS": round(apex.dS, 4),
        "state": apex.state,
        "direction": apex.direction.value,
        "confidence": round(apex.confidence, 3),
        "volume_trend": apex.volume_trend,
        "volume_confirmation": apex.volume_confirmation,
        "momentum": round(apex.momentum, 3),
        "volatility_regime": apex.volatility_regime,
        "verdict": apex.verdict,
        "price": round(price, 2),
        "ema_20": round(ind.ema_20, 2),
        "ema_50": round(ind.ema_50, 2),
        "ema_200": round(ind.ema_200, 2),
        "rsi_14": round(ind.rsi_14, 1),
        "atr_14": round(atr_val, 2),
        "data_points": {
            "1H": len(candles_1h),
            "4H": len(candles_4h),
            "1D": len(candles_1d),
        },
        "timestamp": datetime.now(MYT).isoformat(),
    }
    _write_cache(cache, result)
    return result


def cmd_signal_v2(args):
    """Full trading signal from engine_v2 with position sizing."""
    cache = _cache_key("signal_v2")
    cached = _read_cache(cache)
    if cached:
        return cached

    import sys

    sys.path.insert(0, "/root/WEALTH")
    from trading.core.config import get_config
    from trading.core.models import OHLCV, RiskState
    from trading.backtest.engine_v2 import generate_signal_v2
    from trading.signals.scanner import compute_indicators
    from trading.signals.regime import compute_market_state
    from trading.risk.position_sizer import compute_position_size
    from trading.governance.gate import GovernanceGate

    cfg = get_config()
    df = fetch_ohlcv("1h", "30d")

    def _df_to_ohlcv(df):
        candles = []
        for ts, row in df.iterrows():
            candles.append(
                OHLCV(
                    timestamp=ts.to_pydatetime()
                    if hasattr(ts, "to_pydatetime")
                    else datetime.now(MYT),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row.get("volume", 0))
                    if not np.isnan(row.get("volume", 0))
                    else 0,
                )
            )
        return candles

    candles = _df_to_ohlcv(df)

    if len(candles) < 200:
        return {
            "error": f"Insufficient data: {len(candles)} candles, need 200+",
            "timestamp": datetime.now(MYT).isoformat(),
        }

    # Generate signal
    signal = generate_signal_v2(candles, cfg)

    # Get regime
    ind = compute_indicators(candles, cfg)
    state = compute_market_state(
        candles, ind.ema_20, ind.ema_50, ind.ema_200, ind.rsi_14
    )

    # Position sizing
    risk_state = RiskState(
        equity=cfg.syed_balance_estimate,
        balance=cfg.syed_balance_estimate,
        open_positions=0,
        daily_pnl=0.0,
        can_trade=True,
    )
    lots, risk_amount = compute_position_size(signal, risk_state, cfg)
    signal.suggested_lot = lots
    signal.risk_amount = risk_amount

    # Governance
    gate = GovernanceGate(require_arifos=False)
    signal = gate.evaluate(signal)

    result = {
        "signal": {
            "direction": signal.direction.value,
            "strength": signal.strength.value,
            "confidence": round(signal.confidence, 3),
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit_1": signal.take_profit_1,
            "take_profit_2": signal.take_profit_2,
            "rr_ratio": signal.rr_ratio,
            "confluence_score": signal.confluence_score,
            "suggested_lot": signal.suggested_lot,
            "risk_amount": round(signal.risk_amount, 2) if signal.risk_amount else 0,
            "verdict": signal.verdict.value,
            "judge_reason": signal.judge_reason,
        },
        "regime": {
            "regime": state.regime.value,
            "confidence": state.regime_confidence,
            "price": round(state.price, 2),
            "ema_20": round(state.ema_20, 2),
            "ema_50": round(state.ema_50, 2),
            "ema_200": round(state.ema_200, 2),
            "rsi": round(state.rsi, 1),
        },
        "zones": {
            "buy_zone": {
                "price": state.buy_zone.price,
                "strength": state.buy_zone.strength,
            }
            if state.buy_zone
            else None,
            "sell_zone": {
                "price": state.sell_zone.price,
                "strength": state.sell_zone.strength,
            }
            if state.sell_zone
            else None,
        },
        "confluence_factors": [
            {
                "name": f.name,
                "direction": f.direction.value,
                "weight": f.weight,
                "confidence": f.confidence,
            }
            for f in signal.confluence_factors
        ],
        "timestamp": datetime.now(MYT).isoformat(),
    }
    _write_cache(cache, result)
    return result


# ── CLI Entry ────────────────────────────────────────────────────
# ── Economic Calendar (ForexFactory JSON) ────────────────────────────
def cmd_calendar(args):
    """Fetch USD economic events from ForexFactory JSON API."""
    cache = _cache_key("calendar")
    cached = _read_cache(cache)
    if cached:
        return cached

    import urllib.request
    import json
    from datetime import datetime as dt

    # Use ForexFactory's JSON feed — much cleaner than HTML scraping
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = json.loads(resp.read())
    except Exception as e:
        return {
            "error": str(e),
            "events": [],
            "timestamp": datetime.now(MYT).isoformat(),
        }

    # Filter USD high/medium impact, upcoming only
    now = dt.now()
    events = []
    for ev in raw:
        if ev.get("country") != "USD":
            continue
        impact = ev.get("impact", "Low")
        if impact not in ("High", "Medium"):
            continue
        try:
            ev_dt = dt.fromisoformat(
                ev["date"]
                .replace("Z", "+00:00")
                .replace("-04:00", "-0400")
                .replace("-05:00", "-0500")
            )
            ev_dt_local = ev_dt.astimezone(MYT) if ev_dt.tzinfo else ev_dt
        except Exception:
            ev_dt_local = None

        # Show upcoming + events from last 4 hours (may have actuals)
        if ev_dt_local:
            diff_hours = (ev_dt_local.replace(tzinfo=None) - now).total_seconds() / 3600
            if diff_hours < -4:
                continue

        events.append(
            {
                "datetime": ev_dt_local.isoformat() if ev_dt_local else None,
                "date": ev_dt_local.strftime("%a %b %d") if ev_dt_local else "",
                "time": ev_dt_local.strftime("%H:%M") if ev_dt_local else "",
                "currency": "USD",
                "impact": impact.lower(),
                "event": ev.get("title", ""),
                "actual": ev.get("actual", "") or "—",
                "forecast": ev.get("forecast", "") or "—",
                "previous": ev.get("previous", "") or "—",
            }
        )

    # Sort by datetime
    events.sort(key=lambda x: x.get("datetime") or "")

    result = {
        "events": events[:20],
        "count": len(events),
        "source": "forexfactory.com",
        "next_event": events[0] if events else None,
        "timestamp": datetime.now(MYT).isoformat(),
    }
    _write_cache(cache, result)
    return result


def cmd_snapshot(args):
    """Return raw ticker data — server wraps with schema/asset/coherence_id."""
    return cmd_ticker(args)


# ── Forecast Engine (wealth.forecast.v1) ─────────────────────────
# The organ does not prophesy. It publishes an ATR-scaled drift cone,
# a scenario ladder with falsification levels, and an epistemic tag.
# Every fresh forecast is appended to a local hash-chained log for
# T+N outcome scoring. Sealing to VAULT999 is arifOS's lane, not ours.
FORECAST_LOG = Path("/root/WEALTH/data/forecast_log.jsonl")

_INSTITUTIONAL_CONTEXT = {
    "gold": "Gold bid + soft DXY = monetary-hedge demand; XAU/MYR moderated by ringgit. Pressures no sovereign tripwire directly.",
    "oil": "Brent feeds the PETRONAS fiscal chain (CFFO, dividend, O&G revenue share). Sustained drift toward TRIP 70 pressures the sovereign BODY score.",
    "gas": "LNG/JKM complex feeds PETRONAS gas revenue and Bintulu utilization. Volatility here propagates to the same fiscal chain as Brent.",
}


def _lin_slope(values) -> float:
    """Least-squares slope of a 1-D series, in units-per-step."""
    ys = np.asarray(values, dtype=float)
    n = len(ys)
    if n < 2:
        return 0.0
    xs = np.arange(n, dtype=float)
    denom = float(((xs - xs.mean()) ** 2).sum())
    if denom == 0.0:
        return 0.0
    return float(((xs - xs.mean()) * (ys - ys.mean())).sum() / denom)


def _forecast_log_append(record: dict) -> None:
    """Append forecast to local hash-chained log. Never breaks the endpoint."""
    try:
        FORECAST_LOG.parent.mkdir(parents=True, exist_ok=True)
        prev_hash = ""
        if FORECAST_LOG.exists():
            with FORECAST_LOG.open("r") as f:
                lines = [l for l in f.read().strip().splitlines() if l.strip()]
            if lines:
                prev_hash = json.loads(lines[-1]).get("hash", "")
        body = dict(record)
        body["prev_hash"] = prev_hash
        digest = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()
        body["hash"] = digest
        with FORECAST_LOG.open("a") as f:
            f.write(json.dumps(body, sort_keys=True, default=str) + "\n")
    except Exception:
        pass


def cmd_forecast(args):
    horizon = int(args.get("horizon", 30))
    if horizon not in (30, 60, 90):
        horizon = 30
    cache = _cache_key("forecast", horizon=horizon)
    cached = _read_cache(cache)
    if cached:
        return cached

    df = fetch_ohlcv(interval="1d", period="1y")
    close = df["close"]
    atr_val = round(float(compute_atr(df, 14).iloc[-1]), 2)
    ema20_val = round(float(compute_ema(close, 20).iloc[-1]), 2)
    ema50_val = round(float(compute_ema(close, 50).iloc[-1]), 2)
    ema200_val = round(float(compute_ema(close, 200).iloc[-1]), 2)
    rsi_val = round(float(compute_rsi(close, 14).iloc[-1]), 1)
    price = round(float(close.iloc[-1]), 2)

    # 1. Drift — regression slope of last 20 daily closes, ATR-clamped
    slope = _lin_slope(close.tail(20).values)
    slope = max(-atr_val, min(atr_val, slope))
    slope = round(slope, 4)

    # 2. Regime — matches the Technical Forge definition
    trending = abs(ema20_val - ema50_val) > 0.5 * atr_val
    if trending:
        regime = "TRENDING_UP" if ema20_val > ema50_val else "TRENDING_DOWN"
    else:
        regime = "SIDEWAYS"

    # 3. Cone — p50 drifts, blends toward EMA200; bands are ATR·√t
    blend_w = 0.2 if trending else 0.5
    last_date = df.index[-1].date()
    t_dates, p10, p25, p50, p75, p90 = [], [], [], [], [], []
    for t in range(1, horizon + 1):
        mid = price + slope * t
        mid += (ema200_val - mid) * (1 - np.exp(-t / 20)) * blend_w
        sigma = atr_val * np.sqrt(t)
        t_dates.append((last_date + timedelta(days=t)).isoformat())
        p10.append(round(mid - 1.282 * sigma, 2))
        p25.append(round(mid - 0.674 * sigma, 2))
        p50.append(round(mid, 2))
        p75.append(round(mid + 0.674 * sigma, 2))
        p90.append(round(mid + 1.282 * sigma, 2))

    # 4. Scenario ladder from daily swing S/R — falsification on its face
    sr = find_support_resistance(df)
    r1 = sr["resistance"][0] if sr["resistance"] else round(price + atr_val, 2)
    r2 = sr["resistance"][1] if len(sr["resistance"]) > 1 else round(r1 + 2 * atr_val, 2)
    s1 = sr["support"][0] if sr["support"] else round(price - atr_val, 2)
    s2 = sr["support"][1] if len(sr["support"]) > 1 else round(s1 - 2 * atr_val, 2)
    rate = max(abs(slope), 0.25 * atr_val)

    def _eta(target):
        d = abs(target - price) / rate
        return f"{max(1, int(d * 0.6))}–{max(2, int(d * 1.4))}"

    long_conf = sum([
        ema20_val > ema50_val,
        rsi_val > 55,
        regime == "TRENDING_UP",
        slope > 0,
        price > ema200_val,
    ])
    short_conf = sum([
        ema20_val < ema50_val,
        rsi_val < 45,
        regime == "TRENDING_DOWN",
        slope < 0,
        price < ema200_val,
    ])
    scenarios = [
        {"side": "LONG", "trigger": f"daily close > {r1} (R1)", "objective": r2,
         "invalidation": s1, "confluence": long_conf, "of": 5, "eta_days": _eta(r2)},
        {"side": "SHORT", "trigger": f"daily close < {s1} (S1)", "objective": s2,
         "invalidation": r1, "confluence": short_conf, "of": 5, "eta_days": _eta(s2)},
    ]

    # 5. Bias — one engine, one voice. Derived, never hardcoded.
    if long_conf >= 3 and long_conf > short_conf:
        bias = "BULLISH"
    elif short_conf >= 3 and short_conf > long_conf:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    side200 = "above" if price > ema200_val else "below"
    institutional_read = (
        f"{regime} regime · price {side200} EMA200 ({ema200_val}) · RSI {rsi_val} · ATR {atr_val}. "
        + _INSTITUTIONAL_CONTEXT.get(ASSET_KEY, "")
    ).strip()

    generated_at = datetime.now(MYT).isoformat()
    result = {
        "schema": "wealth.forecast.v1",
        "asset": ASSET_KEY,
        "generated_at": generated_at,
        "horizon_days": horizon,
        "basis": {"close": price, "atr14": atr_val, "slope_per_day": slope,
                  "regime": regime, "rsi": rsi_val,
                  "ema20": ema20_val, "ema50": ema50_val, "ema200": ema200_val},
        "bias": bias,
        "cone": {"t": t_dates, "p10": p10, "p25": p25, "p50": p50, "p75": p75, "p90": p90},
        "scenarios": scenarios,
        "institutional_read": institutional_read,
        "epistemic": "INTERPRET — ATR-scaled drift cone, not prophecy. Falsification levels stated. Human decides.",
    }
    _write_cache(cache, result)
    _forecast_log_append({
        "schema": "wealth.forecastlog.v1", "asset": ASSET_KEY,
        "generated_at": generated_at, "horizon_days": horizon, "close": price,
        "bias": bias, "p50_end": p50[-1], "p10_end": p10[-1], "p90_end": p90[-1],
        "long_objective": r2, "short_objective": s2,
        "long_confluence": long_conf, "short_confluence": short_conf,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description="XNATGAS Natural Gas Data Fetcher")
    parser.add_argument(
        "command",
        choices=[
            "ticker",
            "history",
            "signals",
            "levels",
            "macro",
            "apex",
            "signal_v2",
            "calendar",
            "snapshot",
        "forecast",
        ],
    )
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--period", default="30d")
    parser.add_argument("--horizon", type=int, default=30)
    args = parser.parse_args()

    handlers = {
        "ticker": cmd_ticker,
        "history": cmd_history,
        "signals": cmd_signals,
        "levels": cmd_levels,
        "macro": cmd_macro,
        "apex": cmd_apex,
        "signal_v2": cmd_signal_v2,
        "calendar": cmd_calendar,
        "snapshot": cmd_snapshot,
          "forecast": cmd_forecast,
    }

    try:
        result = handlers[args.command](
            {
            "interval": args.interval,
            "period": args.period,
            "horizon": args.horizon,
        }
        )
        print(json.dumps(result, default=str, indent=2))
    except Exception as e:
        # Stale fallback: serve expired cache rather than VOID the panel
        if args.command == "history":
            stale_key = _cache_key("history", interval=args.interval, period=args.period)
        elif args.command in ("ticker", "snapshot"):
            stale_key = _cache_key("ticker")
        else:
            stale_key = _cache_key(args.command)
        stale = _read_stale(stale_key)
        if stale is not None:
            print(json.dumps(stale, default=str, indent=2))
            sys.exit(0)
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
