import datetime
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from pydantic import BaseModel, Field
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.utils.security import hash_otp as hash_api_key
from app.auth.jwt_handler import verify_token
from app.db.mongo import get_mongo_db
from app.services.alert_service import trigger_alert
from bson import ObjectId

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/data", tags=["data"])
security = HTTPBearer(auto_error=False)

class SensorData(BaseModel):
    device_id: str | None = None
    api_key: str | None = None
    timestamp: str | None = None
    temperature: float = 0.0
    humidity: float = 0.0
    pressure: float = 0.0
    mq2_voltage: float = 0.0
    gas_ppm: float = 0.0
    gas: float = 0.0
    risk_score: float = 0.0
    level: str | None = None
    risk_level: str | None = None
    risk_local: str | None = None
    anomaly: bool = False
    anomaly_flag: bool = False
    risk_reason: str | None = None


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user from optional JWT bearer token"""
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id:
            db = get_mongo_db()
            user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                return {"_id": str(user_doc["_id"]), "email": user_doc.get("email")}
    except Exception as e:
        logger.debug(f"Optional auth token verification failed: {str(e)}")
    return None


async def ensure_device_for_user(db, user_id: str | None, device_id: str):
    """
    Auto-create or update a single device record for the current telemetry source.
    Returns device_id of the device.
    """
    now = datetime.datetime.utcnow()

    device_filter = {"device_id": device_id, "user_id": user_id}
    existing_device = await db.devices.find_one(device_filter)

    if existing_device:
        await db.devices.update_one(
            {"_id": existing_device["_id"]},
            {
                "$set": {
                    "last_seen": now,
                    "updated_at": now,
                    "is_active": True,
                    "status": "online",
                    "device_name": existing_device.get("device_name") or device_id,
                }
            }
        )
        logger.debug("Updated device %s for user %s", device_id, user_id)
    else:
        await db.devices.insert_one({
            "user_id": user_id,
            "device_id": device_id,
            "device_name": device_id,
            "location": "Default",
            "description": "Auto-created from first telemetry data",
            "status": "online",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "last_seen": now,
        })
        logger.info("Auto-created device %s for user %s", device_id, user_id)

    return device_id


@router.post("")
async def post_data(data: SensorData, background_tasks: BackgroundTasks, current_user: dict = Depends(get_optional_user)):
    db = get_mongo_db()
    current_time = datetime.datetime.utcnow()
    level = (data.level or data.risk_level or data.risk_local or "").upper()
    anomaly_detected = bool(data.anomaly or data.anomaly_flag)
    score = float(data.risk_score or 0)

    # Best-effort user/device resolution for alert ownership and auth checks.
    owner_user_id = None
    device_id_to_use = data.device_id or "climascope-pi001"
    
    # Priority 1: JWT-authenticated user (auto-create or update device)
    if current_user:
        owner_user_id = str(current_user.get("_id"))
        device_id_to_use = data.device_id or "climascope-pi001"
        device_id_to_use = await ensure_device_for_user(db, owner_user_id, device_id_to_use)
    # Priority 2: Device ID + API key (existing device auth)
    elif data.device_id:
        device_doc = await db.devices.find_one({"device_id": data.device_id})
        if device_doc:
            owner_user_id = str(device_doc.get("user_id")) if device_doc.get("user_id") else None
            if data.api_key and device_doc.get("api_key_hash"):
                if hash_api_key(data.api_key) != device_doc.get("api_key_hash"):
                    raise HTTPException(status_code=401, detail="Invalid device credentials")
    else:
        # No auth provided - still accept data for sensors and create a default device record.
        logger.warning("Data received without authentication (device_id or JWT token)")
        device_id_to_use = "climascope-pi001"
        await ensure_device_for_user(db, None, device_id_to_use)

    # If we have a device ID but no stored record yet, create/update it now.
    if not current_user and data.device_id:
        await ensure_device_for_user(db, owner_user_id, data.device_id)

    raw_data = data.dict()
    raw_data.pop("api_key", None)
    raw_data["timestamp"] = current_time

    document = {
        "device_id": raw_data.get("device_id") or device_id_to_use or "unknown_device",
        "user_id": owner_user_id,
        "timestamp": current_time,
        "raw": {
            "temperature": raw_data.get("temperature"),
            "humidity": raw_data.get("humidity"),
            "pressure": raw_data.get("pressure"),
            "gas": raw_data.get("gas"),
        },
        "processed": {
            "gas_ppm": raw_data.get("gas_ppm") or raw_data.get("gas"),
            "risk_score": score,
            "level": level or None,
            "anomaly": anomaly_detected,
            "prediction": raw_data.get("prediction"),
        },
    }

    await db.sensor_readings.insert_one(document)

    # Keep device heartbeat authoritative for online/offline UI.
    await db.devices.update_one(
        {"device_id": document["device_id"]},
        {
            "$set": {
                "last_seen": current_time,
                "status": "online",
                "updated_at": current_time,
            },
            "$setOnInsert": {
                "user_id": owner_user_id,
                "device_name": document["device_id"],
                "location": "Default",
                "description": "Auto-created from telemetry heartbeat",
                "is_active": True,
                "created_at": current_time,
            },
        },
        upsert=True,
    )

    if score > 65 or anomaly_detected or level == "HIGH":
        reason = []
        if score > 65:
            reason.append("High risk score detected")
        if level == "HIGH":
            reason.append("High risk level reported")
        if anomaly_detected:
            reason.append("Anomaly detected in sensor readings")
        reason_str = data.risk_reason or " + ".join(reason)
        reason_lower = str(reason_str).lower()
        if (anomaly_detected or level == "HIGH") and ("stable" in reason_lower or "normal range" in reason_lower):
            reason_str = "Anomaly detected in live sensor pattern. Please inspect device and surroundings."
        background_tasks.add_task(
            trigger_alert,
            score,
            level or "MEDIUM",
            reason_str,
            device_id_to_use,
            owner_user_id,
        )

    return {"status": "success", "message": "Data processed", "device_id": device_id_to_use}

@router.get("/latest")
async def get_latest(n: int = 1, device_id: str | None = None):
    db = get_mongo_db()
    query = {}
    if device_id:
        query["device_id"] = device_id
    cursor = db.sensor_readings.find(query, sort=[("timestamp", -1), ("_id", -1)]).limit(n)
    docs = await cursor.to_list(length=n)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        raw = doc.get("raw") or {}
        processed = doc.get("processed") or {}
        if not raw:
            raw = {
                "temperature": doc.get("temperature"),
                "humidity": doc.get("humidity"),
                "pressure": doc.get("pressure"),
                "gas": doc.get("gas"),
            }
            doc["raw"] = raw
        if not processed:
            processed = {
                "gas_ppm": doc.get("gas_ppm", raw.get("gas")),
                "risk_score": doc.get("risk_score"),
                "level": doc.get("level") or doc.get("risk_level") or doc.get("risk_local"),
                "anomaly": bool(doc.get("anomaly") or doc.get("anomaly_flag")),
                "prediction": doc.get("prediction"),
            }
            doc["processed"] = processed
        gas_value = raw.get("gas", doc.get("gas", 0))
        doc["gas_ppm"] = processed.get("gas_ppm", doc.get("gas_ppm", gas_value if gas_value else 0))
        doc["mq2_voltage"] = (gas_value / 100.0) if gas_value else doc.get("mq2_voltage", 0)
    return docs

@router.get("/history")
async def get_history(limit: int = 50, offset: int = 0, device_id: str | None = None):
    db = get_mongo_db()
    query = {}
    if device_id:
        query["device_id"] = device_id
    total = await db.sensor_readings.count_documents(query)
    cursor = db.sensor_readings.find(query, sort=[("timestamp", -1)]).skip(offset).limit(limit)
    docs = await cursor.to_list(length=limit)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        raw = doc.get("raw", {})
        processed = doc.get("processed", {})
        gas_value = raw.get("gas", doc.get("gas", 0))
        doc["gas_ppm"] = processed.get("gas_ppm", doc.get("gas_ppm", gas_value if gas_value else 0))
        doc["mq2_voltage"] = (gas_value / 100.0) if gas_value else doc.get("mq2_voltage", 0)
    return {"total": total, "records": docs}
