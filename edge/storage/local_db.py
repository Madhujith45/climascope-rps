"""
ClimaScope – Edge Local Storage (SQLite)
=========================================
Manages a local SQLite database on the Raspberry Pi for:
  - Persisting every processed reading (durable offline buffer)
  - Queuing unsent records for retry when the backend is unreachable

Schema:  environmental_data
"""

import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, List, Optional

logger = logging.getLogger(__name__)

# Path to the SQLite database file (relative to this file's directory)
_DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH: str = os.path.join(_DB_DIR, "climascope_edge.db")

# DDL – executed once on first run
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS environmental_data (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT    NOT NULL,
    temperature  REAL    NOT NULL,
    humidity     REAL    NOT NULL,
    pressure     REAL    NOT NULL,
    gas          REAL    NOT NULL,
    risk_score   INTEGER NOT NULL,
    risk_level   TEXT    NOT NULL,
    anomaly_flag INTEGER NOT NULL DEFAULT 0,
    risk_reason  TEXT,
    sent         INTEGER NOT NULL DEFAULT 0    -- 0 = pending, 1 = successfully sent
);

CREATE INDEX IF NOT EXISTS idx_env_timestamp ON environmental_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_env_sent       ON environmental_data (sent);
"""


# ─────────────────────────────────────────────────────────────────────────────
# Connection helper
# ─────────────────────────────────────────────────────────────────────────────

@contextmanager
def _get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection (WAL mode for concurrent read/write)."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create the database schema if it does not already exist."""
    with _get_conn() as conn:
        conn.executescript(_SCHEMA_SQL)
    logger.info("Edge SQLite DB initialised at %s", DB_PATH)


def save_reading(data: dict) -> int:
    """
    Persist one processed reading.

    Parameters
    ----------
    data : dict
        Must contain the canonical keys produced by the processing engine.

    Returns
    -------
    int – the new row's primary key (id).
    """
    sql = """
        INSERT INTO environmental_data
            (timestamp, temperature, humidity, pressure, gas,
             risk_score, risk_level, anomaly_flag, risk_reason, sent)
        VALUES
            (:timestamp, :temperature, :humidity, :pressure, :gas,
             :risk_score, :risk_level, :anomaly_flag, :risk_reason, 0)
    """
    params = {
        "timestamp":    data.get("timestamp", datetime.utcnow().isoformat()),
        "temperature":  data["temperature"],
        "humidity":     data["humidity"],
        "pressure":     data["pressure"],
        "gas":          data["gas"],
        "risk_score":   data["risk_score"],
        "risk_level":   data["risk_level"],
        "anomaly_flag": int(data.get("anomaly_flag", False)),
        "risk_reason":  data.get("risk_reason", ""),
    }
    with _get_conn() as conn:
        cursor = conn.execute(sql, params)
        row_id = cursor.lastrowid
    logger.debug("Saved reading id=%d  risk=%s(%d)", row_id, params["risk_level"], params["risk_score"])
    return row_id


def get_unsent_readings(limit: int = 50) -> List[dict]:
    """
    Fetch up to `limit` readings that have not yet been successfully sent
    to the backend.
    """
    sql = """
        SELECT * FROM environmental_data
        WHERE sent = 0
        ORDER BY id ASC
        LIMIT ?
    """
    with _get_conn() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(row) for row in rows]


def mark_as_sent(row_id: int) -> None:
    """Mark a single reading as successfully delivered to the backend."""
    with _get_conn() as conn:
        conn.execute("UPDATE environmental_data SET sent = 1 WHERE id = ?", (row_id,))
    logger.debug("Marked reading id=%d as sent", row_id)


def mark_batch_as_sent(row_ids: List[int]) -> None:
    """Mark multiple readings as sent in a single transaction."""
    if not row_ids:
        return
    placeholders = ",".join("?" for _ in row_ids)
    with _get_conn() as conn:
        conn.execute(
            f"UPDATE environmental_data SET sent = 1 WHERE id IN ({placeholders})",
            row_ids,
        )
    logger.info("Marked %d reading(s) as sent", len(row_ids))


def get_recent_readings(limit: int = 100) -> List[dict]:
    """Retrieve the most recent `limit` readings (regardless of sent status)."""
    sql = """
        SELECT * FROM environmental_data
        ORDER BY id DESC
        LIMIT ?
    """
    with _get_conn() as conn:
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(row) for row in rows]


def purge_sent_older_than_days(days: int = 7) -> int:
    """
    Delete sent readings older than `days` days to control disk usage.

    Returns the number of rows deleted.
    """
    sql = """
        DELETE FROM environmental_data
        WHERE sent = 1
          AND timestamp < datetime('now', ? || ' days')
    """
    with _get_conn() as conn:
        cursor = conn.execute(sql, (f"-{days}",))
        deleted = cursor.rowcount
    if deleted:
        logger.info("Purged %d old sent reading(s)", deleted)
    return deleted
