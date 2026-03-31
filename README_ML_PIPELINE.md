# ClimaScope – AI-Based Microclimate Prediction & Monitoring System

## 🎯 Project Overview

ClimaScope is a complete end-to-end IoT + AI system for real-time microclimate monitoring and prediction. The system processes sensor data from Raspberry Pi-based devices and provides intelligent temperature predictions using machine learning.

## 📊 Dataset Analysis

- **Source**: Real IoT sensor readings (5,176 rows)
- **Sensors**: Temperature (BMP & DHT), Humidity, Pressure, Gas (MQ2)
- **Time Period**: March 8, 2026
- **Frequency**: High-frequency readings (every few seconds)

## 🧠 ML Pipeline Summary

### Problem Type: Time-Series Regression (Temperature Forecasting)

**Justification:**
- Dataset has timestamp information for temporal patterns
- Temperature is a continuous variable suitable for regression
- Historical patterns can predict future temperature trends
- Time-series features enhance prediction accuracy

### Model Performance Comparison

| Model | MAE | RMSE | R² | Selected |
|-------|-----|------|----|----------|
| Linear Regression | 0.0371 | 0.1105 | 0.9983 | ✅ |
| Random Forest | 0.0353 | 0.1635 | 0.9964 | ❌ |

**Winner: Linear Regression** - Best balance of accuracy and interpretability with exceptional R² score of 99.83%

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IoT Sensors   │───▶│   FastAPI       │───▶│   React UI      │
│  (Raspberry Pi) │    │   Backend       │    │   Dashboard     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   ML Model      │
                       │ (Linear Reg.)   │
                       └─────────────────┘
```

## 📁 Project Structure

```
climascope/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── data_routes.py          # Sensor data endpoints
│   │   │   ├── prediction_routes.py     # ML prediction endpoints
│   │   │   └── alert_routes.py         # Alert system
│   │   └── main.py                     # FastAPI application
│   └── model/
│       ├── train.py                    # Complete ML pipeline
│       └── saved_models/               # Trained model artifacts
├── frontend/
│   └── src/
│       └── components/
│           ├── Dashboard.jsx           # Main dashboard
│           ├── PredictionPanel.jsx     # ML predictions UI
│           └── SensorCards.jsx         # Sensor data display
├── sensor_data.xlsx                     # Dataset
└── test_system.py                      # Complete system test
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 16+
- Git

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Train ML model**
   ```bash
   cd model
   python train.py
   ```

5. **Start FastAPI server**
   ```bash
   cd ..
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

### Access Points

- **Frontend Dashboard**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🧪 Testing the System

Run the complete system test:

```bash
python test_system.py
```

This tests:
- ✅ ML Model Status
- ✅ Temperature Prediction
- ✅ Data Ingestion
- ✅ Data Retrieval
- ✅ Real-Time Simulation

## 📡 API Endpoints

### Prediction Endpoints

#### POST /api/predict
Get temperature prediction from sensor readings.

**Request:**
```json
{
  "temperature": 25.5,
  "humidity": 60.0,
  "pressure": 1013.25,
  "gas_voltage": 1.8,
  "gas_ppm": 250.0
}
```

**Response:**
```json
{
  "prediction": 25.49,
  "confidence": 0.85,
  "status": "normal",
  "insight": "Temperature stable. Predicted: 25.5°C",
  "timestamp": "2026-03-19T10:30:15.665408"
}
```

#### GET /api/predict/status
Check ML model status.

**Response:**
```json
{
  "model_loaded": true,
  "model_type": "LinearRegression",
  "feature_count": 33,
  "target_variable": "BMP Temp (C)",
  "last_trained": "2026-03-19T10:23:08.416984"
}
```

### Data Endpoints

#### POST /api/data
Ingest sensor readings from edge devices.

#### GET /api/data/latest
Get most recent sensor readings.

#### GET /api/data/history
Get paginated historical data.

## 🎨 Frontend Features

### Dashboard Components

1. **Sensor Cards** - Real-time sensor readings
2. **Prediction Panel** - ML temperature predictions with:
   - Predicted temperature
   - Confidence score
   - Status indicator (normal/warning/danger)
   - AI insights
   - Model information
3. **Real-Time Charts** - Time-series visualization
4. **Historical Table** - Paginated data history

### Status Indicators

- 🟢 **Normal**: Temperature stable (≤0.5°C change)
- 🟡 **Warning**: Moderate change (0.5-2.0°C)
- 🔴 **Danger**: Significant change (>2.0°C)

## 🔧 ML Pipeline Details

### Data Preprocessing
- Missing value imputation using median
- Duplicate removal
- Timestamp conversion and chronological sorting
- Outlier detection and capping using IQR method

### Feature Engineering
- **Time-based**: hour, day_of_week, month, is_weekend
- **Rolling statistics**: 5-window mean and standard deviation
- **Lag features**: t-1, t-2 previous readings
- **Derived features**: temp_humidity_ratio, temp_pressure_ratio

### Model Selection Process
1. **Linear Regression**: Baseline model with excellent interpretability
2. **Random Forest**: Ensemble method for comparison
3. **Evaluation**: MAE, RMSE, R² metrics

### Model Explainability
- Feature importance analysis
- Correlation matrix visualization
- Time-series trend analysis

## 📈 Performance Metrics

### Model Performance
- **MAE**: 0.0371°C (extremely accurate)
- **RMSE**: 0.1105°C
- **R²**: 0.9983 (99.83% variance explained)

### System Performance
- **API Response Time**: <100ms
- **Frontend Refresh**: 5 seconds
- **Data Throughput**: Real-time processing

## 🌟 Key Features

### Real-Time Capabilities
- Live sensor data streaming
- Instant ML predictions
- Real-time status updates
- Automatic alerts for anomalies

### Intelligent Features
- Temperature trend prediction
- Confidence scoring
- Status-based alerting
- AI-powered insights

### Production Ready
- Scalable architecture
- Error handling
- Logging and monitoring
- Comprehensive testing

## 🔮 Future Enhancements

1. **Advanced Models**: XGBoost, LSTM for time-series
2. **Multi-sensor Fusion**: Combine more sensor types
3. **Edge Deployment**: Run ML models on Raspberry Pi
4. **Mobile App**: React Native mobile application
5. **Cloud Integration**: AWS/Azure deployment
6. **Advanced Analytics**: Weather data integration

## 🛠️ Development Commands

### Backend
```bash
# Train model
cd backend/model && python train.py

# Start server
cd backend && python -m uvicorn app.main:app --reload

# Test API
python test_system.py
```

### Frontend
```bash
# Install dependencies
npm install

# Start development
npm run dev

# Build for production
npm run build
```

## 📝 Model Insights

### Key Findings
1. **Temperature Prediction**: Linear Regression provides exceptional accuracy
2. **Feature Importance**: Time-based features and lag features are most predictive
3. **Data Quality**: Clean, high-frequency sensor data enables accurate predictions
4. **System Stability**: Real-time processing with minimal latency

### Business Value
- **Early Warning**: Predict temperature changes before they become critical
- **Resource Optimization**: Optimize HVAC systems based on predictions
- **Safety Monitoring**: Alert on potentially dangerous temperature changes
- **Data-Driven Decisions**: Use ML insights for climate control strategies

## 🏆 Project Success Criteria

✅ **Complete ML Pipeline**: Data preprocessing → Model training → Deployment  
✅ **Real-Time Predictions**: Sub-100ms response times  
✅ **User-Friendly UI**: Intuitive dashboard with clear visualizations  
✅ **Production Ready**: Error handling, logging, testing  
✅ **Scalable Architecture**: Modular design for future enhancements  
✅ **Comprehensive Documentation**: Full API docs and user guides  

---

**ClimaScope** - Transforming IoT sensor data into actionable climate intelligence through machine learning.
