#!/usr/bin/env python3
"""⚠️ DEPRECATED entrypoint (ZEN 2026-07-11 W6).

Production WEALTH is streamable-http on :18082 via:
  server_federated.py → wealth_mcp/server.py:create_mcp_server()
  systemd: wealth-organ.service

This module still imports internal.monolith for tests/scripts. Do NOT bind
it on :18082 (port conflict with production). Prefer server_federated.py.
"""

from __future__ import annotations

import runpy

from internal.monolith import *  # noqa: F403


if __name__ == "__main__":
    runpy.run_module("internal.monolith", run_name="__main__")
