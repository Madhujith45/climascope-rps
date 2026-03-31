"""
ClimaScope – Backend Data Routes

POST /api/data          – receive a sensor reading from an edge device
GET  /api/data/latest   – return the 10 most recent readings
GET  /api/data/history  – return all stored readings (paginated)
"""

import logging
from typing import List
from datetime import datetime, timedelta
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..auth.auth_routes import get_current_user
from ..db.mongo import get_mongo_db
from ..schemas import SensorDataIn, SensorDataOut, HistoryResponse, StatusResponse
from ..ai.anomaly_detector import detect as ai_detect
from ..utils.security import hash_otp as hash_api_key
from ..utils.rate_limiter import data_limiter, get_client_ip
from ..utils.email import send_alert_email
from ..utils.sms import send_sms_alert
from ..routes.alert_routes import generate_alert

logger = logging.getLogger(__name__)

router = APIRouter(tags=["data"])

ALERT_COOLDOWN_MINUTES = 5


def _coalesce(*values):
    for value in values:
        if value is not None:
            return value
    return None


async def _maybe_generate_threshold_alerts(
    db,
    user_id: str,
    device_id: str,
    temperature: float,
    gas_ppm: float,
):
    """Create temperature/gas alerts with a cooldown to prevent alert spam."""
    if not user_id or user_id == "unknown":
        return

    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = await db.users.find_one({"_id": user_id})
    user_email = user.get("email") if user else None

    now = datetime.utcnow()
    since = now - timedelta(minutes=ALERT_COOLDOWN_MINUTES)

    async def create_if_needed(alert_type: str, severity: str, message: str):
        existing = await db.alerts.find_one({
            "user_id": user_id,
            "device_id": device_id,
            "alert_type": alert_type,
            "is_resolved": False,
            "created_at": {"$gte": since},
        })
        if not existing:
            await generate_alert(user_id, device_id, message, severity, alert_type)
            if user_email:
                send_alert_email(user_email, message)
            send_sms_alert(message)

    if temperature > 45:
        await create_if_needed(
            "HIGH_TEMPERATURE",
            "danger",
            f"High temperature detected ({temperature:.1f} C) on device {device_id}",
        )

    if gas_ppm > 250:
        await create_if_needed(
            "GAS_LEAK",
            "danger",
            f"Gas level critical ({gas_ppm:.1f} ppm) on device {device_id}",
        )


@router.post("/api/data", response_model=StatusResponse, status_code=201)
async def ingest_reading(
    payload: SensorDataIn,
    request: Request,
):
    """
    Receive one sensor reading from an edge device and persist it.

    Required fields: device_id, timestamp, temperature, pressure,
                     mq2_voltage, gas_ppm
    Optional fields: humidity, risk_score, risk_level, anomaly_flag,
                     risk_reason, api_key

    **Device Authentication:**
    If the device has an API key stored (api_key_hash in the device record),
    the request must include a matching `api_key` field. Legacy devices
    without a stored hash are still accepted for backward compatibility.
    """
    # ── Rate limiting ────────────────────────────────────────────────────
    client_ip = get_client_ip(request)
    data_limiter.check_and_record(client_ip)

    # ── Device authentication via API key ────────────────────────────────
    db = get_mongo_db()
    device_record = await db.devices.find_one({"device_id": payload.device_id})

    if device_record and device_record.get("api_key_hash"):
        # Device has an API key configured — validate it
        if not payload.api_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key required for this device",
            )
        if hash_api_key(payload.api_key) != device_record["api_key_hash"]:
            logger.warning(
                "Invalid API key for device=%s from ip=%s",
                payload.device_id, client_ip,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )

    user_id = device_record["user_id"] if device_record else "unknown"
    # ── AI anomaly detection ─────────────────────────────────────────────────
    is_anomaly, risk_reason = ai_detect(
        temperature = payload.temperature,
        pressure    = payload.pressure,
        gas_ppm     = payload.gas_ppm,
        mq2_voltage = payload.mq2_voltage,
    )
    # Edge-supplied flag takes precedence if already set to True
    # Cast to native Python types — numpy.bool_ is not BSON-serializable
    final_anomaly_flag = bool(payload.anomaly_flag or is_anomaly)
    final_risk_reason  = str(risk_reason) if risk_reason else (payload.risk_reason or None)

    if is_anomaly:
        logger.warning(
            "ANOMALY  device=%s  ts=%s  T=%.2f  P=%.2f  gas=%.2f ppm  reason=%s",
            payload.device_id, payload.timestamp,
            payload.temperature, payload.pressure, payload.gas_ppm,
            final_risk_reason,
        )


    record = {
        "user_id": user_id,
        "device_id": str(payload.device_id),
        "timestamp": datetime.fromisoformat(payload.timestamp),
        "temperature": float(payload.temperature),
        "pressure": float(payload.pressure),
        "mq2_voltage": float(payload.mq2_voltage),
        "gas_ppm": float(payload.gas_ppm),
        "humidity": float(payload.humidity) if payload.humidity is not None else None,
        "gas": float(payload.gas_ppm),
        "risk_score": int(payload.risk_score) if payload.risk_score is not None else None,
        "risk_level": str(payload.risk_level) if payload.risk_level else None,
        "risk_local": str(payload.risk_local) if payload.risk_local else None,
        "anomaly_flag": final_anomaly_flag,
        "risk_reason": final_risk_reason,
    }
    
    result = await db.sensor_data.insert_one(record)
    
    # Update device last_seen
    if user_id != "unknown":
        await db.devices.update_one(
            {"device_id": payload.device_id},
            {"$set": {"last_seen": datetime.utcnow()}}
        )

    await _maybe_generate_threshold_alerts(
        db=db,
        user_id=user_id,
        device_id=payload.device_id,
        temperature=float(payload.temperature),
        gas_ppm=float(payload.gas_ppm),
    )

    logger.info(
        "Ingested reading id=%s  device=%s  ts=%s",
        str(result.inserted_id), payload.device_id, payload.timestamp,
    )
    return StatusResponse(status="ok", message=f"Reading stored with id={str(result.inserted_id)}")


def _normalize_record(doc: dict) -> dict:
    """Normalize a MongoDB sensor document to match SensorDataOut schema.

    Records can originate from two sources with different field names:
      - data_routes (POST /api/data): uses anomaly_flag, mq2_voltage, risk_score, etc.
      - prediction_routes (POST /api/predict): uses anomaly, gas_voltage, health_score, etc.

    This helper unifies them so Pydantic serialization never fails.
    """
    gas_ppm = _coalesce(doc.get("gas_ppm"), doc.get("gas"), 0)
    gas_value = _coalesce(doc.get("gas"), doc.get("gas_ppm"), 0)
    mq2_voltage = _coalesce(doc.get("mq2_voltage"), doc.get("gas_voltage"), 0)

    record = {
        "id":           str(doc["_id"]),
        "device_id":    doc.get("device_id"),
        "timestamp":    doc["timestamp"].isoformat() if isinstance(doc.get("timestamp"), datetime) else str(doc.get("timestamp", "")),
        "temperature":  float(doc.get("temperature", 0)),
        "pressure":     float(doc.get("pressure", 0)),
        "mq2_voltage":  float(mq2_voltage),
        "gas_ppm":      float(gas_ppm),
        "humidity":     float(doc["humidity"]) if doc.get("humidity") is not None else None,
        "gas":          float(gas_value),
        "risk_score":   int(doc.get("risk_score") or doc.get("health_score") or 0),
        "risk_level":   doc.get("risk_level") or doc.get("status", "SAFE"),
        "risk_local":   doc.get("risk_local"),
        "anomaly_flag": bool(doc.get("anomaly_flag", doc.get("anomaly", False))),
        "risk_reason":  doc.get("risk_reason"),
    }
    return record


@router.get("/api/data/latest", response_model=List[SensorDataOut])
async def get_latest(
    n: int = Query(default=10, ge=1, le=100, description="Number of latest records to return"),
    device_id: str = Query(default=None, description="Filter by device_id"),
    current_user: dict = Depends(get_current_user)
):
    """Return the *n* most recent sensor readings from MongoDB, newest first."""
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Build query
        query = {"user_id": user_id}
        if device_id:
            query["device_id"] = device_id
        
        # Fetch from MongoDB
        cursor = db.sensor_data.find(query).sort("timestamp", -1).limit(n)
        records = []
        async for doc in cursor:
            records.append(_normalize_record(doc))
            
        return records
    except Exception as e:
        logger.error(f"Get latest data error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest data")


@router.get("/api/data/history", response_model=HistoryResponse)
async def get_history(
    limit: int  = Query(default=1000, ge=1, le=10000, description="Max records per page"),
    offset: int = Query(default=0,    ge=0,           description="Pagination offset"),
    device_id: str = Query(default=None,               description="Filter by device_id"),
    current_user: dict = Depends(get_current_user)
):
    """Return all stored sensor readings for the user from MongoDB, newest first."""
    try:
        db = get_mongo_db()
        user_id = str(current_user["_id"])
        
        # Build query
        query = {"user_id": user_id}
        if device_id:
            query["device_id"] = device_id
            
        # Total count
        total = await db.sensor_data.count_documents(query)
        
        # Fetch records
        cursor = db.sensor_data.find(query).sort("timestamp", -1).skip(offset).limit(limit)
        records = []
        async for doc in cursor:
            records.append(_normalize_record(doc))
            
        return HistoryResponse(total=total, records=records)
    except Exception as e:
        logger.error(f"Get history data error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch history data")
