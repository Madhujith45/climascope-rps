/**
 * ClimaScope – Hero Section
 * Large temperature display + AI insight text
 */
import React, { useEffect, useState } from 'react'

function getAIInsight(data, prediction) {
  if (!data && !prediction) return 'Connecting to sensors…'
  const status = prediction?.status || 'normal'
  const anomaly = prediction?.anomaly
  const temp    = data?.temperature

  if (anomaly)        return 'Anomaly detected — environmental conditions deviate from baseline.'
  if (status === 'danger')  return 'Critical conditions detected. Immediate attention required.'
  if (status === 'warning') return 'Warning: sensor readings approaching threshold limits.'

  const t = Number(temp)
  if (!isNaN(t)) {
    if (t < 18) return `Temperature is ${t.toFixed(1)}°C — cool and stable environment detected.`
    if (t > 35) return `Temperature is ${t.toFixed(1)}°C — elevated conditions, monitor closely.`
    return `Air quality is stable. Temperature ${t.toFixed(1)}°C — no anomalies detected.`
  }
  return 'Environmental conditions are nominal. AI monitoring active.'
}

export default function HeroSection({ data, prediction, loading }) {
  const [displayed, setDisplayed] = useState('')
  const temp = data?.temperature

  // Typewriter effect for AI insight
  const insight = getAIInsight(data, prediction)
  useEffect(() => {
    setDisplayed('')
    let i = 0
    const id = setInterval(() => {
      setDisplayed(insight.slice(0, i + 1))
      i++
      if (i >= insight.length) clearInterval(id)
    }, 22)
    return () => clearInterval(id)
  }, [insight])

  const statusColor = prediction?.status === 'danger'
    ? '#ef4444'
    : prediction?.status === 'warning'
    ? '#f59e0b'
    : '#22c55e'

  return (
    <div
      className="relative glass-card-static overflow-hidden slide-up"
      style={{
        padding: '32px 36px',
        background: `radial-gradient(ellipse 70% 80% at 10% 50%, rgba(20,184,166,0.1) 0%, transparent 60%),
                     radial-gradient(ellipse 50% 60% at 90% 20%, rgba(59,130,246,0.08) 0%, transparent 50%),
                     rgba(13,21,32,0.85)`,
      }}
    >
      {/* Subtle grid texture */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.8) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.8) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative flex flex-col md:flex-row md:items-center gap-8">
        {/* Left: title + insight */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-3">
            <span
              className="inline-block rounded-full text-xs font-semibold px-3 py-1"
              style={{
                background: 'rgba(20,184,166,0.15)',
                border: '1px solid rgba(20,184,166,0.3)',
                color: '#2dd4bf',
              }}
            >
              ⚡ Live Intelligence
            </span>
          </div>
          <h2 className="text-3xl font-bold text-white mb-2 leading-tight">
            Environmental Overview
          </h2>
          <p
            className="text-base leading-relaxed max-w-lg"
            style={{ color: 'var(--text-secondary)', minHeight: 48 }}
          >
            {displayed}
            <span className="animate-pulse ml-0.5" style={{ color: 'var(--teal-400)' }}>|</span>
          </p>

          {/* Quick stats row */}
          {data && (
            <div className="flex flex-wrap gap-4 mt-5">
              {[
                { label: 'Humidity',  value: data.humidity  != null ? `${Number(data.humidity).toFixed(1)}%` : '—', color: '#60a5fa' },
                { label: 'Pressure',  value: data.pressure  != null ? `${Number(data.pressure).toFixed(0)} hPa` : '—', color: '#a78bfa' },
                { label: 'Gas PPM',   value: data.gas_ppm   != null ? `${Number(data.gas_ppm).toFixed(0)} ppm` : '—', color: '#2dd4bf' },
              ].map(s => (
                <div key={s.label} className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: s.color }} />
                  <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{s.label}</span>
                  <span className="text-sm font-semibold" style={{ color: s.color }}>{s.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Big temperature */}
        <div className="flex flex-col items-center shrink-0">
          {loading ? (
            <div className="skeleton w-40 h-24 rounded-2xl" />
          ) : (
            <div className="text-center">
              <div
                className="metric-value number-pop"
                style={{
                  fontSize: 'clamp(64px, 8vw, 88px)',
                  fontWeight: 800,
                  lineHeight: 1,
                  color: statusColor,
                  textShadow: `0 0 40px ${statusColor}55`,
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {temp != null ? Number(temp).toFixed(1) : '—'}
              </div>
              <div className="text-xl font-semibold mt-1" style={{ color: 'var(--text-secondary)' }}>°C</div>
              <div className="text-xs mt-2 font-medium uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
                Temperature
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
