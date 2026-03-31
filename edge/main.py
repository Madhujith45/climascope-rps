"""
ClimaScope – Edge Main Entry Point
====================================
Orchestrates the entire edge pipeline on the Raspberry Pi:

  Loop every SAMPLE_INTERVAL_S seconds:
    1. Read all sensors (DHT22, BMP280, MQ2/ADS1115)
    2. Merge raw readings
    3. Run through the AI risk processing engine
    4. Stamp with ISO-8601 UTC timestamp
    5. Persist to local SQLite
    6. Attempt immediate POST to backend
       (if that fails, the flush-loop retries later)

A daemon thread runs the offline flush loop continuously so unsent data
is delivered as soon as the backend becomes reachable again.

Environment variables (optional):
  CLIMASCOPE_BACKEND_URL   – e.g. http://192.168.1.50:8000
  CLIMASCOPE_INTERVAL      – sampling interval in seconds (default 60)
  CLIMASCOPE_LOG_LEVEL     – DEBUG / INFO / WARNING (default INFO)
"""

import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone

# ── Path bootstrap: ensure sibling packages are importable ────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Project imports ───────────────────────────────────────────────────────────
from sensors import read_dht22, read_bmp280, read_mq2
from processing import process_reading
from storage import init_db, save_reading, get_unsent_readings
from communication import post_reading, run_flush_loop

# ─────────────────────────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────────────────────────

LOG_LEVEL = os.environ.get("CLIMASCOPE_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "climascope.log"),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("climascope.main")

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_INTERVAL_S: float = float(os.environ.get("CLIMASCOPE_INTERVAL", 60))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def read_all_sensors() -> dict:
    """
    Read all sensors and return a merged dict.
    BMP280 also provides a secondary temperature reading for cross-checking;
    we use the DHT22 temperature as the primary value.
    """
    dht_data = read_dht22()
    bmp_data = read_bmp280()
    mq2_data = read_mq2()

    return {
        "temperature": dht_data["temperature"],
        "humidity":    dht_data["humidity"],
        "pressure":    bmp_data["pressure"],
        "altitude":    bmp_data.get("altitude"),
        "gas_index":   mq2_data["gas_index"],
        "gas_raw":     mq2_data["gas_raw"],
        "gas_voltage": mq2_data["gas_voltage"],
        # cross-check temperature from BMP280 (logged but not used in risk)
        "bmp_temperature": bmp_data["temperature"],
    }


def run_sample_cycle() -> None:
    """Execute one complete sense → process → store → send cycle."""
    cycle_start = time.monotonic()
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        # 1. Sensor acquisition
        raw = read_all_sensors()
        logger.debug("Raw sensors: %s", raw)

        # 2. AI processing / risk scoring
        processed = process_reading(raw)
        processed["timestamp"] = ts

        # 3. Local persistence (always succeeds)
        row_id = save_reading(processed)

        # 4. Immediate backend push  (non-blocking on failure)
        sent = post_reading(processed)

        # If post succeeded, mark the just-saved row as sent
        if sent:
            from storage.local_db import mark_as_sent
            mark_as_sent(row_id)

        elapsed = time.monotonic() - cycle_start
        logger.info(
            "[%s]  T=%.1f°C  H=%.1f%%  P=%.1fhPa  Gas=%.1f  "
            "Risk=%d (%s)%s  (%.2fs)",
            ts,
            processed["temperature"],
            processed["humidity"],
            processed["pressure"],
            processed["gas"],
            processed["risk_score"],
            processed["risk_level"],
            "  ⚠ ANOMALY" if processed["anomaly_flag"] else "",
            elapsed,
        )

    except Exception as exc:
        logger.error("Sample cycle error: %s", exc, exc_info=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=" * 60)
    logger.info("ClimaScope Edge Node starting")
    logger.info("  Sampling interval : %.0f s", SAMPLE_INTERVAL_S)
    logger.info("  Backend URL       : %s", os.environ.get("CLIMASCOPE_BACKEND_URL", "http://localhost:8000"))
    logger.info("=" * 60)

    # Initialise local database
    init_db()

    # Start the offline retry flush loop in a daemon thread
    flush_thread = threading.Thread(
        target=run_flush_loop,
        name="flush-loop",
        daemon=True,
    )
    flush_thread.start()
    logger.info("Offline flush loop started (thread: %s)", flush_thread.name)

    # Main sampling loop
    logger.info("Entering main sampling loop…")
    try:
        while True:
            loop_start = time.monotonic()
            run_sample_cycle()

            # Sleep for the remainder of the interval
            elapsed = time.monotonic() - loop_start
            sleep_time = max(0.0, SAMPLE_INTERVAL_S - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("Shutdown requested (SIGINT) – exiting cleanly.")
        sys.exit(0)
    except Exception as exc:
        logger.critical("Fatal error in main loop: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
