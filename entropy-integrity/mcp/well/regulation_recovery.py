"""
well_regulation_recovery — Measure recovery after activation, not only activation itself.

A human who becomes angry and repairs may have better integrity
than one who remains outwardly calm while suppressing feedback.
"""

import uuid
from datetime import datetime, timezone


def well_regulation_recovery(
    activation_events: list[dict],
    baseline_recovery_time: float | None = None,
) -> dict:
    """
    Measure recovery after activation.

    Args:
        activation_events: List of {activation_time, peak_intensity, recovery_time, repair_action}
        baseline_recovery_time: Baseline recovery time in seconds

    Returns:
        Recovery assessment
    """
    if not activation_events:
        return {
            "recovery_id": f"rr-{uuid.uuid4().hex[:12]}",
            "error": "No activation events provided",
        }

    recovery_times = []
    repair_count = 0
    total_events = len(activation_events)

    for event in activation_events:
        activation = event.get("activation_time")
        recovery = event.get("recovery_time")

        if activation and recovery:
            try:
                a = datetime.fromisoformat(activation)
                r = datetime.fromisoformat(recovery)
                recovery_times.append((r - a).total_seconds())
            except (ValueError, TypeError):
                pass

        if event.get("repair_action"):
            repair_count += 1

    avg_recovery = sum(recovery_times) / len(recovery_times) if recovery_times else None
    repair_rate = repair_count / total_events if total_events > 0 else 0.0

    # Recovery score: faster recovery + more repair = better
    if avg_recovery and baseline_recovery_time:
        recovery_ratio = avg_recovery / baseline_recovery_time
        if recovery_ratio < 0.7:
            recovery_quality = "FAST_RECOVERY"
        elif recovery_ratio < 1.3:
            recovery_quality = "NORMAL_RECOVERY"
        else:
            recovery_quality = "SLOW_RECOVERY"
    else:
        recovery_quality = "UNKNOWN"

    return {
        "recovery_id": f"rr-{uuid.uuid4().hex[:12]}",
        "avg_recovery_time": round(avg_recovery, 2) if avg_recovery else None,
        "repair_rate": round(repair_rate, 4),
        "recovery_quality": recovery_quality,
        "event_count": total_events,
        "interpretation": (
            "Strong regulation — fast recovery with active repair" if recovery_quality == "FAST_RECOVERY" and repair_rate > 0.5 else
            "Normal regulation — recovery within baseline" if recovery_quality == "NORMAL_RECOVERY" else
            "Slow regulation — recovery time elevated" if recovery_quality == "SLOW_RECOVERY" else
            "Insufficient data for interpretation"
        ),
        "key_insight": (
            "Activation itself is not the signal. Recovery and repair are the signal."
        ),
        "prohibited": [
            "Cannot declare 'poor regulation' from activation alone",
            "Cannot compare to population norms",
            "Cannot use as permanent trait classification",
        ],
        "metadata": {
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "tool": "well_regulation_recovery",
        },
    }
