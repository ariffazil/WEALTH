"""
well_sabar_latency — Measure temporal compression between stimulus and response.

Measures: response latency, revision latency, volatility, baseline difference.
Does NOT say "loss of sabar" based on speed alone.
"""

import uuid
from datetime import datetime, timezone


def well_sabar_latency(
    events: list[dict],
    baseline_response_latency: float | None = None,
    baseline_revision_latency: float | None = None,
) -> dict:
    """
    Measure temporal compression (sabar latency).

    Args:
        events: List of {stimulus_time, interpretation_time, response_time, revision_time}
        baseline_response_latency: Baseline response time in seconds
        baseline_revision_latency: Baseline revision time in seconds

    Returns:
        {
            "latency_id": str,
            "response_latency": float,
            "revision_latency": float,
            "volatility": float,
            "baseline_delta": float,
            "trajectory": str,
            "interpretation": str,
            "prohibited": [str],
        }
    """
    if not events:
        return {
            "latency_id": f"sl-{uuid.uuid4().hex[:12]}",
            "error": "No events provided",
            "prohibited": ["Cannot infer sabar loss from zero events"],
        }

    response_latencies = []
    revision_latencies = []

    for event in events:
        stimulus = event.get("stimulus_time")
        response = event.get("response_time")
        revision = event.get("revision_time")

        if stimulus and response:
            try:
                s = datetime.fromisoformat(stimulus)
                r = datetime.fromisoformat(response)
                response_latencies.append((r - s).total_seconds())
            except (ValueError, TypeError):
                pass

        if response and revision:
            try:
                r = datetime.fromisoformat(response)
                v = datetime.fromisoformat(revision)
                revision_latencies.append((v - r).total_seconds())
            except (ValueError, TypeError):
                pass

    avg_response = sum(response_latencies) / len(response_latencies) if response_latencies else None
    avg_revision = sum(revision_latencies) / len(revision_latencies) if revision_latencies else None

    # Volatility: standard deviation of response latencies
    if len(response_latencies) > 1:
        mean = avg_response
        variance = sum((x - mean) ** 2 for x in response_latencies) / len(response_latencies)
        volatility = variance ** 0.5
    else:
        volatility = 0.0

    # Baseline delta
    baseline_delta = 0.0
    if baseline_response_latency and avg_response:
        baseline_delta = abs(avg_response - baseline_response_latency) / baseline_response_latency

    # Trajectory interpretation
    trajectory = "STABLE"
    interpretation_parts = []

    if avg_response is not None and baseline_response_latency:
        if avg_response < baseline_response_latency * 0.5:
            trajectory = "ACCELERATING"
            interpretation_parts.append(
                "Response latency is significantly below baseline. "
                "This MAY indicate urgency, focus, or loss of deliberation. "
                "Context required — speed alone is not sabar loss."
            )
        elif avg_response > baseline_response_latency * 1.5:
            trajectory = "DECELERATING"
            interpretation_parts.append(
                "Response latency is above baseline. "
                "This MAY indicate reflection, avoidance, or processing difficulty."
            )
        else:
            interpretation_parts.append("Response latency within normal range.")

    if volatility > baseline_response_latency * 0.3 if baseline_response_latency else False:
        interpretation_parts.append(
            "High volatility in response times. "
            "This MAY indicate inconsistency or variable pressure."
        )

    return {
        "latency_id": f"sl-{uuid.uuid4().hex[:12]}",
        "response_latency": round(avg_response, 2) if avg_response else None,
        "revision_latency": round(avg_revision, 2) if avg_revision else None,
        "volatility": round(volatility, 2),
        "baseline_delta": round(baseline_delta, 4),
        "trajectory": trajectory,
        "interpretation": " ".join(interpretation_parts) or "Insufficient data for interpretation.",
        "event_count": len(events),
        "prohibited": [
            "Cannot declare 'loss of sabar' based on speed alone",
            "Cannot infer impatience without behavioral context",
            "Cannot compare to population norms — individual baseline only",
        ],
        "metadata": {
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "tool": "well_sabar_latency",
        },
    }
