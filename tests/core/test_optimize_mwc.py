from wealth_mcp.tools.optimize_mwc import compute_mwc


def test_cost_minimizing_picks_true_optimum():
    result = compute_mwc(
        players=[
            {"id": "A", "voting_share": 0.34, "cost": 4, "alignment_score": 0.7},
            {"id": "B", "voting_share": 0.34, "cost": 4, "alignment_score": 0.7},
            {"id": "C", "voting_share": 0.51, "cost": 7, "alignment_score": 0.6},
        ],
        majority_threshold=0.5,
        mode="cost_minimizing",
    )

    assert result["feasible"] is True
    assert result["coalition"] == ["C"]
    assert result["total_cost"] == 7
    assert result["coalition_voting_power"] == 0.51


def test_required_players_are_respected_in_exact_search():
    result = compute_mwc(
        players=[
            {"id": "A", "voting_share": 0.30, "cost": 3, "alignment_score": 0.8},
            {"id": "B", "voting_share": 0.25, "cost": 2, "alignment_score": 0.7},
            {"id": "C", "voting_share": 0.35, "cost": 6, "alignment_score": 0.9},
            {"id": "D", "voting_share": 0.10, "cost": 1, "alignment_score": 0.6},
        ],
        majority_threshold=0.5,
        mode="cost_minimizing",
        constraints={"require": ["A"]},
    )

    assert result["feasible"] is True
    assert "A" in result["coalition"]
    assert result["coalition_voting_power"] >= result["majority_needed"]
