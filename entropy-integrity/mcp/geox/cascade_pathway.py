"""
geox_cascade_pathway — Model how one intervention propagates across
geology, groundwater, infrastructure, ecology, communities, capital exposure.
"""

import uuid
from datetime import datetime, timezone


DOMAINS = ["geology", "groundwater", "infrastructure", "ecology", "communities", "capital"]


def geox_cascade_pathway(
    intervention: str,
    cascade_graph: list[dict],
) -> dict:
    """
    Model cascade propagation across domains.

    Args:
        intervention: Description of the initial intervention
        cascade_graph: [{from_domain, to_domain, mechanism, magnitude, latency, reversibility}]

    Returns:
        Cascade pathway analysis
    """
    # Build adjacency
    affected_domains = set()
    for edge in cascade_graph:
        affected_domains.add(edge.get("from_domain", ""))
        affected_domains.add(edge.get("to_domain", ""))

    # Cascade depth (longest path)
    domain_depths = {d: 0 for d in DOMAINS}
    for edge in cascade_graph:
        to_d = edge.get("to_domain", "")
        from_d = edge.get("from_domain", "")
        domain_depths[to_d] = max(domain_depths[to_d], domain_depths.get(from_d, 0) + 1)

    max_depth = max(domain_depths.values()) if domain_depths else 0

    # Irreversible propagation
    irreversible_edges = [
        e for e in cascade_graph if e.get("reversibility") == "IRREVERSIBLE"
    ]
    irreversible_ratio = len(irreversible_edges) / max(len(cascade_graph), 1)

    # Magnitude propagation
    magnitudes = [e.get("magnitude", 0) for e in cascade_graph]
    max_magnitude = max(magnitudes) if magnitudes else 0
    avg_magnitude = sum(magnitudes) / len(magnitudes) if magnitudes else 0

    return {
        "cascade_id": f"cp-{uuid.uuid4().hex[:12]}",
        "intervention": intervention,
        "affected_domains": sorted(affected_domains),
        "cascade_depth": max_depth,
        "edge_count": len(cascade_graph),
        "irreversible_edges": len(irreversible_edges),
        "irreversible_ratio": round(irreversible_ratio, 4),
        "max_magnitude": round(max_magnitude, 4),
        "avg_magnitude": round(avg_magnitude, 4),
        "domain_depths": {d: v for d, v in domain_depths.items() if v > 0},
        "interpretation": (
            "HIGH cascade potential — intervention propagates widely with irreversible edges"
            if max_depth > 3 or irreversible_ratio > 0.5 else
            "MODERATE cascade potential — some cross-domain propagation"
            if max_depth > 1 else
            "LOW cascade potential — intervention appears contained"
        ),
        "reflection": [
            "What downstream effects are not yet measured?",
            "Which cascade edges are reversible vs irreversible?",
            "Is there a monitoring point at each cascade hop?",
        ],
        "metadata": {
            "modeled_at": datetime.now(timezone.utc).isoformat(),
            "tool": "geox_cascade_pathway",
        },
    }
