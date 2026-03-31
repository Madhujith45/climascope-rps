"""
ClimaScope – Backend Database Manager
SQLite + SQLAlchemy (async via aiosqlite)

Schema migration strategy (development)
-----------------------------------------
SQLite has two key limitations:

  1. ALTER TABLE can only ADD a new column; it cannot change the type or
     constraints (e.g. NOT NULL) of an existing column.
  2. SQLAlchemy's create_all() never modifies a table that already exists.

init_db() handles both cases automatically on every startup:

  Phase 1 – create_all()
      Creates tables that do not exist yet (true no-op for existing ones).

  Phase 2 – _migrate_schema()
      For each table that already exists on disk:
        a) ADD COLUMN for every column present in the model that is absent in
           the DB.  Non-destructive: existing rows are unchanged.
        b) If any existing column has a constraint mismatch (e.g. it was
           NOT NULL in the old DB but is now nullable in the current model),
           perform SQLite's recommended table-rebuild sequence to recreate the
           table with the correct schema while preserving all existing rows.

This means the server self-heals on every startup whenever SQLAlchemy models
are updated, with zero manual intervention during development.
"""

import logging
import os
from typing import Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

# ── Database file location ────────────────────────────────────────────────────
_DB_DIR  = os.path.dirname(os.path.abspath(__file__))
_DB_FILE = os.path.normpath(os.path.join(_DB_DIR, "..", "climascope_backend.db"))
DATABASE_URL = f"sqlite+aiosqlite:///{_DB_FILE}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


# ── SQLite type helpers ───────────────────────────────────────────────────────

_SQLA_TO_SQLITE: Dict[str, str] = {
    "INTEGER":  "INTEGER",
    "FLOAT":    "REAL",
    "NUMERIC":  "REAL",
    "VARCHAR":  "TEXT",
    "TEXT":     "TEXT",
    "BOOLEAN":  "INTEGER",   # SQLite stores booleans as 0 / 1
    "DATETIME": "TEXT",
}


def _sqla_type(col) -> str:
    return _SQLA_TO_SQLITE.get(type(col.type).__name__.upper(), "TEXT")


def _col_def(col) -> str:
    """Full SQLite column definition fragment used in CREATE TABLE / rebuild."""
    parts = [col.name, _sqla_type(col)]
    if col.primary_key:
        parts.append("PRIMARY KEY AUTOINCREMENT")
    elif not col.nullable:
        parts.append("NOT NULL DEFAULT ''")
    return " ".join(parts)


# ── Migration ─────────────────────────────────────────────────────────────────

async def _migrate_schema(conn) -> None:
    """
    Bring every mapped table's on-disk schema in line with the current models.

    Phase A – ADD COLUMN
        For each model column absent from the DB, run ALTER TABLE … ADD COLUMN.
        Existing rows simply receive NULL for the new column.

    Phase B – table rebuild (constraint mismatch)
        If any existing column has a different NOT NULL constraint than the
        model declares (e.g. 'humidity' was NOT NULL in the old schema but
        is nullable in the updated model), SQLite cannot ALTER it in place.
        Instead we perform the standard 5-step rebuild:

          1. PRAGMA foreign_keys = OFF
          2. CREATE TABLE <tmp>   — with the correct schema
          3. INSERT INTO <tmp> SELECT … FROM <old>   — copy all rows
          4. DROP TABLE <old>
          5. ALTER TABLE <tmp> RENAME TO <old>
          6. Recreate indexes
          7. PRAGMA foreign_keys = ON
    """
    for table in Base.metadata.sorted_tables:
        # PRAGMA row layout: (cid, name, type, notnull, dflt_value, pk)
        pragma = await conn.execute(text(f"PRAGMA table_info({table.name})"))
        existing: Dict[str, dict] = {
            row[1]: {"notnull": bool(row[3]), "pk": bool(row[5])}
            for row in pragma.fetchall()
        }

        if not existing:
            continue  # table does not exist yet; create_all handles it

        model_cols = {col.name: col for col in table.columns}

        # ── Phase A: add missing columns ──────────────────────────────────────
        for name, col in model_cols.items():
            if name in existing:
                continue
            null_clause = "" if col.nullable else " NOT NULL DEFAULT ''"
            try:
                await conn.execute(
                    text(
                        f"ALTER TABLE {table.name} "
                        f"ADD COLUMN {name} {_sqla_type(col)}{null_clause}"
                    )
                )
                logger.warning(
                    "Migration: added column '%s.%s' (%s)",
                    table.name, name, _sqla_type(col),
                )
            except Exception as exc:
                logger.error(
                    "Migration ADD COLUMN failed for %s.%s: %s",
                    table.name, name, exc,
                )

        # ── Phase B: rebuild if any constraint mismatch ────────────────────────
        mismatches: List[str] = [
            name
            for name, info in existing.items()
            if not info["pk"]
            and name in model_cols
            and info["notnull"] != (not model_cols[name].nullable)
        ]

        if not mismatches:
            continue

        logger.warning(
            "Migration: constraint mismatch in '%s' for columns %s — "
            "rebuilding table to fix schema (all rows are preserved).",
            table.name, mismatches,
        )

        tmp      = f"{table.name}_mig_tmp"
        shared   = [n for n in model_cols if n in existing]
        cols_csv = ", ".join(shared)
        col_defs = ",\n    ".join(_col_def(c) for c in table.columns)

        await conn.execute(text("PRAGMA foreign_keys = OFF"))
        await conn.execute(text(f"CREATE TABLE {tmp} (\n    {col_defs}\n)"))
        await conn.execute(
            text(f"INSERT INTO {tmp} ({cols_csv}) SELECT {cols_csv} FROM {table.name}")
        )
        await conn.execute(text(f"DROP TABLE {table.name}"))
        await conn.execute(text(f"ALTER TABLE {tmp} RENAME TO {table.name}"))

        for idx in table.indexes:
            idx_cols = ", ".join(c.name for c in idx.columns)
            unique   = "UNIQUE " if idx.unique else ""
            await conn.execute(
                text(
                    f"CREATE {unique}INDEX IF NOT EXISTS {idx.name} "
                    f"ON {table.name} ({idx_cols})"
                )
            )

        await conn.execute(text("PRAGMA foreign_keys = ON"))
        logger.warning("Migration: '%s' rebuilt successfully.", table.name)


# ── Public API ────────────────────────────────────────────────────────────────

async def init_db() -> None:
    """
    Initialise the database.  Called once at application startup.

    1. create_all  – creates any tables that don't exist yet (idempotent).
    2. _migrate_schema – adds missing columns and fixes constraint mismatches
       in pre-existing tables so older on-disk DBs are silently upgraded.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_schema(conn)

    logger.info("Database ready: %s", _DB_FILE)


async def get_db():
    """FastAPI dependency that yields a DB session."""
    async with AsyncSessionLocal() as session:
        yield session
