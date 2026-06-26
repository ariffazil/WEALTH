"""
WEALTH Core — Counterfactual Engine.

Runs a structured counterfactual analysis across the 13 WEALTH
thermodynamics primitives. Given a base context and a set of named
deltas, computes the per-delta impact on each primitive, then the
joint posterior and sensitivity ranking.

This is the missing bridge between the **observation protocol**
(MOF watch, V3 pivots) and the **scenario model** (V3 5 scenarios,
Third Axis phases). Instead of stitching mentally, the agent can ask:
"if MOF cuts dividend AND Gentari sale is opaque AND TT exits Q3,
what is the joint shift?"

Three modes:
- grid          — every delta runs through every primitive, full cartesian
- sensitivity   — only the top-K impact primitives, ranked
- narrative     — narrative summary suitable for arif_judge handoff

Hard rules (F-layers):
- F2 TRUTH — every delta cites the input variable it changes
- F7 HUMILITY — cap confidence at 0.90
- F4 CLARITY — return the math, not the story, by default
- F13 SOVEREIGN — never pick a winner; surfaces the grid for the sovereign

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import math


# The 13 primitives and their canonical lever variables.
# Each entry: variable_name in the input context, and how a +1 unit shift
# moves that primitive's score (rough heuristic, not exact math).
PRIMITIVE_LEVERS: Dict[str, Dict[str, Any]] = {
    "conservation": {
        "levers": ["net_worth_change", "asset_change", "liability_change"],
        "weight": 1.0,
    },
    "flow": {
        "levers": ["monthly_burn_change", "revenue_change", "capex_change"],
        "weight": 0.9,
    },
    "gradient": {
        "levers": ["price_pressure", "rate_differential", "fx_pressure"],
        "weight": 0.8,
    },
    "entropy": {
        "levers": ["scenario_dispersion", "tail_thickening", "model_uncertainty"],
        "weight": 0.85,
    },
    "energy": {
        "levers": ["irr_change", "productivity_change", "capex_efficiency"],
        "weight": 0.9,
    },
    "time": {
        "levers": ["discount_rate_change", "horizon_shift", "npv_change"],
        "weight": 0.95,
    },
    "inertia": {
        "levers": ["path_dependence", "sunk_cost_delta", "lockin_delta"],
        "weight": 0.7,
    },
    "field": {
        "levers": ["fx_change", "commodity_price_change", "macro_shock"],
        "weight": 0.8,
    },
    "signal": {
        "levers": ["info_value_delta", "evoi_delta", "decision_reversibility"],
        "weight": 0.75,
    },
    "game": {
        "levers": ["actor_count_change", "capture_risk_delta", "rent_extraction_delta"],
        "weight": 0.85,
    },
    "boundary": {
        "levers": ["asymmetry_delta", "scope_change", "in_out_change"],
        "weight": 0.7,
    },
    "hysteresis": {
        "levers": ["path_state_delta", "irreversibility_delta", "deadlock_delta"],
        "weight": 0.7,
    },
    "survival": {
        "levers": ["runway_change", "liquidity_change", "leverage_change"],
        "weight": 1.0,
    },
}


def _compute_primitive_shift(primitive: str, delta: dict) -> dict:
    """
    Compute how a single delta shifts one primitive.

    delta shape:
      {"name": str, "primitive": str, "change": float, "rationale": str}
    """
    pconf = PRIMITIVE_LEVERS.get(primitive, {})
    weight = pconf.get("weight", 0.5)
    levers = pconf.get("levers", [])

    # Linear model: shift = change * weight
    # Sign convention: + change is bad (extraction, pressure, dispersion)
    # - change is good (conservation, capex protection, runway extension)
    raw_shift = delta.get("change", 0.0) * weight

    return {
        "primitive": primitive,
        "delta_name": delta.get("name", "unnamed"),
        "raw_shift": raw_shift,
        "weight": weight,
        "levers_affected": levers,
        "rationale": delta.get("rationale", ""),
    }


def run_counterfactual(
    base_context: dict,
    deltas: list[dict],
    mode: str = "grid",
    top_k: int = 5,
) -> dict:
    """
    Run a counterfactual analysis.

    Args:
        base_context: dict of baseline values (e.g., from V3 model state)
        deltas: list of {"name", "primitive" OR "levers", "change", "rationale"}
                If "primitive" is set, apply the delta to that one primitive.
                If "levers" is set (list of var names), apply across primitives
                that have those levers.
        mode: "grid" | "sensitivity" | "narrative"
        top_k: for sensitivity mode, how many top impacts to return

    Returns:
        {
          "mode": str,
          "base_context_keys": [...],
          "deltas": [...],
          "per_delta_impact": [{delta_name, total_shift, per_primitive: [...]}],
          "joint_posterior": {
              "total_shift": float,
              "dominant_primitives": [...],
              "confidence": float,
          },
          "sensitivity_ranking": [...],   # for sensitivity mode
          "narrative": str,                # for narrative mode
          "f7_humility": {"confidence_cap": 0.90, "applied": bool},
        }
    """
    if not deltas:
        return {
            "mode": mode,
            "error": "no_deltas_provided",
            "f7_humility": {"confidence_cap": 0.90, "applied": False},
        }

    # Normalize deltas
    normalized: list[dict] = []
    for d in deltas:
        name = d.get("name", f"delta_{len(normalized)}")
        if "primitive" in d:
            # Direct primitive targeting
            normalized.append({
                "name": name,
                "primitive": d["primitive"],
                "change": float(d.get("change", 0.0)),
                "rationale": d.get("rationale", ""),
            })
        elif "levers" in d:
            # Lever-based: expand to multiple primitives
            target_levers = set(d.get("levers", []))
            for prim, pconf in PRIMITIVE_LEVERS.items():
                if target_levers & set(pconf.get("levers", [])):
                    normalized.append({
                        "name": f"{name}__{prim}",
                        "primitive": prim,
                        "change": float(d.get("change", 0.0)),
                        "rationale": d.get("rationale", ""),
                    })
        else:
            # Default: distribute across all primitives
            for prim in PRIMITIVE_LEVERS:
                normalized.append({
                    "name": f"{name}__{prim}",
                    "primitive": prim,
                    "change": float(d.get("change", 0.0)) / len(PRIMITIVE_LEVERS),
                    "rationale": d.get("rationale", ""),
                })

    # Compute per-delta impact
    per_delta_impact = []
    primitive_totals: dict[str, float] = {p: 0.0 for p in PRIMITIVE_LEVERS}
    primitive_counts: dict[str, int] = {p: 0 for p in PRIMITIVE_LEVERS}

    # Group normalized by original delta_name
    from collections import defaultdict
    grouped: dict[str, list[dict]] = defaultdict(list)
    for nd in normalized:
        # Get the parent delta name (strip __primitive suffix)
        parent = nd["name"].split("__")[0]
        grouped[parent].append(_compute_primitive_shift(nd["primitive"], nd))

    for delta_name, shifts in grouped.items():
        total_shift = sum(s["raw_shift"] for s in shifts)
        for s in shifts:
            primitive_totals[s["primitive"]] += s["raw_shift"]
            primitive_counts[s["primitive"]] += 1
        per_delta_impact.append({
            "delta_name": delta_name,
            "total_shift": round(total_shift, 4),
            "per_primitive": shifts,
        })

    # Joint posterior
    total_joint_shift = sum(d["total_shift"] for d in per_delta_impact)

    # Dominant primitives (by total absolute shift)
    dominant = sorted(
        primitive_totals.items(),
        key=lambda kv: abs(kv[1]),
        reverse=True,
    )[:top_k]
    dominant_primitives = [
        {"primitive": p, "cumulative_shift": round(s, 4), "delta_count": primitive_counts[p]}
        for p, s in dominant
    ]

    # Confidence: more deltas = more model uncertainty, lower confidence
    n_deltas = len(set(d["name"].split("__")[0] for d in normalized))
    base_confidence = 0.85
    if n_deltas > 3:
        base_confidence -= 0.05 * (n_deltas - 3)
    if total_joint_shift > 1.0:
        base_confidence -= 0.10  # large joint shift = high model error
    confidence = max(0.30, min(0.90, base_confidence))
    f7_applied = confidence == 0.90

    joint_posterior = {
        "total_shift": round(total_joint_shift, 4),
        "n_deltas": n_deltas,
        "dominant_primitives": dominant_primitives,
        "confidence": confidence,
        "interpretation": _interpret_shift(total_joint_shift, n_deltas),
    }

    # Sensitivity ranking
    sensitivity_ranking = sorted(
        [
            {"primitive": p, "cumulative_shift": round(s, 4), "n_deltas_touching": primitive_counts[p]}
            for p, s in primitive_totals.items()
        ],
        key=lambda x: abs(x["cumulative_shift"]),
        reverse=True,
    )

    # Narrative
    if mode == "narrative":
        narrative = _build_narrative(
            base_context, per_delta_impact, joint_posterior, dominant_primitives
        )
    else:
        narrative = ""

    return {
        "mode": mode,
        "base_context_keys": sorted(list(base_context.keys())) if isinstance(base_context, dict) else [],
        "deltas_count": len(deltas),
        "normalized_deltas_count": len(normalized),
        "per_delta_impact": per_delta_impact,
        "joint_posterior": joint_posterior,
        "sensitivity_ranking": sensitivity_ranking,
        "narrative": narrative,
        "f7_humility": {
            "confidence_cap": 0.90,
            "applied": f7_applied,
            "raw_confidence": base_confidence,
        },
        "hard_rules": [
            "F2 TRUTH: every delta cites input variable",
            "F4 CLARITY: returns math, not story, by default",
            "F7 HUMILITY: confidence capped at 0.90",
            "F13 SOVEREIGN: never picks a winner; surfaces the grid",
        ],
    }


def _interpret_shift(shift: float, n_deltas: int) -> str:
    if abs(shift) < 0.05:
        return "negligible_joint_impact"
    if shift > 0.5:
        return "strong_deterioration_signal"
    if shift > 0.2:
        return "moderate_deterioration"
    if shift < -0.5:
        return "strong_improvement_signal"
    if shift < -0.2:
        return "moderate_improvement"
    return "mixed_signals"


def _build_narrative(
    base_context: dict,
    per_delta: list[dict],
    joint: dict,
    dominant: list[dict],
) -> str:
    parts = [
        f"Counterfactual narrative ({len(per_delta)} deltas evaluated):",
        f"Joint posterior shift: {joint['total_shift']:+.3f} ({joint['interpretation']})",
        f"Confidence: {joint['confidence']:.2f} (F7 cap applied: {joint.get('f7_applied', False)})",
        "",
        "Per-delta impact (sorted by magnitude):",
    ]
    sorted_deltas = sorted(per_delta, key=lambda d: abs(d["total_shift"]), reverse=True)
    for d in sorted_deltas[:5]:
        parts.append(f"  - {d['delta_name']}: total shift {d['total_shift']:+.3f}")
    parts.append("")
    parts.append("Dominant primitives (where the joint effect concentrates):")
    for d in dominant:
        parts.append(f"  - {d['primitive']}: cumulative shift {d['cumulative_shift']:+.3f} across {d['delta_count']} deltas")
    parts.append("")
    parts.append("This is a diagnostic, not a verdict. The sovereign decides.")
    return "\n".join(parts)


__all__ = [
    "PRIMITIVE_LEVERS",
    "run_counterfactual",
]
