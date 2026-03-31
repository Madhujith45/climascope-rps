"""
ClimaScope – Advanced AI Prediction Routes

POST /api/predict       – get intelligent prediction with anomaly detection
GET  /api/predict/status – check model status and information
"""

import logging
import os
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, ConfigDict

# Import our advanced AI utilities
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'model'))
from utils import SystemHealthAnalyzer, InsightGenerator, calculate_prediction_confidence, format_insight_message

# Import database and authentication
from ..db.mongo import get_mongo_db
from ..auth.auth_routes import get_current_user
from ..routes.alert_routes import generate_alert

logger = logging.getLogger(__name__)

router = APIRouter(tags=["prediction"])

# Enhanced Pydantic models for request/response
class SensorReading(BaseModel):
    temperature: float = Field(..., description="Current temperature (°C)")
    humidity: Optional[float] = Field(None, description="Humidity (%)")
    pressure: float = Field(..., description="Atmospheric pressure (hPa)")
    gas_voltage: float = Field(..., description="Gas sensor voltage (V)")
    gas_ppm: float = Field(..., description="Gas concentration (PPM)")
    device_id: Optional[str] = Field(None, description="Device identifier")

class AdvancedPredictionResponse(BaseModel):
    prediction: float = Field(..., description="Predicted temperature (°C)")
    confidence: float = Field(..., description="Confidence score (0-1)")
    status: str = Field(..., description="System status: normal/warning/danger")
    anomaly: bool = Field(..., description="Anomaly detected")
    anomaly_score: float = Field(..., description="Anomaly severity score")
    health_score: int = Field(..., description="System health score (0-100)")
    insight: str = Field(..., description="Comprehensive analysis and recommendations")
    timestamp: str = Field(..., description="Prediction timestamp")
    device_id: str = Field(..., description="Device identifier")

class ModelStatusResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_loaded: bool = Field(..., description="Whether the ML models are loaded")
    regression_model_type: str = Field(..., description="Regression model type")
    anomaly_model_type: str = Field(..., description="Anomaly detection model type")
    feature_count: int = Field(..., description="Number of features used")
    target_variable: str = Field(..., description="Target variable being predicted")
    last_trained: Optional[str] = Field(None, description="When models were last trained")

# Global variables for both models
_regression_model = None
_anomaly_model = None
_regression_scaler = None
_anomaly_scaler = None
_regression_features = None
_anomaly_features = None
_target_column = None

# Health analyzer and insight generator
_health_analyzer = SystemHealthAnalyzer()
_insight_generator = InsightGenerator()

def load_dual_models():
    """Load both regression and anomaly detection models"""
    global _regression_model, _anomaly_model, _regression_scaler, _anomaly_scaler
    global _regression_features, _anomaly_features, _target_column
    
    try:
        import joblib
        
        # Paths to saved components
        model_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'model')
        
        # Regression model paths
        reg_model_path = os.path.join(model_dir, 'saved_models', 'climascope_model.pkl')
        reg_scaler_path = os.path.join(model_dir, 'saved_models', 'preprocessor.pkl')
        reg_features_path = os.path.join(model_dir, 'saved_models', 'feature_columns.pkl')
        target_path = os.path.join(model_dir, 'saved_models', 'target_column.pkl')
        
        # Anomaly model paths
        anomaly_model_path = os.path.join(model_dir, 'saved_models', 'anomaly_model.pkl')
        anomaly_scaler_path = os.path.join(model_dir, 'saved_models', 'anomaly_preprocessor.pkl')
        anomaly_features_path = os.path.join(model_dir, 'saved_models', 'anomaly_features.pkl')
        
        # Load regression model
        if os.path.exists(reg_model_path):
            _regression_model = joblib.load(reg_model_path)
            _regression_scaler = joblib.load(reg_scaler_path) if os.path.exists(reg_scaler_path) else None
            _regression_features = joblib.load(reg_features_path) if os.path.exists(reg_features_path) else None
            _target_column = joblib.load(target_path) if os.path.exists(target_path) else None
            logger.info("Regression model loaded successfully")
        
        # Load anomaly model
        if os.path.exists(anomaly_model_path):
            _anomaly_model = joblib.load(anomaly_model_path)
            _anomaly_scaler = joblib.load(anomaly_scaler_path) if os.path.exists(anomaly_scaler_path) else None
            _anomaly_features = joblib.load(anomaly_features_path) if os.path.exists(anomaly_features_path) else None
            logger.info("Anomaly detection model loaded successfully")
        
        return True
        
    except Exception as e:
        logger.error("Failed to load models: %s", str(e))
        return False

def prepare_regression_features(reading: SensorReading) -> np.ndarray:
    """Prepare features for regression model"""
    # Create a dictionary with the sensor reading
    data = {
        'BMP Temp (C)': reading.temperature,
        'Pressure (hPa)': reading.pressure,
        'DHT Temp (C)': reading.temperature,  # Use same temp for both sensors
        'Humidity (%)': reading.humidity if reading.humidity else 50.0,
        'Gas Voltage (V)': reading.gas_voltage,
        'Gas PPM': reading.gas_ppm
    }
    
    # Create time-based features
    now = datetime.now()
    data.update({
        'hour': now.hour,
        'day_of_week': now.weekday(),
        'month': now.month,
        'is_weekend': int(now.weekday() >= 5)
    })
    
    # Create rolling statistics (using current values as approximation)
    for col in ['BMP Temp (C)', 'Pressure (hPa)', 'DHT Temp (C)', 'Humidity (%)', 'Gas Voltage (V)', 'Gas PPM']:
        data[f'{col}_rolling_mean_5'] = data[col]
        data[f'{col}_rolling_std_5'] = 0.1
        data[f'{col}_lag_1'] = data[col]
        data[f'{col}_lag_2'] = data[col]
    
    # Create derived features
    data['temp_humidity_ratio'] = data['DHT Temp (C)'] / (data['Humidity (%)'] + 1)
    data['temp_pressure_ratio'] = data['DHT Temp (C)'] / (data['Pressure (hPa)'] + 1)
    
    # Convert to DataFrame and select features
    df = pd.DataFrame([data])
    
    # Select only the features the model was trained on
    if _regression_features:
        available_features = [col for col in _regression_features if col in df.columns]
        features = df[available_features].fillna(0)
    else:
        features = df.fillna(0)
    
    return features.values

def prepare_anomaly_features(reading: SensorReading) -> np.ndarray:
    """Prepare features for anomaly detection model"""
    # Create feature dictionary for anomaly detection
    data = {
        'BMP Temp (C)': reading.temperature,
        'DHT Temp (C)': reading.temperature,
        'Humidity (%)': reading.humidity if reading.humidity else 50.0,
        'Pressure (hPa)': reading.pressure,
        'Gas Voltage (V)': reading.gas_voltage,
        'Gas PPM': reading.gas_ppm
    }
    
    # Add rolling statistics (using current values)
    for sensor in ['BMP Temp (C)', 'DHT Temp (C)', 'Humidity (%)', 'Pressure (hPa)', 'Gas Voltage (V)', 'Gas PPM']:
        data[f'{sensor}_rolling_mean_5'] = data[sensor]
        data[f'{sensor}_rolling_std_5'] = 0.1
        data[f'{sensor}_roc_1'] = 0.0  # No change for single reading
    
    # Add multi-sensor features
    data['heat_index'] = data['DHT Temp (C)'] + 0.5 * data['Humidity (%)'] / 10
    data['env_stress'] = (data['Gas PPM'] / 200) * (1013.25 / data['Pressure (hPa)'])
    
    # Convert to DataFrame
    df = pd.DataFrame([data])
    
    # Select anomaly features
    if _anomaly_features:
        available_features = [col for col in _anomaly_features if col in df.columns]
        features = df[available_features].fillna(0)
    else:
        features = df.fillna(0)
    
    return features.values

@router.post("/api/predict", response_model=AdvancedPredictionResponse)
async def get_intelligent_prediction(
    reading: SensorReading,
    current_user: dict = Depends(get_current_user)
):
    """
    Get intelligent prediction with anomaly detection and health analysis.
    
    Enhanced AI pipeline:
    1. Temperature prediction using regression model
    2. Anomaly detection using Isolation Forest
    3. System health score calculation
    4. Insight generation with recommendations
    5. Store results in database
    6. Generate alerts if needed
    """
    # Load models if not already loaded
    if _regression_model is None or _anomaly_model is None:
        if not load_dual_models():
            raise HTTPException(status_code=503, detail="ML models not available")
    
    try:
        user_id = str(current_user["_id"])
        device_id = reading.device_id or "unknown_device"
        
        # Step 1: Temperature Prediction
        reg_features = prepare_regression_features(reading)
        if _regression_scaler:
            reg_features_scaled = _regression_scaler.transform(reg_features)
        else:
            reg_features_scaled = reg_features
        
        temperature_prediction = _regression_model.predict(reg_features_scaled)[0]
        
        # Step 2: Anomaly Detection
        anomaly_features = prepare_anomaly_features(reading)
        if _anomaly_scaler:
            anomaly_features_scaled = _anomaly_scaler.transform(anomaly_features)
        else:
            anomaly_features_scaled = anomaly_features
        
        anomaly_prediction = _anomaly_model.predict(anomaly_features_scaled)[0]
        anomaly_score = _anomaly_model.decision_function(anomaly_features_scaled)[0]
        is_anomaly = bool(anomaly_prediction == -1)
        
        # Step 3: System Health Score Calculation
        health_analysis = _health_analyzer.calculate_system_health_score(
            reading.temperature, reading.humidity or 50.0, 
            reading.pressure, reading.gas_ppm, anomaly_score
        )
        
        health_score = health_analysis['overall_score']
        
        # Step 4: Status Determination
        status = _health_analyzer.determine_status_level(health_score, is_anomaly)
        
        # Step 5: Confidence Calculation
        model_type = type(_regression_model).__name__
        confidence = calculate_prediction_confidence(model_type, anomaly_score, health_score)
        
        # Step 6: Insight Generation
        insight_data = _insight_generator.generate_insight(
            reading.temperature, reading.humidity or 50.0, reading.pressure, reading.gas_ppm,
            is_anomaly, anomaly_score, health_score
        )
        insight_message = format_insight_message(insight_data)
        
        # Step 7: Store in Database
        db = get_mongo_db()
        sensor_data_doc = {
            "user_id": user_id,
            "device_id": device_id,
            "temperature": reading.temperature,
            "humidity": reading.humidity or 50.0,
            "pressure": reading.pressure,
            "gas_voltage": reading.gas_voltage,
            "gas_ppm": reading.gas_ppm,
            "prediction": float(temperature_prediction),
            "health_score": int(health_score),
            "status": status,
            "anomaly": is_anomaly,
            "anomaly_score": float(anomaly_score),
            "timestamp": datetime.utcnow()
        }
        
        # Insert sensor data
        await db.sensor_data.insert_one(sensor_data_doc)
        
        # Step 8: Generate Alerts if needed
        alert_generated = False
        if is_anomaly:
            alert_message = f"⚠️ Anomaly detected on device {device_id}: {insight_message[:100]}"
            await generate_alert(user_id, device_id, alert_message, "danger", "anomaly")
            alert_generated = True
        
        elif status == "danger":
            alert_message = f"🔴 Critical condition on device {device_id}: {insight_message[:100]}"
            await generate_alert(user_id, device_id, alert_message, "danger", "critical")
            alert_generated = True
        
        elif health_score < 70:
            alert_message = f"🟡 Warning condition on device {device_id}: {insight_message[:100]}"
            await generate_alert(user_id, device_id, alert_message, "warning", "warning")
            alert_generated = True
        
        # Update device last_seen
        await db.devices.update_one(
            {"user_id": user_id, "device_id": device_id},
            {"$set": {"last_seen": datetime.utcnow()}}
        )
        
        response_data = AdvancedPredictionResponse(
            prediction=float(temperature_prediction),
            confidence=confidence,
            status=status,
            anomaly=is_anomaly,
            anomaly_score=float(anomaly_score),
            health_score=int(health_score),
            insight=insight_message,
            timestamp=datetime.now().isoformat(),
            device_id=device_id
        )
        
        # Log the prediction
        logger.info(f"Prediction for user {user_id}, device {device_id}: {status} (health: {health_score})")
        
        if alert_generated:
            logger.info(f"Alert generated for user {user_id}, device {device_id}")
        
        return response_data
        
    except Exception as e:
        logger.error("Intelligent prediction failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/api/predict/status", response_model=ModelStatusResponse)
async def get_dual_model_status():
    """Get information about both loaded ML models"""
    regression_loaded = _regression_model is not None
    anomaly_loaded = _anomaly_model is not None
    
    if not regression_loaded and not anomaly_loaded:
        return ModelStatusResponse(
            model_loaded=False,
            regression_model_type="Not loaded",
            anomaly_model_type="Not loaded",
            feature_count=0,
            target_variable="None",
            last_trained=None
        )
    
    # Get model information
    regression_type = type(_regression_model).__name__ if _regression_model else "Not loaded"
    anomaly_type = type(_anomaly_model).__name__ if _anomaly_model else "Not loaded"
    feature_count = len(_regression_features) if _regression_features else 0
    target_variable = _target_column or "Unknown"
    
    # Check when models were last modified
    reg_model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'model', 'saved_models', 'climascope_model.pkl')
    anomaly_model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'model', 'saved_models', 'anomaly_model.pkl')
    
    last_trained = None
    if os.path.exists(reg_model_path) and os.path.exists(anomaly_model_path):
        reg_time = os.path.getmtime(reg_model_path)
        anomaly_time = os.path.getmtime(anomaly_model_path)
        last_trained = datetime.fromtimestamp(max(reg_time, anomaly_time)).isoformat()
    
    return ModelStatusResponse(
        model_loaded=regression_loaded and anomaly_loaded,
        regression_model_type=regression_type,
        anomaly_model_type=anomaly_type,
        feature_count=feature_count,
        target_variable=target_variable,
        last_trained=last_trained
    )

# Load both models on startup
load_dual_models()
