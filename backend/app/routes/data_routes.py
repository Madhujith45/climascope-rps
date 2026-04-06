import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.utils.security import hash_otp as hash_api_key

from app.db.mongo import get_mongo_db
from app.services.alert_service import trigger_alert

router = APIRouter(prefix="/api/data", tags=["data"])

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

@router.post("")
async def post_data(data: SensorData, background_tasks: BackgroundTasks):
    db = get_mongo_db()
    level = (data.level or data.risk_level or data.risk_local or "").upper()
    anomaly_detected = bool(data.anomaly or data.anomaly_flag)
    score = float(data.risk_score or 0)

    # Best-effort user/device resolution for alert ownership and auth checks.
    owner_user_id = None
    if data.device_id:
        device_doc = await db.devices.find_one({"device_id": data.device_id})
        if device_doc:
            owner_user_id = str(device_doc.get("user_id")) if device_doc.get("user_id") else None
            if data.api_key and device_doc.get("api_key_hash"):
                if hash_api_key(data.api_key) != device_doc.get("api_key_hash"):
                    raise HTTPException(status_code=401, detail="Invalid device credentials")

    doc = data.dict()
    doc.pop("api_key", None)
    doc["risk_score"] = score
    doc["level"] = level or None
    doc["anomaly"] = anomaly_detected
    doc["timestamp"] = data.timestamp or datetime.datetime.utcnow().isoformat()

    await db.sensor_readings.insert_one(doc)

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
            data.device_id,
            owner_user_id,
        )

    return {"status": "success", "message": "Data processed"}

@router.get("/latest")
async def get_latest(n: int = 1):
    db = get_mongo_db()
    cursor = db.sensor_readings.find({}, sort=[("timestamp", -1)]).limit(n)
    docs = await cursor.to_list(length=n)
    for doc in docs:
        doc["_id"] = str(doc["_id"])
        doc["gas_ppm"] = doc.get("gas", doc.get("gas_ppm", 0)) if doc.get("gas", 0) else doc.get("gas_ppm", 0)
        doc["mq2_voltage"] = doc.get("gas", 0) / 100.0 if doc.get("gas", 0) else doc.get("mq2_voltage", 0)
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
        doc["gas_ppm"] = doc.get("gas", doc.get("gas_ppm", 0)) if doc.get("gas", 0) else doc.get("gas_ppm", 0)
        doc["mq2_voltage"] = doc.get("gas", 0) / 100.0 if doc.get("gas", 0) else doc.get("mq2_voltage", 0)
    return {"total": total, "records": docs}
