# Auto-Device Creation Implementation

## Overview
The system now automatically creates a "climascope-pi" device when your Raspberry Pi sends telemetry data for the first time. No more manual registration needed!

---

## How It Works

### 1. **Option A: JWT Token Authentication (Recommended for Production)**
Your Pi authenticates with a JWT token from your user account.

```bash
# Send telemetry with JWT Bearer token
curl -X POST http://localhost:8000/api/data \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 28.5,
    "humidity": 65
  }'
```

**What happens:**
- System extracts user from JWT token
- Automatically creates device `climascope-pi` if it doesn't exist
- Updates `last_seen` timestamp on every data arrival
- Stores sensor readings in telemetry collection
- Device status shown as "online" if data received within 45 seconds

### 2. **Option B: Device ID + API Key (Existing Devices)**
If you have pre-registered devices with API keys, use this method:

```bash
curl -X POST http://localhost:8000/api/data \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "climascope-pi",
    "api_key": "YOUR_API_KEY",
    "temperature": 28.5,
    "humidity": 65
  }'
```

---

## Getting Your JWT Token

### Step 1: Signup (if needed)
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password_8char_minimum",
    "full_name": "John Doe",
    "phone": "+919876543210"
  }'
```

### Step 2: Login to Get Token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "user@example.com",
    "password": "secure_password_8char_minimum"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "_id": "507f1f77bcf86cd799439011",
    "email": "user@example.com"
  }
}
```

**Use the `access_token` value in your Pi scripts.**

---

## API Endpoints

### 1. POST /api/data
**Send sensor telemetry data**

**Request:**
```json
{
  "temperature": 28.5,
  "humidity": 65,
  "pressure": 1013.25,
  "gas_ppm": 450,
  "risk_score": 42,
  "level": "NORMAL",
  "anomaly": false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Data processed",
  "device_id": "climascope-pi"
}
```

---

### 2. GET /api/devices
**Retrieve your device information**

**Request:**
```bash
curl -X GET http://localhost:8000/api/devices \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "device_id": "climascope-pi",
  "device_name": "climascope-pi",
  "location": "Default",
  "description": "Auto-created from first telemetry data",
  "created_at": "2026-04-06T10:30:45.123Z",
  "last_seen": "2026-04-06T10:31:20.456Z",
  "is_active": true,
  "status": "online"
}
```

**Status values:**
- `online`: Data received within last 45 seconds
- `slow`: Data received within 5 minutes but older than 45 seconds
- `offline`: No data received in over 5 minutes

---

## Python Example: Raspberry Pi Script

```python
import requests
import time
import json
from datetime import datetime

# Configuration
API_URL = "http://YOUR_SERVER_IP:8000"
JWT_TOKEN = "YOUR_JWT_TOKEN_HERE"

def send_telemetry(temp, humidity, pressure=1013, gas_ppm=0):
    """Send sensor data to backend"""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "temperature": temp,
        "humidity": humidity,
        "pressure": pressure,
        "gas_ppm": gas_ppm,
        "risk_score": 0,
        "level": "NORMAL",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        response = requests.post(f"{API_URL}/api/data", 
                                json=payload, 
                                headers=headers,
                                timeout=10)
        response.raise_for_status()
        print(f"✓ Data sent: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return False


def get_device_status():
    """Check device status"""
    
    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}
    
    try:
        response = requests.get(f"{API_URL}/api/devices",
                               headers=headers,
                               timeout=10)
        response.raise_for_status()
        device = response.json()
        print(f"Device: {device['device_name']}")
        print(f"Status: {device.get('status', 'unknown')}")
        print(f"Last seen: {device.get('last_seen', 'never')}")
        return device
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return None


if __name__ == "__main__":
    # Send data every 60 seconds
    while True:
        print("\n--- Sending telemetry ---")
        send_telemetry(temp=28.5, humidity=65)
        
        print("\n--- Checking device status ---")
        get_device_status()
        
        time.sleep(60)
```

---

## Implementation Details

### What Gets Created
When the first telemetry arrives:

```javascript
{
  user_id: "ObjectId of authenticated user",
  device_id: "climascope-pi",
  device_name: "climascope-pi",
  location: "Default",
  description: "Auto-created from first telemetry data",
  status: "online",
  is_active: true,
  created_at: "2026-04-06T10:30:45.123Z",
  updated_at: "2026-04-06T10:30:45.123Z",
  last_seen: "2026-04-06T10:30:45.123Z"
}
```

### Telemetry Storage
Sensor readings are stored separately in the `sensor_readings` collection:

```javascript
{
  device_id: "climascope-pi",
  timestamp: "2026-04-06T10:30:45.123Z",
  temperature: 28.5,
  humidity: 65,
  pressure: 1013.25,
  gas_ppm: 450,
  risk_score: 42,
  level: "NORMAL",
  anomaly: false
}
```

### Device Update Logic
On every subsequent data arrival:
- `last_seen` timestamp is updated
- `status` is set to "online"
- `updated_at` is refreshed
- Telemetry is stored independently

---

## Frontend Integration

The UI automatically uses this endpoint:

### Devices Page
- Shows connected device named "climascope-pi"
- No longer displays "No devices registered" after first telemetry

### Dashboard
- Device status shows as "Live" when last_seen ≤ 45 seconds
- Shows "Xs ago" for older data
- Shows "Offline" when no data in 45+ seconds

### Analytics
- Data from `climascope-pi` device automatically available
- Charts plot telemetry history by device

---

## Troubleshooting

### Device Not Appearing
1. **Check if data was received:**
   ```bash
   curl -X GET http://localhost:8000/api/data/latest
   ```

2. **Verify JWT token is valid:**
   - Token must be from a valid user account
   - Must include `Authorization: Bearer TOKEN` header

3. **Check MongoDB logs:**
   - Ensure `devices` collection exists
   - Check for indexing on `(user_id, device_id)`

### Device Shows "Offline"
- This is normal if no data received in 45+ seconds
- Pi might be disconnected or not sending data
- Check Pi logs for network/API errors

### Status Not Updating
- Verify `last_seen` field is being updated in MongoDB
- Check that Bearer token is included in requests
- Server might be rejecting requests without auth

---

## Migration from Manual Registration

If you have existing devices registered manually:

1. **Old flow:** Manual device creation + data ingestion
2. **New flow:** Auto-creation on first data + manual creation still supported

**Backward compatible:** Both methods work simultaneously!

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| Device Registration | Manual UI form | Automatic on first telemetry |
| Setup Time | 3 steps | 1 step (send data) |
| UI Empty State | "No devices" on startup | Device appears after first data |
| Device Name | User-defined | "climascope-pi" (automatic) |
| Last Seen | Not tracked | Auto-updated per telemetry |
| Status Indicator | N/A | "Online/Offline/Slow" (automatic) |

---

## Next Steps

1. ✅ Backend implemented with auto-device-creation
2. ✅ GET /api/devices endpoint added
3. ✅ JWT optional auth on POST /api/data
4. 📱 Update Raspberry Pi script to use JWT token
5. 🧪 Test end-to-end: Send data → Device appears → UI shows device

