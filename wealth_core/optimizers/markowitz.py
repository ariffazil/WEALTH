"""
Markowitz Mean-Variance Frontier Optimizer.

APEX Organ: Reality (ΔR) — Energy conservation
Conservation Law: Energy — return vs risk tradeoff

Solves: max μᵀx  s.t. xᵀΣx ≤ γ, Σxᵢ = 1, x ≥ 0
Uses scipy.optimize (SLSQP) for quadratic constraint handling.

F2 TRUTH: Returns are DER (derived from historical data), not OBS.
F7 HUMILITY: Confidence cap 0.90.
F9 ANTI-HANTU: Outputs uncertainty ranges, not point estimates.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize, LinearConstraint

from .apex_mapping import (
    APEXResult,
    APEXVerdict,
    compute_apex_verdict,
    get_optimizer_mapping,
)


@dataclass
class MarkowitzResult:
    """Result of Markowitz optimization."""

    weights: List[float]
    expected_return: float
    variance: float
    sharpe_ratio: float
    risk_free_return: float
    gamma: float  # risk budget used
    solver_status: str
    solver_message: str
    apex: Optional[APEXResult] = None
    uncertainty: Optional[Dict[str, Tuple[float, float]]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "weights": [round(w, 6) for w in self.weights],
            "expected_return": round(self.expected_return, 6),
            "variance": round(self.variance, 6),
            "sharpe_ratio": round(self.sharpe_ratio, 6),
            "risk_free_return": self.risk_free_return,
            "gamma": self.gamma,
            "solver_status": self.solver_status,
            "epistemic_label": "DER",
        }
        if self.apex:
            d["apex"] = self.apex.to_dict()
        if self.uncertainty:
            d["uncertainty"] = {
                k: {"low": round(v[0], 6), "high": round(v[1], 6)}
                for k, v in self.uncertainty.items()
            }
        return d


def markowitz_frontier(
    expected_returns: List[float],
    covariances: List[List[float]],
    risk_aversion: float = 1.0,
    risk_free_rate: float = 0.0,
    asset_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute Markowitz mean-variance optimal portfolio.

    Solves: max μᵀx - (γ/2) xᵀΣx  s.t. Σxᵢ = 1, x ≥ 0
    Or equivalently: max μᵀx  s.t. xᵀΣx ≤ γ, Σxᵢ = 1, x ≥ 0

    Args:
        expected_returns: vector of expected returns (n assets)
        covariances: n×n covariance matrix
        risk_aversion: γ — risk aversion parameter (>0)
        risk_free_rate: risk-free asset return
        asset_names: optional names for assets

    Returns:
        Dict with weights, return, risk, sharpe, apex verdict
    """
    mu = np.array(expected_returns, dtype=np.float64)
    Sigma = np.array(covariances, dtype=np.float64)
    n = len(mu)

    # ── Input validation (F2 TRUTH) ──────────────────────────────────────
    if Sigma.shape != (n, n):
        return _error_result(f"Covariance matrix shape {Sigma.shape} != ({n},{n})")
    if risk_aversion <= 0:
        return _error_result(f"Risk aversion γ={risk_aversion} must be > 0")

    # Ensure PSD (project if needed)
    eigvals = np.linalg.eigvalsh(Sigma)
    if np.any(eigvals < -1e-10):
        # Project to PSD
        eigvals_clipped = np.maximum(eigvals, 0)
        V = np.linalg.eigh(Sigma)[1]
        Sigma = V @ np.diag(eigvals_clipped) @ V.T

    # ── Solve: max μᵀx - (γ/2) xᵀΣx  s.t. Σx=1, x≥0 ──────────────────
    def neg_utility(x: np.ndarray) -> float:
        ret = float(np.dot(mu, x))
        risk = float(np.dot(x, np.dot(Sigma, x)))
        return -(ret - (risk_aversion / 2) * risk)

    def neg_utility_grad(x: np.ndarray) -> np.ndarray:
        return -(mu - risk_aversion * Sigma @ x)

    x0 = np.ones(n) / n  # equal weight start
    constraints = [LinearConstraint(np.ones(n), 1.0, 1.0)]
    bounds = [(0.0, 1.0)] * n

    result = minimize(
        neg_utility,
        x0,
        jac=neg_utility_grad,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    weights = result.x.tolist()
    exp_ret: float = float(np.dot(mu, result.x))
    variance: float = float(np.dot(result.x, np.dot(Sigma, result.x)))
    sharpe = (
        (exp_ret - risk_free_rate) / math.sqrt(variance) if variance > 1e-12 else 0.0
    )

    # ── Uncertainty bands (F9 ANTI-HANTU) ────────────────────────────────
    # Bootstrap uncertainty via perturbation
    uncertainty = _compute_uncertainty(mu, Sigma, result.x, n_sims=100)

    # ── APEX verdict ─────────────────────────────────────────────────────
    constraint_violation = abs(sum(weights) - 1.0)
    apex = compute_apex_verdict(
        optimizer="markowitz_frontier",
        solver_status="ok" if result.success else "warning",
        solver_termination="optimal" if result.success else "suboptimal",
        constraint_violation=constraint_violation,
        input_quality=0.7,  # DER from historical data
        evidence_quality=0.7,
        has_uncertainty_bands=uncertainty is not None,
        weights_sum=sum(weights),
    )

    return MarkowitzResult(
        weights=weights,
        expected_return=exp_ret,
        variance=variance,
        sharpe_ratio=sharpe,
        risk_free_return=risk_free_rate,
        gamma=risk_aversion,
        solver_status="ok" if result.success else "warning",
        solver_message=result.message,
        apex=apex,
        uncertainty=uncertainty,
    ).to_dict()


def markowitz_frontier_sweep(
    expected_returns: List[float],
    covariances: List[List[float]],
    n_points: int = 20,
    risk_free_rate: float = 0.0,
) -> Dict[str, Any]:
    """Compute the full efficient frontier by sweeping risk aversion.

    Returns list of (return, risk, sharpe, weights) for each γ.

    Args:
        expected_returns: vector of expected returns
        covariances: n×n covariance matrix
        n_points: number of points on the frontier
        risk_free_rate: risk-free rate for Sharpe computation

    Returns:
        Dict with frontier points and metadata
    """
    mu = np.array(expected_returns, dtype=np.float64)
    Sigma = np.array(covariances, dtype=np.float64)
    n = len(mu)

    # Sweep gamma from small (aggressive) to large (conservative)
    gamma_values = np.linspace(0.1, 10.0, n_points)
    frontier = []

    for gamma in gamma_values:
        result = markowitz_frontier(
            expected_returns=expected_returns,
            covariances=covariances,
            risk_aversion=gamma,
            risk_free_rate=risk_free_rate,
        )
        if result.get("solver_status") == "ok":
            frontier.append(
                {
                    "gamma": round(gamma, 4),
                    "expected_return": result["expected_return"],
                    "variance": result["variance"],
                    "sharpe_ratio": result["sharpe_ratio"],
                    "weights": result["weights"],
                }
            )

    return {
        "frontier": frontier,
        "n_points": len(frontier),
        "n_assets": n,
        "epistemic_label": "DER",
        "risk_free_rate": risk_free_rate,
    }


def _compute_uncertainty(
    mu: np.ndarray,
    Sigma: np.ndarray,
    x_opt: np.ndarray,
    n_sims: int = 100,
    perturbation: float = 0.1,
) -> Optional[Dict[str, Tuple[float, float]]]:
    """Compute uncertainty bands via parameter perturbation.

    Perturbs expected returns by ±10% and re-solves to get return/risk ranges.
    """
    n = len(mu)
    returns = []
    risks = []

    rng = np.random.default_rng(42)
    for _ in range(n_sims):
        mu_pert = mu * (1 + rng.normal(0, perturbation, n))
        Sigma_pert = Sigma * (1 + rng.normal(0, perturbation * 0.5))

        # Ensure PSD
        eigvals = np.linalg.eigvalsh(Sigma_pert)
        if np.any(eigvals < -1e-10):
            V = np.linalg.eigh(Sigma_pert)[1]
            Sigma_pert = V @ np.diag(np.maximum(eigvals, 0)) @ V.T

        def neg_util(x):
            return -(mu_pert @ x - 0.5 * x @ Sigma_pert @ x)

        constraints = [LinearConstraint(np.ones(n), 1.0, 1.0)]
        bounds = [(0.0, 1.0)] * n
        res = minimize(
            neg_util,
            x_opt,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 500},
        )
        if res.success:
            returns.append(float(mu @ res.x))
            risks.append(float(res.x @ Sigma @ res.x))

    if not returns:
        return None

    return {
        "expected_return": (
            float(np.percentile(returns, 5)),
            float(np.percentile(returns, 95)),
        ),
        "variance": (float(np.percentile(risks, 5)), float(np.percentile(risks, 95))),
    }


def _error_result(msg: str) -> Dict[str, Any]:
    """Return error result dict."""
    return {
        "error": msg,
        "solver_status": "error",
        "epistemic_label": "DER",
        "apex": {
            "verdict": "VOID",
            "warnings": [msg],
        },
    }
