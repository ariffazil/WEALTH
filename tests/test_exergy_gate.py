"""
tests/test_exergy_gate.py

Tests for the WEALTH exergy engine (Tier 5 DRAFT — 888 HOLD ACTIVE).
"""

from __future__ import annotations

import pytest

from internal.engines.exergy import (
    ExergyError,
    calculate_exergy,
    downgrade_verdict_by_exergy,
    exergy_gate,
)
from internal.engines.five_seals import compute_five_seals


class TestCalculateExergy:
    def test_seal_when_eta_at_threshold(self):
        result = calculate_exergy(npv_realized=700_000.0, allocated_capital=1_000.0)
        assert result.eta_x == pytest.approx(0.70)
        assert result.verdict == "SEAL"

    def test_void_when_eta_below_threshold(self):
        result = calculate_exergy(npv_realized=100.0, allocated_capital=1_000.0)
        assert result.verdict == "VOID"
        assert result.meets_threshold is False

    def test_delta_s_increases_requirement(self):
        low_entropy = calculate_exergy(
            npv_realized=700_000.0, allocated_capital=1_000.0, delta_s_allocation=0.0
        )
        high_entropy = calculate_exergy(
            npv_realized=700_000.0, allocated_capital=1_000.0, delta_s_allocation=1.0
        )
        assert high_entropy.eta_x < low_entropy.eta_x

    def test_invalid_capital_raises(self):
        with pytest.raises(ValueError):
            calculate_exergy(npv_realized=100.0, allocated_capital=0.0)
        with pytest.raises(ValueError):
            calculate_exergy(npv_realized=100.0, allocated_capital=-100.0)


class TestExergyGate:
    def test_passes_without_raise(self):
        report = exergy_gate(npv_realized=700_000.0, allocated_capital=1_000.0)
        assert report["meets_threshold"] is True
        assert report["verdict"] == "SEAL"

    def test_heat_waste_raises(self):
        with pytest.raises(ExergyError) as exc_info:
            exergy_gate(npv_realized=100.0, allocated_capital=1_000.0)
        assert exc_info.value.eta_x < 0.70

    def test_non_blocking_mode(self):
        report = exergy_gate(
            npv_realized=100.0, allocated_capital=1_000.0, raise_on_heat_waste=False
        )
        assert report["meets_threshold"] is False
        assert report["verdict"] == "VOID"


class TestVerdictDowngrade:
    def test_seal_preserved(self):
        result = downgrade_verdict_by_exergy(
            "SEAL", npv_realized=700_000.0, allocated_capital=1_000.0
        )
        assert result["original_verdict"] == "SEAL"
        assert result["adjusted_verdict"] == "SEAL"

    def test_seal_downgraded_to_void(self):
        result = downgrade_verdict_by_exergy(
            "SEAL", npv_realized=100.0, allocated_capital=1_000.0
        )
        assert result["original_verdict"] == "SEAL"
        assert result["adjusted_verdict"] == "VOID"
        assert result["exergy"]["verdict"] == "VOID"


class TestFiveSealsExergyIntegration:
    def test_exergy_pass_keeps_value_seal(self):
        seals = compute_five_seals(
            {
                "npv": 100,
                "irr": 0.1,
                "dscr": 1.5,
                "npv_realized": 700_000.0,
                "allocated_capital": 1_000.0,
            },
            "test_tool",
        )
        assert seals["exergy_gate"]["meets_threshold"] is True
        assert seals["value_seal"] != "HEAT_WASTE"

    def test_exergy_fail_downgrades_value_seal(self):
        seals = compute_five_seals(
            {
                "npv": 100,
                "irr": 0.1,
                "dscr": 1.5,
                "npv_realized": 100.0,
                "allocated_capital": 1_000.0,
            },
            "test_tool",
        )
        assert seals["exergy_gate"]["meets_threshold"] is False
        assert seals["value_seal"] == "HEAT_WASTE"

    def test_no_exergy_keys_skips_gate(self):
        seals = compute_five_seals(
            {"npv": 100, "irr": 0.1, "dscr": 1.5}, "test_tool"
        )
        assert "exergy_gate" not in seals
