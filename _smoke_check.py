import requests, uuid
from datetime import datetime

base = "http://localhost:8000"
email = f"smoke_{uuid.uuid4().hex[:8]}@climascope.io"
password = "SecurePass123!"

s = requests.Session()

signup = s.post(f"{base}/auth/signup", json={
    "email": email,
    "password": password,
    "name": "Smoke User"
}, timeout=15)
print("signup", signup.status_code)

login = s.post(f"{base}/auth/login", json={
    "email": email,
    "password": password
}, timeout=15)
print("login", login.status_code)
login.raise_for_status()
token = login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

dev = s.post(f"{base}/devices/add", json={
    "device_name": "Smoke Device",
    "location": "Lab",
    "description": "smoke"
}, headers=headers, timeout=15)
print("device", dev.status_code)
dev.raise_for_status()
dj = dev.json()

ingest = s.post(f"{base}/api/data", json={
    "device_id": dj["device_id"],
    "timestamp": datetime.utcnow().isoformat(),
    "temperature": 49.2,
    "humidity": 60,
    "pressure": 1009.5,
    "mq2_voltage": 2.1,
    "gas_ppm": 320.0,
    "risk_local": "HIGH",
    "api_key": dj["api_key"]
}, timeout=15)
print("ingest", ingest.status_code, ingest.json())

a = s.get(f"{base}/alerts/?limit=10", headers=headers, timeout=15)
print("alerts", a.status_code)
a.raise_for_status()
alerts = a.json().get("alerts", [])
print("alerts_count", len(alerts))
print("alert_types", [x.get("alert_type") for x in alerts[:5]])

latest = s.get(f"{base}/api/data/latest?n=1", headers=headers, timeout=15)
print("latest", latest.status_code)
latest.raise_for_status()
rec = latest.json()[0] if latest.json() else {}
print("latest_gas_ppm", rec.get("gas_ppm"))
print("latest_risk_local", rec.get("risk_local"))
