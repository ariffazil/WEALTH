"""
Tests for WEALTH universal envelope contract.

Every public tool must return a valid WealthEnvelope.
No bare dicts. No raw numbers. No unstructured output.

DITEMPA BUKAN DIBERI.
"""

from __future__ import annotations

import json

from wealth_contracts.envelope import (
    WealthEnvelope,
    WisdomDimension,
    PowerDimension,
    wrap_result,
)
from wealth_contracts.epistemic import (
    EpistemicTag,
    ClaimState,
    EvidenceQuality,
    UncertaintyBand,
    MissingInput,
)
from wealth_contracts.authority import validate_authority


class TestEpistemicTags:
    """F2 TRUTH: epistemic tags must be valid."""

    def test_all_tags_are_strings(self):
        for tag in EpistemicTag:
            assert isinstance(tag.value, str)

    def test_tag_count(self):
        assert len(EpistemicTag) == 5

    def test_observed_is_strongest(self):
        assert EpistemicTag.OBSERVED.value == "OBSERVED"


class TestClaimState:
    """Claim state machine must be valid."""

    def test_draft_is_initial(self):
        assert ClaimState.DRAFT.value == "DRAFT"

    def test_sealed_is_final(self):
        assert ClaimState.SEALED.value == "SEALED"

    def test_void_is_rejection(self):
        assert ClaimState.VOID.value == "VOID"


class TestEvidenceQuality:
    """Evidence quality labels must be valid."""

    def test_strong_is_best(self):
        assert EvidenceQuality.STRONG.value == "STRONG"

    def test_missing_is_worst(self):
        assert EvidenceQuality.MISSING.value == "MISSING"


class TestUncertaintyBand:
    """Uncertainty bands must serialize correctly."""

    def test_creation(self):
        band = UncertaintyBand(p10=100, p50=200, p90=300, distribution="lognormal")
        assert band.p10 == 100
        assert band.p50 == 200
        assert band.p90 == 300
        assert band.distribution == "lognormal"

    def test_to_dict(self):
        band = UncertaintyBand(p10=100, p50=200, p90=300)
        d = band.to_dict()
        assert d["p10"] == 100
        assert d["p50"] == 200
        assert d["p90"] == 300

    def test_from_dict(self):
        d = {"p10": 100, "p50": 200, "p90": 300, "distribution": "normal"}
        band = UncertaintyBand.from_dict(d)
        assert band.p10 == 100
        assert band.distribution == "normal"


class TestMissingInput:
    """Missing inputs must describe what would strengthen output."""

    def test_creation(self):
        m = MissingInput(
            name="DST result",
            description="Drill-stem test pressure data",
            impact_if_obtained="Would upgrade from SPECULATED to DERIVED",
        )
        assert m.name == "DST result"
        assert "SPECULATED" in m.impact_if_obtained

    def test_to_dict(self):
        m = MissingInput("a", "b", "c")
        d = m.to_dict()
        assert d["name"] == "a"


class TestWealthEnvelope:
    """Universal envelope must be well-formed."""

    def test_minimal_envelope(self):
        env = WealthEnvelope(
            tool_name="test_tool",
            domain="capital",
            result={"value": 42},
        )
        d = env.to_dict()
        assert d["tool_name"] == "test_tool"
        assert d["domain"] == "capital"
        assert d["result"] == {"value": 42}
        assert d["execution_authorized"] is False
        assert d["human_final_authority"] == "Arif"

    def test_execution_never_authorized(self):
        """WEALTH computes. It never authorizes execution."""
        env = WealthEnvelope(
            tool_name="test_tool",
            domain="capital",
            result=100,
            execution_authorized=False,
        )
        assert env.execution_authorized is False
        d = env.to_dict()
        assert d["execution_authorized"] is False

    def test_epistemic_tag_present(self):
        """No output without epistemic tag."""
        env = WealthEnvelope(
            tool_name="test_tool",
            domain="capital",
            result=100,
            epistemic_tag=EpistemicTag.DERIVED,
        )
        d = env.to_dict()
        assert d["epistemic_tag"] == "DERIVED"

    def test_roundtrip(self):
        """Envelope must survive dict roundtrip."""
        env = WealthEnvelope(
            tool_name="test_tool",
            domain="risk",
            result={"emv": 0.75},
            epistemic_tag=EpistemicTag.DERIVED,
            evidence_quality=EvidenceQuality.MODERATE,
            uncertainty_band=UncertaintyBand(p10=0.5, p50=0.75, p90=0.9),
            source_attribution=["test_data"],
        )
        d = env.to_dict()
        env2 = WealthEnvelope.from_dict(d)
        assert env2.tool_name == "test_tool"
        assert env2.epistemic_tag == EpistemicTag.DERIVED
        assert env2.uncertainty_band.p50 == 0.75

    def test_json_serialization(self):
        """Envelope must serialize to JSON."""
        env = WealthEnvelope(
            tool_name="test_tool",
            domain="capital",
            result=100,
        )
        j = env.to_json()
        d = json.loads(j)
        assert d["tool_name"] == "test_tool"

    def test_wisdom_dimensions(self):
        """Wisdom dimensions must serialize correctly."""
        env = WealthEnvelope(
            tool_name="test_tool",
            domain="wisdom",
            result="evaluation",
            wisdom_dimensions=[
                WisdomDimension("dignity", 0.8, "preserves human agency"),
                WisdomDimension("sovereignty", 0.6, "creates some dependency"),
            ],
        )
        d = env.to_dict()
        assert len(d["wisdom_dimensions"]) == 2
        assert d["wisdom_dimensions"][0]["dimension"] == "dignity"

    def test_power_dimensions(self):
        """Power dimensions must serialize correctly."""
        env = WealthEnvelope(
            tool_name="test_tool",
            domain="power",
            result="audit",
            power_dimensions=[
                PowerDimension(
                    "capture_risk",
                    "HIGH",
                    "AI model trained on broker data",
                    who_benefits="broker",
                    who_carries_downside="investor",
                ),
            ],
        )
        d = env.to_dict()
        assert d["power_dimensions"][0]["risk_level"] == "HIGH"

    def test_missing_inputs(self):
        """Missing inputs must be listable."""
        env = WealthEnvelope(
            tool_name="test_tool",
            domain="capital",
            result=100,
            missing_inputs=[
                MissingInput("DST data", "Pressure test", "Would upgrade tag"),
            ],
        )
        d = env.to_dict()
        assert len(d["missing_inputs"]) == 1

    def test_warnings_and_errors(self):
        """Warnings and errors must be separate."""
        env = WealthEnvelope(
            tool_name="test_tool",
            domain="capital",
            result=100,
            warnings=["Data is 24h stale"],
            errors=[],
        )
        d = env.to_dict()
        assert len(d["warnings"]) == 1
        assert len(d["errors"]) == 0


class TestAuthorityValidation:
    """Authority validation must catch violations."""

    def test_valid_output(self):
        output = {
            "execution_authorized": False,
            "human_final_authority": "Arif",
            "epistemic_tag": "DERIVED",
        }
        violations = validate_authority(output)
        assert len(violations) == 0

    def test_catches_execution_authorization(self):
        output = {"execution_authorized": True}
        violations = validate_authority(output)
        assert any("execution_authorized" in v for v in violations)

    def test_catches_wrong_sovereign(self):
        output = {"human_final_authority": "AI"}
        violations = validate_authority(output)
        assert any("human_final_authority" in v for v in violations)

    def test_catches_missing_epistemic_tag(self):
        output = {}
        violations = validate_authority(output)
        assert any("epistemic_tag" in v for v in violations)


class TestWrapResult:
    """wrap_result convenience function must work."""

    def test_basic_wrap(self):
        d = wrap_result(
            tool_name="test_tool",
            domain="capital",
            result=42,
            epistemic_tag=EpistemicTag.DERIVED,
        )
        assert d["tool_name"] == "test_tool"
        assert d["result"] == 42
        assert d["epistemic_tag"] == "DERIVED"
        assert d["execution_authorized"] is False
