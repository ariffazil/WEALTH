"""
XAUUSD Trading Stack — Quickstart Module
Import this from any agent to get instant access to gold trading.

Usage:
    import sys
    sys.path.insert(0, "/root/trading")
    from quickstart import get_oanda_client, get_gold_price, run_backtest, get_macro_signals
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Trading stack root
TRADING_ROOT = Path("/root/trading")
CONFIG_DIR = TRADING_ROOT / "config"
DATA_DIR = TRADING_ROOT / "data"
STRATEGIES_DIR = TRADING_ROOT / "strategies"
LOGS_DIR = TRADING_ROOT / "logs"

# Ensure dirs exist
for d in [CONFIG_DIR, DATA_DIR, STRATEGIES_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def _load_env():
    """Load OANDA credentials from config/oanda.env"""
    env_path = CONFIG_DIR / "oanda.env"
    if not env_path.exists():
        return {}
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_oanda_client():
    """
    Get authenticated OANDA API client.
    Returns: oandapyV20.API client or None if credentials not set.
    """
    env = _load_env()
    account_id = env.get("OANDA_ACCOUNT_ID", "")
    api_key = env.get("OANDA_API_KEY", "")

    if "YOUR_" in account_id or "YOUR_" in api_key:
        print("OANDA credentials not set. Edit /root/trading/config/oanda.env")
        print("  1. Sign up: https://www.oanda.com/apply/")
        print("  2. API key: https://www.oanda.com/account/tpa/personal_access_token")
        return None

    from oandapyV20 import API
    environment = env.get("OANDA_ENVIRONMENT", "practice")
    return API(access_token=api_key, environment=environment)


def get_oanda_account_id():
    """Get OANDA account ID from config."""
    env = _load_env()
    return env.get("OANDA_ACCOUNT_ID", "")


def get_gold_price(source="yfinance"):
    """
    Get current gold price.
    source: 'yfinance' (free, delayed) or 'oanda' (live, needs credentials)
    Returns: float price in USD/oz or None.
    """
    if source == "oanda":
        client = get_oanda_client()
        if client:
            from oandapyV20.endpoints.pricing import PricingInfo
            account_id = get_oanda_account_id()
            r = PricingInfo(accountID=account_id, params={"instruments": "XAU_USD"})
            client.request(r)
            prices = r.response["prices"][0]
            bid = float(prices["bids"][0]["price"])
            ask = float(prices["asks"][0]["price"])
            return (bid + ask) / 2
        return None

    # yfinance fallback
    import yfinance as yf
    ticker = yf.Ticker("GC=F")
    hist = ticker.history(period="1d")
    if hist.empty:
        return None
    return float(hist["Close"].iloc[-1])


def get_gold_history(period="1y", interval="1d"):
    """
    Get historical gold data.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    Returns: pandas DataFrame.
    """
    import yfinance as yf
    ticker = yf.Ticker("GC=F")
    data = ticker.history(period=period, interval=interval)
    if hasattr(data.columns, "levels"):
        data.columns = data.columns.get_level_values(0)
    return data


def get_macro_signals():
    """
    Get macro signals relevant to gold.
    Returns: dict with key macro indicators.
    """
    import yfinance as yf

    signals = {}

    # DXY (Dollar Index) — gold moves inverse to USD
    dxy = yf.Ticker("DX-Y.NYB")
    hist = dxy.history(period="5d")
    if not hist.empty:
        signals["dxy"] = float(hist["Close"].iloc[-1])

    # US 10Y Treasury yield
    tnx = yf.Ticker("^TNX")
    hist = tnx.history(period="5d")
    if not hist.empty:
        signals["us_10y_yield"] = float(hist["Close"].iloc[-1])

    # VIX (fear index)
    vix = yf.Ticker("^VIX")
    hist = vix.history(period="5d")
    if not hist.empty:
        signals["vix"] = float(hist["Close"].iloc[-1])

    # Gold price
    gold = get_gold_price()
    if gold:
        signals["xauusd"] = gold

    signals["timestamp"] = datetime.utcnow().isoformat()
    return signals


def run_backtest(strategy="xauusd_rsi_basic", **kwargs):
    """
    Run a backtest strategy.
    strategy: name of strategy file in /root/trading/strategies/
    Returns: path to results.
    """
    strat_path = STRATEGIES_DIR / f"{strategy}.py"
    if not strat_path.exists():
        print(f"Strategy not found: {strat_path}")
        return None

    result = subprocess.run(
        [sys.executable, str(strat_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    print(result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr}", file=sys.stderr)
    return result.returncode == 0


def check_readiness():
    """
    Full readiness check — can we trade?
    Returns: dict with status of each component.
    """
    status = {}

    # Python env
    status["python_env"] = str(TRADING_ROOT / "bin" / "python3")
    status["python_exists"] = (TRADING_ROOT / "bin" / "python3").exists()

    # Packages
    try:
        import backtrader, talib, pandas_ta, yfinance, ccxt, oandapyV20
        status["packages"] = "OK"
    except ImportError as e:
        status["packages"] = f"MISSING: {e}"

    # OANDA credentials
    env = _load_env()
    has_creds = "YOUR_" not in env.get("OANDA_ACCOUNT_ID", "YOUR_")
    status["oanda_creds"] = "SET" if has_creds else "NOT_SET"

    # Research brief
    status["research_brief"] = "/root/XAUUSD_TRADING_RESEARCH.md"
    status["research_exists"] = Path("/root/XAUUSD_TRADING_RESEARCH.md").exists()

    # RSI prompt
    status["rsi_prompt"] = "/root/AAA/prompts/XAUUSD_RSI_UPGRADE_v1.0.md"
    status["rsi_prompt_exists"] = Path("/root/AAA/prompts/XAUUSD_RSI_UPGRADE_v1.0.md").exists()

    # Strategies
    strat_count = len(list(STRATEGIES_DIR.glob("*.py")))
    status["strategies"] = strat_count

    # Overall
    ready = (
        status["python_exists"]
        and status["packages"] == "OK"
        and status["research_exists"]
    )
    status["ready"] = ready
    status["ready_for_live_trading"] = ready and has_creds

    return status


def status_report():
    """Print a human-readable status report."""
    s = check_readiness()
    print("=== XAUUSD Trading Stack Status ===")
    print(f"Python env:      {s['python_env']} {'OK' if s['python_exists'] else 'MISSING'}")
    print(f"Packages:        {s['packages']}")
    print(f"OANDA creds:     {s['oanda_creds']}")
    print(f"Research brief:  {'OK' if s['research_exists'] else 'MISSING'}")
    print(f"RSI prompt:      {'OK' if s['rsi_prompt_exists'] else 'MISSING'}")
    print(f"Strategies:      {s['strategies']} files")
    print(f"Ready (paper):   {'YES' if s['ready'] else 'NO'}")
    print(f"Ready (live):    {'YES' if s['ready_for_live_trading'] else 'NO — need OANDA creds'}")


if __name__ == "__main__":
    status_report()
    print()
    price = get_gold_price()
    if price:
        print(f"Current XAUUSD: ${price:,.2f}")
    else:
        print("Could not fetch gold price")
