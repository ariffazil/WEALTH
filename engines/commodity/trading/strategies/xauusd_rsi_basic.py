#!/usr/bin/env python3
"""XAUUSD RSI Mean-Reversion Strategy — Backtrader skeleton

Uses RSI(14) on H1 timeframe:
  - RSI < 30 → buy (oversold)
  - RSI > 70 → sell (overbought)
  - 1% stop-loss, 2% take-profit

Run: /root/trading/bin/python3 strategies/xauusd_rsi_basic.py
"""
import backtrader as bt
import yfinance as yf
import sys

class RsiMeanReversion(bt.Strategy):
    params = (
        ("period", 14),
        ("overbought", 70),
        ("oversold", 30),
        ("stop_loss", 0.01),
        ("take_profit", 0.02),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.period)

    def next(self):
        if not self.position:
            if self.rsi < self.p.oversold:
                size = int(self.broker.getcash() * 0.95 / self.data.close[0])
                if size > 0:
                    self.buy(size=size)
                    self.stop_price = self.data.close[0] * (1 - self.p.stop_loss)
                    self.tp_price = self.data.close[0] * (1 + self.p.take_profit)
        else:
            if self.rsi > self.p.overbought or \
               self.data.close[0] <= self.stop_price or \
               self.data.close[0] >= self.tp_price:
                self.close()


def run_backtest():
    # Download XAUUSD data (using GLD ETF as proxy — gold futures need broker data)
    print("Downloading XAUUSD proxy data (GLD ETF)...")
    data = yf.download("GC=F", start="2024-01-01", end="2026-07-14", interval="1d", progress=False)

    if data.empty:
        print("ERROR: No data downloaded")
        sys.exit(1)

    # Flatten MultiIndex columns if present
    if hasattr(data.columns, 'levels'):
        data.columns = data.columns.get_level_values(0)

    print(f"Data: {len(data)} bars, {data.index[0]} to {data.index[-1]}")
    print(f"Price range: {data['Close'].min():.2f} - {data['Close'].max():.2f}")

    cerebro = bt.Cerebro()
    cerebro.addstrategy(RsiMeanReversion)

    datafeed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(datafeed)

    cerebro.broker.setcash(10000)
    cerebro.broker.setcommission(commission=0.001)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

    print(f"Starting portfolio: ${cerebro.broker.getvalue():,.2f}")
    results = cerebro.run()
    strat = results[0]
    print(f"Final portfolio:    ${cerebro.broker.getvalue():,.2f}")

    # Report
    sharpe = strat.analyzers.sharpe.get_analysis()
    dd = strat.analyzers.drawdown.get_analysis()
    trades = strat.analyzers.trades.get_analysis()

    print(f"\n--- Results ---")
    print(f"Sharpe Ratio:  {sharpe.get('sharperatio', 'N/A')}")
    print(f"Max Drawdown:  {dd.get('max', {}).get('drawdown', 'N/A'):.2f}%")
    total = trades.get('total', {}).get('total', 0)
    won = trades.get('won', {}).get('total', 0)
    print(f"Trades:        {total} (won: {won}, lost: {total - won})")
    if total > 0:
        print(f"Win Rate:      {won/total*100:.1f}%")

    return cerebro.broker.getvalue()


if __name__ == "__main__":
    final = run_backtest()
    print(f"\nReturn: {(final/10000 - 1)*100:.2f}%")
