#!/usr/bin/env python3
"""WEALTH canonical runtime entrypoint.

Importing this module exposes the internal monolith tool functions for tests and
local scripts. Executing it starts the FastMCP/Starlette runtime.
"""

from __future__ import annotations

import runpy

from internal.monolith import *  # noqa: F403


if __name__ == "__main__":
    runpy.run_module("internal.monolith", run_name="__main__")
