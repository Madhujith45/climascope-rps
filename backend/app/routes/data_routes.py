import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.db.mongo import get_mongo_db
from app.services.alert_service import trigger_alert

router = APIRouter(prefix="/api/data", tags=["data"])

class SensorData(BaseModel):
    device_id: str | None = None
    temperature: float = 0.0
    humidity: float = 0.0
    pressure: float = 0.0
    mq2_voltage: float = 0.0
    gas_ppm: float = 0.0
    gas: float = 0.0
    risk_score: float = 0.0
    level: str | None = None
    anomaly: bool = False

@router.post("")
async def post_data(data: SensorData, background_tasks: BackgroundTasks):
    db = get_mongo_db()
    doc = data.dict()
    doc["timestamp"] = datetime.datetime.utcnow().isoformat()

    await db.sensor_readings.insert_one(doc)

    if data.risk_score > 65 or data.anomaly:
        reason = []
        if data.risk_score > 65:
            reason.append("High risk score detected")
        if data.anomaly:
            reason.append("Anomaly detected in sensor readings")
        reason_str = " + ".join(reason)
        # Assuming trigger_alert requires risk_score string or similar, but the original accepted risk_score float/int, string level, string reason.
        background_tasks.add_task(trigger_alert, data.risk_score, data.level or "Medium", reason_str)

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
