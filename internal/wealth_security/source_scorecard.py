"""
WEALTH Source Scorecard — Per-tool OpenSSF-style score.

Mirror of arifOS arifos_registry/tool_scorecard.py.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class WealthSourceScorecard:
    """Per-tool OpenSSF-style security scorecard for WEALTH tools."""

    tool_name: str
    source_repository: str = "https://github.com/ariffazil/wealth"
    code_review_score: float = 0.0
    dangerous_workflow_score: float = 0.0
    pinned_dependencies_score: float = 0.0
    token_permissions_score: float = 0.0
    binary_artifacts_score: float = 0.0
    license_score: float = 0.0
    test_coverage_score: float = 0.0
    maintenance_score: float = 0.0
    notes: dict = field(default_factory=dict)
    last_evaluated: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    @property
    def composite(self) -> float:
        weights = {
            "code_review": 0.20,
            "dangerous_workflow": 0.20,
            "pinned_dependencies": 0.10,
            "token_permissions": 0.15,
            "binary_artifacts": 0.10,
            "license": 0.05,
            "test_coverage": 0.10,
            "maintenance": 0.10,
        }
        return (
            self.code_review_score * weights["code_review"]
            + self.dangerous_workflow_score * weights["dangerous_workflow"]
            + self.pinned_dependencies_score * weights["pinned_dependencies"]
            + self.token_permissions_score * weights["token_permissions"]
            + self.binary_artifacts_score * weights["binary_artifacts"]
            + self.license_score * weights["license"]
            + self.test_coverage_score * weights["test_coverage"]
            + self.maintenance_score * weights["maintenance"]
        )

    @property
    def tier(self) -> str:
        c = self.composite
        if c >= 8.0:
            return "GOLD"
        if c >= 6.0:
            return "SILVER"
        if c >= 4.0:
            return "BRONZE"
        return "REJECT"
