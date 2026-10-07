"""Pytest configuration for the M5 tests.

Registers the `slow` marker so the @pytest.mark.slow decorator does
not produce a warning.
"""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "slow: mark test as slow (may take >10s)")