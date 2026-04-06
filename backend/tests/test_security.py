"""
ClimaScope - Security & Auth Integration Tests
================================================
Tests the complete security upgrade:
  1. OTP password reset flow (forgot -> verify -> reset)
  2. Device API key authentication
  3. Rate limiting
  4. Existing auth (signup, login, protected endpoints)

Requires the backend to be running at http://localhost:8000.
Run:  venv\\Scripts\\python.exe -m pytest tests\\test_security.py -v
"""

import time
import requests
import pytest
from datetime import datetime, timezone

BASE = "http://127.0.0.1:8000"
TIMEOUT = 10


# Helpers

def _signup(email, password="testpass123", name="Test"):
    return requests.post(f"{BASE}/auth/signup", json={
        "email": email, "password": password, "full_name": name,
    }, timeout=TIMEOUT)


def _login(email, password="testpass123"):
    r = requests.post(f"{BASE}/auth/login", json={
        "email": email, "password": password,
    }, timeout=TIMEOUT)
    if r.status_code == 200:
        token = r.json()["access_token"]
        return r, token, {"Authorization": f"Bearer {token}"}
    return r, None, {}


def _unique_email():
    ts = int(time.time() * 1000)
    return f"sectest_{ts}@example.com"


# ============ TASK 1: OTP Password Reset Flow ============

class TestA_OTPPasswordReset:

    def test_forgot_password_existing_user(self):
        email = _unique_email()
        _signup(email)
        r = requests.post(f"{BASE}/auth/forgot-password",
                          json={"email": email}, timeout=TIMEOUT)
        assert r.status_code == 200
        assert "message" in r.json()

    def test_forgot_password_nonexistent_email(self):
        r = requests.post(f"{BASE}/auth/forgot-password",
                          json={"email": "nobody@example.com"}, timeout=TIMEOUT)
        assert r.status_code == 200

    def test_verify_otp_wrong_code(self):
        email = _unique_email()
        _signup(email)
        requests.post(f"{BASE}/auth/forgot-password",
                      json={"email": email}, timeout=TIMEOUT)
        r = requests.post(f"{BASE}/auth/verify-otp",
                          json={"email": email, "otp": "000000"}, timeout=TIMEOUT)
        assert r.status_code == 400

    def test_verify_otp_no_request(self):
        r = requests.post(f"{BASE}/auth/verify-otp",
                          json={"email": "nobody@example.com", "otp": "123456"},
                          timeout=TIMEOUT)
        assert r.status_code == 400

    def test_reset_password_invalid_token(self):
        r = requests.post(f"{BASE}/auth/reset-password", json={
            "email": "nobody@example.com",
            "new_password": "newpass1234",
            "reset_token": "fake_token_abc",
        }, timeout=TIMEOUT)
        assert r.status_code == 400

    def test_full_otp_flow_via_db(self):
        """Full flow: forgot -> read OTP from DB -> verify -> reset -> login."""
        from pymongo import MongoClient
        import hashlib
        import os

        email = _unique_email()
        _signup(email, password="oldpass1234")

        r = requests.post(f"{BASE}/auth/forgot-password",
                          json={"email": email}, timeout=TIMEOUT)
        assert r.status_code == 200

        mongo_uri = os.getenv("MONGO_URI")
        assert mongo_uri is not None
        mc = MongoClient(mongo_uri)
        db = mc["climascope"]
        otp_rec = db.otp_records.find_one({"email": email, "used": False})
        assert otp_rec is not None
        stored_hash = otp_rec["otp_hash"]

        found_otp = None
        for i in range(1000000):
            candidate = f"{i:06d}"
            if hashlib.sha256(candidate.encode()).hexdigest() == stored_hash:
                found_otp = candidate
                break
        assert found_otp is not None

        r = requests.post(f"{BASE}/auth/verify-otp",
                          json={"email": email, "otp": found_otp}, timeout=TIMEOUT)
        assert r.status_code == 200
        reset_token = r.json()["reset_token"]

        r = requests.post(f"{BASE}/auth/reset-password", json={
            "email": email,
            "new_password": "newpass5678",
            "reset_token": reset_token,
        }, timeout=TIMEOUT)
        assert r.status_code == 200

        r_old, _, _ = _login(email, "oldpass1234")
        assert r_old.status_code == 401

        r_new, token, _ = _login(email, "newpass5678")
        assert r_new.status_code == 200
        assert token is not None

        db.otp_records.delete_many({"email": email})
        mc.close()


# ============ TASK 2: Device API Key Authentication ============

class TestB_DeviceAPIKey:

    def test_new_device_gets_api_key(self):
        email = _unique_email()
        _signup(email)
        _, _, headers = _login(email)

        r = requests.post(f"{BASE}/devices/add", json={
            "device_name": "API Key Test Device",
            "location": "Lab",
        }, headers=headers, timeout=TIMEOUT)
        assert r.status_code == 201
        data = r.json()
        assert "api_key" in data
        assert data["api_key"].startswith("csk_")

    def test_data_ingestion_with_valid_api_key(self):
        email = _unique_email()
        _signup(email)
        _, _, headers = _login(email)

        r = requests.post(f"{BASE}/devices/add", json={
            "device_name": "Valid Key Device",
        }, headers=headers, timeout=TIMEOUT)
        assert r.status_code == 201
        device_id = r.json()["device_id"]
        api_key = r.json()["api_key"]

        r2 = requests.post(f"{BASE}/api/data", json={
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": 25.0,
            "pressure": 1013.25,
            "mq2_voltage": 1.0,
            "gas_ppm": 100.0,
            "api_key": api_key,
        }, timeout=TIMEOUT)
        assert r2.status_code == 201, f"Expected 201: {r2.text}"

    def test_data_ingestion_with_wrong_api_key(self):
        email = _unique_email()
        _signup(email)
        _, _, headers = _login(email)

        r = requests.post(f"{BASE}/devices/add", json={
            "device_name": "Wrong Key Device",
        }, headers=headers, timeout=TIMEOUT)
        assert r.status_code == 201
        device_id = r.json()["device_id"]

        r2 = requests.post(f"{BASE}/api/data", json={
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": 25.0,
            "pressure": 1013.25,
            "mq2_voltage": 1.0,
            "gas_ppm": 100.0,
            "api_key": "csk_wrong_key_12345",
        }, timeout=TIMEOUT)
        assert r2.status_code == 403

    def test_data_ingestion_without_api_key(self):
        email = _unique_email()
        _signup(email)
        _, _, headers = _login(email)

        r = requests.post(f"{BASE}/devices/add", json={
            "device_name": "No Key Device",
        }, headers=headers, timeout=TIMEOUT)
        assert r.status_code == 201
        device_id = r.json()["device_id"]

        r2 = requests.post(f"{BASE}/api/data", json={
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": 25.0,
            "pressure": 1013.25,
            "mq2_voltage": 1.0,
            "gas_ppm": 100.0,
        }, timeout=TIMEOUT)
        assert r2.status_code == 403

    def test_legacy_device_no_key_required(self):
        r = requests.post(f"{BASE}/api/data", json={
            "device_id": "legacy_device_no_key",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": 25.0,
            "pressure": 1013.25,
            "mq2_voltage": 1.0,
            "gas_ppm": 100.0,
        }, timeout=TIMEOUT)
        assert r.status_code == 201


# ============ TASK 3: Bug Fixes Validation ============

class TestC_BugFixes:

    def test_health_check(self):
        r = requests.get(f"{BASE}/", timeout=TIMEOUT)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_login_returns_json(self):
        email = _unique_email()
        _signup(email)
        r, token, _ = _login(email)
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_invalid_login_returns_json_error(self):
        r = requests.post(f"{BASE}/auth/login", json={
            "email": "nouser@example.com",
            "password": "wrongpass",
        }, timeout=TIMEOUT)
        assert r.status_code == 401
        assert "detail" in r.json()

    def test_data_latest_returns_json(self):
        email = _unique_email()
        _signup(email)
        _, _, headers = _login(email)
        r = requests.get(f"{BASE}/api/data/latest", headers=headers, timeout=TIMEOUT)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_data_history_returns_json(self):
        email = _unique_email()
        _signup(email)
        _, _, headers = _login(email)
        r = requests.get(f"{BASE}/api/data/history", headers=headers, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "records" in data


# ============ Auth Regression Tests ============

class TestD_AuthRegression:

    def test_signup(self):
        email = _unique_email()
        r = _signup(email)
        assert r.status_code == 201
        assert r.json()["email"] == email

    def test_signup_duplicate(self):
        email = _unique_email()
        _signup(email)
        r = _signup(email)
        assert r.status_code == 400

    def test_login(self):
        email = _unique_email()
        _signup(email)
        r, token, _ = _login(email)
        assert r.status_code == 200
        assert token is not None
        assert r.json()["token_type"] == "bearer"

    def test_login_wrong_password(self):
        email = _unique_email()
        _signup(email)
        r, _, _ = _login(email, "wrongpassword")
        assert r.status_code == 401

    def test_me_endpoint(self):
        email = _unique_email()
        _signup(email)
        _, _, headers = _login(email)
        r = requests.get(f"{BASE}/auth/me", headers=headers, timeout=TIMEOUT)
        assert r.status_code == 200
        assert r.json()["email"] == email

    def test_verify_endpoint(self):
        email = _unique_email()
        _signup(email)
        _, _, headers = _login(email)
        r = requests.get(f"{BASE}/auth/verify", headers=headers, timeout=TIMEOUT)
        assert r.status_code == 200
        assert r.json()["valid"] is True

    def test_protected_endpoint_without_token(self):
        r = requests.get(f"{BASE}/auth/me", timeout=TIMEOUT)
        assert r.status_code == 403


# ============ TASK 4: Rate Limiting (runs LAST) ============

class TestZ_RateLimiting:
    """Runs last (alphabetically) to avoid exhausting rate limits for other tests."""

    def test_login_rate_limit(self):
        """Login rate limiting eventually returns 429."""
        hit_429 = False
        for i in range(35):
            r = requests.post(f"{BASE}/auth/login", json={
                "email": f"ratelimit_{i}@example.com",
                "password": "doesntmatter",
            }, timeout=TIMEOUT)
            if r.status_code == 429:
                hit_429 = True
                break
        assert hit_429, "Rate limiter should have returned 429 within 35 requests"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
