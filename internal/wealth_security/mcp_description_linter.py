"""
MCP Description Linter — Check tool descriptions for security smells.

Per "MCP Tool Descriptions Are Smelly!" research (arXiv 2602.14878):
"97.1% of analyzed tool descriptions had at least one smell."

Smells detected:
- "smell_1_overbroad": description is too vague or has too-wide blast radius
- "smell_2_unscoped": no scope/explicit authority mentioned
- "smell_3_untyped_io": input/output types not specified
- "smell_4_no_examples": no usage example
- "smell_5_eval_gaps": no failure mode documented
- "smell_6_priv_escalation": description implies elevation of privilege
- "smell_7_secret_touch": description mentions secrets without auth
- "smell_8_unbounded": no upper bound on resource use

F8 LAW: Tools with high smell counts must be re-described or rejected.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class LintResult:
    """Result of an MCP description lint."""

    tool_name: str
    smell_count: int
    smells: list[str] = field(default_factory=list)
    severity: str = "PASS"  # PASS | WARN | FAIL
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "smell_count": self.smell_count,
            "smells": self.smells,
            "severity": self.severity,
            "recommendation": self.recommendation,
        }


class MCPDescriptionLinter:
    """Lint MCP tool descriptions for security smells."""

    def __init__(self):
        self._patterns = {
            "smell_1_overbroad": re.compile(r"\b(any|all|every|unlimited|unrestricted)\b", re.I),
            "smell_2_unscoped": re.compile(r"\b(can|may|might|could)\s+(do|run|execute|modify|delete)\b", re.I),
            "smell_3_untyped_io": re.compile(r"\b(returns?|takes?)\s+(data|results?|things?|stuff)\b", re.I),
            "smell_4_no_examples": None,  # checked by length + presence
            "smell_5_eval_gaps": re.compile(r"\b(can|will)\s+(not\s+)?fail\b", re.I),
            "smell_6_priv_escalation": re.compile(r"\b(become\s+root|escalate|admin\s+mode|god\s+mode)\b", re.I),
            "smell_7_secret_touch": re.compile(r"\b(api_?key|secret|password|token|credential)\b", re.I),
            "smell_8_unbounded": re.compile(r"\b(loop|forever|recursi[vw]e|unbounded)\b", re.I),
        }

    def lint(self, tool_name: str, description: str) -> LintResult:
        """Lint a tool description. Returns LintResult."""
        smells = []
        for smell_name, pattern in self._patterns.items():
            if pattern is None:
                continue
            if pattern.search(description):
                smells.append(smell_name)

        # smell_4_no_examples: short description with no usage hint
        if len(description) < 60 or "e.g." not in description.lower() and "example" not in description.lower():
            smells.append("smell_4_no_examples")

        # Determine severity
        if len(smells) == 0:
            severity = "PASS"
            rec = "Description is clean."
        elif len(smells) <= 2:
            severity = "WARN"
            rec = "Refine description to address smells."
        else:
            severity = "FAIL"
            rec = "Description has too many smells. Rewrite with explicit scope, types, and examples."

        return LintResult(
            tool_name=tool_name,
            smell_count=len(smells),
            smells=smells,
            severity=severity,
            recommendation=rec,
        )
