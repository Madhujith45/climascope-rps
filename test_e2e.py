#!/usr/bin/env python3
"""End-to-end ClimaScope test: Auth -> Device -> Data -> Alerts"""
import asyncio
import httpx
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        print("\n" + "="*70)
        print("CLIMASCOPE END-TO-END FLOW TEST")
        print("="*70)
        
        # Use unique email per test run
        ts = int(time.time() * 1000) % 1000000
        test_email = f"test{ts}@climascope.io"
        
        # Step 1: Signup
        print("\n[1] SIGNUP")
        signup_data = {
            "email": test_email,
            "password": "SecurePass123!",
            "full_name": "Test User"
        }
        
        resp = await client.post(f"{BASE_URL}/auth/signup", json=signup_data)
        print(f"Status: {resp.status_code}")
        if resp.status_code not in [200, 201]:
            print(f"Error: {resp.text}")
            return
        print("Success - User created")
        
        # Step 2: Login
        print("\n[2] LOGIN")
        login_data = {
            "email": test_email,
            "password": "SecurePass123!"
        }
        
        resp = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error: {resp.text}")
            return
        
        result = resp.json()
        token = result.get("access_token")
        print(f"Success - Token: {token[:20]}...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Create Device
        print("\n[3] CREATE DEVICE")
        device_data = {
                "device_name": "Living Room Sensor",
            "description": "Test sensor",
            "location": "Living Room"
        }
        
        resp = await client.post(
            f"{BASE_URL}/devices/add",
            json=device_data,
            headers=headers
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code != 201:
            print(f"Error: {resp.text}")
            return
        
        device = resp.json()
        device_id = device.get("device_id")
        api_key = device.get("api_key")
        print(f"Success - Device ID: {device_id}")
        print(f"API Key: {api_key[:15]}..." if api_key else "No API key returned")
        
        # Step 4: Ingest Safe Data
        print("\n[4] INGEST SAFE SENSOR DATA")
        sensor_data = {
            "device_id": device_id,
            "api_key": api_key,
            "timestamp": datetime.now().isoformat(),
            "temperature": 22.5,
            "pressure": 1013.25,
            "mq2_voltage": 0.5,
            "gas_ppm": 50,
            "humidity": 45.0,
        }
        
        resp = await client.post(
            f"{BASE_URL}/api/data",
            json=sensor_data,
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code not in [200, 201]:
            print(f"Error: {resp.text}")
        else:
            print("Success - Data ingested")
        
        # Step 5: Ingest Alert-Level Data
        print("\n[5] INGEST HIGH TEMPERATURE DATA (ALERT)")
        sensor_data = {
            "device_id": device_id,
            "api_key": api_key,
            "timestamp": datetime.now().isoformat(),
            "temperature": 48.0,
            "pressure": 1010.0,
            "mq2_voltage": 3.5,
            "gas_ppm": 280,
            "humidity": 35.0,
        }
        
        resp = await client.post(
            f"{BASE_URL}/api/data",
            json=sensor_data,
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code not in [200, 201]:
            print(f"Error: {resp.text}")
        else:
            print("Success - Alert data ingested")
        
        # Step 6: Fetch Latest Data
        print("\n[6] FETCH LATEST DATA")
        resp = await client.get(
            f"{BASE_URL}/api/data/latest",
            headers=headers
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                latest = data[0]
                print(f"Latest: Temp={latest.get('temperature')}C, Gas={latest.get('gas_index')}")
            else:
                print(f"Response: {data}")
        else:
            print(f"Error: {resp.text}")
        
        # Step 7: Fetch Alerts
        print("\n[7] FETCH ALERTS")
        resp = await client.get(f"{BASE_URL}/alerts/", headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            alerts = resp.json()
            if isinstance(alerts, list):
                print(f"Total alerts: {len(alerts)}")
                for alert in alerts[:2]:
                    alert_type = alert.get("alert_type", alert.get("type", "UNKNOWN"))
                    status_val = alert.get("status", "N/A")
                    print(f"  - Type: {alert_type}, Status: {status_val}")
            else:
                print(f"Response: {alerts}")
        else:
            print(f"Error: {resp.text}")
        
        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)
        print(f"\nTest credentials:")
        print(f"  Email: {test_email}")
        print(f"  Password: SecurePass123!")
        print(f"\nDevice info:")
        print(f"  Device ID: {device_id}")
        print(f"  API Key: {api_key}")
        print(f"\nOpen http://localhost:5174 to view dashboard")

if __name__ == "__main__":
    asyncio.run(main())
