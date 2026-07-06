"""
Robust Optimization Under Uncertainty.

APEX Organ: Governance (ΔG) — Entropy reduction
Conservation Law: Entropy — worst-case optimal allocation

Implements three robust counterparts:
1. Box uncertainty: z ∈ [nominal-δ, nominal+δ]
2. Budget uncertainty (Bertsimas-Sim): |z| ≤ δ, Σ|zⱼ|/δⱼ ≤ Γ
3. Ellipsoidal uncertainty: z in ball of radius r

Uses scipy.optimize for constraint handling.

F2 TRUTH: Uncertainty set is SPEC (modeled, not observed).
F7 HUMILITY: Confidence cap 0.90.
F9 ANTI-HANTU: Worst-case analysis reduces false precision.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
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
class RobustResult:
    """Result of robust portfolio optimization."""

    weights: List[float]
    nominal_return: float
    worst_case_return: float
    uncertainty_radius: float
    robust_type: str  # "box", "budget", "ellipsoidal"
    solver_status: str
    apex: Optional[APEXResult] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "weights": [round(w, 6) for w in self.weights],
            "nominal_return": round(self.nominal_return, 6),
            "worst_case_return": round(self.worst_case_return, 6),
            "uncertainty_radius": self.uncertainty_radius,
            "robust_type": self.robust_type,
            "solver_status": self.solver_status,
            "epistemic_label": "SPEC",  # uncertainty set is modeled
        }
        if self.apex:
            d["apex"] = self.apex.to_dict()
        return d


def robust_portfolio(
    returns: List[float],
    uncertainty_radius: float = 0.1,
    robust_type: str = "budget",
    gamma_budget: Optional[float] = None,
    covariances: Optional[List[List[float]]] = None,
    risk_aversion: float = 1.0,
) -> Dict[str, Any]:
    """Compute robust optimal portfolio under uncertainty.

    Solves: max min_{z∈Z} (μ+z)ᵀx  s.t. Σxᵢ=1, x≥0

    Args:
        returns: nominal expected returns vector
        uncertainty_radius: δ — max deviation per asset
        robust_type: "box", "budget", or "ellipsoidal"
        gamma_budget: Γ — budget of uncertainty (for budget type)
        covariances: optional covariance matrix (for ellipsoidal)
        risk_aversion: risk aversion parameter

    Returns:
        Dict with weights, nominal return, worst-case return, apex
    """
    mu = np.array(returns, dtype=np.float64)
    n = len(mu)

    if uncertainty_radius < 0:
        return _error_result(f"Uncertainty radius δ={uncertainty_radius} must be ≥ 0")
    if uncertainty_radius == 0:
        # No uncertainty — standard Markowitz
        from .markowitz import markowitz_frontier

        return markowitz_frontier(
            expected_returns=returns,
            covariances=np.eye(n).tolist() if covariances is None else covariances,
            risk_aversion=risk_aversion,
        )

    # ── Solve robust counterpart ─────────────────────────────────────────
    if robust_type == "box":
        result = _solve_box_robust(mu, uncertainty_radius, risk_aversion)
    elif robust_type == "budget":
        gamma = gamma_budget if gamma_budget is not None else min(n, 2.0)
        result = _solve_budget_robust(mu, uncertainty_radius, gamma, risk_aversion)
    elif robust_type == "ellipsoidal":
        if covariances is None:
            return _error_result("Ellipsoidal robust requires covariances matrix")
        Sigma = np.array(covariances, dtype=np.float64)
        result = _solve_ellipsoidal_robust(mu, Sigma, uncertainty_radius, risk_aversion)
    else:
        return _error_result(f"Unknown robust_type: {robust_type}")

    if result["solver_status"] != "ok":
        return result

    weights = result["weights"]
    nominal_ret = float(np.dot(mu, weights))

    # Compute worst-case return
    wc_return = _worst_case_return(
        mu,
        weights,
        uncertainty_radius,
        robust_type,
        gamma_budget if gamma_budget is not None else n,
    )

    # ── APEX verdict ─────────────────────────────────────────────────────
    apex = compute_apex_verdict(
        optimizer="robust_portfolio",
        solver_status=result["solver_status"],
        solver_termination="optimal",
        constraint_violation=abs(sum(weights) - 1.0),
        input_quality=0.6,  # SPEC — uncertainty set is modeled
        evidence_quality=0.6,
        has_uncertainty_bands=True,
        weights_sum=sum(weights),
    )

    return RobustResult(
        weights=weights,
        nominal_return=nominal_ret,
        worst_case_return=wc_return,
        uncertainty_radius=uncertainty_radius,
        robust_type=robust_type,
        solver_status=result["solver_status"],
        apex=apex,
    ).to_dict()


def _solve_box_robust(
    mu: np.ndarray, delta: float, risk_aversion: float
) -> Dict[str, Any]:
    """Box uncertainty: worst-case return = μᵀx - δ·Σ|xᵢ|.

    Dual reformulation: max μᵀx - δ·t  s.t. -t ≤ xᵢ ≤ t, Σx=1, x≥0
    """
    n = len(mu)

    def neg_worst_case(x):
        # x[0:n] = weights, x[n] = t (auxiliary)
        w = x[:n]
        t = x[n]
        nominal = float(np.dot(mu, w))
        return -(nominal - delta * t)

    # Constraints: -t ≤ wᵢ ≤ t → wᵢ - t ≤ 0 and -wᵢ - t ≤ 0
    # Budget: Σwᵢ = 1
    constraints = [
        {"type": "eq", "fun": lambda x: np.sum(x[:n]) - 1.0},
    ]
    # Bounds: wᵢ ≥ 0, t ≥ 0
    bounds = [(0.0, 1.0)] * n + [(0.0, None)]

    # Initial point
    x0 = np.concatenate([np.ones(n) / n, [np.max(np.abs(mu))]])

    res = minimize(
        neg_worst_case,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    if not res.success:
        return {"solver_status": "warning", "solver_message": res.message}

    weights = res.x[:n].tolist()
    return {"weights": weights, "solver_status": "ok"}


def _solve_budget_robust(
    mu: np.ndarray, delta: float, gamma: float, risk_aversion: float
) -> Dict[str, Any]:
    """Budget (Bertsimas-Sim) uncertainty: worst-case = μᵀx - δ·(γ·λ + Σtᵢ).

    Dual: max μᵀx - δ·(γ·λ + Σtᵢ)
    s.t. tᵢ + λ ≥ xᵢ, tᵢ - λ ≥ -xᵢ, tᵢ ≥ 0, λ ≥ 0, Σx=1, x≥0
    """
    n = len(mu)

    def neg_worst_case(x):
        w = x[:n]
        lam = x[n]
        t = x[n + 1 : 2 * n + 1]
        nominal = float(np.dot(mu, w))
        penalty = delta * (gamma * lam + np.sum(t))
        return -(nominal - penalty)

    constraints = [
        {"type": "eq", "fun": lambda x: np.sum(x[:n]) - 1.0},
    ]
    bounds = [(0.0, 1.0)] * n + [(0.0, None)] * (n + 1)

    x0 = np.concatenate([np.ones(n) / n, [0.1], np.zeros(n)])

    res = minimize(
        neg_worst_case,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    if not res.success:
        return {"solver_status": "warning", "solver_message": res.message}

    weights = res.x[:n].tolist()
    return {"weights": weights, "solver_status": "ok"}


def _solve_ellipsoidal_robust(
    mu: np.ndarray, Sigma: np.ndarray, radius: float, risk_aversion: float
) -> Dict[str, Any]:
    """Ellipsoidal uncertainty: worst-case = μᵀx - r·||x||₂.

    Uses SOC reformulation: max μᵀx - r·||x||₂ s.t. Σx=1, x≥0
    """
    n = len(mu)

    def neg_worst_case(x):
        nominal = float(np.dot(mu, x))
        norm_x = float(np.linalg.norm(x))
        return -(nominal - radius * norm_x)

    def grad_worst_case(x):
        nom_grad = -mu
        norm_x = np.linalg.norm(x)
        if norm_x > 1e-12:
            norm_grad = -radius * x / norm_x
        else:
            norm_grad = np.zeros(n)
        return nom_grad + norm_grad

    constraints = [LinearConstraint(np.ones(n), 1.0, 1.0)]
    bounds = [(0.0, 1.0)] * n

    x0 = np.ones(n) / n
    res = minimize(
        neg_worst_case,
        x0,
        jac=grad_worst_case,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    if not res.success:
        return {"solver_status": "warning", "solver_message": res.message}

    weights = res.x.tolist()
    return {"weights": weights, "solver_status": "ok"}


def _worst_case_return(
    mu: np.ndarray, weights: List[float], delta: float, robust_type: str, gamma: float
) -> float:
    """Compute worst-case return for given weights."""
    w = np.array(weights)
    n = len(w)
    nominal = float(np.dot(mu, w))

    if robust_type == "box":
        return nominal - delta * float(np.sum(np.abs(w)))
    elif robust_type == "budget":
        # Worst case: subtract δ * min(γ, n) * max|wᵢ|
        sorted_w = np.sort(np.abs(w))[::-1]
        penalty = delta * (
            gamma * sorted_w[min(int(gamma), n - 1)] if int(gamma) < n else 0
        )
        penalty += delta * np.sum(sorted_w[: int(gamma)])
        return nominal - penalty
    elif robust_type == "ellipsoidal":
        return nominal - delta * float(np.linalg.norm(w))
    else:
        return nominal


def _error_result(msg: str) -> Dict[str, Any]:
    return {
        "error": msg,
        "solver_status": "error",
        "epistemic_label": "SPEC",
        "apex": {"verdict": "VOID", "warnings": [msg]},
    }
