"""
Minimum Winning Coalition (MWC) optimizer — cooperative game theory
for resource allocation. Finds smallest coalition that secures
majority control while minimizing total cost.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import copy
import itertools
import math
from typing import Any


def compute_mwc(
    players: list[dict[str, Any]],
    majority_threshold: float = 0.5,
    mode: str = "cost_minimizing",
    max_coalition_size: int = 10,
    constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Compute optimal Minimum Winning Coalition (MWC).

    Uses cooperative game theory: finds the smallest coalition that
    secures majority control while minimizing total cost. Based on
    Shapley value and coalition formation theory.

    Parameters
    ----------
    players : list[dict]
        List of players. Each dict requires:
        - id (str): unique identifier
        - voting_share (float): voting power (0-1)
        - cost (float): cost of including this player
        - alignment_score (float): strategic alignment (0-1)
    majority_threshold : float
        Absolute voting power needed to win (default 0.5).
    mode : str
        Optimization mode: cost_minimizing | stability_maximizing | balanced.
    max_coalition_size : int
        Maximum coalition size to consider (default 10).
    constraints : dict | None
        {"exclude": ["player_X"], "require": ["player_Y"]}.

    Returns
    -------
    dict with coalition, coalition_voting_power, total_cost, stability_index,
    power_distribution (Shapley-like), alternative_coalitions.
    """
    _validate_players(players)
    cons = constraints or {}
    excluded = set(cons.get("exclude", []))
    required = set(cons.get("require", []))

    # Filter out excluded players
    pool = [p for p in players if p["id"] not in excluded]

    # Separate required players
    req_players = [p for p in pool if p["id"] in required]
    opt_players = [p for p in pool if p["id"] not in required]

    total_power = sum(p["voting_share"] for p in pool)
    req_power = sum(p["voting_share"] for p in req_players)
    req_cost = sum(p["cost"] for p in req_players)

    if total_power == 0:
        return _empty_mwc_result(players, "total voting power is zero")

    needed = majority_threshold
    if req_power >= needed:
        required_case = _finalize_coalition(
            req_players, needed, total_power, mode, opt_players, max_coalition_size
        )
        return _build_mwc_response(required_case, pool, total_power)

    remaining_needed = max(0.0, needed - req_power)

    search = _find_best_coalition(
        pool=pool,
        req_players=req_players,
        opt_players=opt_players,
        needed=needed,
        total_power=total_power,
        mode=mode,
        max_coalition_size=max_coalition_size,
    )

    if not search["feasible"]:
        return _build_mwc_response(
            {
                "coalition": list(req_players),
                "power": req_power,
                "cost": req_cost,
                "feasible": False,
                "needed": needed,
                "total_power": total_power,
            },
            pool,
            total_power,
        )

    return _build_mwc_response(search, pool, total_power)


def _validate_players(players: list[dict]) -> None:
    required = {"id", "voting_share", "cost", "alignment_score"}
    for i, p in enumerate(players):
        missing = required - set(p.keys())
        if missing:
            raise ValueError(f"Player at index {i} missing required keys: {missing}")
        if not (0 <= p["voting_share"] <= 1):
            raise ValueError(
                f"Player '{p.get('id', i)}' voting_share must be in [0, 1]"
            )


def _empty_mwc_result(players: list[dict], reason: str) -> dict[str, Any]:
    return {
        "coalition": [],
        "coalition_voting_power": 0.0,
        "total_cost": 0.0,
        "stability_index": 0.0,
        "power_distribution": {p["id"]: 0.0 for p in players},
        "alternative_coalitions": [],
        "feasible": False,
        "reason": reason,
    }


def _find_best_coalition(
    pool: list[dict],
    req_players: list[dict],
    opt_players: list[dict],
    needed: float,
    total_power: float,
    mode: str,
    max_coalition_size: int,
) -> dict[str, Any]:
    """Exact search over feasible coalitions within size bound."""
    req_ids = {p["id"] for p in req_players}
    max_optional = max(0, min(len(opt_players), max_coalition_size - len(req_players)))
    feasible_candidates: list[dict[str, Any]] = []

    for size in range(max_optional + 1):
        for combo in itertools.combinations(opt_players, size):
            coalition = list(req_players) + list(combo)
            power = coalition_power(coalition)
            if power < needed:
                continue
            cost = sum(p["cost"] for p in coalition)
            stability = _compute_stability(coalition, pool)
            feasible_candidates.append(
                {
                    "coalition": coalition,
                    "power": power,
                    "cost": cost,
                    "stability": stability,
                    "needed": needed,
                    "total_power": total_power,
                }
            )

    if not feasible_candidates:
        return {
            "coalition": list(req_players),
            "power": coalition_power(req_players),
            "cost": sum(p["cost"] for p in req_players),
            "feasible": False,
            "alternatives": [],
            "needed": needed,
            "total_power": total_power,
        }

    best = min(feasible_candidates, key=lambda c: _coalition_rank(c, mode))
    best_ids = [p["id"] for p in best["coalition"]]

    alternatives = []
    for candidate in sorted(feasible_candidates, key=lambda c: _coalition_rank(c, mode)):
        candidate_ids = [p["id"] for p in candidate["coalition"]]
        if candidate_ids == best_ids:
            continue
        alternatives.append(
            {
                "coalition": candidate_ids,
                "voting_power": round(candidate["power"], 4),
                "total_cost": round(candidate["cost"], 4),
                "savings": round(max(0.0, best["cost"] - candidate["cost"]), 4),
            }
        )
        if len(alternatives) >= 5:
            break

    best["feasible"] = True
    best["alternatives"] = alternatives
    return best


def _coalition_rank(candidate: dict[str, Any], mode: str) -> tuple[Any, ...]:
    """Lower tuple is better."""
    excess_power = candidate["power"] - candidate["needed"]
    coalition_size = len(candidate["coalition"])
    if mode == "stability_maximizing":
        return (-candidate["stability"], candidate["cost"], coalition_size, excess_power)
    if mode == "balanced":
        return (candidate["cost"] - candidate["stability"], coalition_size, excess_power)
    return (candidate["cost"], coalition_size, excess_power, -candidate["stability"])


def _finalize_coalition(
    req_players: list[dict],
    needed: float,
    total_power: float,
    mode: str,
    opt_players: list[dict],
    max_size: int,
) -> dict[str, Any]:
    power = sum(p["voting_share"] for p in req_players)
    cost = sum(p["cost"] for p in req_players)
    alt = _find_alternatives(opt_players, req_players, needed, cost, mode, max_size)
    return {
        "coalition": req_players,
        "power": power,
        "cost": cost,
        "feasible": True,
        "alternatives": alt,
        "needed": needed,
        "total_power": total_power,
    }


def _find_alternatives(
    opt_players: list[dict],
    base_players: list[dict],
    needed: float,
    base_cost: float,
    mode: str,
    max_size: int,
) -> list[dict[str, Any]]:
    """Find alternative coalitions by swapping one or more players."""
    alternatives = []
    base_ids = {p["id"] for p in base_players}
    base_power = sum(p["voting_share"] for p in base_players)

    # Try replacing each optional player with another
    for i, current in enumerate(opt_players):
        if len(base_players) >= max_size:
            break
        # Try adding this player to see if we can drop a more expensive one
        test_coal = list(base_players) + [current]
        test_power = base_power + current["voting_share"]
        test_cost = base_cost + current["cost"]

        # Can we drop someone?
        droppable = [
            j
            for j in range(len(base_players))
            if base_players[j]["id"] not in base_ids or True
        ]
        for drop_idx in range(len(base_players)):
            dropped = base_players[drop_idx]
            reduced_power = test_power - dropped["voting_share"]
            reduced_cost = test_cost - dropped["cost"]
            if reduced_power >= needed and reduced_cost < base_cost:
                alt_ids = [p["id"] for p in test_coal if p["id"] != dropped["id"]]
                alt_entry = {
                    "coalition": alt_ids,
                    "voting_power": round(reduced_power, 4),
                    "total_cost": round(reduced_cost, 4),
                    "savings": round(base_cost - reduced_cost, 4),
                }
                if alt_entry not in alternatives:
                    alternatives.append(alt_entry)

        if test_power >= needed and test_cost < base_cost:
            alt_ids = [p["id"] for p in test_coal]
            alt_entry = {
                "coalition": alt_ids,
                "voting_power": round(test_power, 4),
                "total_cost": round(test_cost, 4),
                "savings": round(base_cost - test_cost, 4),
            }
            if alt_entry not in alternatives:
                alternatives.append(alt_entry)

    alternatives.sort(key=lambda a: a["total_cost"])
    return alternatives[:5]


def _build_mwc_response(
    result: dict[str, Any],
    pool: list[dict],
    total_power: float,
) -> dict[str, Any]:
    coalition = result["coalition"]
    current_power = result["power"]
    current_cost = result["cost"]
    feasible = result.get("feasible", True)
    alternatives_raw = result.get("alternatives", [])

    # ── Stability index ────────────────────────────────────────────────
    stability = _compute_stability(coalition, pool)

    # ── Shapley-like power distribution ────────────────────────────────
    power_dist = _shapley_power(pool, coalition, result["needed"])

    # ── Alternative coalitions ─────────────────────────────────────────
    alternatives = []
    for a in alternatives_raw:
        alternatives.append(
            {
                "coalition": a["coalition"],
                "voting_power": a["voting_power"],
                "total_cost": a["total_cost"],
                "savings": a.get("savings", 0.0),
            }
        )

    return {
        "coalition": [p["id"] for p in coalition],
        "coalition_voting_power": round(current_power, 4),
        "total_cost": round(current_cost, 4),
        "stability_index": round(stability, 4),
        "power_distribution": {k: round(v, 4) for k, v in power_dist.items()},
        "alternative_coalitions": alternatives,
        "feasible": feasible,
        "majority_needed": round(result["needed"], 4),
        "total_voting_power": round(total_power, 4),
    }


def _compute_stability(coalition: list[dict], pool: list[dict]) -> float:
    if not coalition:
        return 0.0

    avg_alignment = sum(p["alignment_score"] for p in coalition) / len(coalition)
    coalition_ids = {p["id"] for p in coalition}

    # Cost burden: how evenly is cost distributed?
    costs = [p["cost"] for p in coalition]
    if costs:
        mean_c = sum(costs) / len(costs)
        cv = (
            math.sqrt(sum((c - mean_c) ** 2 for c in costs) / len(costs)) / mean_c
            if mean_c > 0
            else 1.0
        )
        cost_fairness = max(0.0, 1.0 - cv)
    else:
        cost_fairness = 0.0

    # External opposition: voting power outside coalition
    external_power = sum(
        p["voting_share"] for p in pool if p["id"] not in coalition_ids
    )
    margin = coalition_power(coalition) - external_power
    margin_factor = min(1.0, max(0.0, (margin + 0.5) / 1.0))

    stability = 0.4 * avg_alignment + 0.3 * cost_fairness + 0.3 * margin_factor
    return stability


def coalition_power(coalition: list[dict]) -> float:
    return sum(p["voting_share"] for p in coalition)


def _shapley_power(
    pool: list[dict], coalition: list[dict], majority_needed: float
) -> dict[str, float]:
    """
    Compute approximate Shapley-like marginal contribution values.
    For N <= 8, exact enumeration. For larger, Monte Carlo approximation.
    """
    coalition_ids = {p["id"] for p in coalition}
    relevant = [p for p in pool if p["id"] in coalition_ids]
    n = len(relevant)
    values = {p["id"]: 0.0 for p in pool}

    if n == 0:
        return values

    if n <= 8:
        # Exact Shapley via permutation enumeration
        for perm in itertools.permutations(range(n)):
            running = 0.0
            for idx in perm:
                prev = running
                running += relevant[idx]["voting_share"]
                if prev < majority_needed <= running:
                    values[relevant[idx]["id"]] += 1.0
        total_permutations = math.factorial(n)
        for k in values:
            values[k] /= total_permutations
    else:
        # Monte Carlo approximation for large n
        import random

        n_samples = min(5000, 10 * n)
        rng = random.Random(42)
        for _ in range(n_samples):
            perm_indices = list(range(n))
            rng.shuffle(perm_indices)
            running = 0.0
            for idx in perm_indices:
                prev = running
                running += relevant[idx]["voting_share"]
                if prev < majority_needed <= running:
                    values[relevant[idx]["id"]] += 1.0
        for k in values:
            values[k] /= n_samples

    return values
