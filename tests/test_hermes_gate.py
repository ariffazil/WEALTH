"""
HERMES semantic gate tests (FORGED 2026-09-16 — F13 directive:
meaning preconditions capital compute).

Covers: semantic extraction heuristics, HERMES verdict mapping
(PASS/888_HOLD/REWRITE_REQUIRED/BLOCKED), injection hard gate,
transport/protocol failures under enforce vs warn modes, config
switches, and exempt tools.
"""

from __future__ import annotations

import pytest

from wealth_mcp import hermes_gate
from wealth_mcp.hermes_gate import (
    EXEMPT_TOOLS,
    GateProtocolError,
    GateTransportError,
    _outcome_from_verdict,
    build_claim,
    extract_semantic_fields,
    gate_status,
    run_semantic_gate,
)


def _hermes_inner(
    verdict: str = "PASS",
    injection: bool = False,
    violations: list | None = None,
) -> dict:
    return {
        "claim_id": "hc-test01",
        "verdict": verdict,
        "violations": violations
        or [
            {
                "rule": "RASA_GATE_888_HOLD",
                "severity": "888_HOLD",
                "message": "CL-03 interior-state claim",
            }
        ]
        if verdict != "PASS"
        else [],
        "permitted_statement": "statable form",
        "injection_scan": {
            "injection_detected": injection,
            "categories": ["PROMPT_INJECTION"] if injection else [],
        },
    }


# ═══════════════════════════════════════════════════════════════════════
# Semantic extraction
# ═══════════════════════════════════════════════════════════════════════


class TestExtractSemanticFields:
    def test_prose_detected(self):
        args = {
            "declared_purpose": (
                "Maximize dividend stability for the household account"
            )
        }
        fields = extract_semantic_fields(args)
        assert list(fields) == ["declared_purpose"]

    def test_enum_symbol_numbers_not_semantic(self):
        args = {
            "symbol": "GC=F",
            "interval": "1h",
            "trend_bias": "auto",
            "realizations": 1000,
            "sw_cutoff": 0.6,
        }
        assert extract_semantic_fields(args) == {}

    def test_nested_lists_and_dicts(self):
        args = {
            "actual_behaviors": [
                "The committee approves every proposal without reading it"
            ],
            "actors": [
                {"name": "unit-x", "note": "reports only good news to the board"}
            ],
        }
        fields = extract_semantic_fields(args)
        assert "actual_behaviors[0]" in fields
        assert "actors[0].note" in fields

    def test_identity_keys_skipped_even_when_prose(self):
        args = {
            "session_id": "this is a long session id string with spaces",
            "_meta": {"actor_id": "someone wrote a long actor string here"},
            "trace_id": "a trace description that looks like prose honestly",
        }
        assert extract_semantic_fields(args) == {}

    def test_field_cap_at_eight(self):
        args = {
            f"note_{i}": f"behavior number {i} described in prose form always"
            for i in range(20)
        }
        assert len(extract_semantic_fields(args)) == 8

    def test_build_claim_carries_tool_and_fields(self):
        claim = build_claim(
            "capital_entropy", {"declared_purpose": "Stability above all else"}
        )
        assert claim.startswith("[capital_entropy]")
        assert "declared_purpose: Stability above all else" in claim


# ═══════════════════════════════════════════════════════════════════════
# Verdict mapping
# ═══════════════════════════════════════════════════════════════════════


class TestOutcomeMapping:
    def test_pass(self):
        outcome, code, rules = _outcome_from_verdict(_hermes_inner("PASS"))
        assert (outcome, code, rules) == ("PASS", "", [])

    def test_hold(self):
        outcome, code, rules = _outcome_from_verdict(_hermes_inner("888_HOLD"))
        assert outcome == "HOLD"
        assert code == "SEMANTIC_GATE_HOLD"
        assert "RASA_GATE_888_HOLD" in rules

    def test_rewrite_required(self):
        outcome, code, _ = _outcome_from_verdict(_hermes_inner("REWRITE_REQUIRED"))
        assert (outcome, code) == ("REWRITE_REQUIRED", "SEMANTIC_GATE_REWRITE")

    def test_blocked(self):
        outcome, code, _ = _outcome_from_verdict(_hermes_inner("BLOCKED"))
        assert (outcome, code) == ("BLOCKED", "SEMANTIC_GATE_BLOCKED")

    def test_injection_hard_gate_overrides_pass(self):
        inner = _hermes_inner("PASS", injection=True)
        outcome, code, rules = _outcome_from_verdict(inner)
        assert outcome == "INJECTION"
        assert code == "SEMANTIC_GATE_INJECTION"
        assert "INJECTION" in rules and "PROMPT_INJECTION" in rules

    def test_unknown_verdict_raises_protocol(self):
        with pytest.raises(GateProtocolError):
            _outcome_from_verdict(_hermes_inner("MAYBE"))


# ═══════════════════════════════════════════════════════════════════════
# Gate behavior (mocked HERMES wire)
# ═══════════════════════════════════════════════════════════════════════

_PROSE_ARGS = {
    "declared_purpose": (
        "The dividend will replace all government oil revenue because "
        "Arif feels confident about it"
    )
}


def _mock_hermes(monkeypatch, inner=None, exc=None, calls=None):
    def fake_call(url, timeout, claim, tool_name):
        if calls is not None:
            calls.append({"tool": tool_name, "claim": claim})
        if exc is not None:
            raise exc
        return inner if inner is not None else _hermes_inner("PASS")

    monkeypatch.setattr(hermes_gate, "_mcp_claim_validate", fake_call)


class TestRunSemanticGate:
    @pytest.mark.asyncio
    async def test_pass_attaches_claim_id(self, monkeypatch):
        _mock_hermes(monkeypatch, _hermes_inner("PASS"))
        state = await run_semantic_gate("capital_entropy", dict(_PROSE_ARGS))
        assert state["status"] == "PASS"
        assert state["outcome"] == "PASS"
        assert state["claim_id"] == "hc-test01"
        assert "latency_ms" in state

    @pytest.mark.asyncio
    async def test_hold_blocks(self, monkeypatch):
        _mock_hermes(monkeypatch, _hermes_inner("888_HOLD"))
        state = await run_semantic_gate("capital_entropy", dict(_PROSE_ARGS))
        assert state["status"] == "BLOCKED"
        assert state["outcome"] == "HOLD"
        assert state["error_code"] == "SEMANTIC_GATE_HOLD"
        assert "RASA_GATE_888_HOLD" in state["violations"]

    @pytest.mark.asyncio
    async def test_injection_blocks_even_on_pass_verdict(self, monkeypatch):
        _mock_hermes(monkeypatch, _hermes_inner("PASS", injection=True))
        state = await run_semantic_gate("capital_diagnose", dict(_PROSE_ARGS))
        assert state["status"] == "BLOCKED"
        assert state["error_code"] == "SEMANTIC_GATE_INJECTION"

    @pytest.mark.asyncio
    async def test_no_semantic_content_never_calls_hermes(self, monkeypatch):
        calls: list = []
        _mock_hermes(monkeypatch, _hermes_inner("PASS"), calls=calls)
        state = await run_semantic_gate(
            "capital_backtest", {"symbol": "GC=F", "interval": "1h"}
        )
        assert state["status"] == "PASS"
        assert state["outcome"] == "NO_SEMANTIC_CONTENT"
        assert calls == []

    @pytest.mark.asyncio
    async def test_exempt_tool_skips(self, monkeypatch):
        calls: list = []
        _mock_hermes(monkeypatch, _hermes_inner("PASS"), calls=calls)
        state = await run_semantic_gate("capital_primitive", dict(_PROSE_ARGS))
        assert state["outcome"] == "GATE_EXEMPT"
        assert calls == []
        assert "capital_primitive" in EXEMPT_TOOLS

    @pytest.mark.asyncio
    async def test_gate_off_skips(self, monkeypatch):
        monkeypatch.setenv("WEALTH_HERMES_GATE", "off")
        calls: list = []
        _mock_hermes(monkeypatch, _hermes_inner("PASS"), calls=calls)
        state = await run_semantic_gate("capital_entropy", dict(_PROSE_ARGS))
        assert state["status"] == "SKIPPED"
        assert state["outcome"] == "GATE_OFF"
        assert calls == []

    @pytest.mark.asyncio
    async def test_transport_failure_enforce_fail_closed(self, monkeypatch):
        monkeypatch.delenv("WEALTH_HERMES_GATE_MODE", raising=False)
        _mock_hermes(monkeypatch, exc=GateTransportError("connection refused"))
        state = await run_semantic_gate("capital_entropy", dict(_PROSE_ARGS))
        assert state["status"] == "BLOCKED"
        assert state["outcome"] == "UNAVAILABLE"
        assert state["error_code"] == "SEMANTIC_GATE_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_transport_failure_warn_degrades_consciously(
        self, monkeypatch
    ):
        monkeypatch.setenv("WEALTH_HERMES_GATE_MODE", "warn")
        _mock_hermes(monkeypatch, exc=GateTransportError("timeout"))
        state = await run_semantic_gate("capital_entropy", dict(_PROSE_ARGS))
        assert state["status"] == "PASS"
        assert state["outcome"] == "PASS_WARN_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_protocol_failure_enforce_fail_closed(self, monkeypatch):
        monkeypatch.delenv("WEALTH_HERMES_GATE_MODE", raising=False)
        _mock_hermes(monkeypatch, exc=GateProtocolError("no result object"))
        state = await run_semantic_gate("capital_entropy", dict(_PROSE_ARGS))
        assert state["status"] == "BLOCKED"
        assert state["error_code"] == "SEMANTIC_GATE_PROTOCOL"

    @pytest.mark.asyncio
    async def test_protocol_failure_warn_passes(self, monkeypatch):
        monkeypatch.setenv("WEALTH_HERMES_GATE_MODE", "warn")
        _mock_hermes(monkeypatch, exc=GateProtocolError("garbled"))
        state = await run_semantic_gate("capital_entropy", dict(_PROSE_ARGS))
        assert state["status"] == "PASS"
        assert state["outcome"] == "PASS_WARN_PROTOCOL"


class TestGateStatus:
    def test_health_snapshot_shape(self, monkeypatch):
        monkeypatch.delenv("WEALTH_HERMES_GATE", raising=False)
        monkeypatch.delenv("WEALTH_HERMES_GATE_MODE", raising=False)
        snap = gate_status()
        assert snap["gate"] == "hermes_semantic"
        assert snap["enabled"] is True
        assert snap["mode"] == "enforce"
        assert snap["fail_closed"] is True
        assert "PASS" in snap["verdicts"] and "888_HOLD" in snap["verdicts"]
