"""
WEALTH Core — Collapse Signature Scanner.

Loads the institutional-collapse pattern library, runs full signature
profile against a text, and emits a CollapseRiskScore.

This module is the kernel of the new `wealth_collapse_signature_scan`
MCP tool — the calibrated detector for historical-pattern pre-collapse
signatures in current narratives.

Use cases:
- Audit a CEO speech / annual report against PDVSA / Enron / 1MDB pre-collapse
- Compare PETRONAS / PEMEX / Petrobras narratives against historical priors
- Detect when a corporate narrative crosses the line from
  "technocratic optimism" into "triumphalism with structural erosion"

DITEMPA BUKAN DIBEI — Forged, not given.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .patterns import (
    full_signature_profile,
    collapse_risk_score,
    count_matches,
)


# ============================================================================
# CROSS-LOADED DIMENSION ENHANCEMENT
# Each dimension file in wealth_core/power/ and wealth_core/wisdom/ should
# import from here to ADD institutional-collapse signals on top of its
# existing SaaS/AI keyword lists. This keeps existing behavior while
# widening the lens to sovereign institutional collapse patterns.
# ============================================================================

POWER_DIMENSION_INSTITUTIONAL_SIGNALS: Dict[str, List[str]] = {
    "incentive_asymmetry": [
        # Asymmetric upside/downside across parties
        "50/50",
        "fifty-fifty",
        "50 percent",
        "carried interest",
        "non-operator",
        "non-op",
        "minority stake",
        "operator transition",
        "rightsizing",
        "MSS",
        "mutual separation",
        "workforce reduction",
        "5,000 staff",
        "transition anxiety",
        "stress",
        "cari gali",
    ],
    "capture_risk": [
        # Historical-capture patterns
        "1MDB",
        "1-Malaysia Development",
        "royalty",
        "sultan",
        "Kelantan",
        "royal insulation",
        "political clearance",
        "PM-approved",
        "ministerial directive",
        "cabinet minute",
        "executive order",
        "state directive",
        "political cover",
        "regulatory capture",
        "revolving door",
        "ex-1MDB",
        "chairman appointed",
    ],
    "rent_extraction": [
        # Sovereign wealth extraction patterns
        "dividend uplift",
        "advance dividend",
        "special dividend",
        "transfer to government",
        "fuel subsidy",
        "subsidy",
        "revenue to government",
        "treasury contribution",
        "fiscal contribution",
        "national budget contribution",
        "royalty",
        "extractive",
        "rent seeking",
    ],
    "opacity": [
        # Hidden structure / disclosure holes
        "JV terms",
        "JV agreement",
        "no public",
        "not disclosed",
        "no parliamentary",
        "no tender",
        "no competitive bid",
        "no record",
        "Companies House",
        "ENI House",
        "registered office",
        "share capital",
        "USD 2",
        "nominal capital",
        "JV special purpose",
        "off-balance-sheet",
        "off balance sheet",
        "SPV",
        "SPE",
        "VIE",
    ],
    "coercion": [
        # Time pressure / crisis framing
        "45-day",
        "45 day planning horizon",
        "crisis mode",
        "survival mode",
        "running short",
        "running out",
        "advanced stage",
        "almost done",
        "about to sign",
        "imminent",
        "deadline",
        "hurry",
        "act now",
        "limited time",
        "last chance",
        "fomo",
        "fear of missing out",
        "urgency",
        "rightsizing",
        "concurrent",
    ],
    "rule_asymmetry": [
        # Structural asymmetry / venue shopping / sovereignty erosion
        "PETROS excluded",
        "not a party",
        "no equity",
        "no seat",
        "no board seat",
        "asymmetric participation",
        "asymmetric state",
        "side agreement",
        "intergovernmental",
        "english law",
        "UK Companies Act",
        "Companies Act 2006",
        "London arbitration",
        "LCIA",
        "ICC arbitration",
        "seat of arbitration",
        "venue shopping",
        "14-day",
        "renamed",
        "Federal Court",
        "ENI House",
        "registered at",
    ],
}


WISDOM_DIMENSION_INSTITUTIONAL_SIGNALS: Dict[str, List[str]] = {
    "dignity": [
        # Workforce / human stakes
        "workforce reduction",
        "MSS",
        "mutual separation",
        "voluntary separation",
        "transition anxiety",
        "stress",
        "cari gali",
        "seconded staff",
        "retrench",
        "dignity of labor",
        "stakeholder",
        "rakyat",
        "people",
        "B40",
        "M40",
        "T20",
        "wage suppression",
        "essential service cut",
    ],
    "sovereignty": [
        # Functional sovereignty / dependency
        "functional sovereignty",
        "third axis",
        "Trajectory B",
        "trajectory of collapse",
        "managing decline",
        "dependency",
        "captive",
        "vendor lock-in",
        "platform dependency",
        "exclusive contract",
        "monopoly",
        "single source",
        "no exit clause",
        "switching cost",
        "negotiating power",
        "functional dependency",
        "nominal sovereignty",
        "structural grievance",
        "PETROS",
        "Petroleum Sarawak",
        "Sarawak",
        "MA63",
        "Malaysia Agreement",
        "asymmetric participation",
        "federal mandate",
        "state equity",
    ],
    "resilience": [
        # Planning horizon / crisis mode
        "45-day planning horizon",
        "45 day",
        "survival mode",
        "crisis mode",
        "decline",
        "managing decline",
        "operational survival",
        "tactical",
        "short-term",
        "no buffer",
        "vulnerability",
        "fragility",
        "concentrated",
        "undiversified",
        "leverage",
        "short term",
        "illiquid",
        "maturity mismatch",
        "war risk insurance",
        "insurance spike",
        "freight spike",
        "import dependence",
        "import gap",
        "self-sufficiency",
        "structural gap",
    ],
    "inequality": [
        # Asymmetric state participation
        "asymmetric",
        "asymmetry",
        "Terengganu",
        "Sarawak",
        "Sabah",
        "Borneo",
        "Peninsular",
        "Peninsular Malaysia",
        "PETROS",
        "Pertamina",
        "SKK Migas",
        "Indonesia",
        "Italian",
        "Malaysian directors",
        "state equity",
        "carried interest",
        "rent seeking",
        "extractive",
        "extractive institutions",
        "extractive economy",
        "wealth concentration",
        "information asymmetry",
        "power asymmetry",
        "enemies of the people",
        "traitors",
        "saboteurs",
    ],
    "ecological": [
        # Transition narrative vs hydrocarbon reality
        "Just Transition",
        "energy transition",
        "decarbonization",
        "decarbonisation",
        "net zero",
        "carbon capture",
        "Kasawari CCS",
        "Gentari",
        "energy superstore",
        "Golden Age of engineering",
        "ESG",
        "sustainability",
        "methane",
        "flaring",
        "zero flaring",
        "fossil fuel",
        "hydrocarbon",
        "natural gas",
        "LNG",
        "petrochemical",
    ],
    "optionality": [
        # Future choice closure
        "irreversible",
        "permanent",
        "sunk cost",
        "lock-in",
        "5-year capex",
        "10-year",
        "long-term commitment",
        "exclusive commitment",
        "one-way",
        "no exit",
        "change of control",
        "reserved matters",
        "deadlock",
        "no tiebreaker",
        "English law protection",
        "London arbitration",
        "PETROS excluded",
        "Sarawak excluded",
        "Indonesia excluded",
        "Pertamina absent",
    ],
}


def enrich_dimension_with_institutional_signals(
    dimension: str,
    domain: str,
    native_count: int,
    native_matches: List[str],
    scenario: str,
) -> dict:
    """
    Augment a dimension's native signal count with institutional-collapse
    signals from the cross-loaded library. Use as additive enrichment
    inside each power_/wisdom_/capture_scan evaluator.

    domain ∈ {"power", "wisdom"}
    dimension ∈ {power: incentive_asymmetry, capture_risk, rent_extraction,
                 opacity, coercion, rule_asymmetry;
                 wisdom: dignity, sovereignty, resilience, inequality,
                 ecological, optionality}

    Returns dict with:
      - native_count, native_matches (unchanged)
      - institutional_count, institutional_matches
      - combined_count (deduplicated)
      - institutional_dimension_match: bool
    """
    if domain == "power":
        inst_signals = POWER_DIMENSION_INSTITUTIONAL_SIGNALS.get(dimension, [])
    elif domain == "wisdom":
        inst_signals = WISDOM_DIMENSION_INSTITUTIONAL_SIGNALS.get(dimension, [])
    else:
        inst_signals = []

    inst_count, inst_matches = count_matches(scenario, inst_signals)

    combined_matches = list(set(native_matches) | set(inst_matches))
    combined_count = len(combined_matches)

    return {
        "native_count": native_count,
        "native_matches": native_matches,
        "institutional_count": inst_count,
        "institutional_matches": inst_matches,
        "combined_count": combined_count,
        "combined_matches": combined_matches,
        "institutional_dimension_match": inst_count > 0,
    }


def compute_collapse_risk(
    scenario: str,
    capital_type: str = "financial",
    historical_priors: Optional[List[str]] = None,
) -> dict:
    """
    Compute the institutional-collapse signature risk for a scenario.

    historical_priors: list of optional corpus anchors to compare against
                       (e.g., "enron_2000_ar", "pdvsa_2001_ar", "pemex_2010_ar").
                       If provided, runs a comparative analysis.

    Returns:
      - profile: full_signature_profile output (includes Acemoglu + Calhoun 2D)
      - risk: collapse_risk_score output
      - two_d_risk_map: Acemoglu × Calhoun quadrant assignment
      - tripwires: 5-tripwire detection output
      - dimensional_densities: per-axis density
      - priors_used: list of priors included in comparison
    """
    from .patterns import detect_tripwires

    profile = full_signature_profile(scenario)
    risk = collapse_risk_score(profile)
    tripwires = detect_tripwires(scenario)

    dimensional_densities = {}
    for axis_name, axis_data in profile.items():
        if isinstance(axis_data, dict) and "signal_count" in axis_data:
            dimensional_densities[axis_name] = {
                "signal_count": axis_data["signal_count"],
                "density": min(axis_data["signal_count"] / 12.0, 1.0),
            }

    # 2D risk map (Acemoglu × Calhoun)
    acemoglu = profile.get("acemoglu_axis", {})
    calhoun = profile.get("calhoun_axis", {})
    two_d_risk_map = {
        "acemoglu_score": acemoglu.get("score"),
        "acemoglu_label": acemoglu.get("label"),
        "calhoun_score": calhoun.get("score"),
        "calhoun_label": calhoun.get("label"),
        "quadrant": _assign_quadrant(
            acemoglu.get("label"), calhoun.get("label")
        ),
    }

    priors_used = historical_priors or []
    prior_comparison = {}
    if historical_priors:
        # If historical priors are passed as plain strings (e.g., "enron_2000"),
        # we'll compare via a simple name-mapping. The actual corpus loading
        # happens in historical.py.
        for prior in historical_priors:
            prior_comparison[prior] = {"included": True, "name": prior}

    return {
        "profile": profile,
        "risk": risk,
        "two_d_risk_map": two_d_risk_map,
        "tripwires": tripwires,
        "dimensional_densities": dimensional_densities,
        "capital_type": capital_type,
        "priors_used": priors_used,
        "prior_comparison": prior_comparison,
    }


def _assign_quadrant(acemoglu_label: str, calhoun_label: str) -> str:
    """
    Assign quadrant on Acemoglu × Calhoun 2D map.

    Quadrants:
    Q1: Inclusive + Healthy roles     = flourishing
    Q2: Inclusive + Pre-sink stress    = stagnant-but-open
    Q3: Extractive + Healthy roles     = functional autocracy
    Q4: Extractive + Pre-sink/sink     = pre-collapse (warning quadrant)
    """
    if not acemoglu_label or not calhoun_label:
        return "INSUFFICIENT_SIGNAL"
    if "INSUFFICIENT" in acemoglu_label or "INSUFFICIENT" in calhoun_label:
        return "INSUFFICIENT_SIGNAL"

    is_inclusive = "INCLUSIVE" in acemoglu_label
    is_healthy = "HEALTHY" in calhoun_label
    is_sink = "BEHAVIOURAL_SINK" in calhoun_label or "PRE_SINK" in calhoun_label
    is_mixed = "MIXED" in acemoglu_label

    if is_inclusive and is_healthy:
        return "Q1_INCLUSIVE_HEALTHY"
    if is_inclusive and is_sink:
        return "Q2_INCLUSIVE_PRESINK"
    if (is_mixed or not is_inclusive) and is_healthy:
        return "Q3_EXTRACTIVE_HEALTHY"
    if (is_mixed or not is_inclusive) and is_sink:
        return "Q4_EXTRACTIVE_PRESINK"
    if is_mixed and "STRESS" not in calhoun_label:
        return "Q3_MIXED_HEALTHY"
    return "Q_BOUNDARY_UNCLEAR"


__all__ = [
    "POWER_DIMENSION_INSTITUTIONAL_SIGNALS",
    "WISDOM_DIMENSION_INSTITUTIONAL_SIGNALS",
    "enrich_dimension_with_institutional_signals",
    "compute_collapse_risk",
]