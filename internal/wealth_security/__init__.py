"""
WEALTH Security — Tool manifests, MCP description linter, source scorecards.

Per executive verdict Phase 1:
"Add MCP description linter"
"Add basic OPA policy check before any mutation-capable tool"
"""

from .tool_manifest import WealthToolManifest, build_manifest
from .mcp_description_linter import MCPDescriptionLinter, LintResult
from .source_scorecard import WealthSourceScorecard
from .policy_inputs import build_policy_input

__all__ = [
    "WealthToolManifest",
    "build_manifest",
    "MCPDescriptionLinter",
    "LintResult",
    "WealthSourceScorecard",
    "build_policy_input",
]
