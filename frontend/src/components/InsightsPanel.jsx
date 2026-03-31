/**
 * ClimaScope – AI Insights Panel
 * Human-readable summarized intelligence
 */
import React from 'react'

function getInsights(prediction, data) {
  const items = []
  if (!prediction || !data) return items

  const temp    = data.temperature
  const humidity = data.humidity
  const gasPpm  = data.gas_ppm

  if (temp != null) {
    const t = Number(temp)
    if (t > 32)      items.push({ icon: '🌡️', text: 'Temperature elevated — consider ventilation.', severity: 'warn' })
    else if (t < 16) items.push({ icon: '❄️', text: 'Temperature is low — check heating conditions.', severity: 'info' })
    else             items.push({ icon: '✅', text: `Temperature ${t.toFixed(1)}°C is within optimal range.`, severity: 'safe' })
  }

  if (humidity != null) {
    const h = Number(humidity)
    if (h > 80)      items.push({ icon: '💧', text: 'Humidity very high — risk of condensation.', severity: 'warn' })
    else if (h < 30) items.push({ icon: '🏜️', text: 'Air is dry — consider adding moisture.', severity: 'info' })
    else             items.push({ icon: '✅', text: `Humidity ${h.toFixed(0)}% is comfortable.`, severity: 'safe' })
  }

  if (gasPpm != null) {
    const g = Number(gasPpm)
    if (g > 300)     items.push({ icon: '⚠️', text: 'Gas levels rising — ensure proper ventilation.', severity: 'danger' })
    else if (g > 150) items.push({ icon: '🔍', text: 'Gas slightly above baseline. Monitor closely.', severity: 'warn' })
    else             items.push({ icon: '✅', text: 'Air quality is clean. Gas levels nominal.', severity: 'safe' })
  }

  if (prediction.anomaly) {
    items.unshift({ icon: '🤖', text: 'ML model detected an anomaly in sensor pattern.', severity: 'danger' })
  }

  return items.slice(0, 5)
}

const SEV_COLORS = {
  safe:   { bg: 'rgba(34,197,94,0.08)',  border: 'rgba(34,197,94,0.2)',  text: '#86efac' },
  warn:   { bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', text: '#fde68a' },
  danger: { bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.2)',  text: '#fca5a5' },
  info:   { bg: 'rgba(96,165,250,0.08)', border: 'rgba(96,165,250,0.2)', text: '#bfdbfe' },
}

export default function InsightsPanel({ prediction, data, loading }) {
  const insights = getInsights(prediction, data)

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-5">
        <div
          className="flex items-center justify-center rounded-xl"
          style={{
            width: 36, height: 36,
            background: 'rgba(20,184,166,0.12)',
            border: '1px solid rgba(20,184,166,0.2)',
            color: '#2dd4bf',
          }}
        >
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div>
          <div className="text-sm font-semibold text-white">AI Insights</div>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>Human-readable analysis</div>
        </div>
      </div>

      <div className="flex-1 flex flex-col gap-3 overflow-y-auto">
        {loading ? (
          [1,2,3].map(i => <div key={i} className="skeleton h-12 rounded-xl" />)
        ) : insights.length === 0 ? (
          <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
            <div className="text-2xl mb-2">🔍</div>
            <div className="text-sm">Awaiting sensor data…</div>
          </div>
        ) : insights.map((item, i) => {
          const c = SEV_COLORS[item.severity] || SEV_COLORS.info
          return (
            <div
              key={i}
              className="flex items-start gap-3 rounded-xl px-3 py-2.5"
              style={{ background: c.bg, border: `1px solid ${c.border}` }}
            >
              <span className="text-base shrink-0 mt-0.5">{item.icon}</span>
              <span className="text-xs leading-relaxed" style={{ color: c.text }}>{item.text}</span>
            </div>
          )
        })}
      </div>

      {prediction?.timestamp && (
        <div className="mt-4 text-xs text-right" style={{ color: 'var(--text-muted)' }}>
          Analyzed {new Date(prediction.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  )
}
