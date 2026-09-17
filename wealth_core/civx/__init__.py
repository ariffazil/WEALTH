"""
WEALTH CIVX — Civilizational Scenario Intelligence Module.

Embedded in WEALTH as the L10 knowledge axis: long-horizon resilience,
sovereignty, intergenerational burden, and scenario analysis.

Not a prediction engine. Not a crystal ball. A structured way to ask
"what if this continues for 10/20/30 years?"

Status: SAFE_TO_STUDY. Never decision authority until calibrated against
real historical data.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


# ── Schema ─────────────────────────────────────────────────────────────

class ScenarioStatus(str, Enum):
    SAFE_TO_STUDY = "SAFE_TO_STUDY"              # Hypothetical, not decision-ready
    SCENARIO_BOUND = "SCENARIO_BOUND"             # Bounded by explicit assumptions
    CALIBRATION_REQUIRED = "CALIBRATION_REQUIRED" # Needs historical validation
    DECISION_ELIGIBLE = "DECISION_ELIGIBLE"       # Validated, can inform decisions
    NOT_DECISION_AUTHORITY = "NOT_DECISION_AUTHORITY"  # Never replaces human judgment


class ResilienceAxis(str, Enum):
    FISCAL = "FISCAL"                    # Government revenue, debt, fiscal space
    ENERGY = "ENERGY"                    # Energy security, transition, dependency
    FOOD_WATER = "FOOD_WATER"            # Food/water security, agricultural capacity
    INSTITUTIONAL = "INSTITUTIONAL"      # Institutional continuity, governance quality
    SOCIAL_COHESION = "SOCIAL_COHESION"  # Trust, inequality, polarization
    SOVEREIGNTY = "SOVEREIGNTY"          # External dependency, strategic autonomy
    ECOLOGICAL = "ECOLOGICAL"            # Environmental carrying capacity
    DEMOGRAPHIC = "DEMOGRAPHIC"          # Population, aging, workforce
    TECHNOLOGICAL = "TECHNOLOGICAL"      # Digital dependency, infrastructure
    INTERGENERATIONAL = "INTERGENERATIONAL"  # Burden on future generations


@dataclass
class AssumptionAxis:
    """An explicit assumption that drives a scenario."""
    name: str                    # e.g. "oil_price_path"
    description: str
    values: list[str]            # e.g. ["$60/bbl", "$80/bbl", "$100/bbl"]
    basis: str = ""              # Source of the range
    uncertainty: str = "MEDIUM"  # LOW/MEDIUM/HIGH/DEEP


@dataclass
class ScenarioPath:
    """One path through the scenario space."""
    path_id: str
    name: str
    assumptions: dict[str, str]          # axis_name → value
    horizon_years: int                   # How far out
    resilience_scores: dict[str, float]  # axis → 0-1 score
    key_risks: list[str] = field(default_factory=list)
    option_space: str = ""               # What remains possible
    irreversibility: list[str] = field(default_factory=list)
    evidence_basis: str = "INTERPRETATION"
    notes: str = ""


@dataclass
class CivilizationalScenario:
    """A complete scenario study for a domain/country/horizon."""
    domain: str                            # e.g. "Malaysia 2027-2040"
    scope: str
    status: ScenarioStatus = ScenarioStatus.SAFE_TO_STUDY
    assumption_axes: list[AssumptionAxis] = field(default_factory=list)
    paths: list[ScenarioPath] = field(default_factory=list)
    calibration_data: list[str] = field(default_factory=list)  # What would validate this
    limitations: list[str] = field(default_factory=list)
    computed_at: str = ""
    computed_by: str = "WEALTH/CIVX"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = "CIVX-v1.0.0"
        return d


# ── Malaysia Fiscal Durability Seed ────────────────────────────────────

def seed_malaysia_fiscal_2027_2040() -> CivilizationalScenario:
    """Seed case: Malaysia fiscal durability 2027-2040.

    Three oil-price paths × three demographic paths = 9 scenario variants.

    Status: SAFE_TO_STUDY. Not calibrated against historical fiscal outcomes.
    Uses public data (Budget 2027, PETRONAS reports, DOSM demographics).

    Seeded: 2026-09-16
    """
    assumption_axes = [
        AssumptionAxis(
            name="oil_price_brent",
            description="Brent crude average price path over horizon",
            values=["$55/bbl (low)", "$75/bbl (base)", "$95/bbl (high)"],
            basis="EIA/IEA long-range forecasts, historical volatility",
            uncertainty="HIGH",
        ),
        AssumptionAxis(
            name="petroleum_production",
            description="Malaysia crude + condensate production trajectory",
            values=["Declining 3%/yr (depletion)", "Flat (new discoveries offset)", "Growing 1%/yr (deepwater)"],
            basis="PETRONAS annual reports, MPM data",
            uncertainty="MEDIUM",
        ),
        AssumptionAxis(
            name="demographic_path",
            description="Population growth, aging, workforce participation",
            values=["High aging (TFR 1.3, rapid aging)", "Medium aging (TFR 1.5, gradual)", "Managed transition (TFR 1.7, policy success)"],
            basis="DOSM population projections, UN World Population Prospects",
            uncertainty="MEDIUM",
        ),
        AssumptionAxis(
            name="fiscal_reform",
            description="Whether GST/broader tax base is reintroduced",
            values=["No reform (SST stays)", "Partial reform (GST-lite)", "Full reform (GST + property tax)"],
            basis="Political feasibility assessment",
            uncertainty="DEEP",
        ),
        AssumptionAxis(
            name="subsidy_trajectory",
            description="Path of fuel/food subsidy regime",
            values=["Full subsidies maintained", "Gradual rationalization", "Full targeted cash transfers"],
            basis="Historical reform attempts, PADU implementation",
            uncertainty="HIGH",
        ),
    ]

    # Path 1: Best case
    best = ScenarioPath(
        path_id="MY-FISCAL-BEST",
        name="Managed transition — high oil + fiscal reform + demographic adaptation",
        assumptions={
            "oil_price_brent": "$95/bbl (high)",
            "petroleum_production": "Growing 1%/yr (deepwater)",
            "demographic_path": "Managed transition (TFR 1.7, policy success)",
            "fiscal_reform": "Full reform (GST + property tax)",
            "subsidy_trajectory": "Full targeted cash transfers",
        },
        horizon_years=14,
        resilience_scores={
            "FISCAL": 0.8,
            "ENERGY": 0.7,
            "INSTITUTIONAL": 0.7,
            "SOCIAL_COHESION": 0.7,
            "SOVEREIGNTY": 0.8,
            "INTERGENERATIONAL": 0.8,
        },
        key_risks=[
            "Oil price reversal after investment lock-in",
            "GST political backlash (2014 precedent)",
            "Demographic transition slower than assumed",
        ],
        option_space="Full fiscal flexibility. Investment capacity for energy transition. Social safety net funded.",
        irreversibility=[
            "Deepwater infrastructure once committed (30yr lifecycle)",
            "GST political capital spent",
        ],
        evidence_basis="INTERPRETATION",
        notes="Best case requires political will that has historically been absent. Not impossible but not baseline.",
    )

    # Path 2: Base case
    base = ScenarioPath(
        path_id="MY-FISCAL-BASE",
        name="Muddle through — base oil + partial reform + demographic drift",
        assumptions={
            "oil_price_brent": "$75/bbl (base)",
            "petroleum_production": "Flat (new discoveries offset)",
            "demographic_path": "Medium aging (TFR 1.5, gradual)",
            "fiscal_reform": "Partial reform (GST-lite)",
            "subsidy_trajectory": "Gradual rationalization",
        },
        horizon_years=14,
        resilience_scores={
            "FISCAL": 0.5,
            "ENERGY": 0.5,
            "INSTITUTIONAL": 0.5,
            "SOCIAL_COHESION": 0.5,
            "SOVEREIGNTY": 0.6,
            "INTERGENERATIONAL": 0.4,
        },
        key_risks=[
            "Fiscal deficit widens as petroleum revenue declines",
            "MYR depreciation pressure from twin deficits",
            "Aging population strains healthcare + pensions",
            "Energy transition investment delayed",
        ],
        option_space="Limited fiscal flexibility. Incremental reform possible but structural change deferred.",
        irreversibility=[
            "Lost decade of energy transition investment",
            "Brain drain accelerates (skilled workforce outflow)",
            "Fossil fuel infrastructure lock-in",
        ],
        evidence_basis="INTERPRETATION",
        notes="Most likely path based on historical pattern. Not optimal but survivable.",
    )

    # Path 3: Worst case
    worst = ScenarioPath(
        path_id="MY-FISCAL-WORST",
        name="Structural decline — low oil + no reform + rapid aging",
        assumptions={
            "oil_price_brent": "$55/bbl (low)",
            "petroleum_production": "Declining 3%/yr (depletion)",
            "demographic_path": "High aging (TFR 1.3, rapid aging)",
            "fiscal_reform": "No reform (SST stays)",
            "subsidy_trajectory": "Full subsidies maintained",
        },
        horizon_years=14,
        resilience_scores={
            "FISCAL": 0.2,
            "ENERGY": 0.3,
            "INSTITUTIONAL": 0.3,
            "SOCIAL_COHESION": 0.3,
            "SOVEREIGNTY": 0.4,
            "INTERGENERATIONAL": 0.1,
        },
        key_risks=[
            "Sovereign credit downgrade",
            "MYR crisis (capital flight, FX reserve depletion)",
            "Brain drain accelerates (skilled workforce exodus)",
            "Social unrest from subsidy removal pressure",
            "Energy security crisis (net importer by 2035)",
            "Pension/healthcare funding gap for aging population",
        ],
        option_space="Very limited. IMF-style conditionality possible. Sovereignty compromised.",
        irreversibility=[
            "Institutional trust deficit (hard to rebuild)",
            "Human capital loss (10+ years to replace)",
            "Ecological damage from deferred maintenance",
            "Intergenerational debt burden",
        ],
        evidence_basis="INTERPRETATION",
        notes="Low probability but high consequence. Requires combination of adverse factors. Worth studying, not worth panicking.",
    )

    return CivilizationalScenario(
        domain="Malaysia fiscal durability 2027-2040",
        scope="Federal fiscal sustainability under oil price × demographic × reform scenarios",
        status=ScenarioStatus.SAFE_TO_STUDY,
        assumption_axes=assumption_axes,
        paths=[best, base, worst],
        calibration_data=[
            "Historical fiscal deficit vs oil price correlation (2000-2025)",
            "PETRONAS actual dividend vs budget assumption accuracy",
            "GST revenue vs SST revenue actual comparison",
            "DOSM population projection vs actual (2015-2025 validation)",
            "MYR/USD correlation with fiscal fundamentals",
        ],
        limitations=[
            "Not calibrated against historical fiscal outcomes",
            "Political economy variables are deep uncertainty",
            "External shocks (pandemic, war, financial crisis) not modeled",
            "No Monte Carlo — discrete paths only",
            "Resilience scores are ordinal, not cardinal",
            "SAFE_TO_STUDY — not decision authority",
        ],
        computed_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        notes="First CIVX seed. Three paths, five assumption axes. All interpretations tagged. Sovereign decision required before any path is promoted to decision-eligible.",
    )
