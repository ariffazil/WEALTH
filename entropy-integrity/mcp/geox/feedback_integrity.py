"""
geox_feedback_integrity — Check whether physical monitoring is sufficient to detect drift.

Measures: sensor coverage, baseline quality, missing measurements,
reporting delay, threshold manipulation, excluded anomalies.
"""

import uuid
from datetime import datetime, timezone


def geox_feedback_integrity(
    monitoring_system: str,
    sensor_coverage_pct: float,
    baseline_quality: str = "UNKNOWN",
    missing_measurements: list[str] | None = None,
    reporting_delay_hours: float = 0,
    threshold_manipulation_detected: bool = False,
    excluded_anomalies: list[str] | None = None,
) -> dict:
    """
    Assess monitoring feedback integrity.

    Returns:
        Feedback integrity assessment
    """
    # Coverage score
    coverage_score = sensor_coverage_pct / 100

    # Baseline quality
    baseline_scores = {"EXCELLENT": 0.9, "GOOD": 0.7, "ADEQUATE": 0.5, "POOR": 0.3, "UNKNOWN": 0.4}
    baseline_score = baseline_scores.get(baseline_quality.upper(), 0.4)

    # Missing measurements penalty
    missing_count = len(missing_measurements or [])
    missing_penalty = min(0.5, missing_count * 0.1)

    # Reporting delay penalty
    delay_penalty = min(0.3, reporting_delay_hours / 168)  # 1 week = max penalty

    # Threshold manipulation (critical)
    manipulation_penalty = 0.4 if threshold_manipulation_detected else 0.0

    # Excluded anomalies (critical)
    anomaly_penalty = min(0.3, len(excluded_anomalies or []) * 0.1)

    # Composite integrity score
    integrity = max(0.0, min(1.0,
        coverage_score * 0.3 +
        baseline_score * 0.2 -
        missing_penalty -
        delay_penalty -
        manipulation_penalty -
        anomaly_penalty
    ))

    return {
        "integrity_id": f"fi-{uuid.uuid4().hex[:12]}",
        "monitoring_system": monitoring_system,
        "integrity_score": round(integrity, 4),
        "coverage_score": round(coverage_score, 4),
        "baseline_score": round(baseline_score, 4),
        "missing_measurements": missing_measurements or [],
        "reporting_delay_hours": reporting_delay_hours,
        "threshold_manipulation_detected": threshold_manipulation_detected,
        "excluded_anomalies": excluded_anomalies or [],
        "interpretation": (
            "STRONG feedback integrity — monitoring sufficient to detect drift"
            if integrity > 0.7 else
            "WEAK feedback integrity — monitoring gaps may hide drift"
            if integrity > 0.4 else
            "CRITICAL feedback integrity — monitoring insufficient"
        ),
        "reflection": [
            "What sensors are missing?",
            "Are thresholds set to detect meaningful change or to avoid alerts?",
            "What anomalies have been excluded and why?",
        ],
        "metadata": {
            "assessed_at": datetime.now(timezone.utc).isoformat(),
            "tool": "geox_feedback_integrity",
        },
    }
