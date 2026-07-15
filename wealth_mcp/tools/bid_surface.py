"""
Bid Surface — competitive bid scoring and surface topology.
Scoring Primacy (Eureka 4): EMV without bid scoring surface = answering the wrong question.

DITEMPA BUKAN DIBERI — Forged, not given.
"""

from __future__ import annotations

import math
from typing import Any


def compute_bid_surface(
    bids: list[dict[str, Any]],
    reserve_price: float = 0.0,
    mode: str = "first_price",
    scoring_weights: dict[str, float] | None = None,
    bidder_caps: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Score a competitive bid surface for resource allocation.

    Computes bid ranking, bidder surplus, competitive intensity,
    and surface topology. Implements standard auction formats.

    Parameters
    ----------
    bids : list[dict]
        List of bids. Each dict requires:
        - bidder (str): bidder identifier
        - amount (float): monetary bid
        - share_pct (float): requested share (0-100)
        - quality_score (float): non-price quality metric (0-1)
    reserve_price : float
        Minimum acceptable price (default 0.0).
    mode : str
        Auction format: first_price | second_price | scoring | all_pay.
    scoring_weights : dict | None
        Weight dict for scoring mode, e.g. {"price": 0.6, "quality": 0.4}.
        Ignored in non-scoring modes.
    bidder_caps : dict | None
        Per-bidder amount cap, e.g. {"bidder_A": 100.0}.

    Returns
    -------
    dict with ranked_bids, winner, winning_price, total_surplus,
    competitive_intensity (HHI), and surface_metrics.
    """
    _validate_bids(bids)
    weights = scoring_weights or {"price": 0.5, "quality": 0.5}
    caps = bidder_caps or {}

    # ── Phase 1: Apply caps + filter reserves ──────────────────────────
    capped = []
    for b in bids:
        entry = dict(b)
        bidder = entry["bidder"]
        if bidder in caps:
            entry["amount"] = min(entry["amount"], caps[bidder])
        capped.append(entry)

    eligible = [b for b in capped if b["amount"] >= reserve_price]

    if not eligible:
        return _empty_result(mode)

    # ── Phase 2: Score & rank ──────────────────────────────────────────
    scored = _score_bids(eligible, mode, weights)
    ranked = sorted(scored, key=lambda x: x["_score"], reverse=True)

    # ── Phase 3: Winner & price ────────────────────────────────────────
    winner = ranked[0]
    winner_bidder = winner["bidder"]
    winning_price = _resolve_price(ranked, mode, reserve_price)

    # ── Phase 4: Surplus ───────────────────────────────────────────────
    surplus = _compute_surplus(ranked, winning_price, reserve_price, mode)

    # ── Phase 5: Competitive intensity (HHI) ───────────────────────────
    total_amount = sum(b["amount"] for b in ranked)
    hhi = (
        sum((b["amount"] / total_amount) ** 2 for b in ranked)
        if total_amount > 0
        else 0.0
    )

    # ── Phase 6: Surface topology ──────────────────────────────────────
    amounts = [b["amount"] for b in ranked]
    n = len(amounts)
    mean_bid = sum(amounts) / n if n else 0.0
    variance = sum((x - mean_bid) ** 2 for x in amounts) / n if n else 0.0

    ranked_out = []
    for i, b in enumerate(ranked):
        ranked_out.append(
            {
                "rank": i + 1,
                "bidder": b["bidder"],
                "amount": round(b["amount"], 4),
                "quality_score": round(b.get("quality_score", 0.0), 4),
                "share_pct": round(b.get("share_pct", 0.0), 4),
                "composite_score": round(b["_score"], 4),
            }
        )

    surface = {
        "bid_count": len(bids),
        "eligible_count": len(eligible),
        "reserve_met": True,
        "spread": round(max(amounts) - min(amounts), 4) if amounts else 0.0,
        "avg_bid": round(mean_bid, 4),
        "median_bid": round(sorted(amounts)[n // 2], 4) if amounts else 0.0,
        "std_bid": round(math.sqrt(variance), 4),
        "mode": mode,
        "winner_surplus": round(surplus["winner_surplus"], 4),
        "all_pay_total": round(
            sum(b["amount"] for b in ranked) if mode == "all_pay" else 0.0, 4
        ),
        "reserve_price": reserve_price,
    }

    return {
        "ranked_bids": ranked_out,
        "winner": winner_bidder,
        "winning_price": round(winning_price, 4),
        "total_surplus": round(surplus["total"], 4),
        "competitive_intensity": round(hhi, 4),
        "hhi_category": (
            "highly_concentrated"
            if hhi > 0.25
            else "moderately_concentrated"
            if hhi > 0.15
            else "unconcentrated"
        ),
        "surface_metrics": surface,
    }


def _validate_bids(bids: list[dict]) -> None:
    required = {"bidder", "amount", "share_pct", "quality_score"}
    for i, b in enumerate(bids):
        missing = required - set(b.keys())
        if missing:
            raise ValueError(f"Bid at index {i} missing required keys: {missing}")


def _empty_result(mode: str) -> dict[str, Any]:
    return {
        "ranked_bids": [],
        "winner": None,
        "winning_price": 0.0,
        "total_surplus": 0.0,
        "competitive_intensity": 0.0,
        "hhi_category": "unconcentrated",
        "surface_metrics": {
            "bid_count": 0,
            "eligible_count": 0,
            "reserve_met": False,
            "spread": 0.0,
            "avg_bid": 0.0,
            "median_bid": 0.0,
            "std_bid": 0.0,
            "mode": mode,
            "winner_surplus": 0.0,
            "all_pay_total": 0.0,
            "reserve_price": 0.0,
        },
    }


def _score_bids(
    bids: list[dict],
    mode: str,
    weights: dict[str, float],
) -> list[dict]:
    max_amount = max(b["amount"] for b in bids) if bids else 1.0
    for b in bids:
        if mode == "scoring":
            norm_price = b["amount"] / max_amount if max_amount > 0 else 0.0
            w_p = weights.get("price", 0.5)
            w_q = weights.get("quality", 0.5)
            b["_score"] = (w_p * norm_price) + (w_q * b.get("quality_score", 0.5))
        else:
            b["_score"] = b["amount"]
    return bids


def _resolve_price(
    ranked: list[dict],
    mode: str,
    reserve_price: float,
) -> float:
    if mode == "first_price" or mode == "scoring":
        return ranked[0]["amount"]
    elif mode == "second_price":
        return ranked[1]["amount"] if len(ranked) > 1 else reserve_price
    elif mode == "all_pay":
        return ranked[0]["amount"]
    return ranked[0]["amount"]


def _compute_surplus(
    ranked: list[dict],
    winning_price: float,
    reserve_price: float,
    mode: str,
) -> dict[str, float]:
    if mode == "all_pay":
        total = sum(b["amount"] for b in ranked)
        return {"winner_surplus": ranked[0]["amount"] - winning_price, "total": total}
    first_price_surplus = ranked[0]["amount"] - winning_price
    total = sum(b["amount"] for b in ranked) - (len(ranked) * reserve_price)
    return {"winner_surplus": first_price_surplus, "total": total}
