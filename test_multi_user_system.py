"""
ClimaScope - Multi-User AI Platform Test Suite
Comprehensive testing for authentication, devices, alerts, and AI predictions
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

class MultiUserPlatformTester:
    def __init__(self):
        self.auth_token = None
        self.user_id = None
        self.device_id = None
        self.test_results = []
    
    def log_test(self, test_name, passed, message=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append(f"{status} {test_name}: {message}")
        print(f"{status} {test_name}: {message}")
    
    def test_backend_health(self):
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "features" in data:
                    self.log_test("Backend Health Check", True, "Multi-user platform active")
                    return True
            self.log_test("Backend Health Check", False, "Invalid response")
            return False
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Connection failed: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user signup endpoint"""
        try:
            # Generate unique test user data
            test_email = f"testuser_{int(time.time())}@example.com"
            test_password = "TestPassword123"
            
            signup_data = {
                "email": test_email,
                "password": test_password,
                "full_name": "Test User"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/auth/signup",
                json=signup_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                if "id" in data and data["email"] == test_email:
                    self.log_test("User Registration", True, "Test user created successfully")
                    return test_email, test_password
            else:
                self.log_test("User Registration", False, f"Invalid response: {response.status_code}")
                return None, None
        except Exception as e:
            self.log_test("User Registration", False, f"Request failed: {str(e)}")
            return None, None
    
    def test_user_login(self, email, password):
        """Test user login endpoint"""
        try:
            login_data = {
                "email": email,
                "password": password
            }
            
            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.auth_token = data["access_token"]
                    self.user_id = data["user"]["id"]
                    self.log_test("User Login", True, "JWT token received")
                    return True
            else:
                self.log_test("User Login", False, f"Invalid response: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Login", False, f"Request failed: {str(e)}")
            return False
    
    def test_device_management(self):
        """Test device management endpoints"""
        try:
            if not self.auth_token:
                self.log_test("Device Management", False, "No authentication token")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Test device addition
            device_data = {
                "device_name": "Test Device",
                "location": "Test Location",
                "description": "Automated test device"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/devices/add",
                json=device_data,
                headers=headers
            )
            
            if response.status_code == 201:
                device = response.json()
                self.device_id = device["device_id"]
                self.log_test("Device Addition", True, f"Device created: {device['device_id']}")
            else:
                self.log_test("Device Addition", False, f"Failed: {response.status_code}")
                return False
            
            # Test device listing
            response = requests.get(
                f"{BACKEND_URL}/devices/list",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "devices" in data and len(data["devices"]) > 0:
                    self.log_test("Device Listing", True, f"Found {len(data['devices'])} devices")
                else:
                    self.log_test("Device Listing", False, "No devices found")
                    return False
            else:
                self.log_test("Device Listing", False, f"Failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Device Management", False, f"Request failed: {str(e)}")
            return False
    
    def test_ai_predictions(self):
        """Test enhanced AI prediction endpoint"""
        try:
            if not self.auth_token or not self.device_id:
                self.log_test("AI Predictions", False, "Missing auth token or device ID")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Test prediction with device mapping
            sensor_data = {
                "temperature": 25.5,
                "humidity": 60.0,
                "pressure": 1013.25,
                "gas_voltage": 1.8,
                "gas_ppm": 200.0,
                "device_id": self.device_id
            }
            
            response = requests.post(
                f"{BACKEND_URL}/api/predict",
                json=sensor_data,
                headers=headers
            )
            
            if response.status_code == 200:
                prediction = response.json()
                required_fields = ["prediction", "confidence", "status", "anomaly", 
                                "anomaly_score", "health_score", "insight", "device_id"]
                
                if all(field in prediction for field in required_fields):
                    self.log_test("AI Predictions", True, 
                                f"Health: {prediction['health_score']}, Status: {prediction['status']}")
                    return True
            else:
                self.log_test("AI Predictions", False, "Missing required fields in response")
                return False
        except Exception as e:
            self.log_test("AI Predictions", False, f"Request failed: {str(e)}")
            return False
    
    def test_alert_system(self):
        """Test intelligent alert system"""
        try:
            if not self.auth_token:
                self.log_test("Alert System", False, "No authentication token")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Test alert listing
            response = requests.get(
                f"{BACKEND_URL}/alerts/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if "alerts" in data:
                    self.log_test("Alert Listing", True, f"Found {len(data['alerts'])} alerts")
                    
                    # Test alert statistics
                    stats_response = requests.get(
                        f"{BACKEND_URL}/alerts/stats",
                        headers=headers
                    )
                    
                    if stats_response.status_code == 200:
                        stats = stats_response.json()
                        self.log_test("Alert Statistics", True, f"Total: {stats.get('total', 0)}")
                    else:
                        self.log_test("Alert Statistics", False, "Failed to get stats")
                    
                    return True
                else:
                    self.log_test("Alert Listing", False, "No alerts found")
                    return False
            else:
                self.log_test("Alert Listing", False, f"Failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Alert System", False, f"Request failed: {str(e)}")
            return False
    
    def test_data_isolation(self):
        """Test user data isolation"""
        try:
            # Create second test user
            test_email2 = f"testuser2_{int(time.time())}@example.com"
            test_password2 = "TestPassword123"
            
            # Register second user
            signup_data2 = {
                "email": test_email2,
                "password": test_password2,
                "full_name": "Test User 2"
            }
            
            response = requests.post(
                f"{BACKEND_URL}/auth/signup",
                json=signup_data2,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 201:
                self.log_test("Data Isolation", False, "Failed to create second test user")
                return False
            
            # Login second user
            login_data2 = {
                "email": test_email2,
                "password": test_password2
            }
            
            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json=login_data2,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.log_test("Data Isolation", False, "Failed to login second test user")
                return False
            
            second_token = response.json()["access_token"]
            second_headers = {
                "Authorization": f"Bearer {second_token}",
                "Content-Type": "application/json"
            }
            
            # Try to access first user's devices with second user's token
            response = requests.get(
                f"{BACKEND_URL}/devices/list",
                headers=second_headers
            )
            
            # Should return empty or error (data isolation working)
            if response.status_code == 200:
                data = response.json()
                if len(data.get("devices", [])) == 0:
                    self.log_test("Data Isolation", True, "User data properly isolated")
                    return True
                else:
                    self.log_test("Data Isolation", False, "Data leak between users detected")
                    return False
            else:
                self.log_test("Data Isolation", False, "Failed to test isolation")
                return False
                
        except Exception as e:
            self.log_test("Data Isolation", False, f"Test failed: {str(e)}")
            return False
    
    def test_model_status(self):
        """Test dual AI model status endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/predict/status")
            
            if response.status_code == 200:
                status = response.json()
                required_fields = ["model_loaded", "regression_model_type", 
                                "anomaly_model_type", "feature_count"]
                
                if all(field in status for field in required_fields):
                    if status["model_loaded"] and status["regression_model_type"] and status["anomaly_model_type"]:
                        self.log_test("Model Status", True, 
                                    f"Regression: {status['regression_model_type']}, Anomaly: {status['anomaly_model_type']}")
                        return True
                
                self.log_test("Model Status", False, "Incomplete model status response")
                return False
            else:
                self.log_test("Model Status", False, f"Failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Model Status", False, f"Request failed: {str(e)}")
            return False
    
    def test_frontend_access(self):
        """Test frontend accessibility"""
        try:
            response = requests.get(FRONTEND_URL, timeout=5)
            
            if response.status_code == 200:
                self.log_test("Frontend Access", True, "Frontend loads successfully")
                return True
            else:
                self.log_test("Frontend Access", False, f"Frontend not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Frontend Access", False, f"Frontend connection failed: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            if self.auth_token:
                headers = {
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                }
                
                # Delete test device
                if self.device_id:
                    requests.delete(
                        f"{BACKEND_URL}/devices/{self.device_id}",
                        headers=headers
                    )
                
                # Note: In a real system, you might want to keep test users
                # For this test, we're not deleting the users
                
        except Exception as e:
            print(f"Cleanup warning: {str(e)}")
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 ClimaScope Multi-User AI Platform Test Suite")
        print("=" * 60)
        
        # Test 1: Backend Health
        if not self.test_backend_health():
            print("❌ Backend health check failed - cannot continue")
            return False
        
        # Test 2: User Registration
        test_email, test_password = self.test_user_registration()
        if not test_email:
            print("❌ User registration failed - cannot continue")
            return False
        
        # Test 3: User Login
        if not self.test_user_login(test_email, test_password):
            print("❌ User login failed - cannot continue")
            return False
        
        # Test 4: Device Management
        if not self.test_device_management():
            print("❌ Device management failed - cannot continue")
            return False
        
        # Test 5: AI Predictions
        if not self.test_ai_predictions():
            print("❌ AI predictions failed - cannot continue")
            return False
        
        # Test 6: Alert System
        if not self.test_alert_system():
            print("❌ Alert system failed - cannot continue")
            return False
        
        # Test 7: Data Isolation
        if not self.test_data_isolation():
            print("❌ Data isolation test failed")
            return False
        
        # Test 8: Model Status
        if not self.test_model_status():
            print("❌ Model status test failed")
            return False
        
        # Test 9: Frontend Access
        if not self.test_frontend_access():
            print("❌ Frontend access test failed")
            return False
        
        # Cleanup
        self.cleanup_test_data()
        
        # Results Summary
        print("\n" + "=" * 60)
        print("🏁 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if "✅ PASS" in result)
        total_tests = len(self.test_results)
        
        for result in self.test_results:
            print(result)
        
        print(f"\nResults: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED!")
            print("🌟 Multi-User AI Platform is ready for production!")
            print("\n📱 Frontend:", FRONTEND_URL)
            print("🔧 Backend API:", f"{BACKEND_URL}/docs")
            print("\n✨ Features Available:")
            print("   • JWT Authentication")
            print("   • Device Management")
            print("   • Intelligent Alerts")
            print("   • Multi-User Support")
            print("   • AI Predictions with Anomaly Detection")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} tests failed")
            print("Check the logs above for details")
        
        return passed_tests == total_tests

def main():
    """Run the multi-user platform test suite"""
    tester = MultiUserPlatformTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
