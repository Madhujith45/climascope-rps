/**
 * ClimaScope - Smart Metric Grid
 * 4 premium cards with trend arrows, status text, mini predictions, sparklines
 */
import React, { useMemo, useRef, useEffect, useState } from 'react'

const METRICS = [
  { key: 'temperature', label: 'Temperature', unit: '°C', color: '#4a8040', min: 15, max: 45,
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z" /></svg> },
  { key: 'humidity', label: 'Humidity', unit: '%', color: '#4a8040', min: 0, max: 100,
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" /></svg> },
  { key: 'gas_ppm', label: 'Air Quality', unit: 'ppm', color: '#b8860b', min: 0, max: 500,
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg> },
  { key: 'pressure', label: 'Pressure', unit: 'hPa', color: '#b8860b', min: 980, max: 1040,
    icon: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg> },
]

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `${r},${g},${b}`
}

function getTrend(chartData, key) {
  if (!chartData || chartData.length < 6) return { dir: 'stable', delta: 0, text: 'Stable' }
  const recent = chartData.slice(0, 5).map(r => Number(r[key])).filter(v => !isNaN(v))
  const older  = chartData.slice(5, 15).map(r => Number(r[key])).filter(v => !isNaN(v))
  if (recent.length < 2 || older.length < 2) return { dir: 'stable', delta: 0, text: 'Stable' }
  const avgR = recent.reduce((a, b) => a + b, 0) / recent.length
  const avgO = older.reduce((a, b) => a + b, 0) / older.length
  const delta = avgR - avgO
  const abs = Math.abs(delta)
  if (delta > 0.5) {
    return { dir: 'up', delta, text: abs > 3 ? 'Rising fast' : 'Increasing slowly' }
  }
  if (delta < -0.5) {
    return { dir: 'down', delta, text: abs > 3 ? 'Dropping fast' : 'Decreasing slowly' }
  }
  return { dir: 'stable', delta: 0, text: 'Holding steady' }
}

function getPredText(trend, metric) {
  if (trend.dir === 'stable') return null
  const sign = trend.dir === 'up' ? '+' : ''
  const pred = trend.delta * 6 // rough 30min projection (6 x 5min intervals)
  const val  = metric.key === 'pressure' ? Math.round(pred) : pred.toFixed(1)
  return `${sign}${val}${metric.unit} in ~30 min`
}

function Sparkline({ values, color }) {
  if (!values || values.length < 2) return null
  const W = 72, H = 28
  const min = Math.min(...values), max = Math.max(...values)
  const range = max - min || 1
  const pts = values.map((v, i) => `${((i / (values.length - 1)) * W).toFixed(1)},${(H - ((v - min) / range) * H * 0.8 - H * 0.1).toFixed(1)}`).join(' ')
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} className="overflow-visible">
      <polyline points={pts} stroke={color} strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function AnimatedNumber({ value, decimals = 1, color }) {
  const [displayed, setDisplayed] = useState(value)
  const prevRef = useRef(value)

  useEffect(() => {
    const from = prevRef.current, to = value
    if (from === to || isNaN(from) || isNaN(to)) { setDisplayed(to); prevRef.current = to; return }
    let start = null
    const dur = 400
    function step(ts) {
      if (!start) start = ts
      const p = Math.min((ts - start) / dur, 1)
      const eased = 1 - Math.pow(1 - p, 3) // ease out cubic
      setDisplayed(from + (to - from) * eased)
      if (p < 1) requestAnimationFrame(step)
      else prevRef.current = to
    }
    requestAnimationFrame(step)
  }, [value])

  return (
    <span className="metric-value text-3xl font-bold" style={{ color, textShadow: `0 0 20px rgba(${hexToRgb(color)},0.3)` }}>
      {displayed.toFixed(decimals)}
    </span>
  )
}

function MetricCard({ metric, data, chartData, isGlowing }) {
  const raw = data?.[metric.key]
  const value = raw != null ? Number(raw) : null
  const pct = value != null ? Math.min(100, Math.max(0, ((value - metric.min) / (metric.max - metric.min)) * 100)) : 0
  const barColor = pct > 80 ? '#a04030' : pct > 55 ? '#f59e0b' : metric.color

  const trend = getTrend(chartData, metric.key)
  const predText = value != null ? getPredText(trend, metric) : null

  const sparkValues = useMemo(() =>
    chartData.slice(0, 20).reverse().map(r => r[metric.key]).filter(v => v != null).map(Number), [chartData, metric.key])

  return (
    <div
      className="glass-card p-6 flex flex-col gap-2 transition-all duration-300"
      style={isGlowing ? { borderColor: 'rgba(239,68,68,0.5)', boxShadow: '0 0 24px rgba(160,64,48,0.35)' } : {}}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center justify-center rounded-xl"
             style={{ width: 42, height: 42, background: `rgba(${hexToRgb(metric.color)},0.14)`, color: metric.color, border: `1px solid rgba(${hexToRgb(metric.color)},0.25)` }}>
          {metric.icon}
        </div>
        <Sparkline values={sparkValues} color={metric.color} />
      </div>

      {/* Label + trend arrow */}
      <div>
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>{metric.label}</span>
          {value != null && (
            <span className="text-xs font-bold" style={{ color: trend.dir === 'up' ? '#b8860b' : trend.dir === 'down' ? '#9ca3af' : '#4a8040' }}>
              {trend.dir === 'up' ? '↑' : trend.dir === 'down' ? '↓' : '→'}
            </span>
          )}
        </div>
        <div className="flex items-baseline gap-2">
          {value != null ? (
            <AnimatedNumber value={value} decimals={metric.key === 'pressure' ? 0 : 1} color={metric.color} />
          ) : (
            <span className="text-3xl font-bold" style={{ color: metric.color }}>-</span>
          )}
          <span className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>{metric.unit}</span>
        </div>
      </div>

      {/* Status text + mini prediction */}
      {value != null && (
        <div className="text-xs space-y-1 mt-1" style={{ color: 'var(--text-muted)' }}>
          <div>{trend.text}</div>
          {predText && (
            <div style={{ color: trend.dir === 'up' ? '#b8860b' : 'rgba(255,255,255,0.7)' }}>
              ETA {predText}
            </div>
          )}
        </div>
      )}

      {/* Progress bar */}
      <div className="mt-auto pt-2">
        <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
          <div className="h-full rounded-full transition-all duration-700"
               style={{ width: `${pct}%`, background: barColor, boxShadow: `0 0 12px ${barColor}66` }} />
        </div>
      </div>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="glass-card-static p-5 flex flex-col gap-3">
      <div className="flex justify-between"><div className="skeleton w-10 h-10 rounded-xl" /><div className="skeleton w-20 h-7 rounded-lg" /></div>
      <div><div className="skeleton w-16 h-3 rounded mb-2" /><div className="skeleton w-24 h-8 rounded" /></div>
      <div className="skeleton w-full h-1 rounded-full mt-auto" />
    </div>
  )
}

export default function MetricGrid({ data, chartData, loading, alertMetric }) {
  if (loading) return <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{METRICS.map(m => <SkeletonCard key={m.key} />)}</div>
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {METRICS.map(m => <MetricCard key={m.key} metric={m} data={data} chartData={chartData} isGlowing={alertMetric === m.key} />)}
    </div>
  )
}




