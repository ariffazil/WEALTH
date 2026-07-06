"""
Kelly Criterion Optimal Bet Sizing.

APEX Organ: Execution (W) — Work conservation law
Conservation Law: Work — maximum expected log-growth

Solves: max p·log(1+b·f) + (1-p)·log(1-f)  s.t. 0 ≤ f ≤ 1
With risk constraint: E[R^{-λ}] ≤ 1

Uses scipy.optimize for nonlinear optimization.

F2 TRUTH: Win probability p is INTERPRETED, not OBS.
F7 HUMILITY: Confidence cap 0.90.
F9 ANTI-HANTU: Monte Carlo simulation for uncertainty.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize_scalar, minimize

from .apex_mapping import (
    APEXResult,
    APEXVerdict,
    compute_apex_verdict,
    get_optimizer_mapping,
)


@dataclass
class KellyResult:
    """Result of Kelly criterion optimization."""

    optimal_fraction: float
    expected_log_growth: float
    win_probability: float
    odds: float
    risk_constraint: Optional[float]
    analytical_fraction: float  # closed-form Kelly: f* = p - (1-p)/b
    solver_status: str
    apex: Optional[APEXResult] = None
    simulation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "optimal_fraction": round(self.optimal_fraction, 6),
            "expected_log_growth": round(self.expected_log_growth, 6),
            "win_probability": self.win_probability,
            "odds": self.odds,
            "risk_constraint": self.risk_constraint,
            "analytical_fraction": round(self.analytical_fraction, 6),
            "solver_status": self.solver_status,
            "epistemic_label": "INTERPRETED",  # p is interpreted, not observed
        }
        if self.apex:
            d["apex"] = self.apex.to_dict()
        if self.simulation:
            d["simulation"] = self.simulation
        return d


def kelly_sizing(
    win_prob: float,
    odds: float,
    risk_constraint: Optional[float] = None,
    n_simulations: int = 1000,
    n_periods: int = 50,
) -> Dict[str, Any]:
    """Compute Kelly criterion optimal bet fraction.

    Maximizes expected log-growth: E[log(1 + f·R)]
    where R = +b with prob p, -1 with prob (1-p).

    With risk constraint λ: E[R^{-λ}] ≤ 1 (risk-constrained Kelly).

    Args:
        win_prob: probability of winning (0 < p < 1)
        odds: payout odds (b > 0, win returns 1+b per unit wagered)
        risk_constraint: λ — risk aversion parameter (None = standard Kelly)
        n_simulations: Monte Carlo paths for uncertainty estimation
        n_periods: periods per simulation path

    Returns:
        Dict with optimal_fraction, expected_growth, apex verdict
    """
    # ── Input validation (F2 TRUTH) ──────────────────────────────────────
    if not (0 < win_prob < 1):
        return _error_result(f"Win probability p={win_prob} must be in (0,1)")
    if odds <= 0:
        return _error_result(f"Odds b={odds} must be > 0")

    p = win_prob
    b = odds

    # ── Analytical Kelly fraction ─────────────────────────────────────────
    # f* = p - (1-p)/b  (standard Kelly)
    # f* = 0 if p*(b+1) <= 1 (no positive edge)
    if p * (b + 1) <= 1:
        f_analytical = 0.0
    else:
        f_analytical = p - (1 - p) / b

    # ── Solve via scipy ──────────────────────────────────────────────────
    def neg_expected_log_growth(f: float) -> float:
        """Negative expected log-growth (for minimization)."""
        if f <= 0 or f >= 1:
            return 1e10  # infeasible
        win = p * math.log(1 + b * f)
        lose = (1 - p) * math.log(1 - f)
        return -(win + lose)

    if risk_constraint is not None and risk_constraint > 0:
        # Risk-constrained Kelly: E[R^{-λ}] ≤ 1
        lam = risk_constraint
        result = _solve_risk_constrained_kelly(p, b, lam)
    else:
        # Standard Kelly — bounded scalar optimization
        res = minimize_scalar(
            neg_expected_log_growth,
            bounds=(1e-10, 1 - 1e-10),
            method="bounded",
            options={"xatol": 1e-12},
        )
        result = {
            "optimal_fraction": float(res.x),
            "expected_log_growth": float(-res.fun),
            "solver_status": "ok" if res.success else "warning",
            "solver_message": res.message if hasattr(res, "message") else "",
        }

    f_opt = result["optimal_fraction"]
    e_log_growth = result["expected_log_growth"]

    # ── Monte Carlo simulation for uncertainty (F9 ANTI-HANTU) ───────────
    simulation = _monte_carlo_kelly(p, b, f_opt, n_simulations, n_periods)

    # ── APEX verdict ─────────────────────────────────────────────────────
    apex = compute_apex_verdict(
        optimizer="kelly_sizing",
        solver_status=result["solver_status"],
        solver_termination="optimal"
        if result["solver_status"] == "ok"
        else "suboptimal",
        constraint_violation=0.0,
        input_quality=0.6,  # p is INTERPRETED
        evidence_quality=0.6,
        has_uncertainty_bands=simulation is not None,
    )

    return KellyResult(
        optimal_fraction=f_opt,
        expected_log_growth=e_log_growth,
        win_probability=p,
        odds=b,
        risk_constraint=risk_constraint,
        analytical_fraction=f_analytical,
        solver_status=result["solver_status"],
        apex=apex,
        simulation=simulation,
    ).to_dict()


def _solve_risk_constrained_kelly(p: float, b: float, lam: float) -> Dict[str, Any]:
    """Solve risk-constrained Kelly: max E[log(R)] s.t. E[R^{-λ}] ≤ 1.

    Uses scipy SLSQP with the risk constraint.
    """

    def neg_log_growth(x):
        f = x[0]
        if f <= 0 or f >= 1:
            return 1e10
        return -(p * math.log(1 + b * f) + (1 - p) * math.log(1 - f))

    def risk_constraint_fn(x):
        f = x[0]
        # E[R^{-λ}] = p*(1+bf)^{-λ} + (1-p)*(1-f)^{-λ} ≤ 1
        if f <= 0 or f >= 1:
            return -1.0  # infeasible
        val = p * (1 + b * f) ** (-lam) + (1 - p) * (1 - f) ** (-lam)
        return 1.0 - val  # ≥ 0 means constraint satisfied

    from scipy.optimize import LinearConstraint as LC

    x0 = [0.1]
    constraints = [{"type": "ineq", "fun": risk_constraint_fn}]
    bounds = [(1e-10, 1 - 1e-10)]

    res = minimize(
        neg_log_growth,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-12},
    )

    return {
        "optimal_fraction": float(res.x[0]) if res.success else 0.0,
        "expected_log_growth": float(-res.fun) if res.success else 0.0,
        "solver_status": "ok" if res.success else "warning",
        "solver_message": res.message if hasattr(res, "message") else "",
    }


def _monte_carlo_kelly(
    p: float,
    b: float,
    f: float,
    n_sims: int = 1000,
    n_periods: int = 50,
) -> Dict[str, Any]:
    """Monte Carlo simulation of Kelly growth paths.

    Returns summary statistics of terminal wealth distribution.
    """
    if f <= 1e-10:
        return {
            "terminal_wealth_mean": 1.0,
            "terminal_wealth_median": 1.0,
            "terminal_wealth_p5": 1.0,
            "terminal_wealth_p95": 1.0,
            "n_paths": n_sims,
            "n_periods": n_periods,
        }

    rng = np.random.default_rng(42)
    # Each path: product of (1 + f*R_t) over t periods
    # R_t = +b with prob p, -1 with prob 1-p
    outcomes = rng.binomial(1, p, size=(n_sims, n_periods))
    returns = np.where(outcomes, 1 + b * f, 1 - f)
    terminal_wealth = np.prod(returns, axis=1)

    return {
        "terminal_wealth_mean": round(float(np.mean(terminal_wealth)), 4),
        "terminal_wealth_median": round(float(np.median(terminal_wealth)), 4),
        "terminal_wealth_p5": round(float(np.percentile(terminal_wealth, 5)), 4),
        "terminal_wealth_p95": round(float(np.percentile(terminal_wealth, 95)), 4),
        "terminal_wealth_std": round(float(np.std(terminal_wealth)), 4),
        "n_paths": n_sims,
        "n_periods": n_periods,
    }


def _error_result(msg: str) -> Dict[str, Any]:
    """Return error result dict."""
    return {
        "error": msg,
        "solver_status": "error",
        "epistemic_label": "INTERPRETED",
        "apex": {
            "verdict": "VOID",
            "warnings": [msg],
        },
    }
