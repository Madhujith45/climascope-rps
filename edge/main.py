import time
import requests
import json
import os
import logging
from processing.risk_engine import RiskEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import mock or real sensors based on existing project structure
import random

# For demonstration if real sensors fail on dev machine:
def read_sensors():
    return {
        "temperature": round(random.uniform(20.0, 35.0), 2),
        "humidity": round(random.uniform(40.0, 70.0), 2),
        "pressure": round(random.uniform(1000.0, 1020.0), 2),
        "gas": round(random.uniform(0.0, 100.0), 2)
    }

def main():
    engine = RiskEngine(window_size=10)
    backend_url = os.getenv("CLIMASCOPE_BACKEND_URL", "https://climascope-rps.onrender.com/api/data")

    logger.info(f"Using backend: {backend_url}")
    print(f"Starting ClimaScope Edge. Sending data to {backend_url} every 3s")

    while True:
        try:
            # 1. Read Sensors
            sensor_data = read_sensors()
            
            # 2. Call risk engine
            risk_result = engine.process(sensor_data)
            
            # 3. Merge Payload
            payload = {
                **sensor_data,
                **risk_result
            }
            
            print(f"Sending: {payload}")
            
            # 4. POST to Backend
            try:
                response = requests.post(backend_url, json=payload, timeout=2)
                if response.status_code == 200:
                    print("  -> Success")
                else:
                    print(f"  -> Failed: {response.status_code}")
            except Exception as e:
                print(f"  -> Post Error: {e}")

        except Exception as e:
            print(f"Loop error: {e}")
            
        time.sleep(3)

if __name__ == "__main__":
    main()