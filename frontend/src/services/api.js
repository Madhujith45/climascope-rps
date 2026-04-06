/**
 * ClimaScope – Axios API Service
 *
 * Set VITE_BACKEND_URL in your .env file (or Vercel environment variables)
 * to point at your Raspberry Pi / server backend, e.g.:
 *   VITE_BACKEND_URL=http://192.168.1.50:8000
 *
 * During local development the Vite dev-server proxy forwards /api/* to the
 * backend without stripping the /api prefix.
 */

import axios from 'axios'
import { getAuthToken } from './auth'

const BASE_URL =
  import.meta.env.VITE_BACKEND_URL?.replace(/\/$/, '') || ''

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: add auth token if available ──────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = getAuthToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Response interceptor: uniform error logging ───────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || 'Unknown error'
    console.error('[ClimaScope API]', err.config?.url, '→', msg)
    if (err.response?.status === 401) { localStorage.removeItem('token'); localStorage.removeItem('user'); window.location.href = '/login'; } return Promise.reject(err)
  }
)

// ── API methods ───────────────────────────────────────────────────────────────

/**
 * Fetch the N most recent sensor readings (default 10).
 * Returns an array sorted newest-first.
 * @param {number} n – number of records to return (1–100)
 * @returns {Promise<object[]>}
 */
export async function fetchLatest(n = 10) {
  const { data } = await api.get('/api/data/latest', { params: { n } })
  return Array.isArray(data) ? data : []
}

/**
 * Fetch historical readings (newest first).
 * @param {number}      limit    – max records per page (1–10000, default 1000)
 * @param {number}      offset   – pagination offset
 * @param {string|null} deviceId – filter to a specific device_id (optional)
 * @returns {Promise<{total: number, records: object[]}>}
 */
export async function fetchHistory(limit = 1000, offset = 0, deviceId = null) {
  const params = { limit, offset }
  if (deviceId && deviceId.trim()) params.device_id = deviceId.trim()
  const { data } = await api.get('/api/data/history', { params })
  return data
}

/**
 * Get temperature prediction from current sensor readings.
 * @param {object} reading - Sensor reading data
 * @param {number} reading.temperature - Current temperature (°C)
 * @param {number} reading.humidity - Humidity (%)
 * @param {number} reading.pressure - Atmospheric pressure (hPa)
 * @param {number} reading.gas_voltage - Gas sensor voltage (V)
 * @param {number} reading.gas_ppm - Gas concentration (PPM)
 * @returns {Promise<object>} Prediction result with status and confidence
 */
export async function getPrediction(reading) {
  const { data } = await api.post('/api/predict', reading)
  return data
}

/**
 * Get ML model status information.
 * @returns {Promise<object>} Model status details
 */
export async function getModelStatus() {
  const { data } = await api.get('/api/predict/status')
  return data
}

export default api


