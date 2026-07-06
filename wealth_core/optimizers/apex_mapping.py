"""
APEX Governance Layer for WEALTH Optimizers.

Maps each optimizer to its APEX conservation law, computes verdicts,
detects C_dark (shadow optimization), and enforces F1-F13 floors.

G = A · P · E · X · Φ
C_dark = A · (1-P) · (1-X)

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── APEX Organ → Conservation Law Mapping ─────────────────────────────────


class APEXOrgan(Enum):
    """Seven APEX organs, each with a conservation law."""

    REALITY = "reality"  # ΔR — Energy conservation
    GOVERNANCE = "governance"  # ΔG — Entropy reduction
    CIVILIZATION = "civilization"  # I_sys — Statistical coordination
    EXECUTION = "execution"  # W — Work
    MEMORY = "memory"  # ∂M/∂t — Landauer cost
    WITNESS = "witness"  # Ω — Gödel incompleteness
    MEANING = "meaning"  # ∇F — Free energy gradient


class APEXVerdict(Enum):
    """APEX verdicts for optimization results."""

    SEAL = "SEAL"  # Action is lawful, proceed
    SABAR = "SABAR"  # Not unlawful, not yet authorized
    HOLD = "HOLD"  # Requires human or sovereign clarification
    VOID = "VOID"  # Constitutionally prohibited


# ── Optimizer → Organ → Conservation Law ──────────────────────────────────

OPTIMIZER_APEX_MAP: Dict[str, Dict[str, str]] = {
    "markowitz_frontier": {
        "organ": APEXOrgan.REALITY.value,
        "conservation_law": "energy_conservation",
        "description": "Mean-variance frontier — energy (return) vs entropy (risk)",
        "formula": "max μᵀx s.t. xᵀΣx ≤ γ",
    },
    "kelly_sizing": {
        "organ": APEXOrgan.EXECUTION.value,
        "conservation_law": "work",
        "description": "Optimal bet sizing — maximum expected log-growth",
        "formula": "max E[log(1+f·R)]",
    },
    "robust_portfolio": {
        "organ": APEXOrgan.GOVERNANCE.value,
        "conservation_law": "entropy_reduction",
        "description": "Worst-case optimization under uncertainty set",
        "formula": "max min_{z∈Z} cᵀx",
    },
    "chance_constrained": {
        "organ": APEXOrgan.WITNESS.value,
        "conservation_law": "godel_incompleteness",
        "description": "Probabilistic constraint satisfaction — VaR/CVaR",
        "formula": "P(rᵀx ≤ α) ≤ β",
    },
    "two_stage_recourse": {
        "organ": APEXOrgan.MEMORY.value,
        "conservation_law": "landauer_cost",
        "description": "Two-stage stochastic program with recourse",
        "formula": "max cᵀx + E[Q(x,ξ)]",
    },
    "multi_objective_pareto": {
        "organ": APEXOrgan.CIVILIZATION.value,
        "conservation_law": "statistical_coordination",
        "description": "Multi-objective Pareto frontier",
        "formula": "max [f₁(x), f₂(x), ...] Pareto-dominance",
    },
}


# ── APEX Verdict Computation ──────────────────────────────────────────────


@dataclass
class APEXScore:
    """G = A · P · E · X · Φ and C_dark = A · (1-P) · (1-X)."""

    A: float = 0.0  # Adaptation — input quality
    P: float = 0.0  # Precision — measurement rigor
    E: float = 0.0  # Evidence — observable quantity
    X: float = 0.0  # Execution — solver convergence
    Phi: float = 0.0  # Faithfulness — constraint satisfaction

    @property
    def G(self) -> float:
        """Nash bargaining product. G ≥ 0.80 for SEAL."""
        return self.A * self.P * self.E * self.X * self.Phi

    @property
    def C_dark(self) -> float:
        """Shadow optimization score. C_dark < 0.30 required."""
        return self.A * (1 - self.P) * (1 - self.X)

    def to_dict(self) -> Dict[str, float]:
        return {
            "A": round(self.A, 4),
            "P": round(self.P, 4),
            "E": round(self.E, 4),
            "X": round(self.X, 4),
            "Phi": round(self.Phi, 4),
            "G": round(self.G, 4),
            "C_dark": round(self.C_dark, 4),
        }


@dataclass
class FloorCheck:
    """F1-F13 floor compliance result."""

    floor: str
    name: str
    status: str  # PASS, WARN, FAIL
    detail: str = ""


@dataclass
class APEXResult:
    """Complete APEX governance result for an optimization."""

    optimizer: str
    organ: str
    conservation_law: str
    verdict: APEXVerdict
    apex_score: APEXScore
    floor_checks: List[FloorCheck] = field(default_factory=list)
    confidence: float = 0.0  # Capped at 0.90 (F7 HUMILITY)
    epistemic_label: str = "DER"  # DER = derived from historical data
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "optimizer": self.optimizer,
            "organ": self.organ,
            "conservation_law": self.conservation_law,
            "verdict": self.verdict.value,
            "apex_score": self.apex_score.to_dict(),
            "floor_checks": [
                {
                    "floor": fc.floor,
                    "name": fc.name,
                    "status": fc.status,
                    "detail": fc.detail,
                }
                for fc in self.floor_checks
            ],
            "confidence": round(self.confidence, 4),
            "epistemic_label": self.epistemic_label,
            "warnings": self.warnings,
        }


def compute_apex_verdict(
    optimizer: str,
    solver_status: str,
    solver_termination: str,
    constraint_violation: float = 0.0,
    input_quality: float = 0.8,
    evidence_quality: float = 0.7,
    has_uncertainty_bands: bool = False,
    weights_sum: Optional[float] = None,
) -> APEXResult:
    """Compute APEX verdict for an optimization result.

    Args:
        optimizer: optimizer name (key in OPTIMIZER_APEX_MAP)
        solver_status: solver status string ('ok', 'warning', 'error')
        solver_termination: termination condition ('optimal', etc.)
        constraint_violation: max constraint violation (0 = perfect)
        input_quality: quality of input data [0,1]
        evidence_quality: quality of evidence [0,1]
        has_uncertainty_bands: whether output includes uncertainty ranges
        weights_sum: sum of portfolio weights (should be ~1.0)

    Returns:
        APEXResult with verdict, score, and floor checks
    """
    mapping = OPTIMIZER_APEX_MAP.get(optimizer, {})
    organ = mapping.get("organ", "unknown")
    law = mapping.get("conservation_law", "unknown")

    # ── Compute APEX components ──────────────────────────────────────────
    # A = Adaptation — input quality (clamped [0,1])
    A = max(0.0, min(1.0, input_quality))

    # P = Precision — solver convergence + constraint satisfaction
    if solver_status == "ok" and solver_termination == "optimal":
        P = max(0.0, 1.0 - constraint_violation * 10)  # penalize violations
    elif solver_status == "ok":
        P = 0.6  # feasible but not optimal
    else:
        P = 0.2  # solver failed

    # E = Evidence — observable quantity
    E = max(0.0, min(1.0, evidence_quality))
    if has_uncertainty_bands:
        E = min(1.0, E + 0.1)  # bonus for epistemic honesty

    # X = Execution — solver actually converged
    X = 1.0 if (solver_status == "ok" and solver_termination == "optimal") else 0.3

    # Φ = Faithfulness — constraint satisfaction
    Phi = max(0.0, 1.0 - constraint_violation * 5)
    if weights_sum is not None:
        budget_violation = abs(weights_sum - 1.0)
        Phi = Phi * max(0.0, 1.0 - budget_violation * 10)

    score = APEXScore(A=A, P=P, E=E, X=X, Phi=Phi)

    # ── Floor checks ─────────────────────────────────────────────────────
    floors = _check_floors(
        score, constraint_violation, has_uncertainty_bands, weights_sum
    )

    # ── Verdict ──────────────────────────────────────────────────────────
    verdict = _determine_verdict(score, floors)

    # ── Confidence (F7 HUMILITY: cap at 0.90) ────────────────────────────
    confidence = min(0.90, score.G)

    # ── Warnings ─────────────────────────────────────────────────────────
    warnings = []
    if score.C_dark >= 0.30:
        warnings.append(f"C_dark={score.C_dark:.3f} >= 0.30 — shadow optimization risk")
    if not has_uncertainty_bands:
        warnings.append("No uncertainty bands — F9 ANTI-HANTU: output lacks ranges")
    if any(fc.status == "FAIL" for fc in floors):
        warnings.append("Floor violation detected")

    return APEXResult(
        optimizer=optimizer,
        organ=organ,
        conservation_law=law,
        verdict=verdict,
        apex_score=score,
        floor_checks=floors,
        confidence=confidence,
        epistemic_label="DER",
        warnings=warnings,
    )


def _check_floors(
    score: APEXScore,
    constraint_violation: float,
    has_uncertainty_bands: bool,
    weights_sum: Optional[float],
) -> List[FloorCheck]:
    """Check F1-F13 floor compliance."""
    checks = []

    # F1 AMANAH — reversibility (optimization is always reversible)
    checks.append(FloorCheck("F1", "AMANAH", "PASS", "Optimization is reversible"))

    # F2 TRUTH — no false precision
    if score.P >= 0.8:
        checks.append(
            FloorCheck("F2", "TRUTH", "PASS", "Solver converged with high precision")
        )
    elif score.P >= 0.5:
        checks.append(FloorCheck("F2", "TRUTH", "WARN", "Solver convergence moderate"))
    else:
        checks.append(FloorCheck("F2", "TRUTH", "FAIL", "Solver did not converge"))

    # F4 CLARITY — entropy reduction
    if score.G >= 0.5:
        checks.append(FloorCheck("F4", "CLARITY", "PASS", "Result reduces uncertainty"))
    else:
        checks.append(
            FloorCheck("F4", "CLARITY", "WARN", "Low G score — limited clarity")
        )

    # F7 HUMILITY — confidence cap
    checks.append(FloorCheck("F7", "HUMILITY", "PASS", "Confidence capped at 0.90"))

    # F9 ANTI-HANTU — no false precision
    if has_uncertainty_bands:
        checks.append(
            FloorCheck("F9", "ANTI-HANTU", "PASS", "Uncertainty bands present")
        )
    else:
        checks.append(
            FloorCheck(
                "F9", "ANTI-HANTU", "WARN", "No uncertainty bands — point estimate only"
            )
        )

    # F11 AUDIT — traceability
    checks.append(FloorCheck("F11", "AUDIT", "PASS", "APEX score and verdict logged"))

    # Budget constraint check (portfolio-specific)
    if weights_sum is not None:
        if abs(weights_sum - 1.0) < 1e-6:
            checks.append(
                FloorCheck("F_budget", "CONSERVATION", "PASS", "Weights sum to 1.0")
            )
        else:
            checks.append(
                FloorCheck(
                    "F_budget",
                    "CONSERVATION",
                    "FAIL",
                    f"Weights sum={weights_sum:.6f} ≠ 1.0",
                )
            )

    return checks


def _determine_verdict(score: APEXScore, floors: List[FloorCheck]) -> APEXVerdict:
    """Determine APEX verdict from score and floor checks."""
    # VOID if any floor FAIL
    if any(fc.status == "FAIL" for fc in floors):
        return APEXVerdict.VOID

    # HOLD if C_dark too high
    if score.C_dark >= 0.30:
        return APEXVerdict.HOLD

    # SEAL if G ≥ 0.80
    if score.G >= 0.80:
        return APEXVerdict.SEAL

    # SABAR if G ≥ 0.50
    if score.G >= 0.50:
        return APEXVerdict.SABAR

    # HOLD otherwise
    return APEXVerdict.HOLD


def get_optimizer_mapping(optimizer: str) -> Dict[str, str]:
    """Get APEX mapping for an optimizer."""
    return OPTIMIZER_APEX_MAP.get(
        optimizer,
        {
            "organ": "unknown",
            "conservation_law": "unknown",
            "description": f"Unknown optimizer: {optimizer}",
        },
    )
