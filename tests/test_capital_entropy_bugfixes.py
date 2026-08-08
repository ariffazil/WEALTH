"""
F1-F4 Bugfix Tests for capital_entropy (FORGED 2026-08-08).
DITEMPA BUKAN DIBERI — Forged in flow, not in drift.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from wealth_contracts.envelope import wrap_result
from wealth_mcp.tools.canonical import _coerce_dict_to_list_of_dicts


# ═══════════════════════════════════════════════════════════════════════
# F1: CoercedDictListStrict — dict coercion
# ═══════════════════════════════════════════════════════════════════════

class TestF1_CoercedDictListStrict:
    """CoercedDictListStrict should convert dict→list-of-dicts."""

    def test_flat_dict_converts_to_list(self):
        result = _coerce_dict_to_list_of_dicts({"GDP": "5.8%"})
        assert isinstance(result, list)
        assert len(result) == 1
        # Per-key flattening is NOT done; whole dict wrapped as single item
        assert result[0] == {"GDP": "5.8%"}

    def test_dict_with_multiple_keys(self):
        d = {"GDP": "5.8%", "Inflation": "2.1%"}
        result = _coerce_dict_to_list_of_dicts(d)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == d

    def test_list_of_dicts_passes_through(self):
        original = [{"name": "GDP", "value": "5.8%"}]
        result = _coerce_dict_to_list_of_dicts(original)
        assert result == original

    def test_none_returns_none(self):
        result = _coerce_dict_to_list_of_dicts(None)
        assert result is None

    def test_json_string_coerced(self):
        result = _coerce_dict_to_list_of_dicts('[{"name":"GDP","value":"5.8%"}]')
        assert isinstance(result, list)
        assert result[0]["name"] == "GDP"


# ═══════════════════════════════════════════════════════════════════════
# F2: shadow flag propagation
# ═══════════════════════════════════════════════════════════════════════

class TestF2_ShadowReceiptSuppression:
    """shadow=True must propagate to result envelope."""

    def test_shadow_true_propagated(self):
        result = wrap_result(
            tool_name="test_tool", domain="test",
            result={"score": 0.5}, shadow=True,
        )
        assert result.get("shadow") is True

    def test_shadow_false_default(self):
        result = wrap_result(
            tool_name="test_tool", domain="test",
            result={"score": 0.5},
        )
        assert result.get("shadow") is False

    def test_auto_shadow_from_violations(self):
        result = wrap_result(
            tool_name="test_tool", domain="test",
            result={"score": 0.5, "violations": ["F1"]},
        )
        assert result.get("shadow") is True

    def test_explicit_shadow_true_not_overridden_by_violations_absent(self):
        result = wrap_result(
            tool_name="test_tool", domain="test",
            result={"score": 0.5}, shadow=True,
        )
        assert result.get("shadow") is True


# ═══════════════════════════════════════════════════════════════════════
# F3: kappa_r is derived, not constant
# ═══════════════════════════════════════════════════════════════════════

class TestF3_KappaR_NotConstant:
    """kappa_r must not be hardcoded to 0.93."""

    def test_kappa_r_derived_from_observed(self):
        from wealth_contracts.epistemic import EvidenceQuality
        result = wrap_result(
            tool_name="test_tool", domain="test",
            result={"score": 0.5}, evidence_quality=EvidenceQuality.OBSERVED,
        )
        assert result.get("kappa_r") == 0.88

    def test_kappa_r_derived_from_missing(self):
        from wealth_contracts.epistemic import EvidenceQuality
        result = wrap_result(
            tool_name="test_tool", domain="test",
            result={"score": 0.5}, evidence_quality=EvidenceQuality.MISSING,
        )
        assert result.get("kappa_r") == 0.35

    def test_kappa_r_derived_from_moderate(self):
        from wealth_contracts.epistemic import EvidenceQuality
        result = wrap_result(
            tool_name="test_tool", domain="test",
            result={"score": 0.5}, evidence_quality=EvidenceQuality.MODERATE,
        )
        assert result.get("kappa_r") == 0.70

    def test_kappa_r_explicit_override_preserved(self):
        result = wrap_result(
            tool_name="test_tool", domain="test",
            result={"score": 0.5}, kappa_r=0.42,
        )
        assert result.get("kappa_r") == 0.42


# ═══════════════════════════════════════════════════════════════════════
# F4: evidence_quality gate consistency
# ═══════════════════════════════════════════════════════════════════════

class TestF4_EvidenceGateContradiction:
    """MISSING evidence + PASS gate = contradiction unless reflection present."""

    def test_wrap_result_has_evidence_gate_at_server_level(self):
        """_w0_evidence_gate is added by server.py, not wrap_result.

        wrap_result produces the envelope; server.py's _governance_call_tool
        closure (inside create_mcp_server) adds the _w0_evidence_gate field
        based on material_args coverage.
        """
        result = wrap_result(
            tool_name="test_tool", domain="test",
            result={"score": 0.5},
        )
        assert "_w0_evidence_gate" not in result, (
            "_w0_evidence_gate should be added by server.py wrapper, not wrap_result"
        )
