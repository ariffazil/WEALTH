"""Test that all WEALTH modules import cleanly."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_monolith_imports():
    """Verify the monolith can be imported."""
    from internal import monolith
    assert monolith is not None


def test_market_data_imports():
    from internal import market_data
    assert market_data is not None


def test_personal_finance_imports():
    from internal import personal_finance
    assert personal_finance is not None


def test_db_schema_imports():
    from internal import db_schema
    assert db_schema is not None


def test_stock_indicators_imports():
    from internal.stock import indicators
    assert indicators is not None


def test_bursa_schemas_imports():
    from internal.bursa import schemas
    assert schemas is not None


def test_pai_receipt_imports():
    from internal import pai_receipt
    assert pai_receipt is not None


def test_kernel_math_imports():
    from internal import kernel_math
    assert kernel_math is not None


def test_federation_memory_imports():
    from internal import federation_memory
    assert federation_memory is not None


def test_governance_imports():
    from internal import governance
    assert governance is not None
