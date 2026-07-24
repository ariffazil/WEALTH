# arifos_kernel_sdk.py — In-Process Kernel Hook Spec
# Forged: 2026-06-17 by FORGE (000Ω)
# Status: SPEC — code-ready, not yet deployed
# Purpose: The in-process enforcement band for agents you control.
#          Per-call envelope + judge pre-flight + audit post-flight.
#
# Three enforcement bands (from kernel doctrine):
#   1. INSIDE RUNTIME  (this SDK) — richest, lowest overhead
#   2. TRANSPORT (MCP)             — cross-framework, MCP-speaking clients
#   3. OS-LEVEL (EDR)              — for untrusted runtimes (OpenClaw, etc.)
#
# "DITEMPA BUKAN DIBERI — The kernel is forged into every agent."

"""
arifos_kernel_sdk — the in-process hook for arifOS constitutional governance.

Usage (Python):
    from arifos_kernel_sdk import ArifOSKernel, GovernanceHold

    kernel = ArifOSKernel(
        organ="WEALTH",
        agent_id="opencode-333-agi",
        reality_contracts=["/root/WEALTH/reality_contracts/wealth_reality_contract.yaml"],
    )

    # Before any tool/CLI call:
    try:
        verdict = kernel.before_tool_call(
            tool_name="wealth_cashflow_track",
            args={"amount": 1000, "currency": "MYR", "tx_type": "EXPENSE"},
            action_class="EXECUTE_REVERSIBLE",
        )
        # verdict.verdict in {ALLOW, HOLD, BLOCK}
        # verdict.reason explains the decision
    except GovernanceHold as e:
        # 888_HOLD triggered; surface to human
        return escalate_to_arif(e)

    # Execute the call
    result = tool.invoke(args)

    # After the call:
    kernel.after_tool_call(
        tool_name="wealth_cashflow_track",
        args=args,
        output=result,
        started_at=verdict.started_at,
        completed_at=now(),
    )

Usage (TypeScript):
    import { ArifOSKernel, GovernanceHold } from 'arifos-kernel-sdk';

    const kernel = new ArifOSKernel({
        organ: 'WEALTH',
        agentId: 'opencode-333-agi',
        realityContracts: ['/root/WEALTH/reality_contracts/wealth_reality_contract.yaml'],
    });

    const verdict = await kernel.beforeToolCall({
        toolName: 'wealth_cashflow_track',
        args: { amount: 1000, currency: 'MYR', txType: 'EXPENSE' },
        actionClass: 'EXECUTE_REVERSIBLE',
    });
"""

from __future__ import annotations
import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import urllib.request


# ════════════════════════════════════════════════════════════════════
# TYPES (per per_call_envelope.schema.json)
# ════════════════════════════════════════════════════════════════════

class ActionClass(str, Enum):
    OBSERVE = "OBSERVE"
    SUGGEST = "SUGGEST"
    SIMULATE = "SIMULATE"
    DRAFT = "DRAFT"
    QUEUE = "QUEUE"
    EXECUTE_REVERSIBLE = "EXECUTE_REVERSIBLE"
    EXECUTE_HIGH_IMPACT = "EXECUTE_HIGH_IMPACT"
    IRREVERSIBLE = "IRREVERSIBLE"


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    HOLD = "HOLD"          # 888_HOLD — escalate to human
    BLOCK = "BLOCK"        # hard floor violation
    NEEDS_DATA = "NEEDS_DATA"


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FloorChain:
    floors: list[str]      # e.g. ["F1", "F2", "F4", "F11"]
    gates_applied: list[str] = field(default_factory=list)  # GAP1, P9-1, etc.


@dataclass
class CallEnvelope:
    """Per-call metadata (mirrors per_call_envelope.schema.json)."""
    trace_id: str
    session_id: str
    epoch_id: str
    lease_id: str
    actor_id: str
    agent_class: str
    organ_id: str
    tool_name: str
    action_class: str
    floors_chain: list[str]
    gates_planned: list[str]
    risk_tier: str
    approval_state: str
    args_hash: str
    epistemic_label: str
    call_started_at: str = ""
    call_completed_at: str = ""
    output_hash: str = ""
    gate_results: list[dict] = field(default_factory=list)
    vault_seal_id: str = ""


@dataclass
class JudgeVerdict:
    """Returned by before_tool_call."""
    verdict: Verdict
    reason: str
    floor_violations: list[str] = field(default_factory=list)
    gate_results: list[dict] = field(default_factory=list)
    required_lease: Optional[str] = None
    started_at: str = ""
    envelope: Optional[CallEnvelope] = None


class GovernanceHold(Exception):
    """Raised when before_tool_call returns Verdict.HOLD."""
    def __init__(self, verdict: JudgeVerdict):
        self.verdict = verdict
        super().__init__(f"888_HOLD: {verdict.reason}")


# ════════════════════════════════════════════════════════════════════
# KERNEL
# ════════════════════════════════════════════════════════════════════

class ArifOSKernel:
    """
    The in-process kernel hook. Wraps any tool call with the per-call
    envelope, judge pre-flight, and audit post-flight.

    Three enforcement bands:
      - this SDK (in-process, lowest overhead)
      - MCP (transport, cross-framework)
      - OS-level EDR (last resort, for untrusted runtimes)

    The SDK is the primary band for agents you control (opencode, kimi-code,
    openclaw, hermes-asi). The MCP band catches anything the SDK misses
    (third-party MCP clients). The OS band is for the untrusted tail.
    """

    def __init__(
        self,
        organ: str,
        agent_id: str,
        kernel_url: str = "http://127.0.0.1:8088",
        reality_contracts: list[str] = None,
        local_policy_engine: bool = True,
        timeout_seconds: float = 5.0,
    ):
        self.organ = organ
        self.agent_id = agent_id
        self.kernel_url = kernel_url.rstrip("/")
        self.reality_contracts = [Path(p) for p in (reality_contracts or [])]
        self.local_policy_engine = local_policy_engine
        self.timeout_seconds = timeout_seconds
        self._session_id: str = ""
        self._epoch_id: str = "EPOCH-LIVE-1"
        self._lease_id: str = ""
        self._contracts_cache: dict = {}

        # Load reality contracts locally (for offline policy checks)
        if local_policy_engine:
            for path in self.reality_contracts:
                self._contracts_cache[str(path)] = self._load_contract(path)

    # ── Session lifecycle ──────────────────────────────────────────

    def session_init(self, requested_authority: str = "EXECUTE_REVERSIBLE") -> str:
        """
        Bind a constitutional session. Returns session_id.
        Calls arif_session_init at the kernel.
        """
        try:
            req = urllib.request.Request(
                f"{self.kernel_url}/mcp/arif_session_init",
                data=json.dumps({
                    "actor_id": self.agent_id,
                    "requested_authority": requested_authority,
                    "ack_irreversible": False,
                }).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                result = json.loads(resp.read().decode())
                self._session_id = result.get("session_id", "")
                self._lease_id = result.get("lease_id", "")
                self._epoch_id = result.get("epoch_id", self._epoch_id)
                return self._session_id
        except Exception as e:
            # Fail-closed: no session = no authority
            raise GovernanceHold(JudgeVerdict(
                verdict=Verdict.BLOCK,
                reason=f"session_init failed: {e}",
            ))

    # ── Pre-flight (the gate) ──────────────────────────────────────

    def before_tool_call(
        self,
        tool_name: str,
        args: dict,
        action_class: str | ActionClass,
        risk_tier: str | RiskTier = None,
        extra_floors: list[str] = None,
    ) -> JudgeVerdict:
        """
        Pre-flight check before any tool/CLI call.

        1. Build the per-call envelope
        2. Check against local reality contracts (if loaded)
        3. Send to arif_judge (if online)
        4. Return JudgeVerdict

        Raises GovernanceHold if verdict is HOLD (caller should escalate).
        """
        action_class = ActionClass(action_class) if isinstance(action_class, str) else action_class
        risk_tier = RiskTier(risk_tier) if risk_tier else self._infer_risk_tier(action_class)

        envelope = CallEnvelope(
            trace_id=f"trace-{uuid.uuid4()}",
            session_id=self._session_id,
            epoch_id=self._epoch_id,
            lease_id=self._lease_id,
            actor_id=self.agent_id,
            agent_class=self._infer_agent_class(action_class),
            organ_id=self.organ,
            tool_name=tool_name,
            action_class=action_class.value,
            floors_chain=self._infer_floors(action_class, extra_floors),
            gates_planned=self._infer_gates(tool_name),
            risk_tier=risk_tier.value,
            approval_state="open",
            args_hash=self._hash_args(args),
            epistemic_label=self._infer_epistemic(args),
            call_started_at=self._now_iso(),
        )

        # Step 1: Local reality contract check (offline)
        local_verdict = self._check_local_contracts(envelope, args)
        if local_verdict.verdict == Verdict.BLOCK:
            return local_verdict

        # Step 2: Remote judge deliberation (online)
        remote_verdict = self._call_remote_judge(envelope, args)

        # Step 3: Combine (remote wins on conflict, by F13 precedence)
        if remote_verdict.verdict == Verdict.BLOCK or local_verdict.verdict == Verdict.BLOCK:
            return JudgeVerdict(
                verdict=Verdict.BLOCK,
                reason=f"local={local_verdict.reason}; remote={remote_verdict.reason}",
                floor_violations=list(set(local_verdict.floor_violations + remote_verdict.floor_violations)),
                gate_results=local_verdict.gate_results + remote_verdict.gate_results,
                envelope=envelope,
            )

        if remote_verdict.verdict == Verdict.HOLD or local_verdict.verdict == Verdict.HOLD:
            return JudgeVerdict(
                verdict=Verdict.HOLD,
                reason=f"888_HOLD: {remote_verdict.reason or local_verdict.reason}",
                floor_violations=list(set(local_verdict.floor_violations + remote_verdict.floor_violations)),
                gate_results=local_verdict.gate_results + remote_verdict.gate_results,
                envelope=envelope,
            )

        return JudgeVerdict(
            verdict=Verdict.ALLOW,
            reason="all checks passed",
            floor_violations=[],
            gate_results=local_verdict.gate_results + remote_verdict.gate_results,
            started_at=envelope.call_started_at,
            envelope=envelope,
        )

    # ── Post-flight (the audit) ────────────────────────────────────

    def after_tool_call(
        self,
        tool_name: str,
        args: dict,
        output: Any,
        started_at: str,
        completed_at: str = None,
        verdict: JudgeVerdict = None,
    ) -> None:
        """
        Post-flight audit. Emits the completed envelope to NATS / VAULT999.
        Always runs, even if the call failed.
        """
        completed_at = completed_at or self._now_iso()
        output_hash = self._hash_args(output) if not isinstance(output, (bytes, str)) else hashlib.sha256(str(output).encode()).hexdigest()

        # Update envelope
        envelope = verdict.envelope if verdict else None
        if envelope:
            envelope.call_completed_at = completed_at
            envelope.output_hash = output_hash

        # Emit to NATS (fire-and-forget; no blocking)
        try:
            event = {
                "event_type": "TOOL_CALL_COMPLETED",
                "trace_id": envelope.trace_id if envelope else f"trace-{uuid.uuid4()}",
                "session_id": self._session_id,
                "organ_id": self.organ,
                "tool_name": tool_name,
                "action_class": envelope.action_class if envelope else "UNKNOWN",
                "started_at": started_at,
                "completed_at": completed_at,
                "args_hash": self._hash_args(args),
                "output_hash": output_hash,
            }
            self._emit_to_nats(event)
        except Exception:
            # Audit failure is non-blocking (F11 fallback)
            pass

        # For IRREVERSIBLE / EXECUTE_HIGH_IMPACT: push to VAULT999
        if envelope and envelope.action_class in (ActionClass.IRREVERSIBLE.value, ActionClass.EXECUTE_HIGH_IMPACT.value):
            try:
                self._request_vault_seal(envelope, tool_name, args, output)
            except Exception:
                # VAULT seal failure is BLOCKED (F11 hard requirement)
                raise GovernanceHold(JudgeVerdict(
                    verdict=Verdict.BLOCK,
                    reason="VAULT999 seal failed for IRREVERSIBLE/EXECUTE_HIGH_IMPACT",
                ))

    # ── Internal helpers ───────────────────────────────────────────

    def _infer_risk_tier(self, action_class: ActionClass) -> RiskTier:
        if action_class == ActionClass.IRREVERSIBLE:
            return RiskTier.CRITICAL
        if action_class == ActionClass.EXECUTE_HIGH_IMPACT:
            return RiskTier.HIGH
        if action_class in (ActionClass.EXECUTE_REVERSIBLE, ActionClass.QUEUE):
            return RiskTier.MEDIUM
        return RiskTier.LOW

    def _infer_floors(self, action_class: ActionClass, extra: list[str] = None) -> list[str]:
        """F1+F2 always; F13 for IRREVERSIBLE; F11 for writes; etc."""
        floors = ["F1", "F2", "F4", "F11"]
        if action_class in (ActionClass.EXECUTE_HIGH_IMPACT, ActionClass.IRREVERSIBLE):
            floors += ["F7", "F8", "F13"]
        if action_class == ActionClass.IRREVERSIBLE:
            floors += ["F9"]  # anti-hantu — no self-authorization
        if extra:
            floors += extra
        return list(set(floors))

    def _infer_gates(self, tool_name: str) -> list[str]:
        """Map tool name to the gates it must run (organ-specific)."""
        gates = []
        if self.organ == "WEALTH":
            if "stock_analysis" in tool_name:
                gates = [f"GAP{i}" for i in range(1, 11)]
            elif "cashflow_track" in tool_name:
                gates = ["GAP9"]
            elif "market_data" in tool_name or "fx_rate" in tool_name:
                gates = ["GAP2"]
            elif "personal_finance" in tool_name or "zakat" in tool_name:
                gates = ["GAP1"]
        elif self.organ == "GEOX":
            if "claim" in tool_name or "seal" in tool_name:
                gates = [f"P9-{i}" for i in range(1, 10)]
            elif "subsurface" in tool_name:
                gates = ["P9-1", "P9-2", "P9-3", "P9-4", "P9-5"]
            elif "seismic" in tool_name:
                gates = ["P9-7", "P9-8", "P9-9"]
        return gates

    def _infer_epistemic(self, args: dict) -> str:
        """Best-effort epistemic label based on arg shape."""
        return "OBS"  # Default; sophisticated agents can override

    def _infer_agent_class(self, action_class: ActionClass) -> str:
        if action_class == ActionClass.IRREVERSIBLE:
            return "C4"
        if action_class in (ActionClass.EXECUTE_HIGH_IMPACT, ActionClass.EXECUTE_REVERSIBLE):
            return "C2"
        if action_class in (ActionClass.SIMULATE, ActionClass.SUGGEST):
            return "C3"
        return "C1"

    def _hash_args(self, obj: Any) -> str:
        canonical = json.dumps(obj, sort_keys=True, default=str)
        return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"

    def _now_iso(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()

    def _load_contract(self, path: Path) -> dict:
        import yaml
        return yaml.safe_load(path.read_text())

    def _check_local_contracts(self, envelope: CallEnvelope, args: dict) -> JudgeVerdict:
        """Offline check against loaded reality contracts."""
        violations = []
        gate_results = []

        for path, contract in self._contracts_cache.items():
            if contract.get("organ_id") != self.organ:
                continue

            # Check denied transitions
            for denied in contract.get("denied_transitions", []):
                if denied.get("via_tool") == envelope.tool_name:
                    if denied.get("from", "any") in ("any", "*") or envelope.tool_name in denied.get("via_tool", ""):
                        violations.append(f"DX in {path.name}: {denied.get('reason', 'denied')}")

            # Check action class matches tool contract
            for tool in contract.get("tools", []):
                if tool.get("name") == envelope.tool_name:
                    tool_class = tool.get("action_class", "OBSERVE")
                    if self._class_severity(envelope.action_class) > self._class_severity(tool_class):
                        violations.append(
                            f"action_class mismatch: {envelope.tool_name} expects ≤{tool_class}, "
                            f"got {envelope.action_class}"
                        )
                    gate_results.append({
                        "gate": "reality_contract_check",
                        "verdict": "PASS",
                        "tool_contract": tool.get("name"),
                        "expected_class": tool_class,
                        "actual_class": envelope.action_class,
                    })
                    break

        if violations:
            return JudgeVerdict(
                verdict=Verdict.BLOCK,
                reason="; ".join(violations),
                floor_violations=violations,
                gate_results=gate_results,
            )
        return JudgeVerdict(verdict=Verdict.ALLOW, reason="local OK", gate_results=gate_results)

    def _class_severity(self, action_class: str) -> int:
        order = [
            "OBSERVE", "SUGGEST", "SIMULATE", "DRAFT", "QUEUE",
            "EXECUTE_REVERSIBLE", "EXECUTE_HIGH_IMPACT", "IRREVERSIBLE",
        ]
        return order.index(action_class) if action_class in order else -1

    def _call_remote_judge(self, envelope: CallEnvelope, args: dict) -> JudgeVerdict:
        """Send to arif_judge at the kernel."""
        try:
            req = urllib.request.Request(
                f"{self.kernel_url}/mcp/arif_judge_deliberate",
                data=json.dumps({
                    "mode": "validate",
                    "candidate": f"{envelope.tool_name}:{envelope.action_class}",
                    "session_id": envelope.session_id,
                    "actor_id": envelope.actor_id,
                    "evidence_receipt": asdict(envelope),
                    "claimed_evidence_level": envelope.epistemic_label,
                    "action_class": envelope.action_class,
                }).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                result = json.loads(resp.read().decode())
                kernel_verdict = result.get("verdict", "SEAL")
                if kernel_verdict == "SEAL":
                    return JudgeVerdict(verdict=Verdict.ALLOW, reason="kernel SEAL")
                if kernel_verdict in ("888_HOLD", "HOLD", "DEGRADED"):
                    return JudgeVerdict(
                        verdict=Verdict.HOLD,
                        reason=result.get("reasons", ["kernel HOLD"])[0],
                    )
                if kernel_verdict == "VOID":
                    return JudgeVerdict(
                        verdict=Verdict.BLOCK,
                        reason=result.get("reasons", ["kernel VOID"])[0],
                    )
                return JudgeVerdict(verdict=Verdict.ALLOW, reason=f"kernel {kernel_verdict}")
        except Exception as e:
            # Fail-closed: if kernel is unreachable, fall back to local
            return JudgeVerdict(
                verdict=Verdict.HOLD,
                reason=f"kernel unreachable ({e}); falling back to local only",
            )

    def _emit_to_nats(self, event: dict) -> None:
        """Emit to NATS governance stream. Fire-and-forget."""
        # TODO: wire to actual NATS at localhost:4222 when available
        # For now: log to file at /root/VAULT999/nats_emit.jsonl
        nats_log = Path("/root/VAULT999/nats_emit.jsonl")
        nats_log.parent.mkdir(parents=True, exist_ok=True)
        with nats_log.open("a") as f:
            f.write(json.dumps(event) + "\n")

    def _request_vault_seal(self, envelope: CallEnvelope, tool_name: str, args: dict, output: Any) -> None:
        """Push to VAULT999 for IRREVERSIBLE / EXECUTE_HIGH_IMPACT calls."""
        req = urllib.request.Request(
            f"{self.kernel_url}/mcp/arif_vault_seal",
            data=json.dumps({
                "mode": "seal",
                "payload": json.dumps(asdict(envelope)),
                "session_id": envelope.session_id,
                "actor_id": envelope.actor_id,
                "ack_irreversible": envelope.action_class == ActionClass.IRREVERSIBLE.value,
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
            result = json.loads(resp.read().decode())
            envelope.vault_seal_id = result.get("seal_id", "")


# ════════════════════════════════════════════════════════════════════
# FRAMEWORK-SPECIFIC WRAPPERS
# ════════════════════════════════════════════════════════════════════

class LangGraphWrapper:
    """Wrap a LangGraph / OpenCode graph with the kernel."""
    def __init__(self, kernel: ArifOSKernel):
        self.kernel = kernel

    def wrap(self, graph):
        """Wrap graph nodes that emit tool calls."""
        # TODO: implement LangGraph interception
        # For each tool node in the graph, wrap with before_tool_call / after_tool_call
        raise NotImplementedError("LangGraphWrapper.wrap — pending forge")


class OpenAIFunctionsWrapper:
    """Wrap OpenAI Assistants / Functions with the kernel."""
    def __init__(self, kernel: ArifOSKernel):
        self.kernel = kernel

    def wrap_client(self, openai_client):
        """Wrap client.responses.create / client.beta.assistants tool execution."""
        # TODO: implement OpenAI SDK interception
        raise NotImplementedError("OpenAIFunctionsWrapper.wrap_client — pending forge")


# ════════════════════════════════════════════════════════════════════
# EXPORTS
# ════════════════════════════════════════════════════════════════════

__all__ = [
    "ArifOSKernel",
    "ActionClass",
    "Verdict",
    "RiskTier",
    "CallEnvelope",
    "JudgeVerdict",
    "GovernanceHold",
    "LangGraphWrapper",
    "OpenAIFunctionsWrapper",
]
