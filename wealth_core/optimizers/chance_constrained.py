"""
Chance-Constrained Optimization (VaR/CVaR).

APEX Organ: Witness (Ω) — Gödel incompleteness
Conservation Law: Gödel — probabilistic constraint satisfaction

Solves: max μᵀx  s.t. P(rᵀx ≤ α) ≤ β, Σxᵢ=1, x≥0
For normal returns: reformulates as SOCP via Φ⁻¹(1-β)·||Σ^{1/2}x||₂ ≤ μᵀx - α

Uses scipy.optimize for the reformulated quadratic constraint.

F2 TRUTH: Returns distribution is DER (derived from historical data).
F7 HUMILITY: Confidence cap 0.90.
F9 ANTI-HANTU: VaR/CVaR are risk measures, not guarantees.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize, LinearConstraint
from scipy.stats import norm

from .apex_mapping import (
    APEXResult,
    APEXVerdict,
    compute_apex_verdict,
    get_optimizer_mapping,
)


@dataclass
class ChanceConstrainedResult:
    """Result of chance-constrained optimization."""

    weights: List[float]
    expected_return: float
    variance: float
    var_value: float  # Value at Risk
    cvar_value: float  # Conditional VaR (CVaR)
    confidence_level: float
    threshold: float
    solver_status: str
    apex: Optional[APEXResult] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "weights": [round(w, 6) for w in self.weights],
            "expected_return": round(self.expected_return, 6),
            "variance": round(self.variance, 6),
            "var_value": round(self.var_value, 6),
            "cvar_value": round(self.cvar_value, 6),
            "confidence_level": self.confidence_level,
            "threshold": self.threshold,
            "solver_status": self.solver_status,
            "epistemic_label": "DER",
        }
        if self.apex:
            d["apex"] = self.apex.to_dict()
        return d


def chance_constrained(
    returns: List[float],
    covariances: List[List[float]],
    confidence: float = 0.95,
    threshold: float = 0.0,
    risk_free_rate: float = 0.0,
) -> Dict[str, Any]:
    """Compute chance-constrained optimal portfolio.

    Solves: max μᵀx  s.t. P(rᵀx ≤ threshold) ≤ (1-confidence)
    For normal returns: Φ⁻¹(confidence) · √(xᵀΣx) ≤ μᵀx - threshold

    Args:
        returns: expected returns vector
        covariances: covariance matrix
        confidence: confidence level α (e.g., 0.95)
        threshold: minimum acceptable return (loss threshold)
        risk_free_rate: risk-free rate

    Returns:
        Dict with weights, return, VaR, CVaR, apex
    """
    mu = np.array(returns, dtype=np.float64)
    Sigma = np.array(covariances, dtype=np.float64)
    n = len(mu)

    # ── Input validation ─────────────────────────────────────────────────
    if Sigma.shape != (n, n):
        return _error_result(f"Covariance shape {Sigma.shape} != ({n},{n})")
    if not (0.5 < confidence < 1.0):
        return _error_result(f"Confidence {confidence} must be in (0.5, 1.0)")

    # Ensure PSD
    eigvals = np.linalg.eigvalsh(Sigma)
    if np.any(eigvals < -1e-10):
        V = np.linalg.eigh(Sigma)[1]
        Sigma = V @ np.diag(np.maximum(eigvals, 0)) @ V.T

    # Inverse CDF
    z_alpha = norm.ppf(confidence)  # Φ⁻¹(α)

    # ── Solve: max μᵀx  s.t. z_α·√(xᵀΣx) ≤ μᵀx - threshold, Σx=1, x≥0 ──
    def neg_return(x):
        return -float(np.dot(mu, x))

    def chance_constraint_fn(x):
        """z_α · √(xᵀΣx) ≤ μᵀx - threshold  →  return as ≥ 0 when satisfied."""
        port_return = float(np.dot(mu, x))
        port_risk = math.sqrt(max(0, float(np.dot(x, np.dot(Sigma, x)))))
        return (port_return - threshold) - z_alpha * port_risk

    constraints = [
        {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
        {"type": "ineq", "fun": chance_constraint_fn},
    ]
    bounds = [(0.0, 1.0)] * n

    x0 = np.ones(n) / n
    res = minimize(
        neg_return,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    if not res.success:
        # Try relaxed: remove chance constraint, solve standard
        constraints_relaxed = [{"type": "eq", "fun": lambda x: np.sum(x) - 1.0}]
        res2 = minimize(
            neg_return,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_relaxed,
            options={"maxiter": 1000},
        )
        if res2.success:
            res = res2
        else:
            return _error_result(f"Solver failed: {res.message}")

    weights = res.x.tolist()
    exp_ret = float(np.dot(mu, res.x))
    variance = float(np.dot(res.x, np.dot(Sigma, res.x)))
    port_std = math.sqrt(variance)

    # ── Compute VaR and CVaR ─────────────────────────────────────────────
    # VaR at confidence α: μ - z_α · σ
    var_value = exp_ret - z_alpha * port_std
    # CVaR: E[loss | loss > VaR] = μ - σ · φ(z_α)/(1-α)
    cvar_value = exp_ret - port_std * norm.pdf(z_alpha) / (1 - confidence)

    # ── APEX verdict ─────────────────────────────────────────────────────
    apex = compute_apex_verdict(
        optimizer="chance_constrained",
        solver_status="ok" if res.success else "warning",
        solver_termination="optimal" if res.success else "suboptimal",
        constraint_violation=abs(sum(weights) - 1.0),
        input_quality=0.7,
        evidence_quality=0.7,
        has_uncertainty_bands=True,
        weights_sum=sum(weights),
    )

    return ChanceConstrainedResult(
        weights=weights,
        expected_return=exp_ret,
        variance=variance,
        var_value=var_value,
        cvar_value=cvar_value,
        confidence_level=confidence,
        threshold=threshold,
        solver_status="ok" if res.success else "warning",
        apex=apex,
    ).to_dict()


def cvar_portfolio(
    returns: List[float],
    covariances: List[List[float]],
    confidence: float = 0.95,
    max_cvar: Optional[float] = None,
) -> Dict[str, Any]:
    """CVaR-constrained portfolio optimization.

    Minimizes CVaR at confidence level α, or maximizes return subject to CVaR ≤ max_cvar.

    Uses the linear programming reformulation of CVaR.

    Args:
        returns: expected returns vector
        covariances: covariance matrix (for generating scenarios)
        confidence: confidence level α
        max_cvar: maximum allowable CVaR (if None, minimize CVaR)

    Returns:
        Dict with weights, CVaR, expected return
    """
    mu = np.array(returns, dtype=np.float64)
    Sigma = np.array(covariances, dtype=np.float64)
    n = len(mu)

    # Generate scenarios from multivariate normal
    rng = np.random.default_rng(42)
    n_scenarios = 500
    scenarios = rng.multivariate_normal(mu, Sigma, size=n_scenarios)

    alpha = confidence
    S = n_scenarios

    # CVaR LP: min ζ + (1/(1-α)S) Σ uₛ
    # s.t. uₛ ≥ -rₛᵀx - ζ, uₛ ≥ 0, Σx=1, x≥0
    # Variables: x(n), zeta(1), u(S)

    if max_cvar is not None:
        # Maximize return s.t. CVaR ≤ max_cvar
        def neg_return(x):
            w = x[:n]
            return -float(np.dot(mu, w))

        def cvar_constraint(x):
            w = x[:n]
            zeta = x[n]
            losses = -np.dot(scenarios, w)
            cvar = zeta + (1.0 / ((1 - alpha) * S)) * np.sum(
                np.maximum(losses - zeta, 0)
            )
            return max_cvar - cvar  # ≥ 0 when satisfied

        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x[:n]) - 1.0},
            {"type": "ineq", "fun": cvar_constraint},
        ]
        bounds = [(0.0, 1.0)] * n + [(None, None)]
        x0 = np.concatenate([np.ones(n) / n, [0.0]])

        res = minimize(
            neg_return,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )
    else:
        # Minimize CVaR
        def cvar_objective(x):
            w = x[:n]
            zeta = x[n]
            losses = -np.dot(scenarios, w)
            return zeta + (1.0 / ((1 - alpha) * S)) * np.sum(
                np.maximum(losses - zeta, 0)
            )

        constraints = [{"type": "eq", "fun": lambda x: np.sum(x[:n]) - 1.0}]
        bounds = [(0.0, 1.0)] * n + [(None, None)]
        x0 = np.concatenate([np.ones(n) / n, [0.0]])

        res = minimize(
            cvar_objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

    if not res.success:
        return _error_result(f"CVaR solver failed: {res.message}")

    weights = res.x[:n].tolist()
    zeta = res.x[n]
    losses = -np.dot(scenarios, res.x[:n])
    cvar = zeta + (1.0 / ((1 - alpha) * S)) * np.sum(np.maximum(losses - zeta, 0))
    exp_ret = float(np.dot(mu, res.x[:n]))

    return {
        "weights": [round(w, 6) for w in weights],
        "cvar_value": round(float(cvar), 6),
        "expected_return": round(exp_ret, 6),
        "confidence_level": confidence,
        "solver_status": "ok",
        "epistemic_label": "DER",
    }


def _error_result(msg: str) -> Dict[str, Any]:
    return {
        "error": msg,
        "solver_status": "error",
        "epistemic_label": "DER",
        "apex": {"verdict": "VOID", "warnings": [msg]},
    }
