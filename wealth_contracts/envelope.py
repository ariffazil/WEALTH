"""
WEALTH Contracts — Universal output envelope.

Every public WEALTH MCP tool returns this envelope.
LLM-agnostic. Model proposes. MCP contract disciplines.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .epistemic import (
    ClaimState,
    EpistemicTag,
    EvidenceQuality,
    MissingInput,
    UncertaintyBand,
)
from .authority import ExecutionAuthority


class WisdomDimension:
    """Wisdom Economics dimension score."""

    def __init__(
        self,
        dimension: str,
        score: float,
        evidence: str,
        epistemic_tag: EpistemicTag = EpistemicTag.INTERPRETED,
    ):
        self.dimension = dimension
        self.score = max(0.0, min(1.0, score))
        self.evidence = evidence
        self.epistemic_tag = epistemic_tag

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "score": self.score,
            "evidence": self.evidence,
            "epistemic_tag": self.epistemic_tag.value,
        }


class PowerDimension:
    """Power Intelligence dimension score."""

    def __init__(
        self,
        dimension: str,
        risk_level: str,
        evidence: str,
        who_benefits: str = "unknown",
        who_carries_downside: str = "unknown",
    ):
        self.dimension = dimension
        self.risk_level = risk_level  # LOW, MEDIUM, HIGH, CRITICAL
        self.evidence = evidence
        self.who_benefits = who_benefits
        self.who_carries_downside = who_carries_downside

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "risk_level": self.risk_level,
            "evidence": self.evidence,
            "who_benefits": self.who_benefits,
            "who_carries_downside": self.who_carries_downside,
        }


class WealthEnvelope:
    """
    Universal WEALTH output envelope.
    Every public MCP tool returns this.
    LLM-agnostic. Model proposes. MCP contract disciplines.
    """

    def __init__(
        self,
        *,
        tool_name: str,
        domain: str,
        result: Any,
        result_type: str = "scalar",
        epistemic_tag: EpistemicTag = EpistemicTag.ASSUMED,
        claim_state: ClaimState = ClaimState.DRAFT,
        evidence_quality: EvidenceQuality = EvidenceQuality.MISSING,
        uncertainty_band: Optional[UncertaintyBand] = None,
        wisdom_dimensions: Optional[List[WisdomDimension]] = None,
        power_dimensions: Optional[List[PowerDimension]] = None,
        dignity_impact: Optional[str] = None,
        sovereignty_effect: Optional[str] = None,
        capture_risk_level: Optional[str] = None,
        who_benefits: Optional[str] = None,
        who_carries_downside: Optional[str] = None,
        execution_authorized: bool = False,
        execution_authority: ExecutionAuthority = ExecutionAuthority.OBSERVATION,
        human_final_authority: str = "Arif",
        requires_888_hold: bool = False,
        source_attribution: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        missing_inputs: Optional[List[MissingInput]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        tool_version: str = "2026.07.12",
        # Constitutional fields (Gap Ledger Phase 1-3)
        witness: Optional[Dict[str, Any]] = None,
        shadow: bool = False,
        kappa_r: Optional[float] = None,
        psi_le: Optional[float] = None,
        qdf: Optional[str] = None,
        pipeline_stage: Optional[str] = None,
        forge_laws: Optional[List[str]] = None,
    ):
        # Identity
        self.tool_name = tool_name
        self.tool_version = tool_version
        self.domain = domain

        # Result
        self.result = result
        self.result_type = result_type

        # Epistemology
        self.epistemic_tag = epistemic_tag
        self.claim_state = claim_state
        self.evidence_quality = evidence_quality
        self.uncertainty_band = uncertainty_band

        # Wisdom Economics
        self.wisdom_dimensions = wisdom_dimensions
        self.dignity_impact = dignity_impact
        self.sovereignty_effect = sovereignty_effect

        # Power Intelligence
        self.power_dimensions = power_dimensions
        self.capture_risk_level = capture_risk_level
        self.who_benefits = who_benefits
        self.who_carries_downside = who_carries_downside

        # Authority
        self.execution_authorized = execution_authorized
        self.execution_authority = execution_authority
        self.human_final_authority = human_final_authority
        self.requires_888_hold = requires_888_hold

        # Provenance
        self.source_attribution = source_attribution or []
        self.computation_timestamp = datetime.now(timezone.utc).isoformat()
        self.session_id = session_id
        self.actor_id = actor_id
        self.trace_id = trace_id

        # Missing evidence
        self.missing_inputs = missing_inputs or []

        # Metadata
        self.metadata = metadata or {}
        self.warnings = warnings or []
        self.errors = errors or []

        # Constitutional fields (Gap Ledger Phase 1-3)
        self.witness = witness
        self.shadow = shadow
        self.kappa_r = kappa_r
        self.psi_le = psi_le
        self.qdf = qdf
        self.pipeline_stage = pipeline_stage
        self.forge_laws = forge_laws or []

    def to_dict(self) -> dict:
        """Serialize to dict for MCP response."""
        d: Dict[str, Any] = {
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "domain": self.domain,
            "result": self.result,
            "result_type": self.result_type,
            "epistemic_tag": self.epistemic_tag.value,
            "claim_state": self.claim_state.value,
            "evidence_quality": self.evidence_quality.value,
            "execution_authorized": self.execution_authorized,
            "execution_authority": self.execution_authority.value,
            "human_final_authority": self.human_final_authority,
            "requires_888_hold": self.requires_888_hold,
            "source_attribution": self.source_attribution,
            "computation_timestamp": self.computation_timestamp,
            "missing_inputs": [
                m.to_dict() if hasattr(m, "to_dict") else m for m in self.missing_inputs
            ],
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
        }

        if self.uncertainty_band:
            d["uncertainty_band"] = (
                self.uncertainty_band.to_dict()
                if hasattr(self.uncertainty_band, "to_dict")
                else self.uncertainty_band
            )

        if self.wisdom_dimensions:
            d["wisdom_dimensions"] = [
                w.to_dict() if hasattr(w, "to_dict") else w
                for w in self.wisdom_dimensions
            ]

        if self.power_dimensions:
            d["power_dimensions"] = [
                p.to_dict() if hasattr(p, "to_dict") else p
                for p in self.power_dimensions
            ]

        if self.dignity_impact:
            d["dignity_impact"] = self.dignity_impact
        if self.sovereignty_effect:
            d["sovereignty_effect"] = self.sovereignty_effect
        if self.capture_risk_level:
            d["capture_risk_level"] = self.capture_risk_level
        if self.who_benefits:
            d["who_benefits"] = self.who_benefits
        if self.who_carries_downside:
            d["who_carries_downside"] = self.who_carries_downside
        if self.session_id:
            d["session_id"] = self.session_id
        if self.trace_id:
            d["trace_id"] = self.trace_id
        if self.actor_id:
            d["actor_id"] = self.actor_id

        # Constitutional fields
        if self.witness:
            d["witness"] = self.witness
        d["shadow"] = self.shadow
        if self.kappa_r is not None:
            d["kappa_r"] = self.kappa_r
        if self.psi_le is not None:
            d["psi_le"] = self.psi_le
        if self.qdf:
            d["qdf"] = self.qdf
        if self.pipeline_stage:
            d["pipeline_stage"] = self.pipeline_stage
        if self.forge_laws:
            d["forge_laws"] = self.forge_laws

        return d

    def to_json(self, **kwargs) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), default=str, **kwargs)

    @classmethod
    def from_dict(cls, d: dict) -> "WealthEnvelope":
        """Deserialize from dict."""
        epistemic_tag = EpistemicTag(d.get("epistemic_tag", "ASSUMED"))
        claim_state = ClaimState(d.get("claim_state", "DRAFT"))
        evidence_quality = EvidenceQuality(d.get("evidence_quality", "MISSING"))
        execution_authority = ExecutionAuthority(
            d.get("execution_authority", "OBSERVATION")
        )

        uncertainty_band = None
        if d.get("uncertainty_band"):
            uncertainty_band = UncertaintyBand.from_dict(d["uncertainty_band"])

        wisdom_dimensions = None
        if d.get("wisdom_dimensions"):
            wisdom_dimensions = [
                WisdomDimension(
                    dimension=w["dimension"],
                    score=w["score"],
                    evidence=w["evidence"],
                    epistemic_tag=EpistemicTag(w.get("epistemic_tag", "INTERPRETED")),
                )
                for w in d["wisdom_dimensions"]
            ]

        power_dimensions = None
        if d.get("power_dimensions"):
            power_dimensions = [
                PowerDimension(
                    dimension=p["dimension"],
                    risk_level=p["risk_level"],
                    evidence=p["evidence"],
                    who_benefits=p.get("who_benefits", "unknown"),
                    who_carries_downside=p.get("who_carries_downside", "unknown"),
                )
                for p in d["power_dimensions"]
            ]

        missing_inputs = None
        if d.get("missing_inputs"):
            missing_inputs = [
                MissingInput(
                    name=m["name"],
                    description=m["description"],
                    impact_if_obtained=m["impact_if_obtained"],
                )
                for m in d["missing_inputs"]
            ]

        return cls(
            tool_name=d["tool_name"],
            tool_version=d.get("tool_version", "2026.07.12"),
            domain=d["domain"],
            result=d["result"],
            result_type=d.get("result_type", "scalar"),
            epistemic_tag=epistemic_tag,
            claim_state=claim_state,
            evidence_quality=evidence_quality,
            uncertainty_band=uncertainty_band,
            wisdom_dimensions=wisdom_dimensions,
            power_dimensions=power_dimensions,
            dignity_impact=d.get("dignity_impact"),
            sovereignty_effect=d.get("sovereignty_effect"),
            capture_risk_level=d.get("capture_risk_level"),
            who_benefits=d.get("who_benefits"),
            who_carries_downside=d.get("who_carries_downside"),
            execution_authorized=d.get("execution_authorized", False),
            execution_authority=execution_authority,
            human_final_authority=d.get("human_final_authority", "Arif"),
            requires_888_hold=d.get("requires_888_hold", False),
            source_attribution=d.get("source_attribution", []),
            session_id=d.get("session_id"),
            actor_id=d.get("actor_id"),
            missing_inputs=missing_inputs,
            metadata=d.get("metadata", {}),
            warnings=d.get("warnings", []),
            errors=d.get("errors", []),
            witness=d.get("witness"),
            shadow=d.get("shadow", False),
            kappa_r=d.get("kappa_r"),
            psi_le=d.get("psi_le"),
            qdf=d.get("qdf"),
            pipeline_stage=d.get("pipeline_stage"),
            forge_laws=d.get("forge_laws", []),
        )


# ── WEALTH Output Schema (MCP outputSchema contract, FORGED 2026-07-12) ──
# Declared here — passed to @mcp.tool(output_schema=WEALTH_OUTPUT_SCHEMA)
# Fixes 421 Misdirected Request: kernel bridge validates against declared schema.
WEALTH_OUTPUT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "tool_name": {"type": "string"},
        "tool_version": {"type": "string"},
        "domain": {"type": "string"},
        "result": {"type": "object"},
        "result_type": {"type": "string"},
        "epistemic_tag": {
            "type": "string",
            "enum": [
                "OBSERVED",
                "DERIVED",
                "INTERPRETED",
                "SPECULATED",
                "ASSUMED",
                "RETRIEVED",
                "MEMORY",
                "INFERRED",
                "MISSING",
            ],
        },
        "claim_state": {
            "type": "string",
            "enum": [
                "DRAFT",
                "PLAUSIBLE",
                "CONFIRMED",
                "HYPOTHESIS",
                "UNPROVEN",
                "UNFALSIFIABLE",
            ],
        },
        "evidence_quality": {
            "type": "string",
            "enum": [
                "VERIFIED",
                "SEALED",
                "OBSERVED",
                "RETRIEVED",
                "MEMORY",
                "INFERRED",
                "MODERATE",
                "WEAK",
                "MISSING",
            ],
        },
        "execution_authorized": {"type": "boolean"},
        "execution_authority": {
            "type": "string",
            "enum": ["OBSERVATION", "ADVISORY", "EXECUTIVE", "SOVEREIGN"],
        },
        "human_final_authority": {"type": "string"},
        "requires_888_hold": {"type": "boolean"},
        "source_attribution": {"type": "array", "items": {"type": "string"}},
        "computation_timestamp": {"type": "string"},
        "missing_inputs": {"type": "array", "items": {"type": "object"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "errors": {"type": "array", "items": {"type": "string"}},
        "uncertainty_band": {"type": "object", "additionalProperties": True},
        "wisdom_dimensions": {"type": "array", "items": {"type": "object"}},
        "power_dimensions": {"type": "array", "items": {"type": "object"}},
        "capture_risk_level": {"type": "string"},
        "who_benefits": {"type": "string"},
        "who_carries_downside": {"type": "string"},
        "dignity_impact": {"type": "string"},
        "sovereignty_effect": {"type": "string"},
        "session_id": {"type": "string"},
        "trace_id": {"type": "string"},
        "actor_id": {"type": "string"},
        "witness": {"type": "object"},
        "shadow": {"type": "boolean"},
        "kappa_r": {"type": "number"},
        "psi_le": {"type": "number"},
        "pipeline_stage": {"type": "string"},
    },
    "required": [
        "tool_name",
        "domain",
        "result",
        "epistemic_tag",
        "evidence_quality",
        "execution_authorized",
        "execution_authority",
        "source_attribution",
        "computation_timestamp",
    ],
    "additionalProperties": True,
}


def wrap_result(
    tool_name: str,
    domain: str,
    result: Any,
    *,
    epistemic_tag: EpistemicTag = EpistemicTag.DERIVED,
    evidence_quality: EvidenceQuality = EvidenceQuality.MODERATE,
    source_attribution: Optional[List[str]] = None,
    **kwargs,
) -> dict:
    """
    Convenience wrapper: take a raw result and wrap it in WealthEnvelope.
    Returns dict for direct MCP tool return.
    Automatically computes shadow flag and attaches kappar/psile/qdf.
    """
    # Auto-compute shadow flag from violations/holds in result
    shadow = False
    if isinstance(result, dict):
        violations = result.get("violations", [])
        holds = result.get("holds", [])
        shadow = len(violations) > 0 or len(holds) > 0

    # Auto-attach constitutional fields if not provided
    try:
        from wealth_core.math import compute_kappa_r, compute_psi_le, get_qdf_version
    except ImportError:
        compute_kappa_r = lambda a, b: round((a + b) / 2, 4)  # noqa: E731
        compute_psi_le = lambda le, c: round(le / (1.0 + c), 4)  # noqa: E731
        get_qdf_version = lambda: "QDF-v2.0-TRINITY"  # noqa: E731

    kappa_r = kwargs.pop("kappa_r", None)
    psi_le = kwargs.pop("psi_le", None)
    qdf = kwargs.pop("qdf", None)
    witness = kwargs.pop("witness", None)
    pipeline_stage = kwargs.pop("pipeline_stage", None)
    forge_laws = kwargs.pop("forge_laws", None)
    # Pop non-WealthEnvelope kwargs before passing to constructor.
    # source is a provenance tag; route to source_attribution.
    source = kwargs.pop("source", None)
    if source:
        if source_attribution is None:
            source_attribution = [source]
        else:
            source_attribution = list(source_attribution) + [source]

    if kappa_r is None:
        kappa_r = compute_kappa_r(0.9, 0.95)
    if psi_le is None:
        psi_le = compute_psi_le(0.3, 0.5)
    if qdf is None:
        qdf = get_qdf_version()
    if witness is None:
        # C11 2026-08-06: Witness activation path. is_complete defaults to false
        # because WEALTH has no middleware that independently confirms witness
        # sources. The activation path is:
        #   1. Orchestrator (Path A) counts independent evidence sources
        #   2. When human + ai + earth all confirmed → is_complete=true
        #   3. Three witnesses = F3 TRI-WITNESS satisfied
        # Until orchestrator exists, this field is observed telemetry only.
        # Per APEX C8: does NOT gate execution. Describes, does not enforce.
        witness = {
            "human": False,
            "ai": True,
            "earth": False,
            "is_complete": False,
            "missing": ["human", "earth"],
        }

    # Zen C8: governance fields are advisory telemetry, not gating floors.
    # kappa_r < 0.95 does NOT block execution. witness incomplete does NOT block.
    # These are observed quantities — they describe, they do not enforce.
    # Per APEX Audit Directive C8: rename pending coordinated migration.
    governance_advisory = {
        "note": "kappa_r, psi_le, and witness are observed telemetry, not gating floors. "
        "A sub-floor reading does NOT block execution. "
        "These fields describe constitutional alignment; they do not enforce it. "
        "Per APEX Audit Directive 2026-08-04 C8.",
        "kappa_r_is_observed": True,
        "witness_is_observed": True,
    }

    # Inspect result and kwargs for evidence quality / unverified estimate signals
    unverified_found = False
    unverified_fields = []

    def _scan_unverified(obj, depth=0):
        nonlocal unverified_found
        if depth > 4 or not obj:
            return
        if isinstance(obj, str):
            if any(
                u in obj.upper()
                for u in ["ESTIMATE_UNVERIFIED", "UNVERIFIED", "GUESSED", "SPECULATED"]
            ):
                unverified_found = True
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if any(
                    u in str(k).upper()
                    for u in ["EVIDENCE_QUALITY", "QUALITY", "PROVENANCE"]
                ):
                    if any(
                        u in str(v).upper()
                        for u in [
                            "ESTIMATE",
                            "UNVERIFIED",
                            "GUESSED",
                            "SPECULATED",
                            "WEAK",
                        ]
                    ):
                        unverified_found = True
                        unverified_fields.append(str(k))
                _scan_unverified(v, depth + 1)
        elif isinstance(obj, list):
            for elem in obj:
                _scan_unverified(elem, depth + 1)

    if isinstance(result, dict):
        _scan_unverified(result)

    if unverified_found:
        evidence_quality = EvidenceQuality.WEAK
        if epistemic_tag in (EpistemicTag.DERIVED, EpistemicTag.OBSERVED):
            epistemic_tag = EpistemicTag.INTERPRETED

        # Cap confidence in result if present
        if isinstance(result, dict):
            if "confidence" in result and isinstance(
                result["confidence"], (int, float)
            ):
                result["confidence"] = min(0.60, float(result["confidence"]))
            result["evidence_quality"] = "WEAK"
            result["unverified_inputs_detected"] = True

    # Inject governance advisory into result metadata so it appears in every response
    if isinstance(result, dict):
        result.setdefault("_governance_advisory", governance_advisory)

    envelope = WealthEnvelope(
        tool_name=tool_name,
        domain=domain,
        result=result,
        epistemic_tag=epistemic_tag,
        evidence_quality=evidence_quality,
        source_attribution=source_attribution or [],
        shadow=shadow,
        kappa_r=kappa_r,
        psi_le=psi_le,
        qdf=qdf,
        witness=witness,
        pipeline_stage=pipeline_stage,
        forge_laws=forge_laws,
        **kwargs,
    )
    d = envelope.to_dict()
    if unverified_found:
        meta = d.setdefault("metadata", {})
        meta["unverified_inputs_detected"] = True
        if unverified_fields:
            meta["unverified_fields"] = unverified_fields
    return d
