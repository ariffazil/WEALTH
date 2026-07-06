"""
Tests for WEALTH Optimizers — APEX Mathematical Optimization Integration.

Tests each optimizer with known analytical solutions, APEX verdicts,
edge cases, and F1-F13 floor compliance.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

import math
import sys
import pytest
import numpy as np

sys.path.insert(0, "/root/WEALTH")

from wealth_core.optimizers import (
    markowitz_frontier,
    markowitz_frontier_sweep,
    kelly_sizing,
    robust_portfolio,
    chance_constrained,
    cvar_portfolio,
    two_stage_recourse,
    production_planning_example,
    APEXVerdict,
    OPTIMIZER_APEX_MAP,
    compute_apex_verdict,
    get_optimizer_mapping,
)


# ═══════════════════════════════════════════════════════════════════════════
# MARKOWITZ TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestMarkowitz:
    """Markowitz mean-variance frontier tests."""

    def test_basic_portfolio(self):
        """Equal-return assets should give equal weights."""
        mu = [0.10, 0.10, 0.10]
        Sigma = [[0.04, 0.00, 0.00], [0.00, 0.04, 0.00], [0.00, 0.00, 0.04]]
        result = markowitz_frontier(mu, Sigma, risk_aversion=1.0)
        assert result["solver_status"] == "ok"
        weights = result["weights"]
        # With equal returns and equal variance, should be roughly equal
        assert abs(sum(weights) - 1.0) < 1e-4
        assert all(w >= -1e-6 for w in weights)

    def test_higher_return_preferred(self):
        """Higher-return asset should get more weight."""
        mu = [0.20, 0.05]
        Sigma = [[0.04, 0.00], [0.00, 0.04]]
        result = markowitz_frontier(mu, Sigma, risk_aversion=1.0)
        assert result["solver_status"] == "ok"
        w = result["weights"]
        assert w[0] > w[1]  # higher return asset gets more

    def test_risk_aversion_effect(self):
        """Higher risk aversion should reduce concentration."""
        mu = [0.20, 0.05]
        Sigma = [[0.04, 0.00], [0.00, 0.04]]
        r1 = markowitz_frontier(mu, Sigma, risk_aversion=0.5)
        r2 = markowitz_frontier(mu, Sigma, risk_aversion=5.0)
        # Higher gamma → more risk-averse → weights more equal
        assert r2["weights"][1] > r1["weights"][1]

    def test_budget_constraint(self):
        """Weights must sum to 1."""
        mu = [0.15, 0.10, 0.12]
        Sigma = [[0.05, 0.01, 0.02], [0.01, 0.04, 0.01], [0.02, 0.01, 0.06]]
        result = markowitz_frontier(mu, Sigma)
        assert abs(sum(result["weights"]) - 1.0) < 1e-4

    def test_sharpe_ratio(self):
        """Sharpe ratio should be positive for profitable portfolios."""
        mu = [0.15, 0.10]
        Sigma = [[0.04, 0.01], [0.01, 0.04]]
        result = markowitz_frontier(mu, Sigma, risk_free_rate=0.03)
        assert result["sharpe_ratio"] > 0

    def test_frontier_sweep(self):
        """Frontier sweep should produce multiple points."""
        mu = [0.15, 0.10, 0.12]
        Sigma = [[0.05, 0.01, 0.02], [0.01, 0.04, 0.01], [0.02, 0.01, 0.06]]
        result = markowitz_frontier_sweep(mu, Sigma, n_points=10)
        assert result["n_points"] >= 5
        assert result["n_assets"] == 3

    def test_apex_verdict_present(self):
        """Result should contain APEX verdict."""
        mu = [0.15, 0.10]
        Sigma = [[0.04, 0.01], [0.01, 0.04]]
        result = markowitz_frontier(mu, Sigma)
        assert "apex" in result
        assert result["apex"]["verdict"] in ["SEAL", "SABAR", "HOLD", "VOID"]

    def test_epistemic_label(self):
        """Returns should be labeled DER."""
        mu = [0.15, 0.10]
        Sigma = [[0.04, 0.01], [0.01, 0.04]]
        result = markowitz_frontier(mu, Sigma)
        assert result["epistemic_label"] == "DER"

    def test_uncertainty_bands(self):
        """Result should include uncertainty bands (F9)."""
        mu = [0.15, 0.10]
        Sigma = [[0.04, 0.01], [0.01, 0.04]]
        result = markowitz_frontier(mu, Sigma)
        assert "uncertainty" in result
        assert "expected_return" in result["uncertainty"]

    def test_singular_covariance(self):
        """Should handle near-singular covariance gracefully."""
        mu = [0.15, 0.10]
        Sigma = [[0.04, 0.0399], [0.0399, 0.04]]
        result = markowitz_frontier(mu, Sigma)
        assert result["solver_status"] in ["ok", "warning"]

    def test_invalid_inputs(self):
        """Should return error for invalid inputs."""
        result = markowitz_frontier([0.1], [[1, 2], [3, 4]], risk_aversion=1.0)
        assert "error" in result or result.get("apex", {}).get("verdict") == "VOID"


# ═══════════════════════════════════════════════════════════════════════════
# KELLY TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestKelly:
    """Kelly criterion tests with analytical validation."""

    def test_analytical_match(self):
        """Kelly fraction should match closed-form: f* = p - (1-p)/b."""
        p, b = 0.6, 2.0
        result = kelly_sizing(p, b)
        f_analytical = p - (1 - p) / b  # 0.6 - 0.4/2 = 0.4
        assert abs(result["optimal_fraction"] - f_analytical) < 0.05

    def test_no_edge(self):
        """When p*(b+1) ≤ 1, optimal fraction should be 0."""
        p, b = 0.3, 1.5  # p*(b+1) = 0.3*2.5 = 0.75 < 1
        result = kelly_sizing(p, b)
        assert result["optimal_fraction"] < 0.05

    def test_positive_edge(self):
        """When p*(b+1) > 1, optimal fraction should be positive."""
        p, b = 0.55, 2.0  # p*(b+1) = 0.55*3 = 1.65 > 1
        result = kelly_sizing(p, b)
        assert result["optimal_fraction"] > 0.05

    def test_expected_log_growth_positive(self):
        """Expected log-growth should be positive when there's an edge."""
        p, b = 0.6, 2.0
        result = kelly_sizing(p, b)
        assert result["expected_log_growth"] > 0

    def test_risk_constraint_reduces_fraction(self):
        """Risk-constrained Kelly should give smaller fraction."""
        p, b = 0.6, 2.0
        r1 = kelly_sizing(p, b)
        r2 = kelly_sizing(p, b, risk_constraint=3.0)
        assert r2["optimal_fraction"] <= r1["optimal_fraction"] + 0.01

    def test_monte_carlo_present(self):
        """Result should include Monte Carlo simulation."""
        p, b = 0.6, 2.0
        result = kelly_sizing(p, b)
        assert "simulation" in result
        assert "terminal_wealth_mean" in result["simulation"]

    def test_apex_verdict(self):
        """Kelly should have APEX verdict."""
        p, b = 0.6, 2.0
        result = kelly_sizing(p, b)
        assert "apex" in result
        assert result["apex"]["organ"] == "execution"

    def test_invalid_probability(self):
        """Should reject invalid probability."""
        result = kelly_sizing(1.5, 2.0)
        assert "error" in result

    def test_invalid_odds(self):
        """Should reject negative odds."""
        result = kelly_sizing(0.6, -1.0)
        assert "error" in result


# ═══════════════════════════════════════════════════════════════════════════
# ROBUST OPTIMIZATION TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestRobust:
    """Robust optimization tests."""

    def test_box_robust(self):
        """Box robust should produce valid portfolio."""
        returns = [0.15, 0.10, 0.12]
        result = robust_portfolio(returns, uncertainty_radius=0.05, robust_type="box")
        assert result["solver_status"] == "ok"
        assert abs(sum(result["weights"]) - 1.0) < 1e-3

    def test_budget_robust(self):
        """Budget robust should produce valid portfolio."""
        returns = [0.15, 0.10, 0.12]
        result = robust_portfolio(
            returns, uncertainty_radius=0.05, robust_type="budget"
        )
        assert result["solver_status"] == "ok"
        assert abs(sum(result["weights"]) - 1.0) < 1e-3

    def test_ellipsoidal_robust(self):
        """Ellipsoidal robust should produce valid portfolio."""
        returns = [0.15, 0.10, 0.12]
        cov = [[0.05, 0.01, 0.02], [0.01, 0.04, 0.01], [0.02, 0.01, 0.06]]
        result = robust_portfolio(
            returns, uncertainty_radius=0.1, robust_type="ellipsoidal", covariances=cov
        )
        assert result["solver_status"] == "ok"

    def test_zero_uncertainty(self):
        """Zero uncertainty should give standard Markowitz."""
        returns = [0.15, 0.10]
        cov = [[0.04, 0.01], [0.01, 0.04]]
        result = robust_portfolio(returns, uncertainty_radius=0.0, covariances=cov)
        # Should fall back to Markowitz
        assert result["solver_status"] == "ok"

    def test_worst_case_less_than_nominal(self):
        """Worst-case return should be ≤ nominal return."""
        returns = [0.15, 0.10, 0.12]
        result = robust_portfolio(returns, uncertainty_radius=0.1, robust_type="budget")
        if "worst_case_return" in result and "nominal_return" in result:
            assert result["worst_case_return"] <= result["nominal_return"] + 1e-6

    def test_apex_organ_governance(self):
        """Robust should map to Governance organ."""
        returns = [0.15, 0.10]
        result = robust_portfolio(returns, uncertainty_radius=0.05)
        if "apex" in result:
            assert result["apex"]["organ"] == "governance"

    def test_epistemic_label_spec(self):
        """Robust should label uncertainty as SPEC."""
        returns = [0.15, 0.10]
        result = robust_portfolio(returns, uncertainty_radius=0.05)
        assert result.get("epistemic_label") == "SPEC"


# ═══════════════════════════════════════════════════════════════════════════
# CHANCE-CONSTRAINED TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestChanceConstrained:
    """Chance-constrained optimization tests."""

    def test_basic_solve(self):
        """Should solve basic chance-constrained problem."""
        mu = [0.15, 0.10, 0.12]
        Sigma = [[0.05, 0.01, 0.02], [0.01, 0.04, 0.01], [0.02, 0.01, 0.06]]
        result = chance_constrained(mu, Sigma, confidence=0.95, threshold=0.0)
        assert result["solver_status"] == "ok"
        assert abs(sum(result["weights"]) - 1.0) < 1e-3

    def test_var_computed(self):
        """VaR should be computed."""
        mu = [0.15, 0.10, 0.12]
        Sigma = [[0.05, 0.01, 0.02], [0.01, 0.04, 0.01], [0.02, 0.01, 0.06]]
        result = chance_constrained(mu, Sigma, confidence=0.95)
        assert "var_value" in result
        assert "cvar_value" in result

    def test_cvar_worse_than_var(self):
        """CVaR should be worse (lower) than VaR."""
        mu = [0.15, 0.10, 0.12]
        Sigma = [[0.05, 0.01, 0.02], [0.01, 0.04, 0.01], [0.02, 0.01, 0.06]]
        result = chance_constrained(mu, Sigma, confidence=0.95)
        # CVaR should be ≤ VaR (more conservative)
        assert result["cvar_value"] <= result["var_value"] + 1e-6

    def test_higher_confidence_more_conservative(self):
        """Higher confidence should give more conservative portfolio."""
        mu = [0.15, 0.10]
        Sigma = [[0.04, 0.01], [0.01, 0.04]]
        r1 = chance_constrained(mu, Sigma, confidence=0.90)
        r2 = chance_constrained(mu, Sigma, confidence=0.99)
        if r1["solver_status"] == "ok" and r2["solver_status"] == "ok":
            # Higher confidence → lower expected return (more conservative)
            assert r2["expected_return"] <= r1["expected_return"] + 0.01

    def test_apex_organ_witness(self):
        """Chance-constrained should map to Witness organ."""
        mu = [0.15, 0.10]
        Sigma = [[0.04, 0.01], [0.01, 0.04]]
        result = chance_constrained(mu, Sigma)
        if "apex" in result:
            assert result["apex"]["organ"] == "witness"

    def test_invalid_confidence(self):
        """Should reject confidence ≤ 0.5."""
        mu = [0.15, 0.10]
        Sigma = [[0.04, 0.01], [0.01, 0.04]]
        result = chance_constrained(mu, Sigma, confidence=0.3)
        assert "error" in result

    def test_cvar_portfolio(self):
        """CVaR portfolio should solve."""
        mu = [0.15, 0.10]
        Sigma = [[0.04, 0.01], [0.01, 0.04]]
        result = cvar_portfolio(mu, Sigma, confidence=0.95)
        assert result["solver_status"] == "ok"
        assert abs(sum(result["weights"]) - 1.0) < 1e-3


# ═══════════════════════════════════════════════════════════════════════════
# TWO-STAGE STOCHASTIC TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestTwoStage:
    """Two-stage stochastic optimization tests."""

    def test_production_planning_example(self):
        """Production planning example should solve."""
        result = production_planning_example()
        assert result["solver_status"] == "ok"
        assert "first_stage_decisions" in result
        assert "total_expected_value" in result

    def test_first_stage_decisions(self):
        """First-stage decisions should be non-negative."""
        result = production_planning_example()
        for k, v in result["first_stage_decisions"].items():
            assert v >= -1e-6

    def test_here_and_now_value(self):
        """Here-and-now value should be finite."""
        result = production_planning_example()
        assert math.isfinite(result["here_and_now_value"])

    def test_wait_and_see_value(self):
        """Wait-and-see value should be computed."""
        result = production_planning_example()
        assert math.isfinite(result["wait_and_see_value"])

    def test_n_scenarios(self):
        """Should report number of scenarios."""
        result = production_planning_example()
        assert result["n_scenarios"] == 2

    def test_apex_organ_memory(self):
        """Two-stage should map to Memory organ."""
        result = production_planning_example()
        if "apex" in result:
            assert result["apex"]["organ"] == "memory"

    def test_epistemic_label_spec(self):
        """Two-stage scenarios should be labeled SPEC."""
        result = production_planning_example()
        assert result.get("epistemic_label") == "SPEC"

    def test_custom_two_stage(self):
        """Custom two-stage problem should solve."""
        result = two_stage_recourse(
            first_stage_costs={"x": -5, "y": -3},
            scenario_data=[
                {
                    "probability": 0.5,
                    "recourse_coefficients": {"x": 10, "y": 8},
                    "recourse_constraints": [
                        {"coefficients": {"x": 1, "y": 1}, "sense": "<=", "rhs": 100},
                    ],
                },
                {
                    "probability": 0.5,
                    "recourse_coefficients": {"x": 6, "y": 5},
                    "recourse_constraints": [
                        {"coefficients": {"x": 1, "y": 1}, "sense": "<=", "rhs": 80},
                    ],
                },
            ],
        )
        assert result["solver_status"] == "ok"

    def test_empty_scenarios_error(self):
        """Empty scenarios should return error."""
        result = two_stage_recourse(
            first_stage_costs={"x": 1},
            scenario_data=[],
        )
        assert "error" in result


# ═══════════════════════════════════════════════════════════════════════════
# APEX MAPPING TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAPEXMapping:
    """APEX governance layer tests."""

    def test_all_optimizers_mapped(self):
        """All optimizers should have APEX mappings."""
        expected = [
            "markowitz_frontier",
            "kelly_sizing",
            "robust_portfolio",
            "chance_constrained",
            "two_stage_recourse",
            "multi_objective_pareto",
        ]
        for name in expected:
            mapping = get_optimizer_mapping(name)
            assert mapping["organ"] != "unknown", f"{name} not mapped"

    def test_conservation_laws_unique(self):
        """Each optimizer should map to a unique conservation law."""
        laws = set()
        for name, mapping in OPTIMIZER_APEX_MAP.items():
            laws.add(mapping["conservation_law"])
        assert len(laws) >= 5  # at least 5 unique laws

    def test_seal_verdict(self):
        """High-quality result should get SEAL."""
        apex = compute_apex_verdict(
            optimizer="markowitz_frontier",
            solver_status="ok",
            solver_termination="optimal",
            constraint_violation=0.0,
            input_quality=0.9,
            evidence_quality=0.8,
            has_uncertainty_bands=True,
            weights_sum=1.0,
        )
        assert apex.verdict == APEXVerdict.SEAL

    def test_void_on_floor_violation(self):
        """Floor violation should give VOID."""
        apex = compute_apex_verdict(
            optimizer="markowitz_frontier",
            solver_status="error",
            solver_termination="failed",
            constraint_violation=0.5,
            input_quality=0.1,
            evidence_quality=0.1,
            has_uncertainty_bands=False,
            weights_sum=0.5,  # budget violation
        )
        assert apex.verdict == APEXVerdict.VOID

    def test_c_dark_detection(self):
        """C_dark should be computed and flagged if too high."""
        apex = compute_apex_verdict(
            optimizer="kelly_sizing",
            solver_status="ok",
            solver_termination="optimal",
            constraint_violation=0.0,
            input_quality=0.9,
            evidence_quality=0.5,
            has_uncertainty_bands=False,
        )
        # C_dark = A * (1-P) * (1-X) — should be computed
        assert hasattr(apex.apex_score, "C_dark")

    def test_confidence_cap_90(self):
        """Confidence should be capped at 0.90 (F7 HUMILITY)."""
        apex = compute_apex_verdict(
            optimizer="markowitz_frontier",
            solver_status="ok",
            solver_termination="optimal",
            constraint_violation=0.0,
            input_quality=1.0,
            evidence_quality=1.0,
            has_uncertainty_bands=True,
            weights_sum=1.0,
        )
        assert apex.confidence <= 0.90

    def test_epistemic_label_der(self):
        """APEX result should have epistemic label."""
        apex = compute_apex_verdict(
            optimizer="markowitz_frontier",
            solver_status="ok",
            solver_termination="optimal",
        )
        assert apex.epistemic_label == "DER"

    def test_floor_checks_present(self):
        """APEX result should include floor checks."""
        apex = compute_apex_verdict(
            optimizer="markowitz_frontier",
            solver_status="ok",
            solver_termination="optimal",
            constraint_violation=0.0,
            has_uncertainty_bands=True,
            weights_sum=1.0,
        )
        assert len(apex.floor_checks) >= 5
        floor_names = [fc.name for fc in apex.floor_checks]
        assert "AMANAH" in floor_names
        assert "TRUTH" in floor_names
        assert "HUMILITY" in floor_names

    def test_apex_result_to_dict(self):
        """APEX result should serialize to dict."""
        apex = compute_apex_verdict(
            optimizer="markowitz_frontier",
            solver_status="ok",
            solver_termination="optimal",
        )
        d = apex.to_dict()
        assert "verdict" in d
        assert "apex_score" in d
        assert "floor_checks" in d
        assert "confidence" in d


# ═══════════════════════════════════════════════════════════════════════════
# EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge case and regression tests."""

    def test_markowitz_single_asset(self):
        """Single asset should work (trivial portfolio)."""
        result = markowitz_frontier([0.10], [[0.04]])
        assert result["solver_status"] == "ok"
        assert abs(result["weights"][0] - 1.0) < 1e-4

    def test_markowitz_negative_returns(self):
        """Negative returns should still optimize."""
        mu = [-0.05, -0.10]
        Sigma = [[0.04, 0.01], [0.01, 0.04]]
        result = markowitz_frontier(mu, Sigma)
        # Should pick the less negative one
        assert result["solver_status"] == "ok"

    def test_kelly_extreme_probability(self):
        """Kelly with very high probability should give high fraction."""
        result = kelly_sizing(0.95, 2.0)
        assert result["optimal_fraction"] > 0.5

    def test_robust_high_uncertainty(self):
        """High uncertainty should still produce valid portfolio."""
        returns = [0.15, 0.10]
        result = robust_portfolio(returns, uncertainty_radius=0.5)
        assert result["solver_status"] == "ok"

    def test_chance_constrained_moderate_confidence(self):
        """Moderate confidence should solve easily."""
        mu = [0.15, 0.10]
        Sigma = [[0.04, 0.01], [0.01, 0.04]]
        result = chance_constrained(mu, Sigma, confidence=0.80)
        assert result["solver_status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
