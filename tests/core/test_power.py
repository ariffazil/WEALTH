"""
Tests for WEALTH Core — Power Intelligence.

Six dimensions must all return valid risk levels.
DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations


from wealth_core.power import (
    audit_power,
    map_incentives,
    detect_capture,
    detect_rent_extraction,
    score_opacity,
    detect_coercion,
    detect_rule_asymmetry,
    POWER_DIMENSIONS,
)


class TestPowerDimensions:
    """All 6 power dimensions must be present and valid."""

    def test_dimension_count(self):
        assert len(POWER_DIMENSIONS) == 6

    def test_dimension_names(self):
        expected = {"incentive_asymmetry", "capture_risk", "rent_extraction",
                    "opacity", "coercion", "rule_asymmetry"}
        assert set(POWER_DIMENSIONS) == expected


class TestIncentiveMap:
    """Incentive mapping must detect benefit and downside signals."""

    def test_no_signals(self):
        result = map_incentives("buy bonds", [], {})
        assert result["dimension"] == "incentive_asymmetry"
        assert result["risk_level"] == "LOW"

    def test_benefit_skew(self):
        result = map_incentives(
            "commission and fee with spread markup for the advisor",
            ["advisor", "client"],
            {},
        )
        assert result["risk_level"] in ("MEDIUM", "HIGH")
        assert result["benefit_signals"] > 0

    def test_with_actors(self):
        result = map_incentives(
            "deal with commission",
            ["broker", "investor"],
            {},
        )
        assert result["who_benefits"] == "broker"
        assert result["who_carries_downside"] == "investor"


class TestCaptureDetector:
    """Capture detection must find conflicts of interest."""

    def test_no_signals(self):
        result = detect_capture("independent analysis", [], {})
        assert result["dimension"] == "capture_risk"
        assert result["risk_level"] == "LOW"

    def test_capture_detected(self):
        result = detect_capture(
            "sponsored content with affiliate link and conflict of interest",
            [],
            {},
        )
        assert result["risk_level"] in ("HIGH", "CRITICAL")
        assert result["capture_signals"] > 0

    def test_independence_detected(self):
        result = detect_capture(
            "independent fiduciary with third party audit and transparency",
            [],
            {},
        )
        assert result["risk_level"] == "LOW"
        assert result["independence_signals"] > 0


class TestRentExtraction:
    """Rent extraction must detect hidden fees."""

    def test_no_signals(self):
        result = detect_rent_extraction("buy ETF", [], {})
        assert result["dimension"] == "rent_extraction"
        assert result["risk_level"] == "LOW"

    def test_rent_detected(self):
        result = detect_rent_extraction(
            "hidden fee with spread markup and trailing commission",
            [],
            {},
        )
        assert result["risk_level"] in ("MEDIUM", "HIGH")
        assert result["rent_signals"] > 0

    def test_transparency_detected(self):
        result = detect_rent_extraction(
            "all-in cost with transparent pricing and no hidden fee",
            [],
            {},
        )
        assert result["risk_level"] == "LOW"
        assert result["transparent_signals"] > 0


class TestOpacityScorer:
    """Opacity scoring must detect valuation transparency."""

    def test_no_signals(self):
        result = score_opacity("standard valuation", [], {})
        assert result["dimension"] == "opacity"
        assert result["risk_level"] == "LOW"

    def test_opaque(self):
        result = score_opacity(
            "black box proprietary model with unaudited management estimate",
            [],
            {},
        )
        assert result["risk_level"] == "HIGH"
        assert result["opaque_signals"] > 0

    def test_transparent(self):
        result = score_opacity(
            "audited market price with observable input and third party valuation",
            [],
            {},
        )
        assert result["risk_level"] == "LOW"
        assert result["transparent_signals"] > 0


class TestCoercionDetector:
    """Coercion detection must find time-pressure tactics."""

    def test_no_signals(self):
        result = detect_coercion("consider this investment", [], {})
        assert result["dimension"] == "coercion"
        assert result["risk_level"] == "LOW"

    def test_coercion_detected(self):
        result = detect_coercion(
            "act now limited time last chance dont miss this opportunity",
            [],
            {},
        )
        assert result["risk_level"] in ("HIGH", "CRITICAL")
        assert result["coercion_signals"] > 0

    def test_no_pressure(self):
        result = detect_coercion(
            "no rush take your time consider carefully due diligence",
            [],
            {},
        )
        assert result["risk_level"] == "LOW"
        assert result["no_pressure_signals"] > 0


class TestRuleAsymmetry:
    """Rule asymmetry must detect unilateral power."""

    def test_no_signals(self):
        result = detect_rule_asymmetry("standard contract", [], {})
        assert result["dimension"] == "rule_asymmetry"
        assert result["risk_level"] == "LOW"

    def test_asymmetry_detected(self):
        result = detect_rule_asymmetry(
            "sole discretion to amend without notice subject to change at will",
            [],
            {},
        )
        assert result["risk_level"] in ("MEDIUM", "HIGH")
        assert result["rule_change_signals"] > 0

    def test_protection_detected(self):
        result = detect_rule_asymmetry(
            "bilateral mutual consent fixed terms guaranteed irrevocable vested",
            [],
            {},
        )
        assert result["risk_level"] == "LOW"
        assert result["protection_signals"] > 0


class TestAuditPower:
    """audit_power must return all 6 dimensions."""

    def test_all_dimensions_present(self):
        result = audit_power("invest in stock", ["broker", "investor"])
        assert result["all_dimensions_present"] is True
        assert result["dimension_count"] == 6

    def test_overall_capture_risk(self):
        result = audit_power(
            "sponsored content with hidden fee act now limited time",
            ["advisor", "client"],
        )
        assert result["overall_capture_risk"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_dimensions_have_risk_levels(self):
        result = audit_power("standard investment", [])
        for dim in result["dimensions"]:
            assert "dimension" in dim
            assert "risk_level" in dim
            assert dim["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
            assert "evidence" in dim
