"""
WEALTH — Governance Singularity Detector (GSD)
═══════════════════════════════════════════════

EUREKA: Financial records capture numbers. Official documents capture words.
Neither captures the GEOMETRY of corporate structure — who sits where,
where governance exists, where it's absent, where value can flow.

A GOVERNANCE SINGULARITY is a point in corporate structure where:
1. Control concentration — same individuals on multiple boards
2. Oversight vacuum — zero independent directors, no audit committee
3. Transparency gradient — public parent → private subsidiary
4. Value flow potential — inter-entity capital path exists
5. Event horizon — stake sale, IPO, or asset transfer pending

When all five conditions converge, normal governance physics breaks down.
Value flows from high-scrutiny to zero-scrutiny through the singularity point.
The flow is ONE-WAY because the private side has no reporting.

This is NOT accounting fraud. It is STRUCTURAL VECTOR ENGINEERING.
It is legal. It is invisible to auditors. But the GEOMETRY reveals it.

DITEMPA BUKAN DIBERI — The singularity is detected, not alleged.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════
# GOVERNANCE SINGULARITY SCORE (GSS)
# ═══════════════════════════════════════════════════════════════════════════


def detect_governance_singularity(
    entities: List[Dict[str, Any]],
    inter_entity_flows: Optional[List[Dict[str, Any]]] = None,
    pending_transactions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Detect governance singularities across a corporate group.

    A governance singularity exists where the SAME individuals control
    MULTIPLE entities with ASYMMETRIC governance, creating a path for
    undetectable value transfer.

    Args:
        entities: List of entity descriptions, each with:
            - name: entity name
            - type: 'parent' | 'subsidiary' | 'joint_venture'
            - public: True if listed/public reporting
            - board: list of {name, role, independent}
            - audit_committee: bool
            - risk_committee: bool
            - independent_directors: int
            - total_directors: int
        inter_entity_flows: Known capital/asset flows between entities
        pending_transactions: Stake sales, IPOs, asset transfers pending

    Returns:
        {
            gss: 0.0-1.0 governance singularity score,
            singularities: [{entity_pair, nexus_individuals, risk_factors, verdict}],
            flow_vectors: [{from, to, type, risk}],
            recommendation: str,
            escalate: bool
        }
    """
    if not entities or len(entities) < 2:
        return {
            "gss": 0.0,
            "verdict": "INSUFFICIENT_DATA",
            "singularities": [],
            "note": "Need >= 2 entities to detect singularities",
        }

    # ── Step 1: Map board overlaps (who sits where?) ──
    board_map: Dict[str, List[Dict[str, str]]] = {}
    for entity in entities:
        for director in entity.get("board", []):
            name = director.get("name", "")
            if name not in board_map:
                board_map[name] = []
            board_map[name].append({
                "entity": entity["name"],
                "role": director.get("role", "director"),
                "independent": director.get("independent", False),
            })

    # ── Step 2: Find nexus individuals (on >= 2 boards) ──
    nexus = {
        name: roles
        for name, roles in board_map.items()
        if len(roles) >= 2
    }

    # ── Step 3: Score each entity's governance density ──
    gov_scores = {}
    for entity in entities:
        score = _governance_density(entity)
        gov_scores[entity["name"]] = score

    # ── Step 4: Detect governance gradients ──
    singularities = []
    for name, roles in nexus.items():
        entities_controlled = [r["entity"] for r in roles]
        scores = [gov_scores.get(e, 0.5) for e in entities_controlled]

        if len(entities_controlled) >= 2:
            gov_gradient = max(scores) - min(scores)
            if gov_gradient > 0.3:  # significant governance asymmetry
                # Find the high-gov and low-gov entities
                high_gov_idx = scores.index(max(scores))
                low_gov_idx = scores.index(min(scores))
                high_gov_entity = entities_controlled[high_gov_idx]
                low_gov_entity = entities_controlled[low_gov_idx]

                risk_factors = []
                if roles[high_gov_idx].get("role", "").lower() in ("ceo", "president", "group ceo"):
                    risk_factors.append(
                        f"{name} is executive at {high_gov_entity} "
                        f"but also controls {low_gov_entity}"
                    )
                if not roles[low_gov_idx].get("independent", False):
                    risk_factors.append(
                        f"{name} is NOT independent at {low_gov_entity}"
                    )
                if gov_gradient > 0.5:
                    risk_factors.append(
                        f"Governance gradient {gov_gradient:.2f}: "
                        f"{high_gov_entity}({max(scores):.2f}) → "
                        f"{low_gov_entity}({min(scores):.2f})"
                    )

                singularities.append({
                    "nexus_individual": name,
                    "entities_controlled": entities_controlled,
                    "governance_gradient": round(gov_gradient, 2),
                    "high_gov_entity": high_gov_entity,
                    "low_gov_entity": low_gov_entity,
                    "roles": [
                        f"{r['role']} at {r['entity']}"
                        + (" (independent)" if r["independent"] else " (not independent)")
                        for r in roles
                    ],
                    "risk_factors": risk_factors,
                    "severity": "CRITICAL" if gov_gradient > 0.5 else (
                        "HIGH" if gov_gradient > 0.3 else "MEDIUM"
                    ),
                })

    # ── Step 5: Score value flow potential ──
    flow_risk = 0.0
    flow_vectors = []
    if inter_entity_flows:
        for flow in inter_entity_flows:
            from_entity = flow.get("from", "")
            to_entity = flow.get("to", "")
            from_score = gov_scores.get(from_entity, 0.5)
            to_score = gov_scores.get(to_entity, 0.5)
            flow_gradient = from_score - to_score
            flow_type = flow.get("type", "unknown")

            vec = {
                "from": from_entity,
                "to": to_entity,
                "type": flow_type,
                "governance_gradient": round(flow_gradient, 2),
                "direction": "high→low scrutiny" if flow_gradient > 0.1 else (
                    "low→high scrutiny" if flow_gradient < -0.1 else "balanced"
                ),
                "risk": "HIGH" if flow_gradient > 0.3 and flow_type in (
                    "capital_injection", "asset_transfer", "guarantee"
                ) else ("MEDIUM" if flow_gradient > 0.1 else "LOW"),
            }
            flow_vectors.append(vec)
            if vec["risk"] == "HIGH":
                flow_risk += 0.2
            elif vec["risk"] == "MEDIUM":
                flow_risk += 0.1

    # ── Step 6: Event horizon risk ──
    event_horizon_risk = 0.0
    horizon_events = []
    if pending_transactions:
        for tx in pending_transactions:
            entity = tx.get("entity", "")
            tx_type = tx.get("type", "")
            entity_score = gov_scores.get(entity, 0.5)

            risk = 0.0
            if tx_type in ("stake_sale", "ipo", "asset_transfer") and entity_score < 0.4:
                risk = 0.3  # low-gov entity with value extraction event
            elif tx_type in ("stake_sale", "ipo"):
                risk = 0.15

            horizon_events.append({
                "entity": entity,
                "type": tx_type,
                "governance_score": round(entity_score, 2),
                "event_risk": round(risk, 2),
            })
            event_horizon_risk += risk

    # ── Step 7: Compute GSS ──
    nexus_risk = min(1.0, len(nexus) * 0.15)
    singularity_risk = min(1.0, len(singularities) * 0.25)
    gradient_risk = 0.0
    for s in singularities:
        gradient_risk += s["governance_gradient"] * 0.3

    gss = min(1.0, nexus_risk + singularity_risk + gradient_risk + flow_risk + event_horizon_risk)

    # ── Step 8: Verdict ──
    if gss >= 0.8:
        verdict = "CRITICAL_SINGULARITY"
        recommendation = (
            "Governance singularity detected. Same individuals control entities "
            "with extreme governance asymmetry. Value can flow from transparent "
            "to opaque without detection. Independent audit of inter-entity "
            "flows required. 888-HOLD on any stake sale or asset transfer."
        )
        escalate = True
    elif gss >= 0.5:
        verdict = "SIGNIFICANT_ASYMMETRY"
        recommendation = (
            "Significant governance asymmetry with board overlap. "
            "Monitor inter-entity flows. Recommend independent directors "
            "on low-governance entities."
        )
        escalate = gss >= 0.65
    elif gss >= 0.3:
        verdict = "MODERATE_RISK"
        recommendation = "Moderate governance asymmetry. Review board composition for independence gaps."
        escalate = False
    else:
        verdict = "HEALTHY"
        recommendation = "No significant governance singularities detected."
        escalate = False

    return {
        "gss": round(gss, 2),
        "verdict": verdict,
        "nexus_individuals": list(nexus.keys()),
        "nexus_count": len(nexus),
        "singularities": singularities,
        "singularity_count": len(singularities),
        "governance_scores": gov_scores,
        "flow_vectors": flow_vectors,
        "flow_risk": round(flow_risk, 2),
        "event_horizon_events": horizon_events,
        "event_horizon_risk": round(event_horizon_risk, 2),
        "recommendation": recommendation,
        "escalate_to_souverign": escalate,
        "epistemic_tag": "CLAIM" if gss >= 0.5 else "HYPOTHESIS",
        "method": "governance_singularity_detection_v1",
        "note": (
            "This tool detects STRUCTURAL patterns, not financial fraud. "
            "A high GSS does not prove wrongdoing — it identifies corporate "
            "structures where wrongdoing would be UNDETECTABLE. "
            "The absence of evidence is not evidence of absence — "
            "but a structure designed to prevent evidence from existing "
            "is itself a governance failure."
        ),
    }


def _governance_density(entity: Dict[str, Any]) -> float:
    """Score governance density from 0 (none) to 1 (maximum).

    Factors:
      - Independent directors / total directors ratio
      - Audit committee presence
      - Risk committee presence  
      - Public reporting (listed = higher transparency)
      - Independent chair
    """
    score = 0.0
    total = entity.get("total_directors", 5)
    independent = entity.get("independent_directors", 0)

    if total > 0:
        # Independent ratio: up to 0.4 points
        indep_ratio = independent / total
        score += min(0.4, indep_ratio * 0.8)

    # Audit committee: 0.2 points
    if entity.get("audit_committee", False):
        score += 0.2

    # Risk committee: 0.15 points
    if entity.get("risk_committee", False):
        score += 0.15

    # Public reporting: 0.15 points
    if entity.get("public", False):
        score += 0.15

    # Independent chair: 0.1 points
    chair = entity.get("board", [])
    if chair and chair[0].get("independent", False):
        score += 0.1

    return round(min(1.0, score), 2)


# ═══════════════════════════════════════════════════════════════════════════
# CANONICAL TEST: PETRONAS vs GENTARI
# ═══════════════════════════════════════════════════════════════════════════

PETRONAS_GENTARI_TEST = {
    "entities": [
        {
            "name": "PETRONAS Group",
            "type": "parent",
            "public": True,
            "board": [
                {"name": "Mohd Bakke Salleh", "role": "Chairman", "independent": True},
                {"name": "Tengku Muhammad Taufik", "role": "President & GCEO", "independent": False},
                {"name": "Liza Mustapha", "role": "EVP & Group CFO", "independent": False},
                {"name": "Azizan Zakaria", "role": "Independent NED", "independent": True},
                {"name": "Zaharah Ibrahim", "role": "Independent NED", "independent": True},
                {"name": "Abdul Rasheed Ghaffour", "role": "Independent NED", "independent": True},
                {"name": "Shahrazat Haji Ahmad", "role": "Non-Independent NED", "independent": False},
            ],
            "audit_committee": True,
            "risk_committee": True,
            "independent_directors": 4,
            "total_directors": 7,
        },
        {
            "name": "Gentari Sdn Bhd",
            "type": "subsidiary",
            "public": False,
            "board": [
                {"name": "Tengku Muhammad Taufik", "role": "Chairman", "independent": False},
                {"name": "Sushil Purohit", "role": "CEO & Managing Director", "independent": False},
                {"name": "Liza Mustapha", "role": "Director", "independent": False},
                {"name": "Girish Nadkarni", "role": "Director", "independent": False},
                {"name": "Ashok Belani", "role": "Director", "independent": False},
            ],
            "audit_committee": False,
            "risk_committee": False,
            "independent_directors": 0,
            "total_directors": 5,
        },
    ],
    "inter_entity_flows": [
        {"from": "PETRONAS Group", "to": "Gentari Sdn Bhd", "type": "capital_injection", "note": "Parent funding — amount undisclosed"},
        {"from": "Gentari Sdn Bhd", "to": "PETRONAS Group", "type": "dividend", "note": "Unknown if Gentari pays upstream dividend"},
    ],
    "pending_transactions": [
        {"entity": "Gentari Sdn Bhd", "type": "stake_sale", "note": "US$300-500M minority stake being explored since Oct 2024"},
    ],
}
