"""C10 hardening tests — self-attested verification flag must have ZERO authority effect.

Defect (proven live on the serving organ 2026-09-16):
  auth_verified = bool(caller_flag or payload_flag)
  → requires_888 = is_critical and not auth_verified
  → caller typing True cleared an 888_HOLD on blast_radius=critical.
  Receipts: b06020e3 (888 cleared), de238ed7 (888 cleared while INADMISSIBLE_INTENT erroring).

Fix: authority resolved from arifOS kernel session record via
wealth_arifos_bridge.validate_session_at_arifos; fail-closed.

These tests monkeypatch the bridge so they run WITHOUT a live kernel — the point
is to prove the caller flag is inert in every branch, including fail-closed.
"""

import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wealth_mcp.tools import judge_handoff as jh  # noqa: E402
from wealth_mcp.tools import canonical as canon  # noqa: E402


def _patch_bridge(monkeypatch, verdict):
    """Install a fake validate_session_at_arifos returning `verdict`."""
    import wealth_arifos_bridge

    async def fake(session_id=None, actor_id=None, session_token=None, timeout_seconds=3.0):
        return verdict

    monkeypatch.setattr(wealth_arifos_bridge, "validate_session_at_arifos", fake)


def _get_tool(register_fn, name):
    """Register into a stub MCP and pull the decorated coroutine back out."""
    captured = {}

    class StubMCP:
        def tool(self, **kwargs):
            def deco(fn):
                captured[kwargs.get("name") or fn.__name__] = fn
                return fn

            return deco

    register_fn(StubMCP())
    return captured[name]


def _run(coro_fn, **kwargs):
    return asyncio.get_event_loop().run_until_complete(coro_fn(**kwargs))


# ── helper to obtain both implementations ────────────────────────────────
def _tools():
    mirror = _get_tool(jh.register_judge_handoff, "wealth_judge_handoff")
    live = _get_tool(canon.register_canonical_tools, "wealth_judge_handoff")
    return {"mirror": mirror, "live": live}


def _result(tool_out):
    return tool_out.get("result", tool_out)


# ═══════════════════════════════════════════════════════════════════════
# THE BYPASS: self-attested flag must NOT clear 888
# ═══════════════════════════════════════════════════════════════════════
def test_self_attested_flag_does_not_clear_888_kernel_rejected(monkeypatch):
    """Critical blast + caller says verified=True + kernel rejects → 888 STANDS."""
    _patch_bridge(monkeypatch, {"valid": False, "reason": "L11 AUTH: rejected"})
    for label, tool in _tools().items():
        out = _result(
            _run(
                tool,
                mode="prepare",
                intent="bounded specific intent for test",
                reversibility="IRREVERSIBLE",
                blast_radius="critical",
                actor_id="i-arif-gate-probe",
                actor_cryptographically_verified=True,  # THE ATTACK
                session_id="fabricated-888-probe-B",
            )
        )
        assert out["requires_888_hold"] is True, f"{label}: bypass still live"
        assert out["actor_cryptographically_verified"] is False, f"{label}: flag leaked into result"
        assert any("SELF_ATTESTED_VERIFICATION_IGNORED" in w for w in out["warnings"]), (
            f"{label}: caller not told their flag was ignored"
        )


def test_payload_flag_also_inert(monkeypatch):
    """The payload dict route (p.get(...)) must be inert too — OpenClaw's catch."""
    _patch_bridge(monkeypatch, {"valid": False, "reason": "L11 AUTH: rejected"})
    for label, tool in _tools().items():
        out = _result(
            _run(
                tool,
                mode="prepare",
                intent="bounded specific intent for test",
                reversibility="IRREVERSIBLE",
                blast_radius="critical",
                payload={"actor_cryptographically_verified": True},  # THE ATTACK, via payload
                session_id="fabricated-payload-probe",
            )
        )
        assert out["requires_888_hold"] is True, f"{label}: payload bypass still live"


def test_flag_cannot_beat_erroring_validator(monkeypatch):
    """de238ed7 regression: vague intent erroring + flag → 888 must still stand."""
    _patch_bridge(monkeypatch, {"valid": False, "reason": "L11 AUTH: rejected"})
    for label, tool in _tools().items():
        out = _result(
            _run(
                tool,
                mode="prepare",
                intent="test",  # INADMISSIBLE_INTENT
                reversibility="IRREVERSIBLE",
                blast_radius="critical",
                actor_cryptographically_verified=True,
                session_id="fabricated-validator-probe-C",
            )
        )
        assert any("INADMISSIBLE_INTENT" in e for e in out["validation_errors"])
        assert out["requires_888_hold"] is True, f"{label}: boolean beat validator again"


# ═══════════════════════════════════════════════════════════════════════
# FAIL-CLOSED: kernel unreachable must NOT open the gate
# ═══════════════════════════════════════════════════════════════════════
def test_fail_closed_on_unreachable(monkeypatch):
    _patch_bridge(monkeypatch, {"valid": False, "reason": "ARIFOS_UNREACHABLE", "fail_mode": "CLOSED"})
    for label, tool in _tools().items():
        out = _result(
            _run(
                tool,
                mode="prepare",
                intent="bounded specific intent for test",
                reversibility="IRREVERSIBLE",
                blast_radius="critical",
                session_id="some-session",
            )
        )
        assert out["requires_888_hold"] is True, f"{label}: opened on unreachable kernel"
        assert out["actor_verification_source"] == "ARIFOS_UNREACHABLE"


def test_fail_closed_on_exception(monkeypatch):
    """Bridge raising must fail closed, not open."""
    import wealth_arifos_bridge

    async def boom(**kwargs):
        raise RuntimeError("kernel exploded")

    monkeypatch.setattr(wealth_arifos_bridge, "validate_session_at_arifos", boom)
    for label, tool in _tools().items():
        out = _result(
            _run(
                tool,
                mode="prepare",
                intent="bounded specific intent for test",
                reversibility="IRREVERSIBLE",
                blast_radius="critical",
                session_id="some-session",
            )
        )
        assert out["requires_888_hold"] is True, f"{label}: opened on exception"
        assert out["actor_verification_source"] == "ARIFOS_UNREACHABLE"


# ═══════════════════════════════════════════════════════════════════════
# NO REGRESSION: legitimate paths still work
# ═══════════════════════════════════════════════════════════════════════
def test_kernel_verified_session_clears_888(monkeypatch):
    """The intended positive path: kernel says verified → 888 not required."""
    _patch_bridge(monkeypatch, {"valid": True, "actor": "fed/agi-333", "authority": "EXECUTE_REVERSIBLE"})
    for label, tool in _tools().items():
        out = _result(
            _run(
                tool,
                mode="prepare",
                intent="bounded specific intent for test",
                reversibility="IRREVERSIBLE",
                blast_radius="critical",
                session_id="real-kernel-session",
            )
        )
        assert out["requires_888_hold"] is False, f"{label}: legitimate session wrongly held"
        assert out["actor_cryptographically_verified"] is True
        assert out["actor_verification_source"] == "ARIFOS_KERNEL_SESSION"


def test_non_critical_unaffected(monkeypatch):
    """blast_radius != critical → no 888, unchanged behaviour."""
    _patch_bridge(monkeypatch, {"valid": False, "reason": "L11 AUTH: rejected"})
    for label, tool in _tools().items():
        out = _result(
            _run(
                tool,
                mode="prepare",
                intent="bounded specific intent for test",
                reversibility="REVERSIBLE",
                blast_radius="low",
                session_id="some-session",
            )
        )
        assert out["requires_888_hold"] is False, f"{label}: low blast radius wrongly held"


def test_submit_still_blocked_under_888(monkeypatch):
    """submit + critical + no kernel verification → REJECTED_BY_GOVERNANCE."""
    _patch_bridge(monkeypatch, {"valid": False, "reason": "L11 AUTH: rejected"})
    for label, tool in _tools().items():
        out = _result(
            _run(
                tool,
                mode="submit",
                intent="bounded specific intent for test",
                reversibility="IRREVERSIBLE",
                blast_radius="critical",
                actor_cryptographically_verified=True,  # THE ATTACK at submit
                session_id="fabricated-submit-probe",
            )
        )
        assert out["status"] == "REJECTED_BY_GOVERNANCE", f"{label}: submit went through"
        assert out["submitted"] is False
        assert out["hold_reason"] == "888_HOLD_REQUIRED"
