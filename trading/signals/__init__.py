"""Backward-compat shim: trading.signals was renamed to trading.apex.

The fetch_gold.py entry point still imports from trading.signals.* — keep
this shim so the gold-api doesn't break across the package split.
"""
