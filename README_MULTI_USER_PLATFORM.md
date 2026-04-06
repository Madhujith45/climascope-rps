# ClimaScope – Multi-User AI Platform Setup Guide

## 🚀 OVERVIEW

ClimaScope has been transformed into a **production-ready multi-user AI platform** with comprehensive features:

- ✅ **JWT Authentication** (Login/Signup with secure tokens)
- ✅ **MongoDB Integration** (Async database with optimized indexes)
- ✅ **Device Management** (Multi-device support per user)
- ✅ **Intelligent Alerts** (Auto-generated with severity levels)
- ✅ **Enhanced AI Predictions** (Device-aware with anomaly detection)
- ✅ **Personalized Dashboard** (User-specific data and alerts)

---

## 📋 PREREQUISITES

### System Requirements
- **Node.js** 16+ 
- **Python** 3.8+
- **MongoDB** 5.0+ (local or Atlas)
- **Git** for version control

### Required Services
- **MongoDB**: Local instance or MongoDB Atlas account
- **Backend**: Python with FastAPI
- **Frontend**: Node.js with Vite

---

## 🛠️ SETUP INSTRUCTIONS

### Step 1: Backend Setup

#### 1.1 Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### 1.2 Environment Configuration
Create `.env` file in `backend/` directory:
```bash
# Database Configuration
MONGO_URI=<your_mongo_uri>
DATABASE_NAME=climascope

# JWT Configuration
JWT_SECRET=your_super_secret_key_change_in_production

# CORS Configuration
CLIMASCOPE_CORS_ORIGINS=http://localhost:5173
```

#### 1.3 Database Setup
**Option A: Local MongoDB**
```bash
# Start MongoDB service
mongod --dbpath /path/to/your/db
```

**Option B: MongoDB Atlas**
1. Create free account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create new cluster
3. Get connection string
4. Update `MONGO_URI` in `.env`

#### 1.4 Train AI Models
```bash
cd backend/model
python train.py              # Train regression model
python anomaly_train.py       # Train anomaly detection model
```

#### 1.5 Start Backend Server
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Frontend Setup

#### 2.1 Install Dependencies
```bash
cd frontend
npm install
```

#### 2.2 Environment Configuration
Create `.env.local` file in `frontend/` directory:
```bash
VITE_API_URL=http://localhost:8000
```

#### 2.3 Start Frontend Development Server
```bash
cd frontend
npm run dev
```

---

## 🌐 ACCESS POINTS

### Backend API
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/
- **Authentication**: http://localhost:8000/auth/
- **Device Management**: http://localhost:8000/devices/
- **Alert System**: http://localhost:8000/alerts/
- **AI Predictions**: http://localhost:8000/api/predict

### Frontend Application
- **Login Page**: http://localhost:5173/login
- **Signup Page**: http://localhost:5173/signup
- **Dashboard**: http://localhost:5173/dashboard

---

## 🧪 TESTING PROCEDURES

### 1. Backend Testing
```bash
cd backend
python test_multi_user_system.py
```

### 2. Frontend Testing
1. Open http://localhost:5173 in browser
2. Test user registration
3. Test user login
4. Test device management
5. Test alert system

### 3. Integration Testing
1. Create test user account
2. Add test device
3. Send sensor data with device_id
4. Verify predictions and alerts
5. Check database storage

---

## 📱 USER WORKFLOW

### 1. Registration & Login
1. Navigate to `/signup`
2. Enter email and password (min 8 characters)
3. Receive success message
4. Navigate to `/login`
5. Enter credentials
6. Receive JWT token
7. Redirect to dashboard

### 2. Device Management
1. Go to dashboard
2. Use device selector dropdown
3. Click "Add Device" (in future UI)
4. Configure device settings
5. Assign device to location

### 3. Monitoring & Alerts
1. Select device from dropdown
2. View real-time sensor data
3. Monitor AI predictions
4. Check health scores (0-100)
5. Review automatic alerts
6. Manage alert history

---

## 🗄️ DATABASE SCHEMA

### Users Collection
```javascript
{
  "_id": ObjectId,
  "email": "user@example.com",
  "password": "hashed_password",
  "full_name": "John Doe",
  "created_at": ISODate,
  "updated_at": ISODate,
  "is_active": true,
  "role": "user"
}
```

### Devices Collection
```javascript
{
  "_id": ObjectId,
  "user_id": "user_id",
  "device_id": "device_abc123",
  "device_name": "Living Room Sensor",
  "location": "Living Room",
  "description": "Main environmental sensor",
  "created_at": ISODate,
  "updated_at": ISODate,
  "is_active": true,
  "last_seen": ISODate
}
```

### Sensor Data Collection
```javascript
{
  "_id": ObjectId,
  "user_id": "user_id",
  "device_id": "device_abc123",
  "temperature": 25.5,
  "humidity": 60.0,
  "pressure": 1013.25,
  "gas_voltage": 1.8,
  "gas_ppm": 200.0,
  "prediction": 25.49,
  "health_score": 85,
  "status": "normal",
  "anomaly": false,
  "anomaly_score": 0.05,
  "timestamp": ISODate
}
```

### Alerts Collection
```javascript
{
  "_id": ObjectId,
  "user_id": "user_id",
  "device_id": "device_abc123",
  "message": "⚠️ Anomaly detected on device device_abc123",
  "severity": "danger",
  "alert_type": "anomaly",
  "is_read": false,
  "is_resolved": false,
  "created_at": ISODate,
  "resolved_at": null
}
```

---

## 🔧 API ENDPOINTS REFERENCE

### Authentication Endpoints
```
POST /auth/signup          # User registration
POST /auth/login           # User login
POST /auth/logout          # User logout
GET  /auth/me              # Get current user
GET  /auth/verify          # Verify token
```

### Device Management Endpoints
```
POST /devices/add          # Add new device
GET  /devices/list          # List user devices
GET  /devices/{device_id}  # Get device details
PUT  /devices/{device_id}  # Update device
DELETE /devices/{device_id} # Remove device
POST /devices/{device_id}/heartbeat # Update last seen
```

### Alert System Endpoints
```
GET  /alerts/              # List user alerts
POST /alerts/{id}/read     # Mark as read
POST /alerts/{id}/resolve  # Mark as resolved
DELETE /alerts/{id}        # Delete alert
POST /alerts/mark-all-read # Mark all as read
GET  /alerts/stats         # Alert statistics
```

### Enhanced Prediction Endpoints
```
POST /api/predict          # AI prediction with device mapping
GET  /api/predict/status    # Dual model status
```

---

## 🔒 SECURITY FEATURES

### JWT Authentication
- **Secure Token Generation**: 7-day expiration
- **Password Hashing**: bcrypt with salt
- **Token Validation**: Automatic token refresh
- **Protected Routes**: All API endpoints secured

### Data Protection
- **Input Validation**: Pydantic models for all inputs
- **SQL Injection Prevention**: MongoDB with parameterized queries
- **CORS Configuration**: Configurable origins
- **Rate Limiting**: Built-in FastAPI limits

### User Isolation
- **Data Segregation**: Users only see their own data
- **Device Ownership**: Strict user-device mapping
- **Alert Privacy**: User-specific alert system
- **Session Management**: Secure token handling

---

## 🚀 DEPLOYMENT GUIDE

### Development Environment
```bash
# Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend
npm run dev
```

### Production Environment
```bash
# Backend (with Gunicorn)
cd backend
pip install gunicorn
gunicorn app.main:app --workers 4 --bind 0.0.0.0:8000

# Frontend (Build)
cd frontend
npm run build
# Serve dist/ folder with nginx or apache
```

### Environment Variables (Production)
```bash
# Backend
MONGO_URI=<your_mongo_uri>
DATABASE_NAME=climascope_prod
JWT_SECRET=super_secure_production_key
CLIMASCOPE_CORS_ORIGINS=https://yourdomain.com

# Frontend
VITE_API_URL=https://api.yourdomain.com
```

---

## 🎯 KEY FEATURES

### Multi-User Support
- ✅ User registration and login
- ✅ JWT-based authentication
- ✅ Personalized dashboards
- ✅ User data isolation

### Device Management
- ✅ Multi-device per user
- ✅ Device registration and management
- ✅ Device health monitoring
- ✅ Last seen tracking

### Intelligent Alert System
- ✅ Automatic alert generation
- ✅ Severity-based routing
- ✅ Alert history and management
- ✅ Real-time notifications

### Enhanced AI Platform
- ✅ Device-aware predictions
- ✅ Anomaly detection integration
- ✅ Health score calculation
- ✅ Multi-sensor insights

### Database Integration
- ✅ MongoDB with async operations
- ✅ Optimized indexes
- ✅ Scalable architecture
- ✅ Data persistence

---

## 🐛 TROUBLESHOOTING

### Common Issues

#### Backend Won't Start
```bash
# Check MongoDB connection
mongosh --eval "db.adminCommand('ismaster')"

# Check environment variables
python -c "import os; print(os.environ.get('MONGO_URI'))"
```

#### Frontend Can't Connect
```bash
# Check backend status
curl http://localhost:8000/

# Check CORS configuration
curl -H "Origin: http://localhost:5173" http://localhost:8000/
```

#### Authentication Issues
```bash
# Check JWT secret
python -c "import os; print(os.environ.get('JWT_SECRET_KEY'))"

# Verify token manually
python -c "
import jwt
token = 'your_token_here'
try:
    payload = jwt.decode(token, algorithms=['HS256'])
    print('Token valid:', payload)
except:
    print('Token invalid')
"
```

---

## 📈 PERFORMANCE OPTIMIZATION

### Database Optimization
- **Indexes**: Created on frequently queried fields
- **Connection Pooling**: Motor async driver
- **Query Optimization**: Efficient pagination

### Frontend Optimization
- **Code Splitting**: Lazy loading for large apps
- **Caching**: Browser caching for static assets
- **Bundle Size**: Optimized build process

### API Optimization
- **Async Operations**: All database operations async
- **Response Compression**: gzip compression enabled
- **Rate Limiting**: Built-in FastAPI limits

---

## 🎉 SUCCESS CRITERIA

Your multi-user AI platform is successfully running when:

- ✅ Backend server starts without errors
- ✅ MongoDB connection established
- ✅ Frontend loads at http://localhost:5173
- ✅ User can register and login
- ✅ Dashboard displays user-specific data
- ✅ Device management works
- ✅ Alert system generates notifications
- ✅ AI predictions work with device mapping
- ✅ All API endpoints respond correctly

---

## 🚀 NEXT STEPS

1. **Deploy to Production**: Use Docker containers
2. **Add Email Notifications**: SMTP integration for alerts
3. **Implement WebSocket**: Real-time updates without polling
4. **Add Mobile App**: React Native or Flutter application
5. **Scale Database**: MongoDB Atlas for global deployment

---

## 📞 SUPPORT

For issues and questions:
1. Check API documentation: http://localhost:8000/docs
2. Review database logs
3. Check browser console for frontend errors
4. Verify environment variables
5. Test with provided test scripts

**🎯 Your ClimaScope Multi-User AI Platform is now ready for production deployment!**
