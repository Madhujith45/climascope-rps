"""
ClimaScope - Complete System Test
This script tests the entire ML pipeline from data ingestion to prediction
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

def test_model_status():
    """Test ML model status endpoint"""
    print("🔍 Testing ML Model Status...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/predict/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Model Status: {data}")
            return True
        else:
            print(f"❌ Model Status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Model Status error: {e}")
        return False

def test_prediction():
    """Test prediction endpoint with sample data"""
    print("\n🔮 Testing Temperature Prediction...")
    
    # Sample sensor reading
    test_data = {
        "temperature": 25.5,
        "humidity": 60.0,
        "pressure": 1013.25,
        "gas_voltage": 1.8,
        "gas_ppm": 250.0
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/predict",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            prediction = response.json()
            print(f"✅ Prediction Result:")
            print(f"   - Predicted Temperature: {prediction['prediction']:.2f}°C")
            print(f"   - Confidence: {prediction['confidence']:.2f}")
            print(f"   - Status: {prediction['status']}")
            print(f"   - Insight: {prediction['insight']}")
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return False

def test_data_ingestion():
    """Test sensor data ingestion"""
    print("\n📊 Testing Data Ingestion...")
    
    # Generate sample sensor data
    sample_data = {
        "device_id": "test_device_001",
        "timestamp": datetime.now().isoformat(),
        "temperature": round(random.uniform(20, 35), 2),
        "humidity": round(random.uniform(40, 70), 1),
        "pressure": round(random.uniform(1000, 1020), 2),
        "mq2_voltage": round(random.uniform(1.0, 2.5), 3),
        "gas_ppm": round(random.uniform(100, 400), 1)
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/data",
            json=sample_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Data Ingested: {result['message']}")
            return True
        else:
            print(f"❌ Data ingestion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Data ingestion error: {e}")
        return False

def test_data_retrieval():
    """Test data retrieval endpoints"""
    print("\n📋 Testing Data Retrieval...")
    
    try:
        # Test latest data
        response = requests.get(f"{BACKEND_URL}/api/data/latest?n=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {len(data)} latest readings")
            if data:
                latest = data[0]
                print(f"   Latest: {latest['temperature']}°C at {latest['timestamp']}")
        else:
            print(f"❌ Latest data failed: {response.status_code}")
            return False
        
        # Test history
        response = requests.get(f"{BACKEND_URL}/api/data/history?limit=10")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved history: {data['total']} total records")
        else:
            print(f"❌ History data failed: {response.status_code}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Data retrieval error: {e}")
        return False

def test_real_time_simulation():
    """Simulate real-time sensor data"""
    print("\n🔄 Simulating Real-Time Data Stream...")
    
    for i in range(5):
        # Generate realistic sensor data with some variation
        base_temp = 25.0
        base_humidity = 60.0
        base_pressure = 1013.25
        
        sensor_data = {
            "device_id": "sim_device_001",
            "timestamp": datetime.now().isoformat(),
            "temperature": round(base_temp + random.uniform(-2, 3), 2),
            "humidity": round(base_humidity + random.uniform(-5, 8), 1),
            "pressure": round(base_pressure + random.uniform(-2, 2), 2),
            "mq2_voltage": round(random.uniform(1.2, 2.0), 3),
            "gas_ppm": round(random.uniform(150, 300), 1)
        }
        
        try:
            # Ingest data
            response = requests.post(
                f"{BACKEND_URL}/api/data",
                json=sensor_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                # Get prediction for this data
                pred_response = requests.post(
                    f"{BACKEND_URL}/api/predict",
                    json={
                        "temperature": sensor_data["temperature"],
                        "humidity": sensor_data["humidity"],
                        "pressure": sensor_data["pressure"],
                        "gas_voltage": sensor_data["mq2_voltage"],
                        "gas_ppm": sensor_data["gas_ppm"]
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if pred_response.status_code == 200:
                    pred = pred_response.json()
                    status_emoji = "🟢" if pred["status"] == "normal" else "🟡" if pred["status"] == "warning" else "🔴"
                    print(f"   {i+1}/5 {status_emoji} Temp: {sensor_data['temperature']}°C → Predicted: {pred['prediction']:.1f}°C ({pred['status']})")
                else:
                    print(f"   {i+1}/5 ❌ Prediction failed")
            else:
                print(f"   {i+1}/5 ❌ Data ingestion failed")
                
        except Exception as e:
            print(f"   {i+1}/5 ❌ Error: {e}")
        
        time.sleep(1)  # Wait 1 second between readings
    
    return True

def main():
    """Run complete system test"""
    print("🌡️  ClimaScope - Complete System Test")
    print("=" * 50)
    
    # Test individual components
    tests = [
        ("Model Status", test_model_status),
        ("Temperature Prediction", test_prediction),
        ("Data Ingestion", test_data_ingestion),
        ("Data Retrieval", test_data_retrieval),
        ("Real-Time Simulation", test_real_time_simulation)
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
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED! System is ready.")
        print(f"\n📱 Frontend: {FRONTEND_URL}")
        print(f"🔧 Backend API: {BACKEND_URL}/docs")
        print("\nNext steps:")
        print("1. Open the frontend in your browser")
        print("2. View real-time sensor data and predictions")
        print("3. Check the API documentation at /docs")
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Check the errors above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
