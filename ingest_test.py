import asyncio
import motor.motor_asyncio
import uuid
from datetime import datetime
import random

async def ingest():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.climascope
    
    # Get all users
    users = await db.users.find().to_list(10)
    if not users:
        print("No users found")
        return
        
    for user in users:
        user_id = str(user["_id"])
        email = user["email"]
        
        # Get devices for this user
        devices = await db.devices.find({"user_id": user_id}).to_list(10)
        if not devices:
            print(f"No devices for user {email}")
            continue
            
        for device in devices:
            device_id = device["device_id"]
            
            # Ingest a sensor reading
            # In reality, the prediction endpoint also ingests sensor data
            # So I'll just use the prediction endpoint!
            # (Wait, simulation of sensor input)
            
            reading = {
                "user_id": user_id,
                "device_id": device_id,
                "temperature": 25.0 + random.uniform(-2, 2),
                "humidity": 60.0 + random.uniform(-5, 5),
                "pressure": 1013.0 + random.uniform(-2, 2),
                "gas_voltage": 1.5 + random.uniform(-0.1, 0.1),
                "gas_ppm": 200.0 + random.uniform(-10, 10),
                "timestamp": datetime.utcnow()
            }
            
            # Prediction and storage
            # (Simulating what prediction_routes does)
            reading["prediction"] = reading["temperature"] + 0.5
            reading["health_score"] = random.randint(70, 95)
            reading["status"] = "normal"
            reading["anomaly"] = False
            reading["anomaly_score"] = random.uniform(-0.2, 0.2)
            
            await db.sensor_data.insert_one(reading)
            await db.devices.update_one(
                {"device_id": device_id},
                {"$set": {"last_seen": datetime.utcnow()}}
            )
            print(f"Ingested for {email} / {device_id}")

if __name__ == "__main__":
    asyncio.run(ingest())
