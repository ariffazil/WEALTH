"""
System configuration — single source of truth for trading parameters.
All values overridable via environment variables.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TradingConfig:
    """Master configuration for the trading intelligence system."""

    # ── Instrument ──
    symbol: str = "XAUUSD"
    point_value: float = 0.01  # minimum price movement
    pip_value: float = 1.0  # $1 per pip per standard lot for gold
    contract_multiplier: float = 1.0  # contract multiplier for position sizing

    # ── Timeframes ──
    primary_tf: str = "H1"
    confirmation_tf: str = "M15"
    trend_tf: str = "D1"

    # ── Technical Analysis ──
    ema_fast: int = 20
    ema_mid: int = 50
    ema_slow: int = 200
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    atr_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # ── Risk Management ──
    max_risk_per_trade_pct: float = 1.0  # % of equity per trade
    max_daily_loss_pct: float = 3.0  # daily drawdown limit
    max_drawdown_pct: float = 10.0  # max total drawdown
    max_open_positions: int = 3
    min_rr_ratio: float = 2.0  # minimum reward:risk
    kelly_fraction: float = 0.25  # quarter-Kelly (conservative)

    # ── Signal Engine ──
    min_confluence_score: float = 0.6  # minimum to generate signal
    min_confidence: float = 0.55  # minimum confidence to act
    lookback_bars: int = 100  # bars for analysis
    sr_lookback: int = 50  # S/R detection lookback

    # ── Governance ──
    arifos_port: int = 8088
    require_judge: bool = True  # always require arif_judge before execute
    auto_execute: bool = False  # manual confirmation by default
    blast_radius_default: str = "MEDIUM"

    # ── Alerts ──
    telegram_enabled: bool = True
    voice_alerts: bool = True
    voice_language: str = "ms-MY"
    voice_name: str = "ms-MY-OsmanNeural"

    # ── Data ──
    data_dir: str = "/root/trading/data"
    log_dir: str = "/root/trading/logs"
    mt5_enabled: bool = False  # set True when MT5 connection configured
    mt5_login: int = 0
    mt5_server: str = ""
    mt5_password: str = ""  # loaded from env

    # ── Syed Profile ──
    syed_mode: bool = True  # simplified output for Syed
    syed_max_lot: float = 0.10  # max lot size Syed should use
    syed_balance_estimate: float = 500.0  # USD estimated balance

    @classmethod
    def from_env(cls) -> "TradingConfig":
        """Load config from environment with sensible defaults."""
        return cls(
            mt5_enabled=os.getenv("MT5_ENABLED", "false").lower() == "true",
            mt5_login=int(os.getenv("MT5_LOGIN", "0")),
            mt5_server=os.getenv("MT5_SERVER", ""),
            mt5_password=os.getenv("MT5_PASSWORD", ""),
            syed_balance_estimate=float(os.getenv("SYED_BALANCE", "500")),
        )


# Singleton
_config: TradingConfig | None = None


def get_config() -> TradingConfig:
    global _config
    if _config is None:
        _config = TradingConfig.from_env()
    return _config
