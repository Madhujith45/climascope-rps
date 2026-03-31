"""
ClimaScope - Edge Device Simulator & Backend Pipeline Verifier
==============================================================

PURPOSE
-------
Simulates a Raspberry Pi edge node posting environmental sensor data to the
ClimaScope FastAPI backend.  Also runs endpoint verification tests against:

    POST /api/data          - ingest a single reading
    GET  /api/data/latest   - newest N readings
    GET  /api/data/history  - full paginated history with device_id filtering

USAGE
-----
  # Defaults: 5-second interval, 20 readings, device_id=climascope_sim_001
  python tests/simulate_edge.py

  # Large-scale dataset generation for ML training
  python tests/simulate_edge.py --count 5000 --interval 1 --device_id climascope_sim_001

  # Custom options
  python tests/simulate_edge.py --url http://localhost:8000 \
                                 --device_id climascope_sim_002 \
                                 --count 30 \
                                 --interval 3

  # Replay rows from the sample xlsx file instead of random data
  python tests/simulate_edge.py --xlsx "path/to/sensor_data.xlsx"

  # Run endpoint verification only (no simulation loop)
  python tests/simulate_edge.py --verify-only

ENVIRONMENT VARIABLES (override CLI defaults)
---------------------------------------------
  CLIMASCOPE_BACKEND_URL   http://localhost:8000
  CLIMASCOPE_DEVICE_ID     climascope_sim_001
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

# ─────────────────────────────────────────────────────────────────────────────
# Logging ─────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulate_edge.log"),
            mode="a",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("climascope.simulator")

# ─────────────────────────────────────────────────────────────────────────────
# Sensor value ranges matching real ClimaScope hardware ───────────────────────
# ─────────────────────────────────────────────────────────────────────────────

SENSOR_RANGES: Dict[str, tuple] = {
    "temperature": (25.0,  40.0),   # °C  (normal)
    "pressure":    (980.0, 1020.0), # hPa (normal)
    "mq2_voltage": (0.5,   2.5),    # V
    "gas_ppm":     (50.0,  300.0),  # PPM (normal)
}

# Anomaly thresholds (for labelling, not clamping)
ANOMALY_GAS_SPIKE_PPM    = 250.0   # gas_ppm above this -> anomaly
ANOMALY_PRESSURE_DROP    = 15.0    # sudden hPa drop magnitude -> anomaly
ANOMALY_TEMP_SPIKE_C     = 42.0    # temperature above this -> anomaly

# Probability weights: 92 % normal, 4 % gas spike, 2 % pressure drop, 2 % temp spike
_ANOMALY_WEIGHTS = [92, 4, 2, 2]

# ─────────────────────────────────────────────────────────────────────────────
# Payload generation ──────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def generate_reading(device_id: str) -> Dict[str, Any]:
    """Return a single randomly-generated sensor payload with occasional anomalies.

    Anomaly types (injected with configurable probability):
      - Gas spike   : gas_ppm 260-500 ppm  (> ANOMALY_GAS_SPIKE_PPM)
      - Pressure drop: pressure drops 15-30 hPa below baseline
      - Temp spike  : temperature 43-52 °C  (> ANOMALY_TEMP_SPIKE_C)

    All anomalies are flagged in the returned dict so callers can log them.
    """
    # Baseline temperature with mild drift
    temperature = round(random.uniform(*SENSOR_RANGES["temperature"]), 2)

    # Mild negative correlation: higher temp -> slightly lower pressure
    pressure_mid    = sum(SENSOR_RANGES["pressure"]) / 2
    pressure_offset = (temperature - sum(SENSOR_RANGES["temperature"]) / 2) * -0.3
    pressure = round(
        max(SENSOR_RANGES["pressure"][0],
            min(SENSOR_RANGES["pressure"][1],
                random.gauss(pressure_mid + pressure_offset, 8.0))),
        2,
    )

    mq2_voltage = round(random.uniform(*SENSOR_RANGES["mq2_voltage"]), 3)
    gas_ppm     = round(random.uniform(*SENSOR_RANGES["gas_ppm"]), 2)

    anomaly_type: Optional[str] = None

    # Weighted random anomaly injection
    event = random.choices(
        ["normal", "gas_spike", "pressure_drop", "temp_spike"],
        weights=_ANOMALY_WEIGHTS,
        k=1,
    )[0]

    if event == "gas_spike":
        gas_ppm      = round(random.uniform(260.0, 500.0), 2)
        mq2_voltage  = round(min(2.5, mq2_voltage + random.uniform(0.3, 0.8)), 3)
        anomaly_type = "gas_spike"

    elif event == "pressure_drop":
        drop      = round(random.uniform(15.0, 30.0), 2)
        pressure  = round(max(940.0, pressure - drop), 2)
        anomaly_type = "pressure_drop"

    elif event == "temp_spike":
        temperature  = round(random.uniform(43.0, 52.0), 2)
        anomaly_type = "temp_spike"

    reading: Dict[str, Any] = {
        "device_id":   device_id,
        "timestamp":   datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "temperature": temperature,
        "pressure":    pressure,
        "mq2_voltage": mq2_voltage,
        "gas_ppm":     gas_ppm,
    }
    # Attach anomaly metadata so run_simulation can log it clearly
    reading["_anomaly_type"] = anomaly_type
    return reading


def parse_xlsx_readings(xlsx_path: str, device_id: str) -> List[Dict[str, Any]]:
    """Load sensor readings from the sample xlsx file.

    Expected columns (case-insensitive):
        Date, Time, Temperature (C), Pressure (hPa), MQ2 Voltage (V), Gas PPM

    Returns a list of payload dicts ready for POST.
    Requires openpyxl (pip install openpyxl).
    """
    try:
        import openpyxl
    except ImportError:
        logger.error("openpyxl is not installed - run: pip install openpyxl")
        sys.exit(1)

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        logger.error("xlsx file is empty: %s", xlsx_path)
        sys.exit(1)

    # Normalise header names
    raw_headers = [str(h).strip().lower() if h is not None else "" for h in rows[0]]
    col_map: Dict[str, int] = {}
    for idx, h in enumerate(raw_headers):
        if "date"        in h: col_map["date"]        = idx
        if "time"        in h: col_map["time"]        = idx
        if "temperature" in h: col_map["temperature"] = idx
        if "pressure"    in h: col_map["pressure"]    = idx
        if "mq2"         in h: col_map["mq2_voltage"] = idx
        if "gas ppm"     in h: col_map["gas_ppm"]     = idx
        if h == "gas ppm" or "ppm" in h: col_map["gas_ppm"] = idx

    required = {"date", "time", "temperature", "pressure", "mq2_voltage", "gas_ppm"}
    missing  = required - col_map.keys()
    if missing:
        logger.error("xlsx missing required columns: %s  (found: %s)", missing, raw_headers)
        sys.exit(1)

    readings: List[Dict[str, Any]] = []
    for row in rows[1:]:
        if all(row[col_map[k]] is None for k in ("temperature", "pressure")):
            continue  # skip blank rows
        try:
            date_val = row[col_map["date"]]
            time_val = row[col_map["time"]]
            # openpyxl may return datetime objects or strings
            date_str = date_val.strftime("%Y-%m-%d") if hasattr(date_val, "strftime") else str(date_val).split(" ")[0]
            time_str = time_val.strftime("%H:%M:%S") if hasattr(time_val, "strftime") else str(time_val)
            timestamp = f"{date_str}T{time_str}"

            readings.append({
                "device_id":   device_id,
                "timestamp":   timestamp,
                "temperature": float(row[col_map["temperature"]]),
                "pressure":    float(row[col_map["pressure"]]),
                "mq2_voltage": float(row[col_map["mq2_voltage"]]),
                "gas_ppm":     float(row[col_map["gas_ppm"]]),
            })
        except Exception as exc:
            logger.warning("Skipping malformed xlsx row: %s  (%s)", row, exc)

    wb.close()
    logger.info("Loaded %d readings from xlsx: %s", len(readings), xlsx_path)
    return readings

# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers ────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

REQUEST_TIMEOUT_S = 10.0


def _post(base_url: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """POST one reading to /api/data.  Returns parsed JSON on success, None on error."""
    url = f"{base_url}/api/data"
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_S)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        logger.error("Cannot reach backend at %s - is uvicorn running?", base_url)
    except requests.exceptions.Timeout:
        logger.error("Request timed out after %.1fs", REQUEST_TIMEOUT_S)
    except requests.exceptions.HTTPError as exc:
        # Try to surface the validation error detail from FastAPI
        try:
            detail = exc.response.json()
        except Exception:
            detail = exc.response.text
        logger.error("HTTP %d from backend: %s", exc.response.status_code, detail)
    except Exception as exc:
        logger.error("Unexpected POST error: %s", exc)
    return None


def _get(base_url: str, path: str, params: Optional[Dict] = None) -> Optional[Any]:
    """GET an endpoint.  Returns parsed JSON on success, None on error."""
    url = f"{base_url}{path}"
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_S)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        logger.error("Cannot reach %s", url)
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP %d from %s", exc.response.status_code, url)
    except Exception as exc:
        logger.error("Unexpected GET error: %s", exc)
    return None

# ─────────────────────────────────────────────────────────────────────────────
# Simulation loop ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def run_simulation(
    base_url:  str,
    device_id: str,
    count:     int,
    interval:  float,
    readings:  Optional[List[Dict[str, Any]]] = None,
) -> tuple:
    """
    Send *count* sensor readings to the backend spaced *interval* seconds apart.

    Parameters
    ----------
    readings : optional pre-loaded list (from xlsx).  If None, random data
               is generated for each iteration.

    Returns (total_generated, total_stored, anomaly_counts) tuple.
    """
    success_count = 0
    seq = 0  # tracks last iteration in case of early exit
    anomaly_counts: Dict[str, int] = {"gas_spike": 0, "pressure_drop": 0, "temp_spike": 0}
    source = "xlsx replay" if readings else "random generator"
    total = len(readings) if readings else count

    logger.info("=" * 60)
    logger.info("ClimaScope Edge Simulator starting")
    logger.info("  Backend  : %s", base_url)
    logger.info("  Device   : %s", device_id)
    logger.info("  Source   : %s", source)
    logger.info("  Readings : %d", total)
    logger.info("  Interval : %.1f s", interval)
    logger.info("=" * 60)

    for i in range(total):
        seq = i + 1

        # Build payload
        if readings:
            payload = dict(readings[i])
            payload["device_id"] = device_id  # ensure device_id is set
            anomaly_type = None
        else:
            payload = generate_reading(device_id)
            anomaly_type = payload.pop("_anomaly_type", None)

        # Strip internal metadata keys before posting
        post_payload = {k: v for k, v in payload.items() if not k.startswith("_")}

        anomaly_tag = f"  [ANOMALY: {anomaly_type}]" if anomaly_type else ""
        logger.info(
            "[%4d/%d] Sending  ts=%-20s  T=%5.2fC  P=%7.2f hPa  "
            "MQ2=%.3fV  gas=%6.2f ppm%s",
            seq, total,
            post_payload["timestamp"],
            post_payload["temperature"],
            post_payload["pressure"],
            post_payload["mq2_voltage"],
            post_payload["gas_ppm"],
            anomaly_tag,
        )

        if anomaly_type:
            anomaly_counts[anomaly_type] = anomaly_counts.get(anomaly_type, 0) + 1

        result = _post(base_url, post_payload)
        if result:
            logger.info(
                "[%4d/%d] Stored id=%s",
                seq, total, result.get("message", result),
            )
            success_count += 1
        else:
            logger.warning("[%4d/%d] Failed to store reading", seq, total)

        # Wait before next reading (skip wait on last iteration)
        try:
            if i < total - 1 and interval > 0:
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("\nSimulation interrupted by user (Ctrl+C) after %d readings", seq)
            break

    logger.info("-" * 60)
    logger.info(
        "Simulation complete: %d/%d readings ingested successfully",
        success_count, seq,
    )
    return seq, success_count, anomaly_counts

# ─────────────────────────────────────────────────────────────────────────────
# Endpoint verification ───────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def verify_endpoints(base_url: str, device_id: str) -> bool:
    """
    Run a suite of endpoint checks against the live backend.

    Checks
    ------
    1. GET /api/data/latest        - returns a list of ≤ 10 records
    2. GET /api/data/latest?n=5    - honours the n= parameter
    3. GET /api/data/history       - returns total + records
    4. GET /api/data/history?device_id=<device_id>  - filter works
    5. GET /api/data/history?limit=2&offset=0       - pagination works

    Returns True if all checks pass.
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("Running endpoint verification tests ...")
    logger.info("=" * 60)

    passed = 0
    failed = 0

    def check(label: str, condition: bool, extra: str = "") -> None:
        nonlocal passed, failed
        if condition:
            logger.info("  PASS  %s  %s", label, extra)
            passed += 1
        else:
            logger.warning("  FAIL  %s  %s", label, extra)
            failed += 1

    # ── 1. GET /api/data/latest (default n=10) ───────────────────────────────
    data = _get(base_url, "/api/data/latest")
    check(
        "GET /api/data/latest",
        data is not None and isinstance(data, list) and 1 <= len(data) <= 10,
        f"(returned {len(data) if data else 0} records)",
    )
    if data:
        first = data[0]
        check(
            "  > record has expected fields",
            all(k in first for k in ("id", "device_id", "timestamp", "temperature",
                                     "pressure", "mq2_voltage", "gas_ppm")),
            str(list(first.keys())),
        )
        logger.info("  latest reading: ts=%s  T=%.2fC  P=%.2f hPa  "
                    "MQ2=%.3f V  gas=%.2f ppm",
                    first["timestamp"], first["temperature"],
                    first["pressure"],  first["mq2_voltage"],
                    first["gas_ppm"])

    # ── 2. GET /api/data/latest?n=5 ─────────────────────────────────────────
    data5 = _get(base_url, "/api/data/latest", params={"n": 5})
    check(
        "GET /api/data/latest?n=5",
        data5 is not None and isinstance(data5, list) and len(data5) <= 5,
        f"(returned {len(data5) if data5 else 0} records)",
    )

    # ── 3. GET /api/data/history ─────────────────────────────────────────────
    history = _get(base_url, "/api/data/history")
    check(
        "GET /api/data/history",
        history is not None and "total" in history and "records" in history,
        f"(total={history.get('total') if history else '?'})",
    )

    # ── 4. GET /api/data/history?device_id=<device_id> ──────────────────────
    history_filtered = _get(base_url, "/api/data/history",
                            params={"device_id": device_id})
    check(
        f"GET /api/data/history?device_id={device_id}",
        history_filtered is not None and history_filtered.get("total", 0) > 0,
        f"(total={history_filtered.get('total') if history_filtered else '?'})",
    )
    if history_filtered and history_filtered.get("records"):
        ids_match = all(
            r.get("device_id") == device_id
            for r in history_filtered["records"]
        )
        check(
            "  > all returned records match device_id filter",
            ids_match,
        )

    # ── 5. Pagination: limit=2&offset=0 ──────────────────────────────────────
    page = _get(base_url, "/api/data/history", params={"limit": 2, "offset": 0})
    check(
        "GET /api/data/history?limit=2&offset=0",
        page is not None and len(page.get("records", [])) <= 2,
        f"(returned {len(page.get('records', [])) if page else 0} records)",
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    logger.info("-" * 60)
    logger.info(
        "Verification complete: %d passed  |  %d failed",
        passed, failed,
    )
    return failed == 0

# ─────────────────────────────────────────────────────────────────────────────
# CLI ─────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ClimaScope edge device simulator and backend verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("CLIMASCOPE_BACKEND_URL", "http://localhost:8000"),
        metavar="URL",
        help="Backend base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--device_id", "--device",
        dest="device_id",
        default=os.environ.get("CLIMASCOPE_DEVICE_ID", "climascope_sim_001"),
        metavar="DEVICE_ID",
        help="Simulated device identifier (default: climascope_sim_001)",
    )
    parser.add_argument(
        "--count",
        type=int, default=20, metavar="N",
        help="Number of readings to generate (default: 20; use 5000+ for ML training)",
    )
    parser.add_argument(
        "--interval",
        type=float, default=5.0, metavar="SECS",
        help="Seconds between POST requests (default: 5.0; use 0 for bulk generation)",
    )
    parser.add_argument(
        "--xlsx",
        default=None, metavar="PATH",
        help="Replay rows from a sensor_data.xlsx file instead of generating random data",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Skip simulation; run endpoint verification only",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip endpoint verification after simulation",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ── Simulation phase ──────────────────────────────────────────────────────
    total_generated = 0
    total_stored    = 0
    anomaly_summary: Dict[str, int] = {}

    if not args.verify_only:
        readings: Optional[List[Dict[str, Any]]] = None

        if args.xlsx:
            readings = parse_xlsx_readings(args.xlsx, args.device_id)

        try:
            total_generated, total_stored, anomaly_summary = run_simulation(
                base_url=args.url,
                device_id=args.device_id,
                count=args.count,
                interval=args.interval,
                readings=readings,
            )
        except KeyboardInterrupt:
            logger.info("\nInterrupted before first reading was sent.")

    # ── Verification phase ────────────────────────────────────────────────────
    if not args.no_verify:
        all_passed = verify_endpoints(args.url, args.device_id)
        if not all_passed:
            logger.warning(
                "Some verification checks failed - review the output above."
            )
    else:
        logger.info("Endpoint verification skipped (--no-verify)")

    # ── Final summary ─────────────────────────────────────────────────────────
    if not args.verify_only:
        print("")
        print("=" * 50)
        print("  ClimaScope Simulator — Final Summary")
        print("=" * 50)
        print(f"  Device ID            : {args.device_id}")
        print(f"  Total readings generated : {total_generated}")
        print(f"  Total readings stored    : {total_stored}")
        failed = total_generated - total_stored
        print(f"  Failed / not stored      : {failed}")
        if anomaly_summary:
            print("  Anomalies injected:")
            for atype, n in anomaly_summary.items():
                print(f"    {atype:<20s}: {n}")
        print("=" * 50)
        print("")


if __name__ == "__main__":
    main()
