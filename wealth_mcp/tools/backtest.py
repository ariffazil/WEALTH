"""
WEALTH capital_backtest — Strategy backtest runner — Extracted from canonical.py (Phase 1a).
"""

from __future__ import annotations
from typing import Any

from wealth_contracts.envelope import WEALTH_OUTPUT_SCHEMA, wrap_result
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality
from wealth_mcp.tools.types import CoercedDict


def register_backtest(mcp):
    """Register the backtest tool on the given FastMCP instance."""
    # 10. capital_backtest — Strategy backtest runner (FORGED 2026-08-09)
    # ═══════════════════════════════════════════════════════════════════

    @mcp.tool(
        name="capital_backtest",
        output_schema=WEALTH_OUTPUT_SCHEMA,
        description=(
            "Run strategy backtest on XAUUSD using the proven indicator fusion "
            "(EMA alignment + ATR-scaled stops + RSI pullback filter + S/R zones). "
            "Wraps the v2 backtest engine. Returns win rate, profit factor, Sharpe, "
            "max drawdown, and trade log. SIDE EFFECT: writes a vault receipt."
        ),
        tags={"domain": "market", "kind": "deductive", "canonical": "v1"},
    )
    async def capital_backtest(
        symbol: str = "GC=F",
        interval: str = "1h",
        lookback: str = "2y",
        initial_capital: float = 10000.0,
        risk_per_trade_pct: float = 1.0,
        mode: str = "backtest",
        payload: CoercedDict = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        actor_id: str | None = None,
    ) -> dict:
        import sys, os, json as _json, datetime as _dt

        # Add trading path for imports
        _trading_path = "/root/WEALTH/trading"
        if _trading_path not in sys.path:
            sys.path.insert(0, _trading_path)

        _wealth_root = "/root/WEALTH"
        if _wealth_root not in sys.path:
            sys.path.insert(0, _wealth_root)

        m = str(mode).lower()
        p: dict[str, Any] = dict(payload or {})

        # ═══ COMPASS — TradeMaster PRUDEX-Compass distillation (2026-08-18) ═══
        if m == "compass":
            from wealth_core.compass import compute_compass

            equity_curve = p.get("equity_curve") or []
            trade_returns = p.get("trade_returns") or []
            benchmark_returns = p.get("benchmark_returns")
            regime_labels = p.get("regime_labels")
            risk_free_rate = float(p.get("risk_free_rate", 0.0))
            periods_per_year = float(p.get("periods_per_year", 252.0))

            if not equity_curve or not trade_returns:
                return wrap_result(
                    tool_name="capital_backtest",
                    domain="evaluation",
                    result={
                        "status": "ERROR",
                        "error_code": "MISSING_DATA",
                        "message": "compass requires payload.equity_curve and payload.trade_returns",
                    },
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    session_id=session_id,
                    actor_id=actor_id,
                )

            compass = compute_compass(
                equity_curve,
                trade_returns,
                benchmark_returns,
                regime_labels,
                risk_free_rate,
                periods_per_year,
            )
            return wrap_result(
                tool_name="capital_backtest",
                domain="evaluation",
                result={
                    "axes": compass.axes,
                    "overall_score": compass.overall_score,
                    "classification": compass.prudef_label,
                    "regime_performance": compass.regime_performance,
                    "recommendations": compass.recommendations,
                    "framework": "PRUDEX-Compass (TradeMaster distillation)",
                },
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=[
                    "prudex_compass_engine",
                    "trademaster_distillation",
                ],
                session_id=session_id,
                actor_id=actor_id,
            )

        # ═══ STRESS TEST — TradeMaster Market-GAN distillation (2026-08-18) ═══
        if m == "stress_test":
            from wealth_core.stress_test import run_stress_test

            equity_curve = p.get("equity_curve") or []
            trade_returns = p.get("trade_returns") or []
            scenarios_config = p.get("scenarios")
            seed = p.get("seed")

            if not equity_curve or not trade_returns:
                return wrap_result(
                    tool_name="capital_backtest",
                    domain="evaluation",
                    result={
                        "status": "ERROR",
                        "error_code": "MISSING_DATA",
                        "message": "stress_test requires payload.equity_curve and payload.trade_returns",
                    },
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    session_id=session_id,
                    actor_id=actor_id,
                )

            stress = run_stress_test(
                equity_curve, trade_returns, scenarios_config, seed
            )
            return wrap_result(
                tool_name="capital_backtest",
                domain="evaluation",
                result={
                    "baseline": stress.baseline,
                    "scenarios": stress.scenarios,
                    "worst_case": stress.worst_case,
                    "robustness_score": stress.robustness_score,
                    "scenarios_tested": stress.scenarios_tested,
                    "scenarios_survived": stress.scenarios_survived,
                    "recommendations": stress.recommendations,
                    "framework": "Synthetic Adversarial Reality (TradeMaster distillation)",
                },
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["stress_test_engine", "trademaster_distillation"],
                session_id=session_id,
                actor_id=actor_id,
            )

        # ═══ ENSEMBLE — TradeMaster AlphaMix+ distillation (2026-08-18) ═══
        if m == "ensemble":
            import yfinance as yf
            from wealth_core.ensemble import compute_ensemble

            sym = symbol.upper()
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period=lookback, interval=interval)
            except Exception as e:
                return wrap_result(
                    tool_name="capital_backtest",
                    domain="market",
                    result={
                        "status": "ERROR",
                        "error_code": "FETCH_FAILED",
                        "message": str(e)[:200],
                    },
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    session_id=session_id,
                    actor_id=actor_id,
                )

            if hist.empty:
                return wrap_result(
                    tool_name="capital_backtest",
                    domain="market",
                    result={
                        "status": "ERROR",
                        "error_code": "NO_DATA",
                        "message": f"No data for {sym}",
                    },
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    session_id=session_id,
                    actor_id=actor_id,
                )

            closes = [float(r["Close"]) for _, r in hist.iterrows()]
            highs = [float(r["High"]) for _, r in hist.iterrows()]
            lows = [float(r["Low"]) for _, r in hist.iterrows()]

            ensemble = compute_ensemble(closes, highs, lows)
            return wrap_result(
                tool_name="capital_backtest",
                domain="evaluation",
                result={
                    "strategies_tested": ensemble.strategies_tested,
                    "regimes_detected": ensemble.regimes_detected,
                    "regime_strategy_map": ensemble.regime_strategy_map,
                    "strategy_performances": ensemble.strategy_performances,
                    "ensemble_metrics": ensemble.ensemble_metrics,
                    "baseline_metrics": ensemble.baseline_metrics,
                    "improvement": ensemble.improvement,
                    "recommendations": ensemble.recommendations,
                    "framework": "AlphaMix+ Ensemble (TradeMaster distillation)",
                },
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.MODERATE,
                source_attribution=["ensemble_engine", "trademaster_distillation"],
                session_id=session_id,
                actor_id=actor_id,
            )

        try:
            import yfinance as yf

            sym = symbol.upper()
            ticker = yf.Ticker(sym)
            hist = ticker.history(period=lookback, interval=interval)
            if hist.empty:
                return wrap_result(
                    tool_name="capital_backtest",
                    domain="market",
                    result={
                        "status": "ERROR",
                        "error_code": "NO_DATA",
                        "message": f"No data for {sym} at {interval}",
                    },
                    epistemic_tag=EpistemicTag.ASSUMED,
                    evidence_quality=EvidenceQuality.MISSING,
                    session_id=session_id,
                    actor_id=actor_id,
                )

            # Convert to OHLCV list for the backtest engine
            from signals.scanner import OHLCV as _OHLCV

            candles = []
            for idx, row in hist.iterrows():
                candles.append(
                    _OHLCV(
                        timestamp=idx,
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=float(row.get("Volume", 0)),
                    )
                )

            # Configure and run backtest
            from backtest.engine_v2 import BacktestConfig, run_backtest

            cfg = BacktestConfig()
            cfg.initial_equity = float(initial_capital)
            cfg.risk_per_trade = float(risk_per_trade_pct) / 100.0
            cfg.symbol = sym

            bt_result = run_backtest(candles, cfg)

            # Extract key metrics
            metrics = bt_result.get("metrics", {})
            trades = bt_result.get("trades", [])

            summary = {
                "symbol": sym,
                "interval": interval,
                "lookback": lookback,
                "data_points": len(candles),
                "date_range": {
                    "from": str(candles[0].timestamp)[:19] if candles else None,
                    "to": str(candles[-1].timestamp)[:19] if candles else None,
                },
                "initial_capital": float(initial_capital),
                "final_equity": round(float(metrics.get("final_equity", 0)), 2),
                "total_return_pct": round(float(metrics.get("total_return_pct", 0)), 2),
                "total_trades": int(metrics.get("total_trades", 0)),
                "win_rate_pct": round(float(metrics.get("win_rate_pct", 0)), 1),
                "profit_factor": round(float(metrics.get("profit_factor", 0)), 2),
                "sharpe_ratio": round(float(metrics.get("sharpe_ratio", 0)), 2),
                "max_drawdown_pct": round(float(metrics.get("max_drawdown_pct", 0)), 2),
                "avg_win": round(float(metrics.get("avg_win", 0)), 2),
                "avg_loss": round(float(metrics.get("avg_loss", 0)), 2),
                "last_5_trades": [
                    {
                        "entry": t.get("entry_price"),
                        "exit": t.get("exit_price"),
                        "direction": t.get("direction"),
                        "pnl": t.get("pnl"),
                        "exit_reason": t.get("exit_reason", ""),
                    }
                    for t in trades[-5:]
                ],
            }

            return wrap_result(
                tool_name="capital_backtest",
                domain="market",
                result=summary,
                epistemic_tag=EpistemicTag.DERIVED,
                evidence_quality=EvidenceQuality.OBSERVED,
                source_attribution=[f"yfinance:{sym}", "engine_v2"],
                session_id=session_id,
                actor_id=actor_id,
            )

        except ImportError as e:
            import traceback as _tb
            return wrap_result(
                tool_name="capital_backtest",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "IMPORT_FAILED",
                    "message": f"Trading engine import failed: {e}",
                    "traceback": _tb.format_exc(),
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )
        except Exception as e:
            return wrap_result(
                tool_name="capital_backtest",
                domain="market",
                result={
                    "status": "ERROR",
                    "error_code": "BACKTEST_FAILED",
                    "message": str(e)[:300],
                },
                epistemic_tag=EpistemicTag.ASSUMED,
                evidence_quality=EvidenceQuality.MISSING,
                session_id=session_id,
                actor_id=actor_id,
            )

