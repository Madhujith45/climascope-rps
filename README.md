# ClimaScope

**AI-Driven Edge-Based Microclimate Intelligence & Risk Monitoring Payload**

ClimaScope is a research-level environmental monitoring system that runs **entirely at the edge**. All sensor fusion, statistical analysis, anomaly detection, and risk scoring happen on the Raspberry Pi — no cloud AI dependency required. The backend is a thin persistence/API layer; the frontend is a React dashboard hosted anywhere.

---

## Architecture Overview

```
┌──────────────────────────────────┐
│  Raspberry Pi 4 (Edge + Backend) │
│                                  │
│  ┌─────────────┐                 │
│  │  Sensors    │  DHT22, BMP280, │
│  │  (GPIO/I2C) │  MQ2+ADS1115   │
│  └──────┬──────┘                 │
│         │ raw readings           │
│  ┌──────▼────────────────────┐   │
│  │  Edge Processing Engine   │   │
│  │  • Rolling mean/std (n=10)│   │
│  │  • Rate-of-change         │   │
│  │  • Z-score anomaly detect │   │
│  │  • Weighted risk score    │   │
│  └──────┬────────────────────┘   │
│         │ processed payload      │
│  ┌──────▼──────┐  ┌───────────┐  │
│  │ Local SQLite│  │  FastAPI  │  │
│  │ (offline    │  │  Backend  │  │
│  │  buffer)    │  │  :8000    │  │
│  └─────────────┘  └─────┬─────┘  │
└────────────────────────/─────────┘
                         │ HTTP REST
        ┌────────────────▼────────────────┐
        │  React + Vite Frontend          │
        │  (Vercel / localhost:5173)       │
        │  Auto-refresh every 10 seconds  │
        └─────────────────────────────────┘
```

---

## Hardware Configuration

| Component     | Interface | Details                        |
|---------------|-----------|--------------------------------|
| Raspberry Pi 4| —         | 4 GB RAM, Raspberry Pi OS      |
| DHT22         | GPIO 4    | Temp + Humidity                |
| BMP280        | I2C 0x76  | Barometric pressure            |
| MQ2 Gas sensor| Analog    | Connected to ADS1115 A0        |
| ADS1115 ADC   | I2C 0x48  | 16-bit ADC for MQ2             |
| Li-ion + BMS  | —         | 5.1 V regulated via buck conv. |

---

## Risk Model

The risk score (0–100) is computed entirely on the edge using a weighted combination of five normalised components:

| Component                    | Weight |
|------------------------------|--------|
| Gas spike magnitude          | 30 %   |
| Pressure gradient            | 25 %   |
| Temperature rate-of-change   | 20 %   |
| Humidity rate-of-change      | 15 %   |
| Anomaly flag (Z-score > 2.5) | 10 %   |

**Classification:**
- **0–30** → `SAFE` (green)
- **31–65** → `MODERATE` (yellow)
- **66–100** → `HIGH` (red, pulsing)

---

## Project Structure

```
climascope/
├── edge/                    ← Runs on Raspberry Pi
│   ├── sensors/
│   │   ├── dht22.py         ← DHT22 driver
│   │   ├── bmp280.py        ← BMP280 driver
│   │   ├── mq2.py           ← MQ2 + ADS1115 driver
│   │   └── __init__.py
│   ├── processing/
│   │   ├── risk_engine.py   ← AI risk scoring pipeline
│   │   └── __init__.py
│   ├── storage/
│   │   ├── local_db.py      ← SQLite offline buffer
│   │   └── __init__.py
│   ├── communication/
│   │   ├── sender.py        ← HTTP POST + retry queue
│   │   └── __init__.py
│   ├── main.py              ← Edge entry point
│   ├── requirements.txt
│   └── .env.example
│
├── backend/                 ← Runs on Raspberry Pi
│   ├── app/
│   │   ├── main.py          ← FastAPI app + CORS
│   │   ├── database.py      ← SQLAlchemy async engine
│   │   ├── models.py        ← ORM models
│   │   ├── schemas.py       ← Pydantic v2 schemas
│   │   ├── routes/
│   │   │   ├── data_routes.py   ← POST /data, GET /latest, GET /history
│   │   │   ├── alert_routes.py  ← GET /alerts
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                ← Hosted on Vercel
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   ├── vercel.json
│   ├── .env.example
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── components/
│       │   ├── Dashboard.jsx    ← Main orchestrator + auto-refresh
│       │   ├── SensorCards.jsx  ← 4 metric cards
│       │   ├── RiskGauge.jsx    ← SVG circular gauge
│       │   ├── Charts.jsx       ← Chart.js line charts
│       │   └── AlertsPanel.jsx  ← Alert list
│       └── services/
│           └── api.js           ← Axios API client
│
└── README.md
```

---

## Setup Instructions

### Prerequisites

| Tool         | Version  |
|--------------|----------|
| Python       | ≥ 3.10   |
| Node.js      | ≥ 18     |
| npm          | ≥ 9      |
| Raspberry Pi | OS Bookworm / Bullseye (64-bit recommended) |

---

### 1. Raspberry Pi – System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Enable I2C
sudo raspi-config   # Interface Options → I2C → Enable

# Install Python build deps for Adafruit_DHT
sudo apt install -y python3-pip python3-dev libgpiod2 build-essential

# Verify I2C devices (should show 0x48 and 0x76)
sudo i2cdetect -y 1
```

---

### 2. Backend – Raspberry Pi

```bash
cd /home/pi/climascope/backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env to set CLIMASCOPE_CORS_ORIGINS to your Vercel domain.

# Run (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run as systemd service (production)
sudo nano /etc/systemd/system/climascope-backend.service
```

**systemd unit `/etc/systemd/system/climascope-backend.service`:**

```ini
[Unit]
Description=ClimaScope Backend
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/climascope/backend
EnvironmentFile=/home/pi/climascope/backend/.env
ExecStart=/home/pi/climascope/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable climascope-backend
sudo systemctl start climascope-backend
```

---

### 3. Edge – Raspberry Pi

```bash
cd /home/pi/climascope/edge

# Use the same venv as backend (or create a separate one)
source .venv/bin/activate

# Install edge-specific packages
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Set CLIMASCOPE_BACKEND_URL to http://localhost:8000
# (or remote URL if backend is elsewhere)
# Set CLIMASCOPE_INTERVAL=60

# Run (development)
python main.py

# Run as systemd service (production)
sudo nano /etc/systemd/system/climascope-edge.service
```

**systemd unit `/etc/systemd/system/climascope-edge.service`:**

```ini
[Unit]
Description=ClimaScope Edge Sensor Node
After=network.target climascope-backend.service

[Service]
User=pi
WorkingDirectory=/home/pi/climascope/edge
EnvironmentFile=/home/pi/climascope/edge/.env
ExecStart=/home/pi/climascope/backend/.venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable climascope-edge
sudo systemctl start climascope-edge

# Verify logs
journalctl -u climascope-edge -f
```

---

### 4. Frontend – Local Development

```bash
cd D:\climascope\frontend

# Install dependencies
npm install

# Configure environment
copy .env.example .env.local
# Edit .env.local: set VITE_BACKEND_URL=http://<PI_IP>:8000

# Start dev server
npm run dev
# → http://localhost:5173
```

---

### 5. Frontend – Vercel Deployment

```bash
# Option A: Vercel CLI
npm install -g vercel
cd D:\climascope\frontend
vercel

# Option B: GitHub integration
# 1. Push the entire repo to GitHub.
# 2. Import the project in https://vercel.com/new
# 3. Root Directory: frontend
# 4. Framework: Vite (auto-detected)
# 5. Add environment variable:
#      VITE_BACKEND_URL = http://<YOUR_PI_PUBLIC_IP_OR_TUNNEL>:8000
# 6. Deploy.
```

> **Tip – exposing the Pi backend publicly:**
> The Pi should be on a static LAN IP or use a tunnel (e.g. `ngrok`, Cloudflare Tunnel, or port-forwarding on your router) so Vercel can reach it.
>
> ```bash
> # Quick ngrok tunnel (for testing)
> ngrok http 8000
> # Copy the https URL and set it as VITE_BACKEND_URL in Vercel.
> ```

---

## API Reference

| Method | Endpoint   | Description                                      |
|--------|-----------|--------------------------------------------------|
| `POST` | `/data`   | Ingest one processed reading from the edge node  |
| `GET`  | `/latest` | Most recent reading                              |
| `GET`  | `/history?limit=100&offset=0` | Paginated history    |
| `GET`  | `/alerts?level=HIGH&limit=50` | Alert records only   |
| `GET`  | `/`       | Health check                                     |
| `GET`  | `/docs`   | Interactive Swagger UI                           |

---

## Integration Flow

```
Edge main.py
  │
  ├─ read_all_sensors()           # DHT22 + BMP280 + MQ2
  │
  ├─ process_reading(raw)         # risk_engine.py
  │   ├─ push to rolling buffers
  │   ├─ compute mean, std
  │   ├─ compute z-scores → anomaly flag
  │   ├─ compute ROC per metric
  │   └─ weighted risk score + classification
  │
  ├─ save_reading(processed)      # local_db.py  (always runs)
  │
  └─ post_reading(processed)      # sender.py
      ├─ POST /data → backend     (if reachable)
      └─ stays in SQLite queue    (if backend down)
          └─ flush_loop retries every 30 s
```

---

## Offline Operation

The edge node is fully autonomous:

1. If the backend is **unavailable**, readings are saved locally with `sent=0`.
2. A background thread runs `flush_unsent_queue()` every 30 seconds.
3. Once the backend becomes reachable, all queued records are delivered in FIFO order.
4. Old sent records are pruged after 7 days to manage disk space.

---

## License

MIT – see [LICENSE](LICENSE) for details.
