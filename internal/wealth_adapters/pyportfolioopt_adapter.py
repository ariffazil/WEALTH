"""
PyPortfolioOpt Adapter — Lightweight portfolio optimization.

PyPortfolioOpt provides:
- Efficient frontier
- Expected returns models (mean historical, CAPM, Black-Litterman)
- Covariance/risk models (sample, semicovariance, exponential weighted)
- Convex optimization

F8 LAW: PyPortfolioOpt computes. WEALTH audits. arifOS gates. Arif decides.
F1 AMANAH: Adapter wraps pypfopt in try/except; on failure, returns evidence envelope with error.
"""

from __future__ import annotations

import hashlib


from ..wealth_contracts.envelopes import WealthEnvelope, VerdictLabel


class PyPortfolioOptAdapter:
    """Adapter for PyPortfolioOpt — lightweight portfolio optimization."""

    def __init__(self):
        self._available = self._check_availability()
        self.adapter_hash = "b3:" + hashlib.sha256(
            b"wealth_adapters_pyportfolioopt_v0.1"
        ).hexdigest()

    def _check_availability(self) -> bool:
        try:
            import pypfopt  # noqa: F401
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self._available

    def efficient_frontier(
        self,
        prices_df,  # pandas DataFrame of asset prices
        risk_free_rate: float = 0.02,
        weight_bounds: tuple = (0, 1),
    ) -> WealthEnvelope:
        """
        Compute the max-Sharpe portfolio allocation.

        prices_df: pandas DataFrame, columns = tickers, rows = dates.
        Returns WealthEnvelope with verdict + data.
        """
        if not self._available:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                epistemic_status="DER",
                data={"error": "pypfopt not installed"},
                transform_hash=self.adapter_hash,
                notes="Install pypfopt: uv add pyportfolioopt",
            )

        try:
            from pypfopt import EfficientFrontier, expected_returns, risk_models
        except ImportError as e:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": str(e)},
                transform_hash=self.adapter_hash,
            )

        try:
            mu = expected_returns.mean_historical_return(prices_df)
            S = risk_models.sample_cov(prices_df)
            ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
            weights = ef.max_sharpe(risk_free_rate=risk_free_rate)
            cleaned = ef.clean_weights()
            perf = ef.portfolio_performance(verbose=False)

            return WealthEnvelope(
                verdict=VerdictLabel.SAFE_TO_STUDY,
                epistemic_status="DER",
                data={
                    "weights": dict(cleaned),
                    "expected_annual_return": float(perf[0]),
                    "annual_volatility": float(perf[1]),
                    "sharpe_ratio": float(perf[2]),
                    "tickers": list(prices_df.columns),
                    "n_observations": len(prices_df),
                },
                transform_hash=self.adapter_hash,
                notes="Max-Sharpe allocation; F13 SOVEREIGN execution required to act.",
            )
        except Exception as e:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": str(e), "method": "max_sharpe"},
                transform_hash=self.adapter_hash,
            )
