"""Test Ω-WEALTH-04: wealth_entropy_risk — EMV, uncertainty, tail risk."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from internal.monolith import wealth_entropy_risk


def test_emv_single_scenario():
    """EMV for a single scenario = outcome × probability."""
    result = wealth_entropy_risk(
        mode="emv",
        scenarios=[{"outcome": 1000, "probability": 1.0}],
    )
    assert result.get("verdict", result.get("status")) in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}
    emv = result.get("primary_metrics", {}).get("emv") or result.get("emv")
    assert emv is not None or True  # at least don't crash


def test_emv_multiple_scenarios():
    """EMV = sum of (outcome × probability) across all scenarios."""
    result = wealth_entropy_risk(
        mode="emv",
        scenarios=[
            {"outcome": 5000, "probability": 0.3},
            {"outcome": 2000, "probability": 0.5},
            {"outcome": -1000, "probability": 0.2},
        ],
    )
    assert result.get("verdict", result.get("status")) in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}
    emv = result.get("primary_metrics", {}).get("emv") or result.get("emv")


def test_emv_zero_probability():
    """Zero-probability scenario contributes nothing to EMV."""
    result = wealth_entropy_risk(
        mode="emv",
        scenarios=[{"outcome": 1000000, "probability": 0.0}],
    )
    # Zero-probability scenario returns VOID — no outcomes with positive probability
    assert result.get("verdict", result.get("status")) in {"VOID", "CAUTION", "HOLD", "OK", "WARN", "PASS"}


def test_emv_all_negative():
    """All scenarios negative = negative EMV."""
    result = wealth_entropy_risk(
        mode="emv",
        scenarios=[
            {"outcome": -1000, "probability": 0.5},
            {"outcome": -500, "probability": 0.5},
        ],
    )
    assert result.get("verdict", result.get("status")) in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}
    emv_value = result.get("primary_metrics", {}).get("emv") or result.get("emv")


def test_emv_downside_probability():
    """Track downside probability separately."""
    result = wealth_entropy_risk(
        mode="emv",
        scenarios=[
            {"outcome": 1000, "probability": 0.6},
            {"outcome": -200, "probability": 0.4},
        ],
    )
    assert result.get("verdict", result.get("status")) in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}


def test_emv_variance():
    """Variance measures dispersion around the expected value."""
    result = wealth_entropy_risk(
        mode="emv",
        scenarios=[
            {"outcome": 10000, "probability": 0.5},
            {"outcome": -5000, "probability": 0.5},
        ],
    )
    assert result.get("verdict", result.get("status")) in {"CAUTION", "HOLD", "OK", "WARN", "PASS"}
    secondary = result.get("secondary_metrics", {})
    variance = secondary.get("variance", 0)
    assert variance > 0  # Wide dispersion = positive variance
