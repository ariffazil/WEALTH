"""
Trading Intelligence System — Main Orchestrator.
SCANNER → SIGNAL → RISK → JUDGE → EXECUTE → TRACK → ALERT

Usage:
    python -m trading.main scan          # scan only, output signal
    python -m trading.main scan --json   # scan, output JSON
    python -m trading.main alert         # scan + generate alert text
    python -m trading.main status        # risk state + positions
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Optional

from .core.config import get_config, TradingConfig
from .core.models import OHLCV, Signal, Direction, Verdict, Position
from .signals.engine_v2 import generate_signal_v2 as generate_signal
from .signals.scanner import compute_indicators
from .risk.manager import RiskManager
from .risk.position_sizer import compute_position_size
from .governance.gate import GovernanceGate


class TradingSystem:
    """
    Main trading intelligence orchestrator.
    Wires together all components: scanner → signal → risk → judge → alert.
    """

    def __init__(self, cfg: Optional[TradingConfig] = None):
        self.cfg = cfg or get_config()
        self.risk_mgr = RiskManager(self.cfg)
        self.gate = GovernanceGate(require_arifos=self.cfg.require_judge)
        self._last_signal: Optional[Signal] = None

    def process_candles(self, candles: list[OHLCV]) -> Signal:
        """
        Full pipeline: candles → signal with sizing and governance.
        """
        # 1. Generate signal from technical analysis
        signal = generate_signal(candles, self.cfg)

        # 2. Compute position sizing
        risk_state = self.risk_mgr.get_state(self.cfg.syed_balance_estimate)
        lots, risk_amount = compute_position_size(signal, risk_state, self.cfg)
        signal.suggested_lot = lots
        signal.risk_amount = risk_amount

        # 3. Governance gate
        signal = self.gate.evaluate(signal)

        # 4. Additional risk gate
        if signal.verdict == Verdict.PROCEED:
            can_open, reason = self.risk_mgr.can_open_position(
                signal.direction, self.cfg.syed_balance_estimate
            )
            if not can_open:
                signal.verdict = Verdict.HOLD
                signal.judge_reason = f"Risk gate: {reason}"

        self._last_signal = signal
        return signal

    def get_alert(self, syed_mode: bool = True) -> str:
        """Get human-readable alert for the last signal."""
        if self._last_signal is None:
            return "No signal generated yet. Run scan first."
        return self._last_signal.to_alert_text(syed_mode)

    def get_status(self) -> dict:
        """Get system status."""
        risk_state = self.risk_mgr.get_state(self.cfg.syed_balance_estimate)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "symbol": self.cfg.symbol,
                "timeframe": self.cfg.primary_tf,
                "max_risk_pct": self.cfg.max_risk_per_trade_pct,
                "max_daily_loss_pct": self.cfg.max_daily_loss_pct,
                "min_rr_ratio": self.cfg.min_rr_ratio,
                "syed_mode": self.cfg.syed_mode,
            },
            "risk": {
                "equity": risk_state.equity,
                "daily_pnl": risk_state.daily_pnl,
                "daily_pnl_pct": risk_state.daily_pnl_pct,
                "drawdown_pct": risk_state.current_drawdown_pct,
                "open_positions": risk_state.open_positions,
                "can_trade": risk_state.can_trade,
                "block_reason": risk_state.block_reason,
            },
            "last_signal": self._last_signal.to_dict() if self._last_signal else None,
            "governance_log": self.gate.log[-5:] if self.gate.log else [],
        }


def generate_sample_candles(n: int = 100, base_price: float = 4040.0) -> list[OHLCV]:
    """Generate sample OHLCV data for testing. NOT for production."""
    import random
    random.seed(42)
    candles = []
    price = base_price
    now = datetime.now(timezone.utc)
    for i in range(n):
        delta = random.uniform(-8, 8)
        o = price
        h = price + abs(random.uniform(0, 5))
        l = price - abs(random.uniform(0, 5))
        c = price + delta
        if c > h:
            h = c + random.uniform(0, 2)
        if c < l:
            l = c - random.uniform(0, 2)
        from datetime import timedelta
        ts = now - timedelta(hours=n - i)
        candles.append(OHLCV(
            timestamp=ts,
            open=round(o, 2),
            high=round(h, 2),
            low=round(l, 2),
            close=round(c, 2),
            volume=random.uniform(100, 1000),
        ))
        price = c
    return candles


def main():
    parser = argparse.ArgumentParser(description="arifOS Trading Intelligence System")
    parser.add_argument("command", choices=["scan", "alert", "status", "test"],
                        help="Command to run")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--syed", action="store_true", default=True, help="Syed mode (BM)")
    args = parser.parse_args()

    system = TradingSystem()

    if args.command == "test":
        # Run with sample data to verify pipeline
        candles = generate_sample_candles()
        signal = system.process_candles(candles)
        print("=== TEST RUN (sample data) ===")
        print(f"Signal: {signal.direction.value} | Strength: {signal.strength.value}")
        print(f"Confidence: {signal.confidence:.1%} | Confluence: {signal.confluence_score:.3f}")
        print(f"Entry: {signal.entry_price:.2f} | SL: {signal.stop_loss:.2f}")
        print(f"TP1: {signal.take_profit_1:.2f} | TP2: {signal.take_profit_2:.2f}")
        print(f"RR: 1:{signal.rr_ratio:.1f} | Lot: {signal.suggested_lot:.2f}")
        print(f"Verdict: {signal.verdict.value} — {signal.judge_reason}")
        print(f"\nIndicators:")
        if signal.indicators:
            print(f"  EMA20={signal.indicators.ema_20} | EMA50={signal.indicators.ema_50} | EMA200={signal.indicators.ema_200}")
            print(f"  RSI={signal.indicators.rsi_14} | ATR={signal.indicators.atr_14}")
            print(f"  MACD hist={signal.indicators.macd_histogram}")
            print(f"  Support={signal.indicators.support} | Resistance={signal.indicators.resistance}")
            print(f"  Trend={signal.indicators.trend.value}")
        print(f"\nConfluence Factors:")
        for f in signal.confluence_factors:
            print(f"  [{f.direction.value}] {f.name} (w={f.weight:.2f}, c={f.confidence:.2f}) — {f.detail}")
        return

    if args.command == "status":
        status = system.get_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            r = status["risk"]
            print(f"=== arifOS Trading System Status ===")
            print(f"Equity: ${r['equity']:.2f}")
            print(f"Daily P&L: ${r['daily_pnl']:.2f} ({r['daily_pnl_pct']:.1f}%)")
            print(f"Drawdown: {r['drawdown_pct']:.1f}%")
            print(f"Open positions: {r['open_positions']}")
            print(f"Can trade: {r['can_trade']}")
            if r['block_reason']:
                print(f"Block: {r['block_reason']}")
        return

    if args.command in ("scan", "alert"):
        # Try real data first, fall back to sample
        from .signals.data_feed import fetch_xauusd_yfinance
        candles = fetch_xauusd_yfinance(period="1mo", interval="1h")
        if len(candles) < 200:
            candles = generate_sample_candles(250, base_price=4040)
        signal = system.process_candles(candles)
        if args.json:
            print(json.dumps(signal.to_dict(), indent=2))
        else:
            print(system.get_alert(args.syed))
        return


if __name__ == "__main__":
    main()
