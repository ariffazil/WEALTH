"""
wealth_metric_purpose_audit — Audit whether KPIs serve their declared purpose
or have become the purpose themselves.

Detects: proxy drift, metric capture, externalities, gaming incentives, purpose fidelity.
"""

import uuid
from datetime import datetime, timezone


def wealth_metric_purpose_audit(
    declared_purpose: str,
    current_kpis: list[dict],
    actual_behaviors: list[str],
    excluded_outcomes: list[str] | None = None,
) -> dict:
    """
    Audit metric-purpose alignment.

    Args:
        declared_purpose: Stated purpose of the system/decision
        current_kpis: [{name, target, weight, measured_outcome}]
        actual_behaviors: Observed behaviors driven by the metrics
        excluded_outcomes: Outcomes not captured by any KPI

    Returns:
        Metric purpose audit with drift detection
    """
    # Analyze KPI-purpose alignment
    purpose_words = set(declared_purpose.lower().split())
    kpi_alignment = []
    gaming_signals = []

    for kpi in current_kpis:
        kpi_words = set(kpi.get("name", "").lower().split())
        overlap = purpose_words & kpi_words
        alignment = len(overlap) / max(len(purpose_words | kpi_words), 1)
        kpi_alignment.append({
            "kpi": kpi.get("name"),
            "alignment": round(alignment, 4),
            "weight": kpi.get("weight", 0),
        })

        # Gaming detection: if measured_outcome is always at target
        target = kpi.get("target")
        measured = kpi.get("measured_outcome")
        if target is not None and measured is not None:
            if abs(measured - target) < 0.01:
                gaming_signals.append(f"KPI '{kpi.get('name')}' consistently at target — possible gaming")

    # Purpose fidelity
    if kpi_alignment:
        avg_alignment = sum(k["alignment"] for k in kpi_alignment) / len(kpi_alignment)
    else:
        avg_alignment = 0.0

    # Externalities: outcomes not captured
    externality_count = len(excluded_outcomes or [])

    return {
        "audit_id": f"mpa-{uuid.uuid4().hex[:12]}",
        "declared_purpose": declared_purpose,
        "kpi_alignment": kpi_alignment,
        "purpose_fidelity": round(avg_alignment, 4),
        "gaming_signals": gaming_signals,
        "externality_count": externality_count,
        "excluded_outcomes": excluded_outcomes or [],
        "interpretation": (
            "Metrics appear well-aligned with stated purpose" if avg_alignment > 0.6 else
            "Significant proxy drift — metrics may have become the purpose"
            if avg_alignment < 0.3 else
            "Moderate drift — some metrics may be proxies for the real purpose"
        ),
        "reflection": [
            "Are the KPIs measuring the purpose, or have they become the purpose?",
            "What outcomes are excluded from measurement?",
            "Would the behaviors change if the KPIs were removed?",
        ],
        "metadata": {
            "audited_at": datetime.now(timezone.utc).isoformat(),
            "tool": "wealth_metric_purpose_audit",
        },
    }
