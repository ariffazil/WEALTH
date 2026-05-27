"""
WEALTH Personal Finance — PostgreSQL Schema
D1: Personal Finance infrastructure for cashflow, net worth, EPF, and zakat tracking.
Tables: wealth.transactions, wealth.assets, wealth.liabilities, wealth.epf_snapshots, wealth.zakat_records
"""

from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import asyncio
import asyncpg


# --------------------------------------------------------------------------- #
# Connection Pool (singleton)
# --------------------------------------------------------------------------- #

_pool: Optional[asyncpg.Pool] = None

WEALTH_PG_URL = (
    "postgresql://arifos_admin:ArifPostgresVault2026!@localhost:5432/vault999"
)
# Override via env var if different
import os

WEALTH_PG_URL = os.getenv("WEALTH_PG_URL", WEALTH_PG_URL)


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            WEALTH_PG_URL,
            min_size=1,
            max_size=4,
            command_timeout=30,
        )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# --------------------------------------------------------------------------- #
# Schema Definition
# --------------------------------------------------------------------------- #

SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS wealth;

CREATE TABLE IF NOT EXISTS wealth.transactions (
    id          BIGSERIAL PRIMARY KEY,
    owner       TEXT    NOT NULL DEFAULT 'arif',
    date        DATE    NOT NULL,
    description TEXT    NOT NULL,
    category    TEXT    NOT NULL,           -- salary|expense|income|investment|loan|savings|zakat
    subcategory TEXT,
    amount      NUMERIC(16, 4) NOT NULL,    -- positive = inflow, negative = outflow
    currency    TEXT    NOT NULL DEFAULT 'MYR',
    metadata    JSONB   DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_txn_owner_date   ON wealth.transactions(owner, date DESC);
CREATE INDEX IF NOT EXISTS idx_txn_category     ON wealth.transactions(owner, category);
CREATE INDEX IF NOT EXISTS idx_txn_date_range    ON wealth.transactions(owner, date) WHERE owner = 'arif';

CREATE TABLE IF NOT EXISTS wealth.assets (
    id           BIGSERIAL PRIMARY KEY,
    owner        TEXT    NOT NULL DEFAULT 'arif',
    name         TEXT    NOT NULL,
    asset_class  TEXT    NOT NULL,          -- epf|property|vehicle|shares|cash|crypto|other
    current_value NUMERIC(16, 4) NOT NULL,
    cost_basis   NUMERIC(16, 4),
    currency     TEXT    NOT NULL DEFAULT 'MYR',
    metadata     JSONB   DEFAULT '{}',
    as_of        DATE    NOT NULL DEFAULT CURRENT_DATE,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_asset_owner      ON wealth.assets(owner);
CREATE INDEX IF NOT EXISTS idx_asset_class     ON wealth.assets(owner, asset_class);

CREATE TABLE IF NOT EXISTS wealth.liabilities (
    id              BIGSERIAL PRIMARY KEY,
    owner           TEXT    NOT NULL DEFAULT 'arif',
    name            TEXT    NOT NULL,
    liability_class TEXT    NOT NULL,       -- mortgage|car_loan|personal_loan|credit_card|student_loan|other
    outstanding     NUMERIC(16, 4) NOT NULL,
    original_amount NUMERIC(16, 4),
    interest_rate   NUMERIC(8, 4),          -- annualised, e.g. 0.0480 = 4.80%
    maturity_date   DATE,
    currency        TEXT    NOT NULL DEFAULT 'MYR',
    metadata        JSONB   DEFAULT '{}',
    as_of           DATE    NOT NULL DEFAULT CURRENT_DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_liab_owner       ON wealth.liabilities(owner);

CREATE TABLE IF NOT EXISTS wealth.epf_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    owner           TEXT    NOT NULL DEFAULT 'arif',
    snapshot_date   DATE    NOT NULL,
    account_1       NUMERIC(16, 4) DEFAULT 0,
    account_2       NUMERIC(16, 4) DEFAULT 0,
    total           NUMERIC(16, 4) GENERATED ALWAYS AS (account_1 + account_2) STORED,
    annual_rate     NUMERIC(6, 4)  DEFAULT 0.0515,   -- 5.15% default
    metadata        JSONB   DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(owner, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_epf_owner_date  ON wealth.epf_snapshots(owner, snapshot_date DESC);

CREATE TABLE IF NOT EXISTS wealth.zakat_records (
    id              BIGSERIAL PRIMARY KEY,
    owner           TEXT    NOT NULL DEFAULT 'arif',
    year            INTEGER NOT NULL,
    calculation_date DATE   NOT NULL,
    wealth_base     NUMERIC(16, 4) NOT NULL,  -- nisab threshold applied
    rate            NUMERIC(5, 4)  NOT NULL DEFAULT 0.025,  -- 2.5%
    amount          NUMERIC(16, 4) NOT NULL,
    currency        TEXT    NOT NULL DEFAULT 'MYR',
    paid            BOOLEAN DEFAULT FALSE,
    paid_date       DATE,
    metadata        JSONB   DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(owner, year)
);

CREATE INDEX IF NOT EXISTS idx_zakat_owner_year ON wealth.zakat_records(owner, year);
"""


async def init_schema():
    """Create all WEALTH personal finance tables. Idempotent — uses IF NOT EXISTS."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)


# --------------------------------------------------------------------------- #
# CRUD helpers
# --------------------------------------------------------------------------- #


async def upsert_transaction(
    owner: str,
    date: date,
    description: str,
    category: str,
    amount: float,
    currency: str = "MYR",
    subcategory: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO wealth.transactions
                (owner, date, description, category, subcategory, amount, currency, metadata)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            RETURNING id
            """,
            owner,
            date,
            description,
            category,
            subcategory,
            amount,
            currency,
            metadata or {},
        )
        return row["id"]


async def get_transactions(
    owner: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    limit: int = 500,
):
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = "SELECT * FROM wealth.transactions WHERE owner = $1"
        params = [owner]
        if start_date:
            params.append(start_date)
            query += f" AND date >= ${len(params)}"
        if end_date:
            params.append(end_date)
            query += f" AND date <= ${len(params)}"
        if category:
            params.append(category)
            query += f" AND category = ${len(params)}"
        query += " ORDER BY date DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        return await conn.fetch(query, *params)


async def upsert_asset(
    owner: str,
    name: str,
    asset_class: str,
    current_value: float,
    cost_basis: Optional[float] = None,
    currency: str = "MYR",
    as_of: Optional[date] = None,
    metadata: Optional[dict] = None,
) -> int:
    pool = await get_pool()
    as_of = as_of or date.today()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO wealth.assets
                (owner, name, asset_class, current_value, cost_basis, currency, as_of, metadata)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT (owner, name, as_of)
            DO UPDATE SET current_value = EXCLUDED.current_value,
                          updated_at      = NOW()
            RETURNING id
            """,
            owner,
            name,
            asset_class,
            current_value,
            cost_basis,
            currency,
            as_of,
            metadata or {},
        )
        return row["id"]


async def get_assets(owner: str, asset_class: Optional[str] = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if asset_class:
            return await conn.fetch(
                "SELECT * FROM wealth.assets WHERE owner=$1 AND asset_class=$2 ORDER BY as_of DESC",
                owner,
                asset_class,
            )
        return await conn.fetch(
            "SELECT * FROM wealth.assets WHERE owner=$1 ORDER BY as_of DESC",
            owner,
        )


async def upsert_liability(
    owner: str,
    name: str,
    liability_class: str,
    outstanding: float,
    original_amount: Optional[float] = None,
    interest_rate: Optional[float] = None,
    maturity_date: Optional[date] = None,
    currency: str = "MYR",
    as_of: Optional[date] = None,
    metadata: Optional[dict] = None,
) -> int:
    pool = await get_pool()
    as_of = as_of or date.today()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO wealth.liabilities
                (owner, name, liability_class, outstanding, original_amount, interest_rate, maturity_date, currency, as_of, metadata)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            ON CONFLICT (owner, name)
            DO UPDATE SET outstanding   = EXCLUDED.outstanding,
                          updated_at     = NOW()
            RETURNING id
            """,
            owner,
            name,
            liability_class,
            outstanding,
            original_amount,
            interest_rate,
            maturity_date,
            currency,
            as_of,
            metadata or {},
        )
        return row["id"]


async def get_liabilities(owner: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM wealth.liabilities WHERE owner=$1 ORDER BY liability_class",
            owner,
        )


async def upsert_epf_snapshot(
    owner: str,
    snapshot_date: date,
    account_1: float,
    account_2: float,
    annual_rate: float = 0.0515,
    metadata: Optional[dict] = None,
) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO wealth.epf_snapshots
                (owner, snapshot_date, account_1, account_2, annual_rate, metadata)
            VALUES ($1,$2,$3,$4,$5,$6)
            ON CONFLICT (owner, snapshot_date)
            DO UPDATE SET account_1 = EXCLUDED.account_1,
                          account_2 = EXCLUDED.account_2,
                          annual_rate = EXCLUDED.annual_rate
            RETURNING id
            """,
            owner,
            snapshot_date,
            account_1,
            account_2,
            annual_rate,
            metadata or {},
        )
        return row["id"]


async def get_epf_snapshots(owner: str, limit: int = 12):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM wealth.epf_snapshots WHERE owner=$1 ORDER BY snapshot_date DESC LIMIT $2",
            owner,
            limit,
        )


async def get_latest_epf(owner: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM wealth.epf_snapshots WHERE owner=$1 ORDER BY snapshot_date DESC LIMIT 1",
            owner,
        )


async def upsert_zakat_record(
    owner: str,
    year: int,
    calculation_date: date,
    wealth_base: float,
    rate: float = 0.025,
    amount: float = 0,
    currency: str = "MYR",
    paid: bool = False,
    paid_date: Optional[date] = None,
    metadata: Optional[dict] = None,
) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO wealth.zakat_records
                (owner, year, calculation_date, wealth_base, rate, amount, currency, paid, paid_date, metadata)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            ON CONFLICT (owner, year)
            DO UPDATE SET calculation_date = EXCLUDED.calculation_date,
                          wealth_base       = EXCLUDED.wealth_base,
                          amount            = EXCLUDED.amount,
                          paid              = EXCLUDED.paid,
                          paid_date         = EXCLUDED.paid_date
            RETURNING id
            """,
            owner,
            year,
            calculation_date,
            wealth_base,
            rate,
            amount,
            currency,
            paid,
            paid_date,
            metadata or {},
        )
        return row["id"]


async def get_zakat_records(owner: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM wealth.zakat_records WHERE owner=$1 ORDER BY year DESC",
            owner,
        )
