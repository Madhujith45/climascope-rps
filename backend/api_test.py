"""Quick API validation script for ClimaScope backend."""
import requests
from datetime import datetime

BASE = "http://127.0.0.1:8000"

def test_all():
    print("=" * 60)
    print("ClimaScope API Validation")
    print("=" * 60)

    # 1. Health
    r = requests.get(f"{BASE}/")
    print(f"\n[1] HEALTH CHECK: {r.status_code} -> {r.json()['status']}")

    # 2. Login
    r = requests.post(f"{BASE}/auth/login", json={
        "email": "testx2@climascope.io",
        "password": "testpass123"
    })
    print(f"[2] LOGIN: {r.status_code}")
    if r.status_code != 200:
        print("   Login failed, trying signup first...")
        rs = requests.post(f"{BASE}/auth/signup", json={
            "email": "testx2@climascope.io",
            "password": "testpass123",
            "full_name": "Test User"
        })
        print(f"   SIGNUP: {rs.status_code}")
        r = requests.post(f"{BASE}/auth/login", json={
            "email": "testx2@climascope.io",
            "password": "testpass123"
        })
        print(f"   LOGIN retry: {r.status_code}")

    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Devices
    r = requests.get(f"{BASE}/devices/list", headers=headers)
    devs = r.json().get("devices", [])
    print(f"[3] DEVICES LIST: {r.status_code} -> {len(devs)} device(s)")

    if not devs:
        rd = requests.post(f"{BASE}/devices/add", json={
            "device_name": "Test Pi",
            "location": "Lab",
            "description": "Test node"
        }, headers=headers)
        print(f"   ADD DEVICE: {rd.status_code}")
        devs = [rd.json()] if rd.status_code == 201 else []

    device_id = devs[0]["device_id"] if devs else "dev_001"
    print(f"   Using device: {device_id}")

    # 4. POST sensor data
    payload = {
        "device_id": device_id,
        "timestamp": datetime.now().isoformat(),
        "temperature": 28.5,
        "pressure": 1013.25,
        "mq2_voltage": 1.2,
        "gas_ppm": 120.5,
        "humidity": 65.0,
        "risk_score": 25,
        "risk_level": "SAFE",
        "anomaly_flag": False
    }
    r = requests.post(f"{BASE}/api/data", json=payload)
    print(f"[4] POST /api/data: {r.status_code} -> {r.json()}")

    # 5. GET latest
    r = requests.get(f"{BASE}/api/data/latest", headers=headers)
    count = len(r.json()) if r.status_code == 200 else "ERROR"
    print(f"[5] GET /api/data/latest: {r.status_code} -> {count} record(s)")

    # 6. GET history
    r = requests.get(f"{BASE}/api/data/history", headers=headers)
    total = r.json().get("total") if r.status_code == 200 else "ERROR"
    print(f"[6] GET /api/data/history: {r.status_code} -> total={total}")

    # 7. GET alerts
    r = requests.get(f"{BASE}/alerts/", headers=headers)
    alert_data = r.json() if r.status_code == 200 else {}
    print(f"[7] GET /alerts/: {r.status_code} -> {alert_data.get('total', 'ERROR')} alert(s)")

    # 8. Model status
    r = requests.get(f"{BASE}/api/predict/status")
    loaded = r.json().get("model_loaded") if r.status_code == 200 else "ERROR"
    print(f"[8] MODEL STATUS: {r.status_code} -> loaded={loaded}")

    # 9. POST anomalous data (should trigger alert via predict)
    print(f"\n[9] POST anomalous data to /api/predict...")
    r = requests.post(f"{BASE}/api/predict", json={
        "temperature": 55.0,
        "humidity": 95.0,
        "pressure": 950.0,
        "gas_voltage": 4.5,
        "gas_ppm": 500.0,
        "device_id": device_id
    }, headers=headers)
    if r.status_code == 200:
        pred = r.json()
        print(f"   Status: {pred['status']}, Anomaly: {pred['anomaly']}, Health: {pred['health_score']}")
    else:
        print(f"   Status: {r.status_code}, Error: {r.text[:200]}")

    # 10. Re-check alerts after anomaly
    r = requests.get(f"{BASE}/alerts/", headers=headers)
    alert_data = r.json() if r.status_code == 200 else {}
    print(f"[10] ALERTS after anomaly: {alert_data.get('total', 'ERROR')} alert(s), unread={alert_data.get('unread_count', '?')}")

    print("\n" + "=" * 60)
    print("API VALIDATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_all()
