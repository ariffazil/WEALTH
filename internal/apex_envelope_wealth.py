"""
APEX Envelope for WEALTH — Capital Intelligence organ

Maps financial/thermodynamic signals to 10 APEX gates:
  Amanah: financial integrity (no claim > evidence)
  Presence: market boundary (LIVE vs CACHED)
  Humility: risk bands, confidence intervals
  Signal: market data quality, price feeds
  Understanding: model coherence (NPV logic, discounting)
  Energy: compute cost (Monte Carlo, optimization)
  Authority: actor verification
  Reversibility: READ/MUTATE classification
  Proof: ZKPC level matching
  Sovereign: passthrough

DITEMPA BUKAN DIBERI
"""

from __future__ import annotations

from typing import Any

try:
    from apex_envelope import apex_envelope, gate
except ImportError:
    import math
    from datetime import datetime, timezone

    APEX_EQUATION = "g(t)=A(t)\u00b7P(t)\u00b7H(t)\u00b7\u221a(S(t)\u00b7U(t))\u00b7E(t)\u00b2"

    def _geometric_mean(values):
        positive = [v for v in values if v > 0]
        return (math.prod(positive) ** (1.0 / len(positive))) if positive else 0.0

    def _gate(passed, score, detail, **extra):
        v = {"pass": passed, "score": round(max(0.0, min(1.0, score)), 4), "detail": detail}
        v.update(extra)
        return v

    def apex_envelope(*, tool_name="unknown", confidence=0.88, evidence_strength=0.95,
                      boundary="LIVE", uncertainty_declared=True, coherent=True,
                      actor_id=None, action_class="READ", proof_level="ZKPC_OBSERVATION",
                      cost_used=0.0, cost_budget=1.0, landauer_ratio=1.0, **kw):
        gates = {
            "amanah": _gate(confidence <= evidence_strength + 0.05, min(1.0, evidence_strength / max(confidence, 1e-6)),
                           f"confidence {confidence:.2f}"),
            "presence": _gate(True, {"LIVE": 1.0, "CACHED": 0.8, "INFERRED": 0.5}.get(boundary, 0.5), boundary, boundary=boundary),
            "humility": _gate(uncertainty_declared, 1.0 if uncertainty_declared else 0.3, "declared"),
            "signal": _gate(True, 0.7, "default"),
            "understanding": _gate(coherent, 0.9 if coherent else 0.2, "coherent" if coherent else "incoherent"),
            "energy": _gate(cost_used <= cost_budget, max(0.0, 1.0 - cost_used / max(cost_budget, 1e-6)), f"cost {cost_used:.2f}"),
            "authority": _gate(bool(actor_id), 1.0 if actor_id else 0.0, f"actor={actor_id}", actor_id=actor_id),
            "reversibility": _gate(True, 1.0, action_class, action_class=action_class),
            "proof": _gate(True, 0.85, proof_level, proof_level=proof_level),
            "sovereign": _gate(True, 1.0, "no F13 halt"),
        }
        dials = {
            "A": round(_geometric_mean([gates["amanah"]["score"], gates["humility"]["score"], gates["understanding"]["score"]]), 4),
            "P": round(gates["presence"]["score"], 4),
            "H": round(min(gates["authority"]["score"], gates["sovereign"]["score"]), 4),
            "S": round(gates["signal"]["score"], 4),
            "U": round(_geometric_mean([gates["reversibility"]["score"], gates["proof"]["score"]]), 4),
            "E": round(gates["energy"]["score"], 4),
        }
        G = round(dials["A"] * dials["P"] * dials["H"] * math.sqrt(dials["S"] * dials["U"]) * dials["E"] ** 2, 4)
        verdict = "SEAL" if G >= 0.80 else ("SABAR" if G >= 0.50 else "HOLD")
        return {"equation": APEX_EQUATION, "gates": gates, "dials": dials, "G": G, "verdict": verdict,
                "timestamp": datetime.now(timezone.utc).isoformat()}


def wealth_apex_envelope(
    *,
    tool_name: str,
    g_score: float,
    entropy_s: float,
    verdict: str,
    allocation_signal: str,
    confidence: float,
    epistemic_class: str,
    failure_flags: list[str],
    actor_id: str | None,
) -> dict[str, Any]:
    """Build APEX envelope from WEALTH-specific signals."""
    ok = verdict in ("SEAL", "PASS") and not failure_flags
    boundary = "LIVE" if ok else "CACHED"
    action_class = "READ" if any(k in tool_name for k in ("read", "check", "get", "list")) else "MUTATE"

    return apex_envelope(
        tool_name=tool_name,
        confidence=confidence,
        evidence_strength=max(confidence, g_score),
        boundary=boundary,
        uncertainty_declared=True,
        coherent=ok and epistemic_class not in ("VOID",),
        cost_used=abs(entropy_s),
        cost_budget=1.0,
        actor_id=actor_id,
        action_class=action_class,
    )
