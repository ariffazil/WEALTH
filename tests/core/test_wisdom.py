"""
Tests for WEALTH Core — Wisdom Economics.

Six dimensions must all return valid scores.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import pytest

from wealth_core.wisdom import (
    compute_wisdom,
    evaluate_dignity_impact,
    evaluate_sovereignty_risk,
    evaluate_resilience,
    evaluate_inequality_effect,
    evaluate_ecological_cost,
    evaluate_optionality,
    WISDOM_DIMENSIONS,
)


class TestWisdomDimensions:
    """All 6 wisdom dimensions must be present and valid."""

    def test_dimension_count(self):
        assert len(WISDOM_DIMENSIONS) == 6

    def test_dimension_names(self):
        expected = {"dignity", "sovereignty", "resilience",
                    "inequality", "ecological", "optionality"}
        assert set(WISDOM_DIMENSIONS) == expected


class TestDignityImpact:
    """Dignity impact must detect erosion and preservation signals."""

    def test_neutral(self):
        result = evaluate_dignity_impact("invest in bonds", "financial", {})
        assert result["dimension"] == "dignity"
        assert result["score"] == 0.5  # No signals
        assert result["epistemic_tag"] == "ASSUMED"

    def test_erosion_detected(self):
        result = evaluate_dignity_impact(
            "predatory lending to vulnerable communities", "financial", {}
        )
        assert result["score"] < 0.5
        assert result["erosion_signals"] > 0

    def test_preservation_detected(self):
        result = evaluate_dignity_impact(
            "universal access to healthcare with fair wage", "financial", {}
        )
        assert result["score"] > 0.5
        assert result["preservation_signals"] > 0

    def test_score_bounded(self):
        result = evaluate_dignity_impact("anything", "financial", {})
        assert 0.0 <= result["score"] <= 1.0


class TestSovereigntyRisk:
    """Sovereignty risk must detect dependency and autonomy."""

    def test_neutral(self):
        result = evaluate_sovereignty_risk("buy stocks", "financial", {})
        assert result["dimension"] == "sovereignty"
        assert result["score"] == 0.5

    def test_dependency_detected(self):
        result = evaluate_sovereignty_risk(
            "vendor lock-in with proprietary format and no exit clause", "financial", {}
        )
        assert result["score"] < 0.5
        assert result["dependency_signals"] > 0

    def test_autonomy_detected(self):
        result = evaluate_sovereignty_risk(
            "open standard with interoperable and portable data", "financial", {}
        )
        assert result["score"] > 0.5
        assert result["autonomy_signals"] > 0


class TestResilience:
    """Resilience must detect fragility and robustness."""

    def test_neutral(self):
        result = evaluate_resilience("allocate capital", "financial", {})
        assert result["dimension"] == "resilience"
        assert result["score"] == 0.5

    def test_fragility_detected(self):
        result = evaluate_resilience(
            "concentrated undiversified single point of failure", "financial", {}
        )
        assert result["score"] < 0.5
        assert result["fragility_signals"] > 0

    def test_resilience_detected(self):
        result = evaluate_resilience(
            "diversified portfolio with liquid reserve and hedged positions", "financial", {}
        )
        assert result["score"] > 0.5
        assert result["resilience_signals"] > 0


class TestInequalityEffect:
    """Inequality effect must detect widening and narrowing."""

    def test_neutral(self):
        result = evaluate_inequality_effect("invest in index fund", "financial", {})
        assert result["dimension"] == "inequality"
        assert result["score"] == 0.5

    def test_widening_detected(self):
        result = evaluate_inequality_effect(
            "wealth concentration through monopoly profit and rent seeking", "financial", {}
        )
        assert result["score"] < 0.5
        assert result["widen_signals"] > 0

    def test_narrowing_detected(self):
        result = evaluate_inequality_effect(
            "progressive inclusive universal access with financial inclusion", "financial", {}
        )
        assert result["score"] > 0.5
        assert result["narrow_signals"] > 0


class TestEcologicalCost:
    """Ecological cost must detect high and low cost signals."""

    def test_neutral(self):
        result = evaluate_ecological_cost("buy property", "financial", {})
        assert result["dimension"] == "ecological"
        assert result["score"] == 0.5

    def test_high_cost_detected(self):
        result = evaluate_ecological_cost(
            "fossil fuel mining with carbon emission and deforestation", "financial", {}
        )
        assert result["score"] < 0.5
        assert result["high_cost_signals"] > 0

    def test_low_cost_detected(self):
        result = evaluate_ecological_cost(
            "renewable clean energy with carbon neutral and sustainable", "financial", {}
        )
        assert result["score"] > 0.5
        assert result["low_cost_signals"] > 0


class TestOptionalityPreserve:
    """Optionality must detect door-closing and door-opening signals."""

    def test_neutral(self):
        result = evaluate_optionality("make investment", "financial", {})
        assert result["dimension"] == "optionality"
        assert result["score"] == 0.5

    def test_door_closing(self):
        result = evaluate_optionality(
            "irreversible permanent lock-in with no return", "financial", {}
        )
        assert result["score"] < 0.5
        assert result["door_closing_signals"] > 0

    def test_door_opening(self):
        result = evaluate_optionality(
            "reversible flexible staged pilot with option value", "financial", {}
        )
        assert result["score"] > 0.5
        assert result["option_preserving_signals"] > 0


class TestComputeWisdom:
    """compute_wisdom must return all 6 dimensions."""

    def test_all_dimensions_present(self):
        result = compute_wisdom("invest in renewable energy", "financial")
        assert result["all_dimensions_present"] is True
        assert result["dimension_count"] == 6

    def test_dimensions_have_scores(self):
        result = compute_wisdom("invest in renewable energy", "financial")
        for dim in result["dimensions"]:
            assert "dimension" in dim
            assert "score" in dim
            assert "evidence" in dim
            assert "epistemic_tag" in dim
            assert 0.0 <= dim["score"] <= 1.0
