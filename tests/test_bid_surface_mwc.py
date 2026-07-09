import pytest
from wealth_mcp.tools.bid_surface import compute_bid_surface
from wealth_mcp.tools.optimize_mwc import compute_mwc

def test_compute_bid_surface_first_price():
    bids = [
        {"bidder": "propa", "amount": 150.0, "share_pct": 30.0, "quality_score": 0.90},
        {"bidder": "dialog", "amount": 200.0, "share_pct": 50.0, "quality_score": 0.85},
    ]
    res = compute_bid_surface(bids, reserve_price=100.0, mode="first_price")
    assert res["winner"] == "dialog"
    assert res["winning_price"] == 200.0
    assert len(res["ranked_bids"]) == 2
    assert res["ranked_bids"][0]["bidder"] == "dialog"
    assert res["ranked_bids"][1]["bidder"] == "propa"

def test_compute_bid_surface_scoring():
    bids = [
        {"bidder": "propa", "amount": 100.0, "share_pct": 30.0, "quality_score": 0.95},
        {"bidder": "dialog", "amount": 120.0, "share_pct": 40.0, "quality_score": 0.70},
    ]
    # In scoring mode, composite = 0.5 * price/max_price + 0.5 * quality_score
    # Max price is 120.
    # Propa composite: 0.5 * (100/120) + 0.5 * 0.95 = 0.4167 + 0.475 = 0.8917
    # Dialog composite: 0.5 * (120/120) + 0.5 * 0.70 = 0.50 + 0.35 = 0.85
    # So propa should win!
    res = compute_bid_surface(bids, reserve_price=50.0, mode="scoring", scoring_weights={"price": 0.5, "quality": 0.5})
    assert res["winner"] == "propa"
    assert res["winning_price"] == 100.0

def test_compute_mwc_cost_minimizing():
    players = [
        {"id": "propa", "voting_share": 0.30, "cost": 15.0, "alignment_score": 0.95},
        {"id": "dialog", "voting_share": 0.40, "cost": 20.0, "alignment_score": 0.85},
        {"id": "smj_energy", "voting_share": 0.15, "cost": 5.0, "alignment_score": 0.90},
        {"id": "bridge_petroleum", "voting_share": 0.15, "cost": 8.0, "alignment_score": 0.80},
    ]
    res = compute_mwc(players, majority_threshold=0.5, mode="cost_minimizing")
    assert res["feasible"] is True
    # Exact optimum is dialog + smj_energy (0.55 voting power, cost 25).
    assert res["coalition"] == ["dialog", "smj_energy"]
    assert res["total_cost"] == 25.0
    assert res["coalition_voting_power"] == 0.55


def test_compute_bid_surface_second_price_single_bid_uses_reserve():
    bids = [
        {"bidder": "solo", "amount": 100.0, "share_pct": 100.0, "quality_score": 0.9},
    ]
    res = compute_bid_surface(bids, reserve_price=10.0, mode="second_price")
    assert res["winner"] == "solo"
    assert res["winning_price"] == 10.0


def test_compute_mwc_power_distribution_uses_true_majority_threshold():
    players = [
        {"id": "A", "voting_share": 0.30, "cost": 3.0, "alignment_score": 0.8},
        {"id": "B", "voting_share": 0.25, "cost": 2.0, "alignment_score": 0.7},
        {"id": "C", "voting_share": 0.45, "cost": 9.0, "alignment_score": 0.5},
    ]
    res = compute_mwc(players, majority_threshold=0.5, mode="cost_minimizing")
    assert res["coalition"] == ["A", "B"]
    assert res["power_distribution"]["A"] == 0.5
    assert res["power_distribution"]["B"] == 0.5
    assert res["power_distribution"]["C"] == 0.0
