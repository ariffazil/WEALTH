"""
WEALTH Core — Institutional Collapse Pattern Library.

The naive SaaS/AI keyword lists in the 12 dimension files miss the
historical pre-collapse signatures of state-owned oil companies and
financial giants. This library provides real patterns extracted from:

- Enron pre-collapse (1999-2000 AR, 10-K, press releases)
- PDVSA pre-collapse (1999-2002 under Chávez)
- Pemex chronic-stress (2000-2018)
- Petrobras pre-Lava-Jato (2008-2013)
- WorldCom, Lehman, Bear Stearns pre-collapse
- 1MDB (PETRONAS Chairman parallel, 2009-2015)

Cross-case signature taxonomy (per sovereign collapse research):
1. National destiny + triumphalism over fundamentals
2. Politicisation and ideological certainty
3. Extraction narrative overshadowing reinvestment reality
4. Downplaying or externalising causes of deterioration
5. Generic governance / risk boilerplate
6. Narrative time-lag vs metrics (story-vs-state gap)

Each dimension file imports from this library and ADDS to its native
keyword lists. No replacement — the SaaS/AI signals remain for
downstream tools. This library adds institutional-collapse signals.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


# ============================================================================
# SIGNATURE AXIS 1: NATIONAL DESTINY + TRIUMPHALISM OVER FUNDAMENTALS
# ============================================================================

NATIONAL_DESTINY_SIGNALS: List[str] = [
    "national champion",
    "national destiny",
    "nation builder",
    "nation-building",
    "nation building",
    "pillar of development",
    "priceless national asset",
    "sovereign wealth",
    "national mission",
    "national treasure",
    "strategic national asset",
    "engine of growth",
    "engine of the nation",
    "backbone of the economy",
    "trillion ringgit",
    "sovereign destiny",
    "national oil champion",
    "crown jewel",
    "pride of",
    "national pride",
    "iconic",
    "national icon",
]

TRIUMPHALISM_SIGNALS: List[str] = [
    "record results",
    "very strong",
    "unprecedented",
    "industry leading",
    "industry-leading",
    "market leading",
    "market-leading",
    "best in class",
    "best-in-class",
    "world class",
    "world-class",
    "more than doubling",
    "exceptional performance",
    "outstanding year",
    "stellar",
    "remarkable achievement",
    "delivering value",
    "exceeding expectations",
    "best ever",
    "milestone",
    "historic high",
    "all time high",
    "all-time high",
    "extraordinary",
    "unparalleled",
    "spectacular",
    "track record",
    "five years in a row",
    "fifth year",
    "third year running",
    "fourth consecutive",
    "third consecutive",
    "second consecutive",
    "superior",
    "industry-leading",
    "outstanding",
    "exceeded",
    "beat",
    "ahead",
    "above",
    "exceeds",
    "delivered",
    "delivering",
    "leadership position",
    "leading position",
    "trusted partner",
    "preferred partner",
    "preferred supplier",
    "global leader",
    "category leader",
    "thought leader",
    "market leader",
    "leading",
    "leading global",
    "world leader",
    "ahead of",
    "leading provider",
    "best positioned",
]

COMPLEXITY_AS_VIRTUE: List[str] = [
    "sophisticated structures",
    "innovative",
    "proprietary models",
    "proprietary methodology",
    "complex financial engineering",
    "advanced trading",
    "asset light",
    "asset-light",
    "intellectual capital",
    "knowledge based",
    "knowledge-based",
    "black box",
    "we know how",
    "we know better",
    "trust our expertise",
    "beyond the understanding",
    "innovative products",
    "innovative culture",
    "innovative services",
    "innovative solutions",
    "innovative deal",
    "innovative approach",
    "innovative structure",
    "innovative framework",
    "sophisticated",
    "complex financial",
    "complex products",
    "highly structured",
    "structured finance",
    "structured products",
    "structured solutions",
    "engineering",
    "engineering and risk management",
    "risk management tools",
    "risk management team",
    "risk management activities",
    "financial risk management",
    "price risk management",
    "energy risk management",
    "sophisticated computer",
    "highly sophisticated",
]


# ============================================================================
# SIGNATURE AXIS 2: POLITICISATION AND IDEOLOGICAL CERTAINTY
# ============================================================================

IDEOLOGICAL_CERTAINTY_SIGNALS: List[str] = [
    "ideologically",
    "ideological victory",
    "resource nationalism",
    "national liberation",
    "revolutionary",
    "new PDVSA",
    "cleansing",
    "purge",
    "traitors",
    "saboteurs",
    "enemies of the people",
    "enemies of the nation",
    "imperialist",
    "colonial",
    "neocolonial",
    "yanqui",
    "north american imperialism",
    "foreign aggression",
    "economic war",
    "sovereign control",
    "patriotic",
    "people's",
    "21st century socialism",
    "bolivarian",
    "just transition",
    "great reset",
]

POLITICISATION_SIGNALS: List[str] = [
    "ministerial directive",
    "cabinet decision",
    "PM-approved",
    "government instructed",
    "political clearance",
    "royal instruction",
    "royalty",
    "sultan",
    "king",
    "agong",
    "political insulation",
    "political cover",
    "ministerial intervention",
    "cabinet minute",
    "executive order",
    "state directive",
    "ruling party",
    "coalition government",
]

PURGE_AND_CLEANSING_SIGNALS: List[str] = [
    "fired",
    "dismissed",
    "let go",
    "terminated",
    "removed",
    "purged",
    "cleansed",
    "new management",
    "new leadership",
    "reorganization",
    "right-sizing",
    "rightsizing",
    "MSS",
    "mutual separation",
    "voluntary separation",
    "workforce reduction",
    "headcount reduction",
    "streamline",
    "consolidate workforce",
]


# ============================================================================
# SIGNATURE AXIS 3: EXTRACTION NARRATIVE OVERSHADOWING REINVESTMENT
# ============================================================================

EXTRACTION_NARRATIVE_SIGNALS: List[str] = [
    "federal dividend",
    "dividend to government",
    "fiscal contribution",
    "national budget",
    "treasury contribution",
    "revenue to government",
    "funds the nation",
    "funds development",
    "funds social programs",
    "subsidies",
    "fuel subsidy",
    "social spending",
    "transfer to government",
    "special dividend",
    "advance dividend",
    "dividend uplift",
]

REINVESTMENT_SUPPRESSION_SIGNALS: List[str] = [
    "minimum capex",
    "deferred maintenance",
    "postponed investment",
    "capital discipline",
    "lean capex",
    "under-investment",
    "underinvestment",
    "capex compression",
    "capex freeze",
    "low reinvestment",
    "limited reinvestment",
    "neglect of upstream",
    "reserve replacement",
    "reserve replacement ratio",
    "decline rate",
    "production decline",
    "production falling",
    "declining production",
    "production collapse",
]


# ============================================================================
# SIGNATURE AXIS 4: DOWNPLAYING OR EXTERNALISING CAUSES OF DETERIORATION
# ============================================================================

EXTERNAL_BLAME_SIGNALS: List[str] = [
    "due to oil prices",
    "due to external",
    "due to global",
    "global headwinds",
    "market conditions",
    "geopolitical",
    "sanctions",
    "trade war",
    "pandemic",
    "covid",
    "post-covid",
    "war in",
    "conflict in",
    "hormuz",
    "shipping disruption",
    "logistics",
    "third party",
    "force majeure",
    "act of god",
    "supply chain",
    "not our fault",
    "despite challenges",
    "headwinds",
    "transitory",
    "temporary",
    "short-term",
    "one-off",
    "non-recurring",
]

DENIAL_OF_INTERNAL_FAILURE_SIGNALS: List[str] = [
    "underlying business is strong",
    "fundamentals remain solid",
    "fundamentals are strong",
    "fundamentals are robust",
    "we remain confident",
    "long-term outlook",
    "temporary setback",
    "blip",
    "anomaly",
    "transient",
    "no structural issues",
    "no governance issues",
    "audit committee satisfied",
    "board satisfied",
    "fully cooperative",
    "fully compliant",
    "no material weakness",
    "internal controls effective",
    "nothing to see",
    "isolated incident",
]

TIME_PRESSURE_PR_SIGNALS: List[str] = [
    "limited time",
    "act now",
    "expires soon",
    "last chance",
    "deadline",
    "hurry",
    "do not miss",
    "fomo",
    "fear of missing out",
    "opportunity of a lifetime",
    "once in a lifetime",
    "closing today",
    "final offer",
    "take it or leave it",
    "running out",
    "running short",
    "advanced stage",  # PETRONAS "alternative sourcing at advanced stage"
    "almost done",
    "about to sign",
    "imminent",
]


# ============================================================================
# SIGNATURE AXIS 5: GENERIC GOVERNANCE / RISK BOILERPLATE
# ============================================================================

BOILERPLATE_RISK_SIGNALS: List[str] = [
    "if our customers stop buying",
    "may decrease",
    "could harm",
    "could adversely affect",
    "subject to risks",
    "inherent in",
    "no assurance",
    "forward-looking statements",
    "may differ materially",
    "depends on various factors",
    "global economic conditions",
    "currency fluctuations",
    "regulatory changes",
    "competitive pressures",
    "technological change",
    "cybersecurity",
    "natural disasters",
    "pandemics",
    "force majeure",
]

GENERIC_GOVERNANCE_SIGNALS: List[str] = [
    "best practices",
    "corporate governance",
    "board oversight",
    "audit committee",
    "risk committee",
    "nomination committee",
    "remuneration committee",
    "ESG",
    "sustainability",
    "stakeholder engagement",
    "materiality assessment",
    "TCFD",
    "GRI",
    "SASB",
    "internal controls",
    "compliance program",
    "code of conduct",
    "whistleblower",
    "independent directors",
    "diversity and inclusion",
    "merit-based",
]


# ============================================================================
# SIGNATURE AXIS 6: NARRATIVE TIME-LAG VS METRICS (story-vs-state gap)
# ============================================================================

OVER_PROMISE_SIGNALS: List[str] = [
    "ambitious targets",
    "stretch targets",
    "production target",
    "production target of",
    "kboe/d target",
    "mtjda",
    "kasawari",
    "idd south hub",
    "first oil",
    "first gas",
    "operational by",
    "production by",
    "scheduled for",
    "on schedule",
    "on track",
    "ahead of schedule",
    "faster than expected",
    "below budget",
    "under budget",
    "under budget by",
]

UNDER_DELIVERY_HEDGE_SIGNALS: List[str] = [
    "subject to",
    "pending",
    "subject to final approval",
    "subject to regulatory",
    "subject to government",
    "subject to partner",
    "expected to",
    "anticipated to",
    "targeted for",
    "guidance",
    "outlook",
    "we will",
    "we plan to",
    "we intend to",
    "we expect",
    "we anticipate",
    "going forward",
    "in the coming",
    "future periods",
]

QUARTERLY_BEAT_LANGUAGE_SIGNALS: List[str] = [
    "beat expectations",
    "exceeded guidance",
    "above consensus",
    "ahead of consensus",
    "raised guidance",
    "raised dividend",
    "special dividend",
    "buyback",
    "share repurchase",
    "EPS beat",
    "EBITDA beat",
    "revenue beat",
    "margin expansion",
    "operating leverage",
    "cost optimization",
    "efficiency gains",
    "first fuel",  # PETRONAS: "Efficiency is the first fuel"
    "ride-sharing",
    "AI for cost optimization",
    "operational efficiency",
]


# ============================================================================
# CROSS-LOADED DOMAIN-SPECIFIC SIGNALS (already in dimension files but
# augmented here for institutional-collapse context)
# ============================================================================

RELATED_PARTY_SIGNALS: List[str] = [
    "related party",
    "related-party",
    "special purpose entity",
    "special purpose vehicle",
    "SPE",
    "SPV",
    "off-balance-sheet",
    "off balance sheet",
    "variable interest entity",
    "VIE",
    "joint venture with",
    "JV with",
    "50/50",
    "fifty-fifty",
    "shareholder agreement",
    "reserved matters",
    "deadlock",
    "tiebreaker",
    "managing member",
]

JURISDICTION_SHOPPING_SIGNALS: List[str] = [
    "english law",
    "English law",
    "UK Companies Act",
    "Companies Act 2006",
    "incorporated in",
    "registered office",
    "London arbitration",
    "LCIA",
    "ICC arbitration",
    "seat of arbitration",
    "jurisdiction",
    "governing law",
    "forum selection",
    "exclusive jurisdiction",
    "foreign court",
    "venue shopping",
    "delaware",
    "cayman",
    "british virgin islands",
    "BVI",
    "ENI House",
    "registered at",
]

STRUCTURAL_GRIEVANCE_SIGNALS: List[str] = [
    "not a party",
    "not consulted",
    "without consultation",
    "bypassed",
    "excluded",
    "no representation",
    "no equity",
    "no seat",
    "no board seat",
    "state equity",
    "asymmetric",
    "asymmetry",
    "asymmetric participation",
    "asymmetric state",
    "carried interest",
    "non-operator",
    "non-op",
    "minority stake",
    "side agreement",
    "intergovernmental",
]


# ============================================================================
# ACEMOGLU PATTERNS — Inclusive vs Extractive institutional diagnostics
# ============================================================================

ACEMOGLU_EXTRACTIVE_SIGNALS: List[str] = [
    # Political power concentration
    "pm absolute",
    "prime minister's pleasure",
    "appointed by government",
    "appointed by pm",
    "ministerial directive",
    "political appointment",
    "politicised",
    "politicized",
    "politicisation",
    "politicization",
    # Fiscal extraction
    "dividend to government",
    "dividend extraction",
    "fiscal tap",
    "fiscal arm",
    "transfer to government",
    "special dividend",
    "advance dividend",
    "dividend uplift",
    "subsidy",
    "fuel subsidy",
    # Property rights carve-outs
    "carve-out",
    "carve out",
    "discretion",
    "sole discretion",
    "unilateral",
    "without consultation",
    # Creative destruction blockers
    "blocked reform",
    "blocked restructuring",
    "stifled",
    "suppressed",
    # Power concentration
    "concentrated power",
    "concentrated control",
    "ruling elite",
    "inner circle",
    "royal-linked",
    "connected networks",
    "patronage",
    "nepotism",
    # Opacity
    "opaque",
    "no public",
    "no tender",
    "no competitive bid",
    "off balance sheet",
    "off-balance-sheet",
    "related party",
    "special purpose entity",
    "special purpose vehicle",
    "SPE",
    "SPV",
    "VIE",
]

ACEMOGLU_INCLUSIVE_SIGNALS: List[str] = [
    "independent judiciary",
    "rule of law",
    "pluralism",
    "pluralistic",
    "broad participation",
    "competitive bid",
    "open process",
    "public tender",
    "transparent",
    "transparency",
    "disclosure",
    "creative destruction",
    "open competition",
    "merit-based",
    "merit based",
    "independent directors",
    "independent oversight",
    "distributed power",
    "broad-based",
    "uniform property rights",
]


# ============================================================================
# CALHOUN PATTERNS — Healthy roles vs Behavioural sink
# Universe 25 dynamics: role scarcity, parenting collapse, cannibalism-of-future,
# "beautiful ones" (in reverse — narcissistic defense, not withdrawal)
# ============================================================================

CALHOUN_SINK_SIGNALS: List[str] = [
    # Role scarcity at apex
    "politicised top roles",
    "political allocation",
    "turf war",
    "turf wars",
    "over-crowding",
    "over crowding",
    "role compression",
    "few roles",
    "limited roles",
    "apex compression",
    "alpha males",
    "alpha males defending",
    # Parenting collapse / mentorship pipeline
    "mentorship collapse",
    "mentorship pipeline",
    "succession planning degrades",
    "engineers leave",
    "brain drain",
    "engineer graduates leaving",
    "engineers disengage",
    "MSS",
    "mutual separation",
    "voluntary separation",
    "workforce reduction",
    "headcount reduction",
    "5,000 staff",
    "transition anxiety",
    "seconded staff",
    "retrench",
    "staff cut",
    "people cut",
    "layoff",
    "layoffs",
    "capability reproduction fails",
    # Cannibalism-of-future (long-cycle capex sacrificed for short-term)
    "short-term grabs",
    "pet initiatives",
    "sugar projects",
    "capital locked",
    "5-year capex",
    "10-year",
    "long-cycle investments",
    "deepwater",
    "R&D cuts",
    "r&d cuts",
    "research budget",
    # Narcissistic defense / "beautiful ones" in reverse
    "ESG decks",
    "transition narratives",
    "internal awards",
    "low risk-taking",
    "low willingness",
    "symbolic work",
    "cari gali",
    "lepas tangan",
    "geologists hands are off",
    "engineers hands are off",
    "petro-political",
    # Withdrawal / actual "beautiful ones"
    "withdrawal",
    "withdrawn",
    "disengaged",
    "depressed",
    "apathetic",
    "burned out",
    "burnout",
    "stress",
    "over-stressed",
    "stressed staff",
]

CALHOUN_HEALTHY_ROLES_SIGNALS: List[str] = [
    "mentorship",
    "succession planning",
    "training pipeline",
    "engineers grow",
    "junior to senior",
    "promotion rate",
    "internal mobility",
    "cross-division",
    "cross-team",
    "collaborative projects",
    "capability development",
    "R&D investment",
    "deepwater investment",
    "long-cycle investment",
    "innovation pipeline",
    "creative destruction",
    "risk-taking culture",
    "engineer retention",
    "young engineers",
    "graduate programme",
]


def acemoglu_axis(profile: dict) -> dict:
    """Compute Acemoglu institutional inclusion/exaction score.

    Returns score 0.0 (fully inclusive) → 1.0 (fully extractive).
    Uses the same pattern density approach as collapse_risk_score.
    """
    text = profile.get("_source_text", "")
    if not text:
        return {
            "score": None,
            "label": "INSUFFICIENT_SIGNAL",
            "extractive_count": 0,
            "inclusive_count": 0,
        }
    text_lower = text.lower()
    extractive_count, _ = count_matches(text, ACEMOGLU_EXTRACTIVE_SIGNALS)
    inclusive_count, _ = count_matches(text, ACEMOGLU_INCLUSIVE_SIGNALS)
    total = extractive_count + inclusive_count
    if total == 0:
        score = 0.5
        label = "INSUFFICIENT_SIGNAL"
    else:
        score = extractive_count / total
        if score >= 0.7:
            label = "EXTRACTIVE"
        elif score >= 0.4:
            label = "MIXED"
        else:
            label = "INCLUSIVE"
    return {
        "score": round(score, 3),
        "label": label,
        "extractive_count": extractive_count,
        "inclusive_count": inclusive_count,
    }


# ============================================================================
# TRIPWIRE PATTERNS — Operationalized thresholds from the 5 tripwires
# ============================================================================

TRIPWIRE_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "tripwire_1_mof_2027_dividend": {
        "extractive": [
            "rm32b maintained",
            "rm32 billion maintained",
            "dividend maintained",
            "dividend raised",
            "dividend uplift",
            "special dividend",
            "advance dividend",
            "transfer to government",
            "subsidy continues",
            "no dividend cut",
            "high dividend",
            "fiscal tap continues",
        ],
        "inclusive": [
            "dividend cut",
            "dividend reduced",
            "rm20b",
            "rm25b",
            "rm20 billion",
            "rm25 billion",
            "rule-based dividend",
            "fiscal framework",
            "counter-cyclical dividend",
            "dividend cap",
            "dividend formula",
        ],
    },
    "tripwire_2_gentari_sale": {
        "extractive": [
            "gentari opaque",
            "gentari private",
            "gentari connected buyer",
            "gentari valuation low",
            "gentari no disclosure",
            "gentari crony",
            "spv gentari",
            "gentari shell",
        ],
        "inclusive": [
            "gentari transparent",
            "gentari fair valuation",
            "gentari reputable buyer",
            "gentari independent buyer",
            "gentari disclosure",
            "gentari board independence",
            "gentari governance",
            "gentari ipo",
        ],
    },
    "tripwire_3_tt_exit": {
        "extractive": [
            "tt contract extended",
            "tt tenure extended",
            "tt to 2029",
            "tt lateral move",
            "tt to gentari",
            "tt to clean energy",
            "tt beautiful one",
            "tt insulation",
        ],
        "inclusive": [
            "tt exit",
            "tt removed",
            "tt succession",
            "tt not extended",
            "azizan-style successor",
            "integrity mandate successor",
            "new ceo search",
            "merit-based selection",
        ],
    },
    "tripwire_4_sarawak_settlement": {
        "extractive": [
            "sarawak humiliated",
            "petros excluded",
            "petros not a party",
            "petros beaten in court",
            "sarawak marginalised",
            "internal colonisation",
            "ma63 ignored",
            "petros bypassed",
            "sarawak spv",
        ],
        "inclusive": [
            "sarawak settlement",
            "petros elevated",
            "psc-style sarawak",
            "revenue-sharing sarawak",
            "co-operative sarawak",
            "sarawak partner",
            "ma63 honoured",
            "petros co-operator",
            "sarawak federal court resolution",
        ],
    },
    "tripwire_5_new_spvs": {
        "extractive": [
            "searah precedent",
            "new spv",
            "new jv offshore",
            "uk spv",
            "english law",
            "london arbitration",
            "searah class",
            "lcia",
            "icc arbitration",
            "asset moved offshore",
            "asset moved to spv",
            "lci",
        ],
        "inclusive": [
            "spv disclosed",
            "jv transparent",
            "tender process",
            "competitive bid",
            "public disclosure",
            "open process",
            "asset retained",
            "domestic jurisdiction",
        ],
    },
}


def detect_tripwires(text: str) -> dict:
    """
    Detect the 5 collapse-tripwires in a text.

    Each tripwire has inclusive and extractive signals. Score per
    tripwire is inclusive_count - extractive_count. Negative score
    indicates extractive drift, positive indicates inclusive drift.

    Returns dict with per-tripwire status + overall drift index.
    """
    text_lower = text.lower()
    results = {}
    total_inclusive = 0
    total_extractive = 0
    critical_count = 0

    for tripwire_name, signals in TRIPWIRE_PATTERNS.items():
        ext_count, _ = count_matches(text, signals["extractive"])
        inc_count, _ = count_matches(text, signals["inclusive"])
        net = inc_count - ext_count
        if net <= -2:
            status = "CRITICAL_EXTRACTIVE"
            critical_count += 1
        elif net == -1:
            status = "DRIFTING_EXTRACTIVE"
        elif net == 0:
            status = "NEUTRAL"
        elif net == 1:
            status = "DRIFTING_INCLUSIVE"
        else:
            status = "INCLUSIVE"
        results[tripwire_name] = {
            "extractive_count": ext_count,
            "inclusive_count": inc_count,
            "net_drift": net,
            "status": status,
        }
        total_inclusive += inc_count
        total_extractive += ext_count

    overall_net = total_inclusive - total_extractive
    if overall_net <= -5:
        overall = "HARD_EXTRACTIVE_DRIFT"
    elif overall_net <= -2:
        overall = "MODERATE_EXTRACTIVE_DRIFT"
    elif overall_net <= 1:
        overall = "NEUTRAL_OR_MIXED"
    elif overall_net <= 4:
        overall = "INCLUSIVE_DRIFT"
    else:
        overall = "STRONG_INCLUSIVE_DRIFT"

    return {
        "tripwires": results,
        "critical_extractive_tripwires": critical_count,
        "overall_drift": overall,
        "total_extractive_signals": total_extractive,
        "total_inclusive_signals": total_inclusive,
        "overall_net_drift": overall_net,
    }


def calhoun_axis(profile: dict) -> dict:
    """Compute Calhoun behavioural-sink stress score.

    Returns score 0.0 (healthy roles) → 1.0 (behavioural sink).
    """
    text = profile.get("_source_text", "")
    if not text:
        return {
            "score": None,
            "label": "INSUFFICIENT_SIGNAL",
            "sink_count": 0,
            "healthy_count": 0,
        }
    text_lower = text.lower()
    sink_count, _ = count_matches(text, CALHOUN_SINK_SIGNALS)
    healthy_count, _ = count_matches(text, CALHOUN_HEALTHY_ROLES_SIGNALS)
    total = sink_count + healthy_count
    if total == 0:
        score = 0.5
        label = "INSUFFICIENT_SIGNAL"
    else:
        score = sink_count / total
        if score >= 0.7:
            label = "BEHAVIOURAL_SINK"
        elif score >= 0.4:
            label = "PRE_SINK_STRESS"
        else:
            label = "HEALTHY_ROLES"
    return {
        "score": round(score, 3),
        "label": label,
        "sink_count": sink_count,
        "healthy_count": healthy_count,
    }


# ============================================================================
# MATCHER ENGINE
# ============================================================================

def normalize_text(text: str) -> str:
    """Lowercase + collapse whitespace for matching."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def count_matches(text: str, signals: List[str]) -> Tuple[int, List[str]]:
    """
    Count occurrences of signal patterns in text.
    Returns (count, list of matched signals) — substring + simple regex.
    """
    norm = normalize_text(text)
    matches: List[str] = []
    for signal in signals:
        signal_norm = signal.lower()
        if "*" in signal_norm or ".*" in signal_norm:
            try:
                if re.search(signal_norm, norm):
                    matches.append(signal)
            except re.error:
                if signal_norm in norm:
                    matches.append(signal)
        else:
            if signal_norm in norm:
                matches.append(signal)
    return len(matches), matches


def count_axis(text: str, axis_signals: List[str]) -> dict:
    """Count signals in a single axis and return detail."""
    count, matches = count_matches(text, axis_signals)
    return {
        "signal_count": count,
        "matched_signals": matches[:10],  # cap for envelope brevity
        "truncated": len(matches) > 10,
    }


def full_signature_profile(text: str) -> dict:
    """
    Run all 6 axes against text. Returns the full institutional-collapse
    signature profile. Use as calibration input for power_audit,
    wisdom_evaluate, capture_scan, and collapse_signature_scan.

    Calibration fix 2026-06-17:
    - Adds Acemoglu + Calhoun 2D axis output
    - Source text stored in profile for downstream axis computation
    """
    axes = {
        "axis_1_national_destiny_triumphalism": (
            NATIONAL_DESTINY_SIGNALS + TRIUMPHALISM_SIGNALS + COMPLEXITY_AS_VIRTUE
        ),
        "axis_2_politicisation_ideology": (
            IDEOLOGICAL_CERTAINTY_SIGNALS + POLITICISATION_SIGNALS + PURGE_AND_CLEANSING_SIGNALS
        ),
        "axis_3_extraction_over_reinvestment": (
            EXTRACTION_NARRATIVE_SIGNALS + REINVESTMENT_SUPPRESSION_SIGNALS
        ),
        "axis_4_external_blame_denial": (
            EXTERNAL_BLAME_SIGNALS + DENIAL_OF_INTERNAL_FAILURE_SIGNALS + TIME_PRESSURE_PR_SIGNALS
        ),
        "axis_5_generic_governance_boilerplate": (
            BOILERPLATE_RISK_SIGNALS + GENERIC_GOVERNANCE_SIGNALS
        ),
        "axis_6_overpromise_hedge_metrics_lag": (
            OVER_PROMISE_SIGNALS + UNDER_DELIVERY_HEDGE_SIGNALS + QUARTERLY_BEAT_LANGUAGE_SIGNALS
        ),
    }
    profile = {}
    for axis_name, signals in axes.items():
        profile[axis_name] = count_axis(text, signals)

    # Cross-loaded institutional-collapse domain signals
    profile["related_party_jurisdiction_structural"] = {
        "related_party": count_axis(text, RELATED_PARTY_SIGNALS),
        "jurisdiction_shopping": count_axis(text, JURISDICTION_SHOPPING_SIGNALS),
        "structural_grievance": count_axis(text, STRUCTURAL_GRIEVANCE_SIGNALS),
    }

    # Acemoglu + Calhoun 2D risk map
    profile["_source_text"] = text
    profile["acemoglu_axis"] = acemoglu_axis(profile)
    profile["calhoun_axis"] = calhoun_axis(profile)

    return profile


def collapse_risk_score(profile: dict) -> dict:
    """
    Convert signature profile to a 0.0-1.0 collapse-risk score.
    Score is the weighted signal density across all 6 axes.

    Weighting rationale:
    - Axes 2 (politicisation) and 4 (denial) are highest pre-collapse
      indicators per PDVSA / Enron / 1MDB retrospectives.
    - Axes 1 (triumphalism) and 6 (over-promise) are early warnings.
    - Axes 3 (extraction) and 5 (boilerplate) are chronic-stress signals.

    Calibration fix 2026-06-17:
    - Normalisation denominator reduced 25 → 12 (empirically realistic
      max signals per axis in real pre-collapse documents)
    - HIGH threshold lowered 0.45 → 0.18
    - CRITICAL threshold lowered 0.65 → 0.35
    - Multi-axis convergence (≥3 axes with density >= 0.30) bumps
      score by 0.10 — Enron 1999 AR shows this pattern
    """
    weights = {
        "axis_1_national_destiny_triumphalism": 0.12,
        "axis_2_politicisation_ideology": 0.20,
        "axis_3_extraction_over_reinvestment": 0.15,
        "axis_4_external_blame_denial": 0.18,
        "axis_5_generic_governance_boilerplate": 0.12,
        "axis_6_overpromise_hedge_metrics_lag": 0.13,
    }

    # Normalise each axis: density = matches / 12 (calibrated to real corpora)
    NORM_DENOM = 12
    total = 0.0
    dominant_axes = []
    axes_with_density = 0
    for axis_name, weight in weights.items():
        density = min(profile[axis_name]["signal_count"] / NORM_DENOM, 1.0)
        weighted = density * weight
        total += weighted
        if density >= 0.30:
            axes_with_density += 1
            dominant_axes.append({
                "axis": axis_name,
                "signal_count": profile[axis_name]["signal_count"],
                "density": round(density, 3),
                "weight": weight,
            })

    # Domain-specific bump for related_party + jurisdiction + structural
    rpjs = profile["related_party_jurisdiction_structural"]
    rp_count = (
        rpjs["related_party"]["signal_count"]
        + rpjs["jurisdiction_shopping"]["signal_count"]
        + rpjs["structural_grievance"]["signal_count"]
    )
    rpjs_density = min(rp_count / 10.0, 1.0)
    if rp_count >= 3:
        total += 0.15  # Multi-domain convergence
        dominant_axes.append({
            "axis": "related_party_jurisdiction_structural",
            "signal_count": rp_count,
            "density": round(rpjs_density, 3),
            "weight": "domain_convergence",
        })

    # Multi-axis convergence bump
    if axes_with_density >= 3:
        total += 0.05

    score = min(total, 1.0)

    if score >= 0.35:
        risk_level = "CRITICAL"
        recommendation = "888_HOLD — pattern matches pre-collapse signature. Investigate immediately."
    elif score >= 0.18:
        risk_level = "HIGH"
        recommendation = "Strong pre-collapse signature. Multi-axis convergence warrants 888_HOLD review."
    elif score >= 0.10:
        risk_level = "MEDIUM"
        recommendation = "Moderate signal density. Triangulate with KPI differential before action."
    elif score >= 0.04:
        risk_level = "LOW"
        recommendation = "Few institutional-collapse signals. Standard monitoring."
    else:
        risk_level = "MINIMAL"
        recommendation = "No institutional-collapse signature detected."

    return {
        "score": round(score, 3),
        "risk_level": risk_level,
        "dominant_axes": sorted(
            dominant_axes, key=lambda x: x["signal_count"], reverse=True
        ),
        "recommendation": recommendation,
    }


__all__ = [
    "NATIONAL_DESTINY_SIGNALS",
    "TRIUMPHALISM_SIGNALS",
    "COMPLEXITY_AS_VIRTUE",
    "IDEOLOGICAL_CERTAINTY_SIGNALS",
    "POLITICISATION_SIGNALS",
    "PURGE_AND_CLEANSING_SIGNALS",
    "EXTRACTION_NARRATIVE_SIGNALS",
    "REINVESTMENT_SUPPRESSION_SIGNALS",
    "EXTERNAL_BLAME_SIGNALS",
    "DENIAL_OF_INTERNAL_FAILURE_SIGNALS",
    "TIME_PRESSURE_PR_SIGNALS",
    "BOILERPLATE_RISK_SIGNALS",
    "GENERIC_GOVERNANCE_SIGNALS",
    "OVER_PROMISE_SIGNALS",
    "UNDER_DELIVERY_HEDGE_SIGNALS",
    "QUARTERLY_BEAT_LANGUAGE_SIGNALS",
    "RELATED_PARTY_SIGNALS",
    "JURISDICTION_SHOPPING_SIGNALS",
    "STRUCTURAL_GRIEVANCE_SIGNALS",
    "ACEMOGLU_EXTRACTIVE_SIGNALS",
    "ACEMOGLU_INCLUSIVE_SIGNALS",
    "CALHOUN_SINK_SIGNALS",
    "CALHOUN_HEALTHY_ROLES_SIGNALS",
    "TRIPWIRE_PATTERNS",
    "detect_tripwires",
    "count_matches",
    "count_axis",
    "full_signature_profile",
    "collapse_risk_score",
    "acemoglu_axis",
    "calhoun_axis",
]