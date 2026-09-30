"""Agent-package marker for GOLD_WAVE_FORGE.

This package deliberately has NO top-level re-exports — every agent
module imports its dependencies directly (e.g. ``from . import
_000_causality as _causality``). That avoids the circular-import
surfaces that arise from re-exporting an entire graph at package
load time.
"""