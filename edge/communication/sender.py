"""
ClimaScope – Backend Communication Layer
==========================================
Handles HTTP POST of processed readings to the FastAPI backend.
Implements an offline-resilient retry queue:
  - Attempts to POST latest reading immediately after each sample.
  - If the backend is DOWN, the record is kept in the local SQLite queue (sent=0).
  - A background flush loop periodically retries all unsent records.
  - Exponential back-off prevents hammering an unavailable server.
"""

import logging
import os
import time
from datetime import datetime
from typing import Optional

import requests

from storage.local_db import get_unsent_readings, mark_batch_as_sent

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration  (override via environment variables)
# ─────────────────────────────────────────────────────────────────────────────

BACKEND_URL: str = os.environ.get("CLIMASCOPE_BACKEND_URL", "https://climascope-rps.onrender.com")
POST_ENDPOINT: str = f"{BACKEND_URL}/api/data"

logger.info(f"Using backend: {BACKEND_URL}")

DEVICE_ID: str = os.environ.get("CLIMASCOPE_DEVICE_ID", "climascope-pi001")
API_KEY: str = os.environ.get("CLIMASCOPE_API_KEY", "")  # Device API key for auth

REQUEST_TIMEOUT_S: float = 5.0        # per-request timeout
FLUSH_INTERVAL_S: float  = 30.0       # how often the flush loop runs
MAX_FLUSH_BATCH: int     = 50         # max records sent per flush cycle

# Exponential back-off for POST failures
_MIN_BACKOFF_S: float  = 5.0
_MAX_BACKOFF_S: float  = 300.0
_BACKOFF_FACTOR: float = 2.0

_current_backoff: float = _MIN_BACKOFF_S
_last_success_time: Optional[float] = None


def _build_payload(data: dict) -> dict:
    """Convert a storage row / processed reading dict to the API payload shape.

    The backend's SensorDataIn schema requires:
        device_id, timestamp, temperature, pressure, mq2_voltage, gas_ppm
    Optional: humidity, risk_score, risk_level, anomaly_flag, risk_reason
    """
    payload = {
        "device_id":    data.get("device_id", DEVICE_ID),
        "timestamp":    data.get("timestamp", datetime.utcnow().isoformat()),
        "temperature":  data["temperature"],
        "humidity":     data.get("humidity"),
        "pressure":     data["pressure"],
        "mq2_voltage":  float(data.get("mq2_voltage", data.get("gas_voltage", 0.0))),
        "gas_ppm":      float(data.get("gas_ppm", data.get("gas", 0.0))),
        "risk_score":   data.get("risk_score"),
        "risk_level":   data.get("risk_level"),
        "anomaly_flag": bool(data.get("anomaly_flag", False)),
        "risk_reason":  data.get("risk_reason", ""),
    }
    # Include API key if configured
    api_key = data.get("api_key") or API_KEY
    if api_key:
        payload["api_key"] = api_key
    return payload


def post_reading(data: dict) -> bool:
    """
    Attempt to POST a single processed reading to the backend.

    Returns
    -------
    bool – True if the request succeeded (HTTP 2xx), False otherwise.
    """
    global _current_backoff, _last_success_time

    payload = _build_payload(data)
    try:
        response = requests.post(
            POST_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT_S,
        )
        response.raise_for_status()

        _current_backoff = _MIN_BACKOFF_S   # reset on success
        _last_success_time = time.monotonic()
        logger.debug("POST /data → %d", response.status_code)
        return True

    except requests.exceptions.ConnectionError:
        logger.warning("Backend unreachable (%s) – queued locally", POST_ENDPOINT)
    except requests.exceptions.Timeout:
        logger.warning("Backend request timed out (%.1fs)", REQUEST_TIMEOUT_S)
    except requests.exceptions.HTTPError as exc:
        logger.error("Backend HTTP error: %s", exc)
    except Exception as exc:
        logger.error("Unexpected POST error: %s", exc)

    # Increase back-off for subsequent attempts
    _current_backoff = min(_current_backoff * _BACKOFF_FACTOR, _MAX_BACKOFF_S)
    return False


def flush_unsent_queue() -> int:
    """
    Attempt to send all locally queued (unsent) readings to the backend.

    Returns the number of records successfully flushed.
    """
    unsent = get_unsent_readings(limit=MAX_FLUSH_BATCH)
    if not unsent:
        return 0

    logger.info("Flushing %d unsent reading(s)…", len(unsent))
    flushed_ids = []

    for record in unsent:
        success = post_reading(record)
        if success:
            flushed_ids.append(record["id"])
        else:
            # Stop the batch on first failure; keep back-off semantics.
            logger.warning(
                "Flush aborted after %d/%d – backend still unavailable",
                len(flushed_ids),
                len(unsent),
            )
            break

    mark_batch_as_sent(flushed_ids)
    return len(flushed_ids)


def run_flush_loop() -> None:
    """
    Blocking flush loop – intended to be run in a daemon thread.
    Periodically retries all unsent readings with adaptive sleep.
    """
    logger.info(
        "Flush loop started (interval=%.0fs, backoff=%.0fs–%.0fs)",
        FLUSH_INTERVAL_S, _MIN_BACKOFF_S, _MAX_BACKOFF_S,
    )
    while True:
        sleep_secs = max(FLUSH_INTERVAL_S, _current_backoff)
        time.sleep(sleep_secs)
        try:
            flushed = flush_unsent_queue()
            if flushed:
                logger.info("Flush loop: delivered %d record(s)", flushed)
        except Exception as exc:
            logger.error("Flush loop error: %s", exc)
