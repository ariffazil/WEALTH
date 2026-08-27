"""
WEALTH MCP tools package — per-tool modules extracted from canonical.py (Phase 1a).
"""

from wealth_mcp.tools.bid_surface import compute_bid_surface
from wealth_mcp.tools.optimize_mwc import compute_mwc
from wealth_mcp.tools.types import (
    CoercedList,
    CoercedIntList,
    CoercedDict,
    CoercedDictList,
    CoercedDictListStrict,
    CoercedStrList,
    _coerce_json_string,
    _coerce_dict_to_list_of_dicts,
    _call_legacy_tool,
)

# Register functions for each tool module
from wealth_mcp.tools.primitive import register_primitive
from wealth_mcp.tools.health import register_health
from wealth_mcp.tools.diagnose import register_diagnose
from wealth_mcp.tools.market import register_market
from wealth_mcp.tools.ledger import register_ledger
from wealth_mcp.tools.registry import register_registry
from wealth_mcp.tools.entropy import register_entropy
from wealth_mcp.tools.judge_handoff import register_judge_handoff
from wealth_mcp.tools.indicator import register_indicator
from wealth_mcp.tools.backtest import register_backtest
from wealth_mcp.tools.entry_plan import register_entry_plan

__all__ = [
    "compute_bid_surface",
    "compute_mwc",
    "CoercedList",
    "CoercedIntList",
    "CoercedDict",
    "CoercedDictList",
    "CoercedDictListStrict",
    "CoercedStrList",
    "_coerce_json_string",
    "_coerce_dict_to_list_of_dicts",
    "_call_legacy_tool",
    "register_primitive",
    "register_health",
    "register_diagnose",
    "register_market",
    "register_ledger",
    "register_registry",
    "register_entropy",
    "register_judge_handoff",
    "register_indicator",
    "register_backtest",
    "register_entry_plan",
]
