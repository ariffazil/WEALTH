"""Compatibility entrypoint for the canonical WEALTH valuation kernel."""

from internal.monolith import mcp

__all__ = ["mcp"]


if __name__ == "__main__":
    mcp.run()
