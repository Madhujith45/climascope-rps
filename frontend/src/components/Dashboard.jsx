/**
 * ClimaScope – Next-Gen AI Dashboard
 * AI-driven content sections fetching data and rendering logic.
 */
import React, { useState, useEffect, useCallback } from 'react'
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
    try {
      const result = await getPrediction({
        temperature: reading.temperature  ?? 0,
        humidity:    reading.humidity      ?? 50,
        pressure:    reading.pressure      ?? 1013,
        gas_voltage: reading.mq2_voltage   ?? 1.5,
        gas_ppm:     reading.gas_ppm       ?? 200,
      })
      setPrediction(result)
    } catch { /* silently ignore */ }
  }, [])

  // ── auto-refresh (3.5s) ──────────────────────────────────────────
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
  const status = prediction?.status || 'normal'
  const contextTint =
    status === 'danger'
      ? 'radial-gradient(ellipse 100% 40% at 50% 0%, rgba(239,68,68,0.04) 0%, transparent 60%)'
      : status === 'warning'
      ? 'radial-gradient(ellipse 100% 40% at 50% 0%, rgba(245,158,11,0.03) 0%, transparent 60%)'
      : 'none'

  // Determine if a metric should glow red (alert highlight)
  const alertMetric = prediction?.anomaly
    ? (Number(latestReading?.gas_ppm) > 200 ? 'gas_ppm' : 'temperature')
    : null

  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in" style={{ backgroundImage: contextTint }}>
      {/* Error Banner */}
      {error && (
        <div className="mb-5 flex items-center gap-3 rounded-2xl border border-red-500/20 bg-red-500/10 px-5 py-3 text-sm text-red-300">
          <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error === 'Failed to fetch sensor data' ? 'Server unavailable — retrying automatically…' : error}
        </div>
      )}

      {/* ── AI Decision Box (top) ──────────────────────────── */}
      <AIDecisionBox
        prediction={prediction}
        data={latestReading}
        chartData={chartData}
        loading={loading}
      />

      {/* ── Hero Section ─────────────────────────────────────── */}
      <HeroSection data={latestReading} prediction={prediction} loading={loading} />

      {/* ── Core Metrics Grid ────────────────────────────────── */}
      <div className="mt-6">
        <MetricGrid data={latestReading} chartData={chartData} loading={loading} alertMetric={alertMetric} />
      </div>

      {/* ── Row: Status Block + Stability Score + Risk Gauge ─────────────── */}
      <div className="mt-6 grid gap-5 lg:grid-cols-6">
        <div className="lg:col-span-2">
          <StatusBlock prediction={prediction} loading={loading || !prediction} />
        </div>
        <div className="lg:col-span-2">
          <StabilityScore prediction={prediction} data={latestReading} loading={loading || !prediction} />
        </div>
        <div className="lg:col-span-2">
          <RiskGauge 
            score={latestReading?.risk_score} 
            riskLevel={latestReading?.level} 
            anomalyFlag={latestReading?.anomaly} 
            riskReason={null} 
          />
        </div>
      </div>

      {/* ── Row: Trend Chart + Insights + Risk ─────────────── */}
      <div className="mt-6 grid gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TrendChart data={chartData} loading={loading} />
        </div>
        <div className="lg:col-span-1 flex flex-col gap-5">
          <InsightsPanel prediction={prediction} data={latestReading} loading={loading || !prediction} />
          <RiskTimeline prediction={prediction} chartData={chartData} loading={loading || !prediction} />
        </div>
      </div>

      {/* ── Row: Alerts + Device Panel ───────────────────────── */}
      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <AlertsSection />
        <DevicePanel selectedDevice={selectedDevice} onDeviceChange={() => {}} />
      </div>

      {!loading && !latestReading && !error && (
        <div className="mt-10 mb-10 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
          No sensor data received from devices. Waiting for devices...
        </div>
      )}
    </div>
  )
}
