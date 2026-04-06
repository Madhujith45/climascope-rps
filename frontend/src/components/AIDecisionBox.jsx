/**
 * ClimaScope - AI Decision Box
 * Dynamic intelligence bar: recommendation + confidence + trend direction
 */
import React, { useEffect, useState } from 'react'

function getTrend(chartData, key) {
  if (!chartData || chartData.length < 6) return { dir: 'stable', delta: 0 }
  const recent = chartData.slice(0, 5).map(r => Number(r[key])).filter(v => !isNaN(v))
  const older  = chartData.slice(5, 15).map(r => Number(r[key])).filter(v => !isNaN(v))
  if (recent.length < 2 || older.length < 2) return { dir: 'stable', delta: 0 }
  const avgR = recent.reduce((a, b) => a + b, 0) / recent.length
  const avgO = older.reduce((a, b) => a + b, 0) / older.length
  const delta = avgR - avgO
  if (delta > 1)  return { dir: 'rising',  delta }
  if (delta < -1) return { dir: 'falling', delta }
  return { dir: 'stable', delta }
}

function getDecision(prediction, data, chartData) {
  if (!prediction || !data) return { text: 'Connecting to AI system...', severity: 'info', why: '' }

  const gasTrend  = getTrend(chartData, 'gas_ppm')
  const tempTrend = getTrend(chartData, 'temperature')
  const gas  = Number(data.gas_ppm)
  const temp = Number(data.temperature)

  if (prediction.anomaly) {
    const why = gasTrend.dir === 'rising'
      ? `Gas level increased by ${Math.abs(gasTrend.delta).toFixed(1)} ppm in last 10 readings.`
      : tempTrend.dir === 'rising'
      ? `Temperature rose by ${Math.abs(tempTrend.delta).toFixed(1)}°C recently.`
      : 'Multiple sensor values deviate from the learned baseline.'
    return { text: 'Anomaly detected - review environmental conditions immediately.', severity: 'danger', why }
  }

  if (prediction.status === 'danger') {
    return {
      text: 'Critical conditions detected. Consider evacuation or ventilation.',
      severity: 'danger',
      why: `Temperature: ${temp.toFixed(1)}°C, Gas: ${gas.toFixed(0)} ppm - both exceed safe thresholds.`,
    }
  }

  if (prediction.status === 'warning' || gas > 200) {
    return {
      text: 'Gas levels rising. Recommend opening ventilation.',
      severity: 'warning',
      why: gasTrend.dir === 'rising'
        ? `Gas levels increased ${Math.abs(gasTrend.delta).toFixed(1)} ppm over recent readings.`
        : `Gas at ${gas.toFixed(0)} ppm is approaching the warning threshold.`,
    }
  }

  if (temp > 32) {
    return {
      text: 'Temperature elevated, otherwise stable. Monitor for changes.',
      severity: 'warning',
      why: `Temperature at ${temp.toFixed(1)}°C - above comfortable range.`,
    }
  }

  return {
    text: 'System is stable. No action required.',
    severity: 'safe',
    why: 'All environmental parameters within normal range for the last 10 minutes.',
  }
}

const ARROW = {
  rising:  { icon: '↑', label: 'Rising',  color: '#b8860b' },
  falling: { icon: '↓', label: 'Falling', color: '#9ca3af' },
  stable:  { icon: '→', label: 'Stable',  color: '#4a8040' },
}

const SEV_STYLE = {
  safe:    { bg: 'rgba(34, 197, 94, 0.12)',  border: 'rgba(34,197,94,0.4)',  glow: '0 0 30px rgba(200,168,64,0.18)',  icon: 'OK', color: '#4a8040' },
  warning: { bg: 'rgba(251,146,60,0.08)', border: 'rgba(251,146,60,0.2)', glow: '0 0 30px rgba(251,146,60,0.15)', icon: 'WARNING', color: '#fdba74' },
  danger:  { bg: 'rgba(160,64,48,0.12)',  border: 'rgba(160,64,48,0.35)',  glow: '0 0 30px rgba(239,68,68,0.12)',  icon: 'ALERT', color: '#e8b0a6' },
  info:    { bg: 'rgba(255,255,255,0.06)', border: 'rgba(138, 128, 96, 0.2)', glow: '0 0 30px rgba(200,168,64,0.18)', icon: 'AI', color: 'rgba(255,255,255,0.75)' },
}

export default function AIDecisionBox({ prediction, data, chartData, loading }) {
  const [showWhy, setShowWhy] = useState(false)
  const { text, severity, why } = getDecision(prediction, data, chartData)
  const s = SEV_STYLE[severity] || SEV_STYLE.info
  const tempTrend = getTrend(chartData, 'temperature')
  const arrow = ARROW[tempTrend.dir]
  const confidence = prediction?.confidence

  if (loading) {
    return <div className="skeleton h-16 w-full rounded-2xl mb-4" />
  }

  return (
    <div
      className="rounded-2xl px-5 py-4 mb-5 transition-all duration-300 slide-up"
      style={{ background: s.bg, border: `1px solid ${s.border}`, boxShadow: s.glow }}
    >
      <div className="flex items-center gap-3 flex-wrap">
        {/* Icon */}
        <span className="text-lg shrink-0">{s.icon}</span>

        {/* Main decision text */}
        <span className="font-medium text-sm flex-1 min-w-0" style={{ color: s.color }}>
          {text}
        </span>

        {/* Trend arrow */}
        <div
          className="flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-semibold shrink-0"
          style={{ background: 'rgba(255,255,255,0.06)', color: arrow.color }}
        >
          <span className="text-base">{arrow.icon}</span>
          {arrow.label}
        </div>

        {/* Confidence */}
        {confidence != null && (
          <div className="flex items-center gap-1.5 text-xs shrink-0" style={{ color: 'var(--text-muted)' }}>
            <span className="font-medium" style={{ color: confidence >= 0.8 ? '#86efac' : confidence >= 0.6 ? '#fde68a' : '#e8b0a6' }}>
              {Math.round(confidence * 100)}%
            </span>
            confidence
          </div>
        )}

        {/* Why button */}
        {why && (
          <button
            onClick={() => setShowWhy(!showWhy)}
            className="text-xs font-medium rounded-lg px-2 py-1 transition-opacity hover:opacity-70"
            style={{ background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.7)' }}
          >
            {showWhy ? 'Hide' : 'Why?'}
          </button>
        )}
      </div>

      {/* Why explanation collapsible */}
      {showWhy && why && (
        <div
          className="mt-3 pt-3 text-xs leading-relaxed"
          style={{ borderTop: `1px solid ${s.border}`, color: 'var(--text-secondary)' }}
        >
          Insight: {why}
        </div>
      )}
    </div>
  )
}





