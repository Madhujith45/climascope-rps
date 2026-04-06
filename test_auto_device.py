#!/usr/bin/env python3
"""
Quick test script to send telemetry and trigger auto-device-creation
Run this after logging in to get your JWT token
"""

import requests
import json
from datetime import datetime

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# Your API server URL
API_URL = "http://localhost:8000"

# Get this from login response
JWT_TOKEN = "your_jwt_token_here"  # Replace with actual token from login

# ============================================================================
# STEP 1: Get JWT Token (if you don't have one)
# ============================================================================

def login(email: str, password: str):
    """Login and get JWT token"""
    url = f"{API_URL}/auth/login"
    payload = {
        "identifier": email,
        "password": password
    }
    
    print(f"🔐 Logging in as {email}...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✓ Login successful!")
        print(f"✓ JWT Token: {token[:50]}...")
        return token
    else:
        print(f"✗ Login failed: {response.text}")
        return None


# ============================================================================
# STEP 2: Send Telemetry Data
# ============================================================================

def send_telemetry(token: str, temp: float = 28.5, humidity: float = 65):
    """Send sensor telemetry - this triggers device auto-creation"""
    url = f"{API_URL}/api/data"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "temperature": temp,
        "humidity": humidity,
        "pressure": 1013.25,
        "gas_ppm": 450,
        "risk_score": 42,
        "level": "NORMAL",
        "anomaly": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"\n📡 Sending telemetry data...")
    print(f"   Temperature: {temp}°C")
    print(f"   Humidity: {humidity}%")
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Telemetry sent successfully!")
        print(f"✓ Response: {json.dumps(data, indent=2)}")
        return True
    else:
        print(f"✗ Failed to send telemetry: {response.text}")
        return False


# ============================================================================
# STEP 3: Check Device Created
# ============================================================================

def get_device(token: str):
    """Fetch your device info"""
    url = f"{API_URL}/api/devices"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔍 Checking for device...")
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        device = response.json()
        print(f"✓ Device found!")
        print(f"   Device ID: {device.get('device_id')}")
        print(f"   Name: {device.get('device_name')}")
        print(f"   Status: {device.get('status', 'unknown').upper()}")
        print(f"   Last Seen: {device.get('last_seen')}")
        print(f"   Active: {device.get('is_active')}")
        return device
    elif response.status_code == 404:
        print(f"✗ Device not found - send telemetry first!")
        return None
    else:
        print(f"✗ Error: {response.text}")
        return None


# ============================================================================
# MAIN TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ClimaScope Auto-Device Creation Test")
    print("=" * 70)
    
    # Option A: If you already have a JWT token
    if JWT_TOKEN != "your_jwt_token_here":
        token = JWT_TOKEN
        print(f"\n✓ Using provided JWT token")
    else:
        # Option B: Login to get token
        print("\n1️⃣  LOGIN STEP")
        email = input("Enter your email: ")
        password = input("Enter your password: ")
        token = login(email, password)
        
        if not token:
            print("\n❌ Login failed. Exiting.")
            exit(1)
    
    # Send telemetry (this creates the device)
    print("\n2️⃣  SEND TELEMETRY (triggers auto-device-creation)")
    success = send_telemetry(token, temp=28.5, humidity=65)
    
    if not success:
        print("\n❌ Failed to send telemetry. Exiting.")
        exit(1)
    
    # Check device
    print("\n3️⃣  CHECK DEVICE")
    device = get_device(token)
    
    if device:
        print("\n✅ SUCCESS! Device auto-created!")
        print("\n📋 Next steps:")
        print("   1. Refresh your browser")
        print("   2. Go to Dashboard → Connected Devices")
        print("   3. Device 'climascope-pi' should appear with status 'ONLINE'")
        print("   4. Go to Hardware Nodes page to see full device details")
    else:
        print("\n❌ Device wasn't created")
        print("   Check backend logs for errors")

    print("\n" + "=" * 70)
