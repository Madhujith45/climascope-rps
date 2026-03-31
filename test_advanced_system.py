"""
ClimaScope - Advanced AI System Test
Tests the enhanced system with anomaly detection, health scores, and insights
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

def test_advanced_prediction():
    """Test advanced AI prediction with all new features"""
    print("🧠 Testing Advanced AI Prediction...")
    
    # Test case 1: Normal conditions
    test_data = {
        "temperature": 22.5,
        "humidity": 55.0,
        "pressure": 1013.25,
        "gas_voltage": 1.6,
        "gas_ppm": 180.0
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/predict",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Normal Case:")
            print(f"   Prediction: {result['prediction']:.2f}°C")
            print(f"   Health Score: {result['health_score']}/100")
            print(f"   Anomaly: {result['anomaly']}")
            print(f"   Status: {result['status']}")
            print(f"   Insight: {result['insight'][:80]}...")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_anomaly_detection():
    """Test anomaly detection with extreme values"""
    print("\n🚨 Testing Anomaly Detection...")
    
    # Test case 2: High temperature anomaly
    anomaly_data = {
        "temperature": 38.0,  # High temp
        "humidity": 75.0,  # High humidity
        "pressure": 990.0,  # Low pressure
        "gas_voltage": 2.8,  # High gas voltage
        "gas_ppm": 450.0   # High gas
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/predict",
            json=anomaly_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Anomaly Case:")
            print(f"   Prediction: {result['prediction']:.2f}°C")
            print(f"   Health Score: {result['health_score']}/100")
            print(f"   Anomaly: {result['anomaly']}")
            print(f"   Anomaly Score: {result['anomaly_score']:.3f}")
            print(f"   Status: {result['status']}")
            print(f"   Insight: {result['insight'][:80]}...")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_gas_spike():
    """Test gas spike detection"""
    print("\n💨 Testing Gas Spike Detection...")
    
    gas_spike_data = {
        "temperature": 25.0,
        "humidity": 50.0,
        "pressure": 1013.25,
        "gas_voltage": 3.5,  # Very high gas voltage
        "gas_ppm": 600.0   # Extreme gas spike
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/predict",
            json=gas_spike_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Gas Spike Case:")
            print(f"   Prediction: {result['prediction']:.2f}°C")
            print(f"   Health Score: {result['health_score']}/100")
            print(f"   Anomaly: {result['anomaly']}")
            print(f"   Status: {result['status']}")
            print(f"   Insight: {result['insight'][:80]}...")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_pressure_instability():
    """Test pressure instability detection"""
    print("\n🔵 Testing Pressure Instability...")
    
    pressure_data = {
        "temperature": 24.0,
        "humidity": 45.0,
        "pressure": 970.0,  # Very low pressure
        "gas_voltage": 1.8,
        "gas_ppm": 200.0
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/predict",
            json=pressure_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Pressure Instability Case:")
            print(f"   Prediction: {result['prediction']:.2f}°C")
            print(f"   Health Score: {result['health_score']}/100")
            print(f"   Anomaly: {result['anomaly']}")
            print(f"   Status: {result['status']}")
            print(f"   Insight: {result['insight'][:80]}...")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_dual_model_status():
    """Test dual model status endpoint"""
    print("\n🔧 Testing Dual Model Status...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/predict/status")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Dual Model Status:")
            print(f"   Models Loaded: {result['model_loaded']}")
            print(f"   Regression Model: {result['regression_model_type']}")
            print(f"   Anomaly Model: {result['anomaly_model_type']}")
            print(f"   Feature Count: {result['feature_count']}")
            print(f"   Target Variable: {result['target_variable']}")
            print(f"   Last Trained: {result['last_trained']}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\n⚡ Testing Edge Cases...")
    
    edge_cases = [
        {
            "name": "Very Low Temperature",
            "data": {
                "temperature": 10.0,
                "humidity": 20.0,
                "pressure": 1050.0,
                "gas_voltage": 1.0,
                "gas_ppm": 50.0
            }
        },
        {
            "name": "Very High Temperature",
            "data": {
                "temperature": 45.0,
                "humidity": 85.0,
                "pressure": 950.0,
                "gas_voltage": 4.0,
                "gas_ppm": 800.0
            }
        },
        {
            "name": "Missing Humidity",
            "data": {
                "temperature": 25.0,
                "humidity": None,  # Test missing value handling
                "pressure": 1013.25,
                "gas_voltage": 1.8,
                "gas_ppm": 200.0
            }
        }
    ]
    
    passed = 0
    for case in edge_cases:
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/predict",
                json=case["data"],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {case['name']}:")
                print(f"   Health Score: {result['health_score']}/100")
                print(f"   Status: {result['status']}")
                print(f"   Confidence: {result['confidence']:.2f}")
                passed += 1
            else:
                print(f"❌ {case['name']} Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {case['name']} Error: {e}")
    
    print(f"Edge Cases: {passed}/{len(edge_cases)} passed")
    return passed == len(edge_cases)

def test_performance():
    """Test system performance under load"""
    print("\n⚡ Testing System Performance...")
    
    start_time = time.time()
    requests_made = 0
    
    # Make multiple rapid requests
    for i in range(10):
        test_data = {
            "temperature": 20.0 + i,
            "humidity": 50.0 + i,
            "pressure": 1013.25 + i,
            "gas_voltage": 1.5 + (i * 0.1),
            "gas_ppm": 150.0 + (i * 10)
        }
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/predict",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                requests_made += 1
                
        except Exception:
            continue  # Skip failed requests for performance test
        
        time.sleep(0.1)  # Small delay between requests
    
    end_time = time.time()
    total_time = end_time - start_time
    
    if requests_made > 0:
        avg_response_time = (total_time / requests_made) * 1000  # Convert to ms
        requests_per_second = requests_made / total_time
        
        print(f"✅ Performance Test Results:")
        print(f"   Requests Made: {requests_made}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Avg Response Time: {avg_response_time:.0f}ms")
        print(f"   Requests/Second: {requests_per_second:.1f}")
        
        # Performance criteria
        if avg_response_time < 200 and requests_per_second > 4:
            print("   🟢 Performance: EXCELLENT")
            return True
        elif avg_response_time < 500 and requests_per_second > 2:
            print("   🟡 Performance: GOOD")
            return True
        else:
            print("   🔴 Performance: NEEDS IMPROVEMENT")
            return False
    
    return False

def main():
    """Run comprehensive advanced system test"""
    print("🚀 ClimaScope - Advanced AI System Test")
    print("Enhanced Intelligence with Anomaly Detection & Health Scoring")
    print("=" * 60)
    
    # Run all test suites
    tests = [
        ("Dual Model Status", test_dual_model_status),
        ("Advanced Prediction", test_advanced_prediction),
        ("Anomaly Detection", test_anomaly_detection),
        ("Gas Spike Detection", test_gas_spike),
        ("Pressure Instability", test_pressure_instability),
        ("Edge Cases", test_edge_cases),
        ("Performance Test", test_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 ADVANCED SYSTEM TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL ADVANCED TESTS PASSED!")
        print("🌟 System is ready for production deployment!")
        print("\n📱 Frontend: http://localhost:5173")
        print("🔧 Backend API: http://localhost:8000/docs")
        print("\n🆕 NEW FEATURES AVAILABLE:")
        print("   • Anomaly Detection (Isolation Forest)")
        print("   • System Health Scoring (0-100)")
        print("   • Multi-Sensor Intelligence")
        print("   • Advanced AI Insights")
        print("   • Real-time Status Indicators")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check system logs.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
