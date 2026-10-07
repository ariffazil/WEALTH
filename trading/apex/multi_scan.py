#!/usr/bin/env python3
"""Multi-instrument scanner CLI.

Scans all 5 instruments (XAUUSD/OIL/GAS/KLCI/USMYR) via yfinance, computes
indicators + market state, and emits JSON + human-readable summary.

Per CHRON×WEALTH×HERMES synthesis 2026-09-18 — closes gap "KLCI + GAS not in
trading scanner".

Usage:
  python3 multi_scan.py                      # scan all 5, default 30d
  python3 multi_scan.py --instruments XAUUSD,KLCI
  python3 multi_scan.py --lookback 90d
  python3 multi_scan.py --quiet              # JSON only

Output:
  stdout: human-readable summary by default
  /root/WEALTH/trading/cron/multi_scan_latest.json: full result

DITEMPA BUKAN DIBERI ⚒️
"""

from __future__ import annotations

import json
import sys
import argparse
import pandas as pd
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

# Make sibling modules importable. Use trading.* absolute path so the
# script works regardless of invocation (direct, -m, etc).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # /root/WEALTH

from trading.core.models import OHLCV
from trading.core.instruments import (
    INSTRUMENTS,
    get,
    all_symbols,
    InstrumentConfig,
    VolatilityClass,
)
from trading.apex.scanner import compute_indicators
from trading.apex.regime import compute_market_state, MarketState, Regime

import yfinance as yf

DEFAULT_OUTPUT = Path("/root/WEALTH/trading/cron/multi_scan_latest.json")


def _fetch_candles(cfg: InstrumentConfig, lookback_days: int) -> list[OHLCV]:
    """Fetch daily OHLCV via yfinance. Handles pandas 3.0 MultiIndex columns."""
    from datetime import timedelta as _td

    end = datetime.now(timezone.utc).date()
    start = end - _td(days=lookback_days)
    df = yf.download(
        cfg.yfinance_ticker,
        start=start.isoformat(),
        end=(end + _td(days=1)).isoformat(),
        progress=False,
        auto_adjust=True,
    )
    if df is None or df.empty:
        return []

    cols = df.columns
    is_multi = isinstance(cols, pd.MultiIndex)
    t = cfg.yfinance_ticker

    def get_close(row):
        return float(row[("Close", t)] if is_multi else row["Close"])

    def get_open(row):
        return float(row[("Open", t)] if is_multi else row["Open"])

    def get_high(row):
        return float(row[("High", t)] if is_multi else row["High"])

    def get_low(row):
        return float(row[("Low", t)] if is_multi else row["Low"])

    def get_volume(row):
        try:
            return float(row[("Volume", t)] if is_multi else row["Volume"])
        except (KeyError, ValueError):
            return 0.0

    candles = []
    for idx, row in df.iterrows():
        ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        candles.append(
            OHLCV(
                timestamp=ts,
                open=get_open(row),
                high=get_high(row),
                low=get_low(row),
                close=get_close(row),
                volume=get_volume(row),
                timeframe="D1",
            )
        )
    return candles


class _ScanConfig:
    """Adapter from InstrumentConfig to scanner.compute_indicators cfg."""

    def __init__(self, ic: InstrumentConfig):
        self.ema_fast = ic.ema_fast
        self.ema_mid = ic.ema_mid
        self.ema_slow = ic.ema_slow
        self.atr_period = ic.atr_period
        self.rsi_period = ic.rsi_period
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.sr_lookback = 50
        self.bb_period = 20


def scan_one(symbol: str, lookback_days: int) -> dict:
    """Scan a single instrument. Returns dict with instrument/indicators/regime/stops."""
    cfg = get(symbol)
    candles = _fetch_candles(cfg, lookback_days)

    if not candles or len(candles) < 50:
        return {
            "instrument": symbol,
            "status": "INSUFFICIENT_DATA",
            "candles": len(candles),
            "min_required": 50,
        }

    scan_cfg = _ScanConfig(cfg)
    indicators = compute_indicators(candles, scan_cfg)
    market_state: MarketState = compute_market_state(
        candles,
        ema_20=indicators.ema_20,
        ema_50=indicators.ema_50,
        ema_200=indicators.ema_200,
        rsi=indicators.rsi_14,
    )

    # ATR-based stop loss + take profit (synthesis: zone retest + macro)
    atr_val = indicators.atr_14
    atr_stop_distance = atr_val * cfg.atr_stop_multiplier
    if market_state.buy_zone:
        suggested_entry = market_state.buy_zone.price
        suggested_stop = round(suggested_entry - atr_stop_distance, cfg.decimal_places)
        suggested_target = round(
            suggested_entry + atr_stop_distance * 2, cfg.decimal_places
        )
    else:
        suggested_entry = market_state.price
        suggested_stop = round(suggested_entry - atr_stop_distance, cfg.decimal_places)
        suggested_target = round(
            suggested_entry + atr_stop_distance * 2, cfg.decimal_places
        )

    return {
        "instrument": symbol,
        "status": "OK",
        "config": {
            "yfinance_ticker": cfg.yfinance_ticker,
            "instrument_class": cfg.instrument_class.value,
            "volatility_class": cfg.volatility_class.value,
            "session": cfg.session.value,
            "atr_stop_multiplier": cfg.atr_stop_multiplier,
            "decimal_places": cfg.decimal_places,
        },
        "indicators": {
            "timestamp": indicators.timestamp.isoformat(),
            "close": round(
                indicators.timestamp and candles[-1].close, cfg.decimal_places
            ),
            "ema_20": round(indicators.ema_20, cfg.decimal_places),
            "ema_50": round(indicators.ema_50, cfg.decimal_places),
            "ema_200": round(indicators.ema_200, cfg.decimal_places),
            "rsi_14": round(indicators.rsi_14, 1),
            "macd_line": round(indicators.macd_line, 4),
            "macd_signal": round(indicators.macd_signal, 4),
            "macd_histogram": round(indicators.macd_histogram, 4),
            "atr_14": round(indicators.atr_14, cfg.decimal_places),
            "support": round(indicators.support, cfg.decimal_places),
            "resistance": round(indicators.resistance, cfg.decimal_places),
            "bb_upper": round(indicators.bb_upper, cfg.decimal_places),
            "bb_mid": round(indicators.bb_mid, cfg.decimal_places),
            "bb_lower": round(indicators.bb_lower, cfg.decimal_places),
            "psar": round(indicators.psar, cfg.decimal_places),
            "psar_trend": indicators.psar_trend,
            "pivot": round(indicators.pivot, cfg.decimal_places),
            "trend": indicators.trend.value,
        },
        "regime": {
            "regime": market_state.regime.value,
            "regime_confidence": market_state.regime_confidence,
            "description": market_state.description,
            "buy_zone": (
                {
                    "price": market_state.buy_zone.price,
                    "strength": market_state.buy_zone.strength,
                    "type": market_state.buy_zone.zone_type,
                }
                if market_state.buy_zone
                else None
            ),
            "sell_zone": (
                {
                    "price": market_state.sell_zone.price,
                    "strength": market_state.sell_zone.strength,
                    "type": market_state.sell_zone.zone_type,
                }
                if market_state.sell_zone
                else None
            ),
            "last_swing_high": round(market_state.last_swing_high, cfg.decimal_places),
            "last_swing_low": round(market_state.last_swing_low, cfg.decimal_places),
        },
        "trade_plan": {
            "suggested_entry": suggested_entry,
            "suggested_stop": suggested_stop,
            "suggested_target": suggested_target,
            "atr_used": round(atr_val, cfg.decimal_places),
            "stop_distance": round(atr_stop_distance, cfg.decimal_places),
            "rr_ratio": 2.0,  # target is 2× stop
        },
    }


def scan_all(instruments: list[str], lookback_days: int) -> dict:
    """Scan all requested instruments. Returns dict with per-instrument + meta."""
    results = {}
    errors = {}
    for sym in instruments:
        try:
            r = scan_one(sym, lookback_days)
            if r.get("status") == "OK":
                results[sym] = r
            else:
                errors[sym] = r
        except Exception as e:
            errors[sym] = {"instrument": sym, "status": "ERROR", "error": str(e)}
    return {
        "schema": "multi_scan_v1",
        "version": "1.0.0",
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "lookback_days": lookback_days,
        "instruments_requested": instruments,
        "results": results,
        "errors": errors,
        "summary": {
            "total_requested": len(instruments),
            "scanned_ok": len(results),
            "errors": len(errors),
        },
    }


def print_human(result: dict, quiet: bool = False) -> None:
    if quiet:
        return
    print(
        f"Multi-instrument scan — {result['scanned_at'][:19]} UTC — {result['lookback_days']}d lookback"
    )
    print(
        f"  Scanned: {result['summary']['scanned_ok']}/{result['summary']['total_requested']} OK, {result['summary']['errors']} errors"
    )
    print()
    for sym, r in result["results"].items():
        ind = r["indicators"]
        reg = r["regime"]
        plan = r["trade_plan"]
        cfg = r["config"]
        print(
            f"  {sym:6} ({cfg['yfinance_ticker']:7}) | close={ind['close']:>9.{cfg['decimal_places']}f}  RSI={ind['rsi_14']:>5.1f}  ATR={ind['atr_14']:>7.{cfg['decimal_places']}f}"
        )
        print(
            f"          trend={ind['trend']:<5} regime={reg['regime']:<10} conf={reg['regime_confidence']:.2f}  volatility={cfg['volatility_class']}"
        )
        if reg["buy_zone"]:
            bz = reg["buy_zone"]
            print(
                f"          buy_zone:  ${bz['price']:.{cfg['decimal_places']}f} (strength={bz['strength']})"
            )
        if reg["sell_zone"]:
            sz = reg["sell_zone"]
            print(
                f"          sell_zone: ${sz['price']:.{cfg['decimal_places']}f} (strength={sz['strength']})"
            )
        print(
            f"          plan: entry=${plan['suggested_entry']:.{cfg['decimal_places']}f} stop=${plan['suggested_stop']:.{cfg['decimal_places']}f} target=${plan['suggested_target']:.{cfg['decimal_places']}f} (RR 1:2)"
        )
        print()
    if result["errors"]:
        print("Errors:")
        for sym, e in result["errors"].items():
            print(f"  {sym}: {e.get('error', e.get('status', '?'))}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Multi-instrument scanner (5 instruments)")
    ap.add_argument(
        "--instruments",
        type=str,
        default=None,
        help=f"Comma-separated symbols. Default: all ({','.join(all_symbols())})",
    )
    ap.add_argument(
        "--lookback",
        type=int,
        default=365,
        help="Days of history (default 365 — covers EMA 200). Min 250.",
    )
    ap.add_argument(
        "--output", type=str, default=str(DEFAULT_OUTPUT), help="JSON output path"
    )
    ap.add_argument(
        "--quiet", action="store_true", help="JSON output only (no human summary)"
    )
    args = ap.parse_args()

    if args.instruments:
        instruments = [s.strip().upper() for s in args.instruments.split(",")]
    else:
        instruments = all_symbols()

    result = scan_all(instruments, args.lookback)

    # Write JSON
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str))

    print_human(result, quiet=args.quiet)
    print(f"JSON: {out_path}")

    return 0 if result["summary"]["scanned_ok"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
