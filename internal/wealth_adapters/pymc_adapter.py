"""
PyMC Adapter — Bayesian uncertainty quantification.

Per executive verdict: "PyMC is a probabilistic programming library for Bayesian
modeling and probabilistic ML."

F2 TRUTH: posterior distributions are honest about epistemic uncertainty.
F7 HUMILITY: confidence cap 0.90 (Bayesian posteriors exceed this for trivial reasons).
"""

from __future__ import annotations

import hashlib
from typing import Optional

from ..wealth_contracts.envelopes import WealthEnvelope, VerdictLabel


class PyMCAdapter:
    """Adapter for PyMC Bayesian inference."""

    def __init__(self):
        self._available = self._check_availability()
        self.adapter_hash = "b3:" + hashlib.sha256(
            b"wealth_adapters_pymc_v0.1"
        ).hexdigest()

    def _check_availability(self) -> bool:
        try:
            import pymc as pm
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self._available

    def infer_posterior(
        self,
        observed_data,
        prior_mean: float = 0.0,
        prior_std: float = 1.0,
        samples: int = 1000,
        chains: int = 4,
    ) -> WealthEnvelope:
        """
        Run a simple Gaussian-mean Bayesian inference.

        Returns the posterior mean, std, and 95% HDI (highest density interval).
        """
        if not self._available:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": "PyMC not installed"},
                transform_hash=self.adapter_hash,
            )

        try:
            import pymc as pm
            import arviz as az
        except ImportError as e:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": str(e)},
                transform_hash=self.adapter_hash,
            )

        try:
            with pm.Model() as model:
                mu = pm.Normal("mu", mu=prior_mean, sigma=prior_std)
                sigma = pm.HalfNormal("sigma", sigma=1.0)
                obs = pm.Normal("obs", mu=mu, sigma=sigma, observed=observed_data)
                trace = pm.sample(samples, chains=chains, progressbar=False, return_inferencedata=True)

            summary = az.summary(trace, var_names=["mu"], hdi_prob=0.95)
            hdi = az.hdi(trace, var_names=["mu"], hdi_prob=0.95)

            return WealthEnvelope(
                verdict=VerdictLabel.SAFE_TO_STUDY,
                epistemic_status="DER",
                data={
                    "method": "PyMC_Normal_Normal",
                    "posterior_mu_mean": float(summary["mean"].iloc[0]),
                    "posterior_mu_std": float(summary["sd"].iloc[0]),
                    "posterior_mu_hdi_2.5": float(hdi["mu"].iloc[0]),
                    "posterior_mu_hdi_97.5": float(hdi["mu"].iloc[1]),
                    "n_samples": samples,
                    "n_chains": chains,
                    "n_observed": len(observed_data),
                },
                transform_hash=self.adapter_hash,
                notes="Bayesian posterior via PyMC + ArviZ. HDI = 95% Highest Density Interval. F13 SOVEREIGN execution required to act on uncertainty.",
            )
        except Exception as e:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": str(e), "method": "infer_posterior"},
                transform_hash=self.adapter_hash,
            )
