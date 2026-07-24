"""Forge 1 — WEALTH Ingress Session Contract Tests."""
import json
import pytest
from wealth_contracts.envelope import WealthEnvelope, wrap_result, WEALTH_OUTPUT_SCHEMA
from wealth_contracts.epistemic import EpistemicTag, EvidenceQuality

class TestSessionContract:
    """Acceptance tests for Forge 1: WEALTH must echo session identity."""

    def test_envelope_carries_session_identity(self):
        """WealthEnvelope must store and serialize session_id, actor_id, trace_id."""
        env = WealthEnvelope(
            tool_name="test",
            domain="test",
            result={"value": 42},
            session_id="SEAL-test1234567890ab",
            actor_id="arif",
            trace_id="trace-abc-123",
        )
        d = env.to_dict()
        assert d["session_id"] == "SEAL-test1234567890ab"
        assert d["actor_id"] == "arif"
        assert d["trace_id"] == "trace-abc-123"

    def test_wrap_result_passes_identity(self):
        """wrap_result must pass session_id, actor_id, trace_id to envelope."""
        result = wrap_result(
            tool_name="capital_health",
            domain="capital",
            result={"net_worth": 1000000},
            session_id="SEAL-health00000001",
            actor_id="arif",
            trace_id="trace-health-001",
        )
        assert result["session_id"] == "SEAL-health00000001"
        assert result["actor_id"] == "arif"
        assert result["trace_id"] == "trace-health-001"

    def test_output_schema_includes_identity_fields(self):
        """WEALTH_OUTPUT_SCHEMA must declare session_id, actor_id, trace_id."""
        props = WEALTH_OUTPUT_SCHEMA["properties"]
        assert "session_id" in props
        assert "actor_id" in props
        assert "trace_id" in props
        assert props["session_id"]["type"] == "string"
        assert props["actor_id"]["type"] == "string"
        assert props["trace_id"]["type"] == "string"

    def test_missing_session_still_works(self):
        """Tools must work without session for backward compat (observational only)."""
        env = WealthEnvelope(
            tool_name="test",
            domain="test",
            result={"value": 0},
            session_id=None,
            actor_id=None,
            trace_id=None,
        )
        d = env.to_dict()
        assert "session_id" not in d
        assert "actor_id" not in d
        assert "trace_id" not in d
