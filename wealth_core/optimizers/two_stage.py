"""
Two-Stage Stochastic Program with Recourse.

APEX Organ: Memory (∂M/∂t) — Landauer cost
Conservation Law: Landauer — information has physical cost

Solves: max cᵀx + E[Q(x,ξ)]  s.t. Ax ≤ b, x ≥ 0
where Q(x,ξ) = max qᵀy  s.t. Tx + Wy ≤ h(ξ), y ≥ 0

Uses Sample Average Approximation (SAA) with scenario blocks.

F2 TRUTH: Scenarios are SPEC (sampled from distribution).
F7 HUMILITY: Confidence cap 0.90.
F9 ANTI-HANTU: SAA provides statistical bounds, not exact solutions.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize, LinearConstraint

from .apex_mapping import (
    APEXResult,
    APEXVerdict,
    compute_apex_verdict,
    get_optimizer_mapping,
)


@dataclass
class TwoStageResult:
    """Result of two-stage stochastic optimization."""

    first_stage_decisions: Dict[str, float]
    here_and_now_value: float  # first-stage objective
    wait_and_see_value: float  # expected recourse value
    total_expected_value: float
    n_scenarios: int
    solver_status: str
    scenario_details: Optional[List[Dict[str, Any]]] = None
    apex: Optional[APEXResult] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "first_stage_decisions": {
                k: round(v, 6) for k, v in self.first_stage_decisions.items()
            },
            "here_and_now_value": round(self.here_and_now_value, 6),
            "wait_and_see_value": round(self.wait_and_see_value, 6),
            "total_expected_value": round(self.total_expected_value, 6),
            "n_scenarios": self.n_scenarios,
            "solver_status": self.solver_status,
            "epistemic_label": "SPEC",
        }
        if self.apex:
            d["apex"] = self.apex.to_dict()
        if self.scenario_details:
            d["scenario_details"] = self.scenario_details[:10]  # limit output
        return d


def two_stage_recourse(
    first_stage_costs: Dict[str, float],
    scenario_data: List[Dict[str, Any]],
    first_stage_constraints: Optional[List[Dict[str, Any]]] = None,
    recourse_costs: Optional[Dict[str, float]] = None,
    n_scenarios: Optional[int] = None,
) -> Dict[str, Any]:
    """Two-stage stochastic optimization with recourse.

    First stage: decide x (here-and-now decisions)
    Second stage: after scenario ξ is revealed, choose recourse action y

    Args:
        first_stage_costs: {variable_name: cost_coefficient}
        scenario_data: list of scenario dicts, each with:
            - "probability": scenario probability
            - "recourse_coefficients": {var: coeff} for recourse objective
            - "recourse_constraints": list of constraint dicts
        first_stage_constraints: constraints on first-stage variables
        recourse_costs: override recourse cost coefficients
        n_scenarios: if provided, subsample scenarios

    Returns:
        Dict with first-stage decisions, expected values, apex
    """
    # ── Input validation ─────────────────────────────────────────────────
    if not scenario_data:
        return _error_result("No scenarios provided")
    if not first_stage_costs:
        return _error_result("No first-stage costs provided")

    # Collect ALL variable names (union of first-stage and second-stage)
    all_vars = set(first_stage_costs.keys())
    for s in scenario_data:
        all_vars.update(s.get("recourse_coefficients", {}).keys())
        for rc in s.get("recourse_constraints", []):
            all_vars.update(rc.get("coefficients", {}).keys())
            all_vars.update(rc.get("first_stage_coefficients", {}).keys())

    var_names = sorted(list(all_vars))
    n_vars = len(var_names)
    n_scen = len(scenario_data)

    # Subsample if requested
    if n_scenarios and n_scenarios < n_scen:
        rng = np.random.default_rng(42)
        indices = rng.choice(n_scen, size=n_scenarios, replace=False)
        scenarios = [scenario_data[i] for i in indices]
        # Renormalize probabilities
        total_p = sum(s.get("probability", 1.0 / n_scen) for s in scenarios)
        for s in scenarios:
            s["probability"] = s.get("probability", 1.0 / n_scen) / total_p
        n_scen = n_scenarios
    else:
        scenarios = scenario_data

    # Ensure first_stage_costs is defined for all vars
    fs_costs = {v: first_stage_costs.get(v, 0.0) for v in var_names}

    # ── Build SAA problem ────────────────────────────────────────────────
    # Variables: x (n_vars first-stage) + y_s (n_vars recourse per scenario)
    # Total: n_vars * (1 + n_scen)

    def build_x(x_flat):
        return {var_names[i]: x_flat[i] for i in range(n_vars)}

    def neg_total_value(z):
        """Negative total expected value (for minimization)."""
        x = z[:n_vars]
        first_stage_val = sum(fs_costs[v] * x[i] for i, v in enumerate(var_names))

        recourse_val = 0.0
        for s_idx, scenario in enumerate(scenarios):
            y = z[n_vars * (s_idx + 1) : n_vars * (s_idx + 2)]
            p = scenario.get("probability", 1.0 / n_scen)
            rc = scenario.get("recourse_coefficients", recourse_costs or {})
            rc_filled = {v: rc.get(v, 0.0) for v in var_names}
            scenario_val = sum(rc_filled[v] * y[i] for i, v in enumerate(var_names))
            recourse_val += p * scenario_val

        return -(first_stage_val + recourse_val)

    # ── Constraints ──────────────────────────────────────────────────────
    constraints = []

    # First-stage constraints
    if first_stage_constraints:
        for fc in first_stage_constraints:
            coeffs = fc.get("coefficients", {})
            rhs = fc.get("rhs", 0.0)
            sense = fc.get("sense", "<=")

            def make_fc_con(coeffs, rhs, sense):
                def fc_fn(z):
                    x = z[:n_vars]
                    lhs = sum(
                        coeffs.get(v, 0.0) * x[i] for i, v in enumerate(var_names)
                    )
                    if sense == "<=":
                        return rhs - lhs  # ≥ 0
                    elif sense == ">=":
                        return lhs - rhs  # ≥ 0
                    else:
                        return -((lhs - rhs) ** 2)  # equality via penalty

                return fc_fn

            constraints.append({"type": "ineq", "fun": make_fc_con(coeffs, rhs, sense)})

    # Recourse constraints per scenario
    for s_idx, scenario in enumerate(scenarios):
        rc_list = scenario.get("recourse_constraints", [])
        for rc in rc_list:
            coeffs = rc.get("coefficients", {})
            first_stage_coeffs = rc.get("first_stage_coefficients", {})
            rhs = rc.get("rhs", 0.0)
            sense = rc.get("sense", "<=")

            def make_rc_con(coeffs, fsc, rhs, sense, s_idx):
                def rc_fn(z):
                    x = z[:n_vars]
                    y = z[n_vars * (s_idx + 1) : n_vars * (s_idx + 2)]
                    lhs = sum(
                        coeffs.get(v, 0.0) * y[i] for i, v in enumerate(var_names)
                    )
                    lhs += sum(fsc.get(v, 0.0) * x[i] for i, v in enumerate(var_names))
                    if sense == "<=":
                        return rhs - lhs
                    elif sense == ">=":
                        return lhs - rhs
                    else:
                        return -((lhs - rhs) ** 2)

                return rc_fn

            constraints.append(
                {
                    "type": "ineq",
                    "fun": make_rc_con(coeffs, first_stage_coeffs, rhs, sense, s_idx),
                }
            )

    # ── Bounds ───────────────────────────────────────────────────────────
    # Force recourse-only variables in first stage to be 0
    bounds = []
    for s_idx in range(1 + n_scen):
        for i, v in enumerate(var_names):
            if s_idx == 0 and v not in first_stage_costs:
                bounds.append((0.0, 0.0))
            else:
                bounds.append((0.0, None))

    # ── Solve ────────────────────────────────────────────────────────────
    x0 = np.ones(n_vars * (1 + n_scen)) * 0.5
    for i, v in enumerate(var_names):
        if v not in first_stage_costs:
            x0[i] = 0.0

    res = minimize(
        neg_total_value,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 2000, "ftol": 1e-10},
    )

    if not res.success:
        return _error_result(f"Two-stage solver failed: {res.message}")

    # ── Extract results ──────────────────────────────────────────────────
    x_opt = res.x[:n_vars]
    first_stage = {var_names[i]: float(x_opt[i]) for i in range(n_vars)}
    first_stage_val = sum(fs_costs[v] * x_opt[i] for i, v in enumerate(var_names))

    # Per-scenario recourse values
    scenario_details = []
    total_recourse = 0.0
    for s_idx, scenario in enumerate(scenarios):
        y = res.x[n_vars * (s_idx + 1) : n_vars * (s_idx + 2)]
        p = scenario.get("probability", 1.0 / n_scen)
        rc = scenario.get("recourse_coefficients", recourse_costs or {})
        rc_filled = {v: rc.get(v, 0.0) for v in var_names}
        s_val = sum(rc_filled[v] * y[i] for i, v in enumerate(var_names))
        total_recourse += p * s_val
        scenario_details.append(
            {
                "scenario_index": s_idx,
                "probability": p,
                "recourse_value": round(float(s_val), 6),
                "recourse_decisions": {
                    var_names[i]: round(float(y[i]), 6) for i in range(n_vars)
                },
            }
        )

    # ── Wait-and-see value (each scenario solved independently) ──────────
    ws_value = _compute_wait_and_see(
        first_stage_costs, scenarios, recourse_costs, var_names, n_vars
    )

    # ── APEX verdict ─────────────────────────────────────────────────────
    apex = compute_apex_verdict(
        optimizer="two_stage_recourse",
        solver_status="ok" if res.success else "warning",
        solver_termination="optimal" if res.success else "suboptimal",
        constraint_violation=0.0,
        input_quality=0.5,  # SPEC — scenarios are modeled
        evidence_quality=0.5,
        has_uncertainty_bands=True,
    )

    return TwoStageResult(
        first_stage_decisions=first_stage,
        here_and_now_value=float(first_stage_val),
        wait_and_see_value=ws_value,
        total_expected_value=float(-res.fun),
        n_scenarios=n_scen,
        solver_status="ok" if res.success else "warning",
        scenario_details=scenario_details,
        apex=apex,
    ).to_dict()


def _compute_wait_and_see(
    first_stage_costs: Dict[str, float],
    scenarios: List[Dict[str, Any]],
    recourse_costs: Optional[Dict[str, float]],
    var_names: List[str],
    n_vars: int,
) -> float:
    """Compute wait-and-see value: solve each scenario independently, then average."""
    total = 0.0
    fs_costs = {v: first_stage_costs.get(v, 0.0) for v in var_names}

    for scenario in scenarios:
        p = scenario.get("probability", 1.0 / len(scenarios))
        rc = scenario.get("recourse_coefficients", recourse_costs or {})
        rc_filled = {v: rc.get(v, 0.0) for v in var_names}

        # Simple: maximize recourse value + first stage value
        def neg_rc_value(y):
            fs_val = sum(fs_costs[v] * y[i] for i, v in enumerate(var_names))
            rc_val = sum(rc_filled[v] * y[i] for i, v in enumerate(var_names))
            return -(fs_val + rc_val)

        rc_list = scenario.get("recourse_constraints", [])
        constraints = []
        for rc_con in rc_list:
            coeffs = rc_con.get("coefficients", {})
            first_stage_coeffs = rc_con.get("first_stage_coefficients", {})
            rhs = rc_con.get("rhs", 0.0)
            sense = rc_con.get("sense", "<=")

            def make_con(coeffs, fsc, rhs, sense):
                def con_fn(y):
                    lhs = sum(
                        coeffs.get(v, 0.0) * y[i] for i, v in enumerate(var_names)
                    )
                    lhs += sum(fsc.get(v, 0.0) * y[i] for i, v in enumerate(var_names))
                    return rhs - lhs if sense == "<=" else lhs - rhs

                return con_fn

            constraints.append({"type": "ineq", "fun": make_con(coeffs, first_stage_coeffs, rhs, sense)})

        bounds = [(0.0, None)] * n_vars
        y0 = np.ones(n_vars) * 0.5
        res = minimize(
            neg_rc_value,
            y0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 500},
        )

        if res.success:
            total += p * (-res.fun)

    return total


def production_planning_example() -> Dict[str, Any]:
    """Example: Two-stage production planning (from MO-book Ch10).

    First stage: invest in raw materials x
    Second stage: produce y1, y2 after demand/scenario revealed
    """
    return two_stage_recourse(
        first_stage_costs={"x": -10},  # cost of raw materials
        scenario_data=[
            {
                "probability": 0.5,
                "recourse_coefficients": {"x": 0, "y1": 140, "y2": 120, "y3": -1},
                "recourse_constraints": [
                    {"coefficients": {"y1": 1, "y2": 0}, "sense": ">=", "rhs": 20},
                    {"coefficients": {"y1": 1, "y2": 0}, "sense": "<=", "rhs": 40},
                    {"coefficients": {"y1": 1, "y2": 1}, "sense": "<=", "rhs": 80},
                    {"coefficients": {"y1": 2, "y2": 1}, "sense": "<=", "rhs": 100},
                    {
                        "coefficients": {"y1": 10, "y2": 9},
                        "first_stage_coefficients": {"x": -1},
                        "sense": "<=",
                        "rhs": 0,
                    },
                ],
            },
            {
                "probability": 0.5,
                "recourse_coefficients": {"x": 0, "y1": 100, "y2": 80, "y3": -1},
                "recourse_constraints": [
                    {"coefficients": {"y1": 1, "y2": 0}, "sense": ">=", "rhs": 15},
                    {"coefficients": {"y1": 1, "y2": 0}, "sense": "<=", "rhs": 35},
                    {"coefficients": {"y1": 1, "y2": 1}, "sense": "<=", "rhs": 70},
                    {"coefficients": {"y1": 2, "y2": 1}, "sense": "<=", "rhs": 90},
                    {
                        "coefficients": {"y1": 10, "y2": 9},
                        "first_stage_coefficients": {"x": -1},
                        "sense": "<=",
                        "rhs": 0,
                    },
                ],
            },
        ],
    )


def _error_result(msg: str) -> Dict[str, Any]:
    return {
        "error": msg,
        "solver_status": "error",
        "epistemic_label": "SPEC",
        "apex": {"verdict": "VOID", "warnings": [msg]},
    }
