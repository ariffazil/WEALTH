"""
Governance Gate — connects trading signals to arifOS constitutional judgment.
F1: Every trade reversible (SL exists) or held.
F2: Signal carries epistemic labels.
F7: Confidence capped at 0.90.
F11: Every signal logged with full provenance.
F13: Arif holds final veto.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from typing import Optional

from ..core.models import Signal, Verdict, Direction, EpistemicLabel


class GovernanceGate:
    """
    Constitutional gate between signal generation and execution.
    Every signal must pass through this gate.
    """

    def __init__(self, require_arifos: bool = True):
        self.require_arifos = require_arifos
        self._log: list[dict] = []

    def evaluate(self, signal: Signal) -> Signal:
        """
        Evaluate a signal against constitutional floors.
        Returns the signal with verdict set.
        """
        reasons = []
        verdict = Verdict.PROCEED

        # F1 AMANAH — must have stop loss
        if signal.stop_loss <= 0:
            verdict = Verdict.BLOCK
            reasons.append("F1: No stop loss — irreversible risk")

        # F2 TRUTH — must have confluence factors
        if not signal.confluence_factors:
            verdict = Verdict.BLOCK
            reasons.append("F2: No confluence factors — no evidence basis")

        # F7 HUMILITY — confidence cap
        if signal.confidence > 0.90:
            signal.confidence = 0.90
            reasons.append("F7: Confidence capped at 0.90")

        # RR ratio minimum
        if signal.rr_ratio < 1.5:
            verdict = Verdict.HOLD
            reasons.append(f"RR ratio {signal.rr_ratio:.1f} < 1.5 — insufficient reward")

        # Direction must be clear
        if signal.direction == Direction.FLAT:
            verdict = Verdict.SABAR
            reasons.append("No clear direction — SABAR (wait)")

        # Strength must be at least WEAK
        if signal.strength.value == "NONE":
            verdict = Verdict.SABAR
            reasons.append("Signal strength NONE — not enough confluence")

        # Confluence score threshold
        if signal.confluence_score < 0.3:
            verdict = Verdict.SABAR
            reasons.append(f"Confluence score {signal.confluence_score:.3f} too low")

        # Log
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signal_id": signal.signal_id,
            "direction": signal.direction.value,
            "confidence": signal.confidence,
            "confluence_score": signal.confluence_score,
            "rr_ratio": signal.rr_ratio,
            "verdict": verdict.value,
            "reasons": reasons,
        }
        self._log.append(entry)

        signal.verdict = verdict
        signal.judge_reason = "; ".join(reasons) if reasons else "All gates passed"

        # Optionally call arifOS arif_judge
        if self.require_arifos and verdict == Verdict.PROCEED:
            arif_verdict = self._call_arif_judge(signal)
            if arif_verdict:
                signal.verdict = arif_verdict
                signal.judge_reason = f"arifOS: {signal.judge_reason}"

        return signal

    def _call_arif_judge(self, signal: Signal) -> Optional[Verdict]:
        """
        Call arifOS arif_judge MCP tool.
        Returns Verdict or None if arifOS unreachable.
        """
        try:
            # Use the arif_judge tool via the MCP interface
            # This is a lightweight HTTP call to the kernel
            import urllib.request
            import urllib.error

            payload = json.dumps({
                "tool": "arif_judge",
                "arguments": {
                    "actor": "trading-system",
                    "intent": f"Execute {signal.direction.value} trade on {signal.symbol}",
                    "domain": "trading",
                    "reversibility_level": "reversible_with_sl",
                    "blast_radius": "MEDIUM",
                    "evidence": [{
                        "type": "signal",
                        "direction": signal.direction.value,
                        "confidence": signal.confidence,
                        "rr_ratio": signal.rr_ratio,
                        "confluence_score": signal.confluence_score,
                    }],
                },
            }).encode()

            req = urllib.request.Request(
                f"http://localhost:{8088}/mcp",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                if isinstance(data, dict):
                    v = data.get("verdict", data.get("result", {}).get("verdict", ""))
                    if "SEAL" in str(v).upper() or "PROCEED" in str(v).upper():
                        return Verdict.PROCEED
                    elif "HOLD" in str(v).upper():
                        return Verdict.HOLD
                    elif "BLOCK" in str(v).upper():
                        return Verdict.BLOCK
                    elif "SABAR" in str(v).upper():
                        return Verdict.SABAR
        except Exception:
            pass  # fail-open: if arifOS down, use local verdict

        return None

    @property
    def log(self) -> list[dict]:
        return list(self._log)

    def last_verdict(self) -> Optional[dict]:
        return self._log[-1] if self._log else None
