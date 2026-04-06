/**
 * ClimaScope – Next-Gen AI Dashboard
 * AI-driven content sections fetching data and rendering logic.
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { useOutletContext } from 'react-router-dom'
import { getAuthToken } from '../services/auth'
import { getPrediction } from '../services/api'
import toast from 'react-hot-toast'

import AIDecisionBox   from './AIDecisionBox'
import HeroSection     from './HeroSection'
import MetricGrid      from './MetricGrid'
import StatusBlock     from './StatusBlock'
import StabilityScore  from './StabilityScore'
import TrendChart      from './TrendChart'
import RiskTimeline    from './RiskTimeline'
import AlertsSection   from './AlertsSection'
import DevicePanel     from './DevicePanel'
import InsightsPanel   from './InsightsPanel'
import RiskGauge       from './RiskGauge'

const REFRESH_MS   = 10_000
const CHART_POINTS = 60

function parseReadingTimestamp(reading) {
  if (!reading) return null
  const raw = reading.timestamp || reading.created_at || reading.ts || reading.time
  if (!raw) return null
  const date = new Date(raw)
  return Number.isNaN(date.getTime()) ? null : date
}

function normalizeDeviceLabel(deviceId) {
  if (!deviceId) return deviceId
  return String(deviceId).trim() === 'climascope_001' ? 'climascope-pi001' : deviceId
}

function getRawReading(reading) {
  return reading?.raw || {}
}

function getProcessedReading(reading) {
  return reading?.processed || {}
}

export default function Dashboard() {
  const { selectedDevice, user } = useOutletContext()
  const [latestReading,  setLatestReading]  = useState(null)
  const [chartData,      setChartData]      = useState([])
  const [prediction,     setPrediction]     = useState(null)
  const [lastUpdated,    setLastUpdated]    = useState(null)
  const [loading,        setLoading]        = useState(true)
  const [error,          setError]          = useState('')

  // ── fetch latest sensor data ─────────────────────────────────────
  const fetchData = useCallback(async () => {
    const token = getAuthToken()
    if (!token) return

    const url = selectedDevice
      ? `/api/data/latest?n=${CHART_POINTS}&device_id=${selectedDevice}`
      : `/api/data/latest?n=${CHART_POINTS}`

    try {
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      if (!res.ok) throw new Error('Failed to fetch sensor data')
      const data = await res.json()
      const arr  = Array.isArray(data) ? data : [data]
      setChartData(arr)
      setLatestReading(arr[0] ?? null)
      setLastUpdated(Date.now())
      setError('')
    } catch (e) {
      if (!error) toast.error('Check server connection...')
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [selectedDevice, error])

  // ── fetch AI prediction ───────────────────────────────────────────
  const fetchPrediction = useCallback(async (reading) => {
    if (!reading) return
    const raw = getRawReading(reading)
    try {
      const result = await getPrediction({
        temperature: raw.temperature  ?? 0,
        humidity:    raw.humidity     ?? 50,
        pressure:    raw.pressure     ?? 1013,
        gas_voltage: raw.mq2_voltage  ?? raw.gas_voltage ?? 1.5,
        gas_ppm:     raw.gas          ?? raw.gas_ppm ?? 200,
      })
      setPrediction(result)
    } catch { /* silently ignore */ }
  }, [])

  // ── auto-refresh (10s) ───────────────────────────────────────────
  useEffect(() => {
    fetchData()
    const id = setInterval(fetchData, REFRESH_MS)
    return () => clearInterval(id)
  }, [fetchData])

  // ── trigger prediction when latest reading changes ───────────────
  useEffect(() => {
    if (latestReading) fetchPrediction(latestReading)
  }, [latestReading, fetchPrediction])

  // ── Context-aware tint ─────────────────────────────────────────
  const displayPrediction = useMemo(() => {
    if (!latestReading) return prediction

    const raw = getRawReading(latestReading)
    const processed = getProcessedReading(latestReading)
    const readingAnomaly = Boolean(processed?.anomaly ?? latestReading?.anomaly ?? latestReading?.anomaly_flag)
    const readingLevel = String(
      processed?.level || latestReading?.level || latestReading?.risk_level || latestReading?.risk_local || ''
    ).toUpperCase()
    const readingRiskScore = Number(processed?.risk_score ?? latestReading?.risk_score)
    const hasReadingRisk = readingLevel.length > 0 || Number.isFinite(readingRiskScore)

    if (!hasReadingRisk) return prediction

    let statusFromReading = 'normal'
    if (readingAnomaly || readingLevel === 'HIGH') {
      statusFromReading = 'danger'
    } else if (readingLevel === 'MODERATE' || (Number.isFinite(readingRiskScore) && readingRiskScore >= 50)) {
      statusFromReading = 'warning'
    }

    return {
      ...(prediction || {}),
      status: statusFromReading,
      anomaly: readingAnomaly,
      health_score: Number.isFinite(readingRiskScore)
        ? Math.max(0, Math.min(100, 100 - readingRiskScore))
        : prediction?.health_score,
    }
  }, [latestReading, prediction])

  const connectionInfo = useMemo(() => {
    const latestTs = parseReadingTimestamp(latestReading)
    const latestDeviceId = normalizeDeviceLabel(latestReading?.device_id || null)
    const dataAgeMs = latestTs ? Date.now() - latestTs.getTime() : Number.POSITIVE_INFINITY
    const isFresh = Number.isFinite(dataAgeMs) && dataAgeMs <= 45_000
    const hasDevice = Boolean(latestDeviceId)

    if (hasDevice && isFresh) {
      return {
        connected: true,
        label: `Connected to Pi (${latestDeviceId})`,
        helper: 'Receiving real-time sensor data',
      }
    }

    if (chartData.length > 0) {
      return {
        connected: false,
        label: 'No device connected',
        helper: 'Showing history from stored data',
      }
    }

    return {
      connected: false,
      label: 'No device connected',
      helper: 'Connect Pi (climascope) to get real-time data',
    }
  }, [latestReading, chartData])

  const status = displayPrediction?.status || 'normal'
  const contextTint =
    status === 'danger'
      ? 'radial-gradient(ellipse 100% 40% at 50% 0%, rgba(239,68,68,0.04) 0%, transparent 60%)'
      : status === 'warning'
      ? 'radial-gradient(ellipse 100% 40% at 50% 0%, rgba(245,158,11,0.03) 0%, transparent 60%)'
      : 'none'

  // Determine if a metric should glow red (alert highlight)
  const alertMetric = displayPrediction?.anomaly
    ? (Number(getProcessedReading(latestReading)?.gas_ppm ?? getRawReading(latestReading)?.gas) > 200 ? 'gas_ppm' : 'temperature')
    : null

  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-12 overflow-y-auto page-in" style={{ backgroundImage: contextTint }}>
      {/* Error Banner */}
      {error && (
        <div className="mb-5 flex items-center gap-3 rounded-2xl border border-red-500/20 bg-red-500/10 px-5 py-3.5 text-sm text-red-300">
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error === 'Failed to fetch sensor data' ? 'Server unavailable — retrying automatically…' : error}
        </div>
      )}

      <div className="mb-5 flex items-center justify-between rounded-2xl border px-4 py-3"
           style={{
             borderColor: connectionInfo.connected ? 'rgba(74,128,64,0.4)' : 'rgba(184,134,11,0.35)',
             background: connectionInfo.connected ? 'rgba(74,128,64,0.12)' : 'rgba(184,134,11,0.10)'
           }}>
        <div>
          <p className="text-sm font-semibold" style={{ color: connectionInfo.connected ? '#8fd488' : '#d9b260' }}>
            {connectionInfo.label}
          </p>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {connectionInfo.helper}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
          <span className="inline-block h-2 w-2 rounded-full"
                style={{ background: connectionInfo.connected ? '#4a8040' : '#b8860b' }} />
          {connectionInfo.connected ? 'Live' : 'Offline'}
        </div>
      </div>

      {/* ── AI Decision Box (top) ──────────────────────────── */}
      <AIDecisionBox
        prediction={displayPrediction}
        data={latestReading}
        chartData={chartData}
        loading={loading}
      />

      {/* ── Hero Section ─────────────────────────────────────── */}
      <HeroSection data={latestReading} prediction={displayPrediction} loading={loading} />

      {/* ── Core Metrics Grid ────────────────────────────────── */}
      <div className="mt-7">
        <MetricGrid data={latestReading} chartData={chartData} loading={loading} alertMetric={alertMetric} />
      </div>

      {/* ── Row: Status Block + Stability Score + Risk Gauge ─────────────── */}
      <div className="mt-7 grid gap-5 lg:grid-cols-6">
        <div className="lg:col-span-2">
          <StatusBlock prediction={displayPrediction} loading={loading || !displayPrediction} />
        </div>
        <div className="lg:col-span-2">
          <StabilityScore prediction={displayPrediction} data={latestReading} loading={loading || !displayPrediction} />
        </div>
        <div className="lg:col-span-2">
          <RiskGauge 
            score={latestReading?.processed?.risk_score} 
            riskLevel={latestReading?.processed?.level} 
            anomalyFlag={latestReading?.processed?.anomaly} 
            riskReason={null} 
          />
        </div>
      </div>

      {/* ── Row: Trend Chart + Insights + Risk ─────────────── */}
      <div className="mt-7 grid gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TrendChart data={chartData} loading={loading} />
        </div>
        <div className="lg:col-span-1 flex flex-col gap-5">
          <InsightsPanel prediction={displayPrediction} data={latestReading} loading={loading || !displayPrediction} />
          <RiskTimeline prediction={displayPrediction} chartData={chartData} loading={loading || !displayPrediction} />
        </div>
      </div>

      {/* ── Row: Alerts + Device Panel ───────────────────────── */}
      <div className="mt-7 grid gap-5 lg:grid-cols-2">
        <AlertsSection />
        <DevicePanel selectedDevice={selectedDevice} onDeviceChange={() => {}} />
      </div>

      {!loading && !latestReading && !error && (
        <div className="mt-12 mb-10 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
          No sensor data received from devices. Waiting for devices...
        </div>
      )}
    </div>
  )
}

