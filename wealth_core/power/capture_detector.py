"""
WEALTH Core — Power Intelligence: Capture Detector.

Is this advice captured by interest?

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from wealth_contracts.epistemic import EpistemicTag

CAPTURE_SIGNALS = [
    "sponsored",
    "partner content",
    "affiliate",
    "paid promotion",
    "conflict of interest",
    "related party",
    "insider",
    "connected",
    "lobbying",
    "regulatory capture",
    "revolving door",
    "self-dealing",
    "tied selling",
    "bundled",
    "captive",
]

INDEPENDENCE_SIGNALS = [
    "independent",
    "fiduciary",
    "arm length",
    "disclosed conflict",
    "third party audit",
    "transparency",
    "open process",
    "competitive bid",
    "disinterested",
    "objective",
]

# Pattern-based detection for known Malaysian/regional governance patterns
# Each pattern: keyword list + weight + description
CAPTURE_PATTERNS: list[dict] = [
    {
        "id": "1mdb_chairman_parallel",
        "keywords": ["1mdb", "1mdb chairman", "parallel structure", "off-book", "sovereign fund bypass"],
        "weight": 0.9,
        "description": "Governance bypass via parallel sovereign fund structures",
    },
    {
        "id": "royal_insulation",
        "keywords": ["royal prerogative", "royal immunity", "sultan", "agong", "royal charter", "istana"],
        "weight": 0.7,
        "description": "Insulation from oversight via royal/constitutional shield",
    },
    {
        "id": "petros_exclusion",
        "keywords": ["petros", "petronas exclusion", "national oil carve-out", "oil royalty bypass"],
        "weight": 0.8,
        "description": "National oil company operating outside standard fiscal oversight",
    },
    {
        "id": "uk_spv",
        "keywords": ["uk spv", "london listing", "offshore spv", "labuan", "special purpose vehicle offshore"],
        "weight": 0.7,
        "description": "Offshore SPV structure reducing domestic transparency",
    },
    {
        "id": "venue_shopping",
        "keywords": ["venue shopping", "jurisdiction shopping", "forum shopping", "arbitration bypass"],
        "weight": 0.6,
        "description": "Selecting jurisdiction to avoid regulatory scrutiny",
    },
    {
        "id": "asymmetric_state_participation",
        "keywords": ["state participation", "government stake", "sovereign wealth fund", "government-linked company", "glc"],
        "weight": 0.7,
        "description": "State participation with asymmetric information advantage",
    },
    {
        "id": "mss_concurrent_jv",
        "keywords": ["management service", "service fee", "concurrent jv", "joint venture management", "technical service fee"],
        "weight": 0.6,
        "description": "Management service structure extracting fee outside ownership",
    },
    {
        "id": "structural_sovereignty_loss",
        "keywords": ["structural adjustment", "imf condition", "bailout condition", "debt trap", "creditor control"],
        "weight": 0.9,
        "description": "Structural sovereignty erosion via debt or conditional financing",
    },
]

WISDOM_PATTERNS: list[dict] = [
    {
        "id": "sovereignty_dependency",
        "keywords": ["foreign control", "strategic asset sale", "national interest", "dependency", "supply chain risk"],
        "weight": 0.8,
        "description": "Capital flow creating strategic dependency",
    },
    {
        "id": "dignity_erosion",
        "keywords": ["worker exploitation", "forced labour", "land grab", "displacement", "indigenous rights"],
        "weight": 0.9,
        "description": "Capital allocation eroding human dignity",
    },
    {
        "id": "resilience_failure",
        "keywords": ["single point of failure", "concentration risk", "just-in-time", "supply chain concentration"],
        "weight": 0.7,
        "description": "Capital structure failing resilience test",
    },
    {
        "id": "ecological_transition",
        "keywords": ["stranded asset", "climate risk", "carbon exposure", "environmental liability", "just transition"],
        "weight": 0.6,
        "description": "Capital exposed to ecological transition risk",
    },
    {
        "id": "optionality_close",
        "keywords": ["lock-in", "exclusivity", "non-compete", "long-term contract", "exit penalty", "vendor lock"],
        "weight": 0.7,
        "description": "Capital allocation closing future optionality",
    },
]


def match_patterns(
    scenario: str,
    patterns: list[dict],
) -> dict:
    """Match scenario text against named patterns. Returns matched pattern IDs + count."""
    scenario_lower = scenario.lower()
    matched = []
    for pattern in patterns:
        hits = sum(1 for kw in pattern["keywords"] if kw in scenario_lower)
        if hits > 0:
            matched.append({
                "pattern_id": pattern["id"],
                "weight": pattern["weight"],
                "hit_count": hits,
                "description": pattern["description"],
            })
    return {
        "matched_patterns": matched,
        "pattern_count": len(matched),
        "total_expected": len(patterns),
        "signal_density": len(matched) / max(1, len(patterns)),
    }


def detect_capture(
    scenario: str,
    actors: list[str],
    context: dict,
) -> dict:
    """
    Detect capture risk in a capital scenario.

    Returns: {dimension, risk_level, evidence, who_benefits, who_carries_downside,
              capture_signals, independence_signals, capture_patterns, wisdom_patterns}
    """
    scenario_lower = scenario.lower()

    # Basic signal counting
    capture_count = sum(
        1 for signal in CAPTURE_SIGNALS if signal in scenario_lower
    )
    independence_count = sum(
        1 for signal in INDEPENDENCE_SIGNALS if signal in scenario_lower
    )

    # Pattern-based detection (Fix 1)
    capture_patterns_result = match_patterns(scenario, CAPTURE_PATTERNS)
    wisdom_patterns_result = match_patterns(scenario, WISDOM_PATTERNS)

    total = capture_count + independence_count
    pattern_bonus = capture_patterns_result["pattern_count"]
    total_signals = total + pattern_bonus

    if total_signals == 0:
        risk_level = "LOW"
        evidence = "No capture signals or patterns detected"
    elif capture_count + pattern_bonus > independence_count * 2:
        risk_level = "CRITICAL"
        evidence = (
            f"Strong capture signals: {capture_count} keywords + {pattern_bonus} patterns "
            f"vs {independence_count} independence signals"
        )
    elif capture_count + pattern_bonus > independence_count:
        risk_level = "HIGH"
        evidence = (
            f"Moderate capture signals: {capture_count} keywords + {pattern_bonus} patterns "
            f"vs {independence_count} independence signals"
        )
    else:
        risk_level = "LOW"
        evidence = f"Independence signals dominate: {independence_count} vs {capture_count} keywords"

    return {
        "dimension": "capture_risk",
        "risk_level": risk_level,
        "evidence": evidence,
        "epistemic_tag": EpistemicTag.INTERPRETED.value,
        "who_benefits": "captured advisor" if capture_count > 0 else "unknown",
        "who_carries_downside": "client/investor" if capture_count > 0 else "unknown",
        "capture_signals": capture_count,
        "independence_signals": independence_count,
        "capture_patterns": capture_patterns_result["matched_patterns"],
        "capture_pattern_count": capture_patterns_result["pattern_count"],
        "wisdom_patterns": wisdom_patterns_result["matched_patterns"],
        "wisdom_pattern_count": wisdom_patterns_result["pattern_count"],
    }
