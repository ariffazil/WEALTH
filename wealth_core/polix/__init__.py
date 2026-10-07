"""
WEALTH POLIX — Power Topology Intelligence Module.

Embedded in WEALTH as the L4 knowledge axis: political economy, power analysis,
capture detection, rent extraction, and rule asymmetry.

Not a separate organ. Not a political party. A witness of power structures.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


# ── Schema ─────────────────────────────────────────────────────────────

class PowerActorType(str, Enum):
    STATE = "STATE"                  # Government, ministry, regulator
    SOE = "SOE"                      # State-owned enterprise (PETRONAS, Khazanah)
    GLC = "GLC"                      # Government-linked company
    REGULATOR = "REGULATOR"          # BNM, SC, MCMC, etc.
    PRIVATE = "PRIVATE"              # Private corporation
    CIVIL_SOCIETY = "CIVIL_SOCIETY"  # NGOs, media, academia
    INTERNATIONAL = "INTERNATIONAL"  # IMF, World Bank, ASEAN, etc.
    LABOR = "LABOR"                  # Unions, workforce
    UNKNOWN = "UNKNOWN"


class CaptureRisk(str, Enum):
    LOW = "LOW"              # Independent, transparent, accountable
    MODERATE = "MODERATE"    # Some opacity or concentration
    HIGH = "HIGH"            # Significant capture indicators
    CRITICAL = "CRITICAL"    # Documented capture or structural capture
    UNMEASURED = "UNMEASURED"


class RentType(str, Enum):
    RESOURCE_RENT = "RESOURCE_RENT"        # Oil/gas/mineral extraction
    MONOPOLY_RENT = "MONOPOLY_RENT"        # Market power, licensing
    REGULATORY_RENT = "REGULATORY_RENT"    # Rule manipulation
    INFORMATION_RENT = "INFORMATION_RENT"  # Asymmetric knowledge
    POLITICAL_RENT = "POLITICAL_RENT"      # Connection-based access
    FISCAL_RENT = "FISCAL_RENT"            # Tax/subsidy manipulation


@dataclass
class PowerActor:
    """A named entity in the power topology."""
    name: str
    actor_type: PowerActorType
    formal_mandate: str = ""
    resource_access: str = ""          # What resources they control
    decision_authority: str = ""       # What decisions they can make
    accountability_paths: str = ""     # Who they answer to
    opacity_score: float = 0.0        # 0=transparent, 1=opaque
    capture_risk: CaptureRisk = CaptureRisk.UNMEASURED
    notes: str = ""


@dataclass
class RentFlow:
    """A documented rent extraction pathway."""
    rent_type: RentType
    source: str                        # Where the rent comes from
    beneficiary: str                   # Who captures it
    cost_bearer: str                   # Who pays
    estimated_annual_value: str = ""   # Order of magnitude
    evidence_basis: str = ""           # OBS/DER/INT/SPEC
    reversibility: str = ""            # How hard to change
    notes: str = ""


@dataclass
class RuleAsymmetry:
    """A documented asymmetry in rules or enforcement."""
    description: str
    who_benefits: str
    who_bears_cost: str
    evidence_basis: str = "INTERPRETATION"
    reform_difficulty: str = ""        # LOW/MEDIUM/HIGH/STRUCTURAL
    notes: str = ""


@dataclass
class PowerTopology:
    """Complete power topology for a domain/sector/regime."""
    domain: str                        # e.g. "Malaysia fiscal regime"
    scope: str                         # e.g. "federal petroleum revenue"
    actors: list[PowerActor] = field(default_factory=list)
    rent_flows: list[RentFlow] = field(default_factory=list)
    rule_asymmetries: list[RuleAsymmetry] = field(default_factory=list)
    capture_score: CaptureRisk = CaptureRisk.UNMEASURED
    coercion_signals: list[str] = field(default_factory=list)
    geopolitical_exposure: list[str] = field(default_factory=list)
    evidence_quality: str = "INTERPRETATION"
    computed_at: str = ""
    computed_by: str = "WEALTH/POLIX"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["schema_version"] = "POLIX-v1.0.0"
        return d


# ── Malaysia Fiscal Regime Seed ────────────────────────────────────────

def seed_malaysia_fiscal() -> PowerTopology:
    """Seed case: Malaysia federal fiscal regime — PETRONAS, petroleum revenue,
    GST/SST, federal-state fiscal relations.

    Evidence basis: INTERPRETATION from public sources (federal budget docs,
    PETRONAS annual reports, Auditor-General reports, parliamentary records).
    Not insider knowledge. Not classified. Not opinion.

    Seeded: 2026-09-16
    """
    actors = [
        PowerActor(
            name="PETRONAS",
            actor_type=PowerActorType.SOE,
            formal_mandate="National petroleum corporation. Sole concessionaire for upstream oil/gas under Petroleum Development Act 1974.",
            resource_access="Full upstream petroleum rights. Downstream, gas, LNG, shipping, solar, hydrogen.",
            decision_authority="Board-appointed. PM as Minister of Finance (Incorporated) is sole shareholder.",
            accountability_paths="Annual report to Parliament. Auditor-General review. But operational autonomy is high.",
            opacity_score=0.6,
            capture_risk=CaptureRisk.MODERATE,
            notes="Structural dual role: commercial entity AND national resource custodian. Dividend policy is politically sensitive.",
        ),
        PowerActor(
            name="Ministry of Finance (MoF)",
            actor_type=PowerActorType.STATE,
            formal_mandate="Federal fiscal policy, budget, taxation, government investment.",
            resource_access="Federal budget, taxation powers, PETRONAS dividends, debt issuance.",
            decision_authority="Budget allocation, tax policy, subsidy design, fiscal transfers.",
            accountability_paths="Parliament, Cabinet, PM (who is also MoF).",
            opacity_score=0.5,
            capture_risk=CaptureRisk.MODERATE,
            notes="PM holds MoF portfolio — concentration of fiscal + executive power.",
        ),
        PowerActor(
            name="Bank Negara Malaysia (BNM)",
            actor_type=PowerActorType.REGULATOR,
            formal_mandate="Monetary policy, financial stability, currency management, Islamic finance regulation.",
            resource_access="Foreign reserves, monetary policy tools, regulatory authority.",
            decision_authority="OPR (interest rate), FX intervention, bank licensing, macroprudential policy.",
            accountability_paths="Board of directors. Annual report to Parliament. Governor appointed by PM.",
            opacity_score=0.3,
            capture_risk=CaptureRisk.LOW,
            notes="Relatively independent. Governor appointment is political but operational independence is maintained.",
        ),
        PowerActor(
            name="Securities Commission (SC)",
            actor_type=PowerActorType.REGULATOR,
            formal_mandate="Capital market regulation, investor protection, market integrity.",
            resource_access="Regulatory authority over Bursa Malaysia, fund managers, listed companies.",
            decision_authority="Listing rules, enforcement actions, licensing.",
            accountability_paths="Board. Annual report to PM.",
            opacity_score=0.4,
            capture_risk=CaptureRisk.MODERATE,
            notes="Regulatory capture risk from industry revolving door.",
        ),
        PowerActor(
            name="State Governments (esp. Sabah, Sarawak, Terengganu)",
            actor_type=PowerActorType.STATE,
            formal_mandate="State-level governance, land, natural resources (state jurisdiction under Constitution).",
            resource_access="Petroleum royalty (5% standard, 10% claimed by East Malaysia), state land, timber, minerals.",
            decision_authority="State-level resource policy, land allocation, state GLCs.",
            accountability_paths="State legislature. Federal fiscal transfers create dependency.",
            opacity_score=0.7,
            capture_risk=CaptureRisk.HIGH,
            notes="East Malaysia has stronger resource claims under Malaysia Agreement 1963 (MA63). Federal fiscal transfers create leverage.",
        ),
        PowerActor(
            name="Cabinet / Economic Planning Unit (EPU)",
            actor_type=PowerActorType.STATE,
            formal_mandate="National development planning, public investment, GLC oversight.",
            resource_access="Development budget, GLC appointments, mega-project approval.",
            decision_authority="5-year plans, GLC board appointments, project greenlighting.",
            accountability_paths="PM and Cabinet. Parliament for budget approval.",
            opacity_score=0.6,
            capture_risk=CaptureRisk.MODERATE,
            notes="EPU has outsized influence on allocation without proportional public scrutiny.",
        ),
    ]

    rent_flows = [
        RentFlow(
            rent_type=RentType.RESOURCE_RENT,
            source="Petroleum extraction (upstream)",
            beneficiary="Federal government (via PETRONAS dividend + petroleum tax + export duty)",
            cost_bearer="State governments (fixed 5% royalty, not profit share), future generations (depletion), local communities (environmental)",
            estimated_annual_value="RM 60-80B (PETRONAS dividend + tax + royalty, varies with oil price)",
            evidence_basis="DERIVED",
            reversibility="STRUCTURAL — requires legislative change (Petroleum Development Act 1974)",
            notes="The 5% royalty cap is a structural rule asymmetry. States with petroleum bear extraction costs but receive a fixed fraction.",
        ),
        RentFlow(
            rent_type=RentType.REGULATORY_RENT,
            source="Sugar/flour/cement licensing oligopoly",
            beneficiary="Licensed producers (few families/corporations)",
            cost_bearer="Consumers (higher prices), new entrants (barriers)",
            estimated_annual_value="RM 2-5B (estimated consumer surplus loss)",
            evidence_basis="INTERPRETATION",
            reversibility="MEDIUM — requires regulatory reform, political will",
            notes="Approved Permits (APs) and licensing create artificial scarcity. Classic regulatory capture.",
        ),
        RentFlow(
            rent_type=RentType.FISCAL_RENT,
            source="Subsidy regime (fuel, cooking oil, rice)",
            beneficiary="Consumers (diffuse), but disproportionate benefit to high-consumption households",
            cost_bearer="Federal budget (RM 50-80B annually), future fiscal space",
            estimated_annual_value="RM 50-80B",
            evidence_basis="DERIVED",
            reversibility="HIGH — politically sensitive, successive governments struggle",
            notes="Subsidies are regressive in practice (rich consume more fuel). B40-targeted replacement is technically feasible but politically costly.",
        ),
        RentFlow(
            rent_type=RentType.POLITICAL_RENT,
            source="GLC board appointments and procurement",
            beneficiary="Connected individuals and networks",
            cost_bearer="GLC performance, minority shareholders, public trust",
            estimated_annual_value="UNMEASURED — performance drag is diffuse",
            evidence_basis="INTERPRETATION",
            reversibility="MEDIUM — requires governance reform, appointment independence",
            notes="GLC board appointments are political patronage instruments. Performance impact is real but hard to isolate.",
        ),
    ]

    asymmetries = [
        RuleAsymmetry(
            description="Petroleum royalty capped at 5% for states. Federal receives majority of petroleum revenue.",
            who_benefits="Federal government (fiscal consolidation, spending flexibility)",
            who_bears_cost="Petroleum-producing states (especially Terengganu, Sabah, Sarawak)",
            evidence_basis="OBSERVATION",
            reform_difficulty="STRUCTURAL",
            notes="Constitutional + legislative. Sabah/Sarawak claim 10%+ under MA63. Political negotiation ongoing.",
        ),
        RuleAsymmetry(
            description="PM holds MoF portfolio. Executive and fiscal authority concentrated in one person.",
            who_benefits="PM/executive branch (fiscal discretion without Cabinet constraint)",
            who_bears_cost="Parliamentary oversight, checks and balances",
            evidence_basis="OBSERVATION",
            reform_difficulty="HIGH",
            notes="Convention, not law. But structural concentration of power is documented.",
        ),
        RuleAsymmetry(
            description="GST replaced by SST — regressive shift reducing tax base and fiscal resilience.",
            who_benefits="Consumers (lower visible tax), businesses (simpler compliance)",
            who_bears_cost="Federal fiscal space (RM 20-25B annual revenue loss), future generations",
            evidence_basis="DERIVED",
            reform_difficulty="HIGH",
            notes="GST is economically superior (broader base, self-enforcing chain). SST is politically easier but fiscally weaker.",
        ),
    ]

    return PowerTopology(
        domain="Malaysia fiscal regime",
        scope="Federal petroleum revenue, taxation, subsidies, GLC governance, federal-state fiscal relations",
        actors=actors,
        rent_flows=rent_flows,
        rule_asymmetries=asymmetries,
        capture_score=CaptureRisk.MODERATE,
        coercion_signals=[
            "Federal fiscal transfers create state dependency",
            "PETRONAS dividend pressure during low oil prices",
            "Subsidy reform political cost exceeds fiscal benefit in short term",
        ],
        geopolitical_exposure=[
            "Oil price volatility (Brent correlation)",
            "China demand slowdown (commodity export)",
            "US rate cycle (MYR pressure, capital flows)",
            "ASEAN supply chain shift",
        ],
        evidence_quality="INTERPRETATION",
        computed_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        notes="Seed case. Public sources only. No insider knowledge. Requires cross-validation with BNM, MoF, PETRONAS primary data.",
    )


def seed_petronas_glc() -> PowerTopology:
    """Seed case: PETRONAS/GLC governance structure.

    Evidence basis: INTERPRETATION from public annual reports, governance codes.
    """
    actors = [
        PowerActor(
            name="PETRONAS Board",
            actor_type=PowerActorType.SOE,
            formal_mandate="Strategic oversight of national petroleum corporation.",
            resource_access="Full upstream/downstream petroleum, LNG, solar, hydrogen.",
            decision_authority="Capital allocation, dividend recommendation, strategic direction.",
            accountability_paths="PM (sole shareholder). Auditor-General. Parliament (annual report).",
            opacity_score=0.6,
            capture_risk=CaptureRisk.MODERATE,
            notes="Board appointments are political. But operational competence has historically been high.",
        ),
        PowerActor(
            name="Khazanah Nasional",
            actor_type=PowerActorType.SOE,
            formal_mandate="Sovereign wealth fund. Strategic investments. GLC restructuring.",
            resource_access="RM 100B+ portfolio. Major stakes in CIMB, Axiata, PLUS, IHH, etc.",
            decision_authority="Investment decisions, GLC board appointments, fund allocation.",
            accountability_paths="PM (chairman). Board. Annual report.",
            opacity_score=0.5,
            capture_risk=CaptureRisk.MODERATE,
            notes="Dual mandate: commercial returns AND strategic national interest. Tension is structural.",
        ),
        PowerActor(
            name="PNB (Permodalan Nasional Berhad)",
            actor_type=PowerActorType.SOE,
            formal_mandate="National unit trust. Bumiputera wealth accumulation.",
            resource_access="RM 300B+ AUM. Major stakes in Sime Darby, Maybank, UMW.",
            decision_authority="Investment strategy, fund distribution.",
            accountability_paths="Board. PM. Annual report.",
            opacity_score=0.4,
            capture_risk=CaptureRisk.LOW,
            notes="Largest fund manager in Malaysia. Social mandate (Bumiputera equity) is explicit.",
        ),
    ]

    return PowerTopology(
        domain="PETRONAS/GLC governance",
        scope="National petroleum corporation and government-linked investment companies",
        actors=actors,
        rent_flows=[],
        rule_asymmetries=[
            RuleAsymmetry(
                description="GLC board appointments are political patronage instruments, not merit-based governance.",
                who_benefits="Political appointees, connected networks",
                who_bears_cost="GLC performance, minority shareholders, public trust",
                evidence_basis="INTERPRETATION",
                reform_difficulty="MEDIUM",
                notes="Malaysia Corporate Governance Code exists but enforcement is weak.",
            ),
        ],
        capture_score=CaptureRisk.MODERATE,
        evidence_quality="INTERPRETATION",
        computed_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        notes="Seed case. Public sources only.",
    )
