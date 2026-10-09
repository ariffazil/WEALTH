"""Agent 888 — JUDGE.

The admission verdict for the wave-forge challenger.

Verdicts
========

* **USE** — M4-WAVE passes the full admission rule (beats M0 AND
  M4-TREND AND M2). The path is ready for human review; promotion
  out of SHADOW_CHALLENGER still requires F13 authorisation.
* **HOLD** — the pipeline ran but the admission rule failed (e.g.
  M4-WAVE beats M0 but not M4-TREND). Stay SHADOW_CHALLENGER; collect
  more evidence.
* **QUARANTINE** — an upstream gate failed (no validated modes,
  endpoint stability below floor, audit couldn't run). The challenger
  is unsafe to look at right now; investigate before the next run.

The judge cannot self-authorise USE out of SHADOW_CHALLENGER — that
is an F13 boundary. The judge can only *recommend* USE; a separate
human/F13 step must ratify.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from . import _555_auditor as _auditor
from . import _000_causality as _causality
from . import _111_decomposer as _decomposer
from . import _333_path_forge as _path_forge
from . import _444_stability as _stability
from . import _222_wave_state as _wave_state


VALID_VERDICTS = frozenset({"USE", "HOLD", "QUARANTINE"})


@dataclass(frozen=True)
class JudgeVerdict:
    """The 888-JUDGE output."""

    verdict: str = "HOLD"
    reason_codes: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    admission_passed: bool = False
    observed_at: str = ""

    def __post_init__(self) -> None:
        if self.verdict not in VALID_VERDICTS:
            self.verdict = "HOLD"

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": "888-JUDGE",
            "verdict": self.verdict,
            "reason_codes": list(self.reason_codes),
            "admission_passed": bool(self.admission_passed),
            "evidence": dict(self.evidence),
            "observed_at": self.observed_at,
        }


def AGENT_888_Judge(
    *,
    cert: _causality.CausalityCertificate,
    decomp: _decomposer.DecompositionRecord,
    wave_state: _wave_state.WaveStatePosterior,
    path: _path_forge.ForgePath,
    stability: _stability.StabilityReport,
    audit: _auditor.AuditReport,
) -> JudgeVerdict:
    """Compute the admission verdict.

    Precedence (highest first):

    1. QUARANTINE — any upstream gate failed (causality / decomposition /
       wave-state / path / audit).
    2. HOLD — pipeline ran cleanly but admission rule failed (any of
       ``M4-WAVE beats M0`` / ``beats M4-TREND`` / ``beats M2`` is
       false).
    3. USE — every admission rule passed.

    The admission rule is the task contract. The judge is the lane that
    enforces it mechanically — there is no prose exception path.
    """
    observed_at = datetime.now(timezone.utc).isoformat()
    codes: list[str] = []
    evidence: dict[str, Any] = {}

    # ── QUARANTINE gate ────────────────────────────────────────────────
    quarantine_reasons: list[str] = []
    if not cert.ok:
        quarantine_reasons.append(f"causality_failed:{','.join(cert.failures)}")
    if not decomp.ok:
        quarantine_reasons.append(f"decomposition_failed:{','.join(decomp.failures)}")
    if not wave_state.ok:
        quarantine_reasons.append(f"wave_state_failed:{','.join(wave_state.failures)}")
    if not path.ok:
        quarantine_reasons.append(f"path_forge_failed:{','.join(path.failures)}")
    if not stability.ok:
        quarantine_reasons.append(
            f"stability_below_floor:{stability.endpoint_stability:.3f}"
        )
    if not audit.ok:
        quarantine_reasons.append(f"audit_failed:{','.join(audit.failures)}")
    if quarantine_reasons:
        codes.append("QUARANTINE")
        codes.extend(quarantine_reasons)
        return JudgeVerdict(
            verdict="QUARANTINE",
            reason_codes=codes,
            evidence={"quarantine_reasons": quarantine_reasons},
            admission_passed=False,
            observed_at=observed_at,
        )

    # ── HOLD vs USE — admission rule ───────────────────────────────────
    evidence["skill_vs_M0"] = audit.skill_vs_M0
    evidence["skill_vs_M2"] = audit.skill_vs_M2
    evidence["skill_vs_M4_TREND"] = audit.skill_vs_M4_TREND
    evidence["endpoint_stability"] = stability.endpoint_stability

    passes = audit.promotion_recommended

    if not passes:
        codes.append("ADMISSION_RULE_FAILED")
        codes.extend(audit.reason.split(";"))
        return JudgeVerdict(
            verdict="HOLD",
            reason_codes=codes,
            evidence=evidence,
            admission_passed=False,
            observed_at=observed_at,
        )

    codes.append("ADMISSION_PASSED")
    codes.append("M4_WAVE_BEATS_M0")
    codes.append("M4_WAVE_BEATS_M2")
    codes.append("M4_WAVE_BEATS_M4_TREND")
    codes.append("PROMOTION_REQUIRES_F13_AUTHORIZATION")
    return JudgeVerdict(
        verdict="USE",
        reason_codes=codes,
        evidence=evidence,
        admission_passed=True,
        observed_at=observed_at,
    )


__all__ = [
    "AGENT_888_Judge",
    "JudgeVerdict",
    "VALID_VERDICTS",
]