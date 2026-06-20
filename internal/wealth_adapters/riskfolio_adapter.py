"""
Riskfolio-Lib Adapter — Convex portfolio optimization.

Per executive verdict: "Riskfolio-Lib is stronger than basic mean-variance; supports
many convex risk measures, drawdown risk, CVaR, EVaR, risk parity, Black-Litterman."

F8 LAW: Riskfolio computes. WEALTH audits. arifOS gates. Arif decides.
"""

from __future__ import annotations

import hashlib

from ..wealth_contracts.envelopes import WealthEnvelope, VerdictLabel


class RiskfolioAdapter:
    """Adapter for Riskfolio-Lib convex portfolio optimization."""

    def __init__(self):
        self._available = self._check_availability()
        self.adapter_hash = "b3:" + hashlib.sha256(
            b"wealth_adapters_riskfolio_v0.1"
        ).hexdigest()

    def _check_availability(self) -> bool:
        try:
            import riskfolio as rp
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self._available

    def optimize_cvar(
        self,
        returns,  # pandas DataFrame of asset returns
        risk_aversion: float = 1.0,
    ) -> WealthEnvelope:
        """
        Compute the minimum-CVaR (Conditional Value at Risk) portfolio.

        CVaR = expected loss in the worst α% of cases.
        """
        if not self._available:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": "riskfolio-lib not installed"},
                transform_hash=self.adapter_hash,
            )

        try:
            import riskfolio as rp
        except ImportError as e:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": str(e)},
                transform_hash=self.adapter_hash,
            )

        try:
            port = rp.Portfolio(returns=returns)
            port.assets_stats(method_mu="hist", method_cov="hist")
            weights = port.optimization(
                model="Classic",
                rm="CVaR",  # Risk measure: Conditional Value at Risk
                obj="MinRisk",
                rf=0.0,
                l=0,  # No L2 regularization
            )
            cleaned = port.clean_weights()

            return WealthEnvelope(
                verdict=VerdictLabel.SAFE_TO_STUDY,
                epistemic_status="DER",
                data={
                    "method": "MinRisk_CVaR",
                    "weights": dict(cleaned),
                    "tickers": list(returns.columns),
                    "n_observations": len(returns),
                    "risk_aversion": risk_aversion,
                },
                transform_hash=self.adapter_hash,
                notes="CVaR optimization via Riskfolio-Lib. F13 SOVEREIGN execution required to act.",
            )
        except Exception as e:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": str(e), "method": "optimize_cvar"},
                transform_hash=self.adapter_hash,
            )
