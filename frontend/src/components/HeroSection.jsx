/**
 * ClimaScope - Hero Section
 * Large temperature display + AI insight text
 */
import React, { useEffect, useState } from 'react'

function getAIInsight(data, prediction) {
  if (!data && !prediction) return 'Connecting to sensors...'
  const status = prediction?.status || 'normal'
  const anomaly = prediction?.anomaly
  const temp    = data?.temperature

  if (anomaly)        return 'Anomaly detected - environmental conditions deviate from baseline.'
  if (status === 'danger')  return 'Critical conditions detected. Immediate attention required.'
  if (status === 'warning') return 'Warning: sensor readings approaching threshold limits.'

  const t = Number(temp)
  if (!isNaN(t)) {
    if (t < 18) return `Temperature is ${t.toFixed(1)}°C - cool and stable environment detected.`
    if (t > 35) return `Temperature is ${t.toFixed(1)}°C - elevated conditions, monitor closely.`
    return `Air quality is stable. Temperature ${t.toFixed(1)}°C - no anomalies detected.`
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

  return (
    <div
      className="relative glass-card-static overflow-hidden slide-up"
      style={{
        padding: '20px',
        background: `linear-gradient(90deg, rgba(200,168,64,0.18), rgba(200,168,64,0.08)), rgba(30, 35, 20, 0.6)`,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.35)',
      }}
    >
      <div className="relative flex flex-col md:flex-row md:items-center gap-8">
        {/* Left: title + temperature */}
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] mb-3" style={{ color: 'var(--text-secondary)' }}>
            Environmental Overview
          </div>

          {loading ? (
            <div className="skeleton w-40 h-20 rounded-2xl mb-3" />
          ) : (
            <div className="flex items-end gap-2 mb-3">
              <div
                className="metric-value"
                style={{
                  fontSize: 'clamp(56px, 7vw, 72px)',
                  lineHeight: 0.95,
                  fontWeight: 800,
                  color: '#9a6f08',
                  textShadow: '0 0 24px rgba(200,168,64,0.25)',
                }}
              >
                {temp != null ? Number(temp).toFixed(1) : '-'}
              </div>
              <div className="text-5xl font-bold" style={{ color: 'var(--text-secondary)' }}>°c</div>
            </div>
          )}

          <p className="text-lg leading-relaxed max-w-2xl" style={{ color: 'var(--text-secondary)' }}>
            {displayed}
          </p>
        </div>

        {/* Right: status badges */}
        <div className="flex flex-col gap-3 shrink-0 self-start md:self-center">
          <span
            className="inline-flex items-center justify-center text-sm px-4 py-2 rounded-full font-semibold"
            style={{
              color: '#4a8040',
              border: '1px solid rgba(74,128,64,0.35)',
              background: 'rgba(74,128,64,0.12)',
            }}
          >
            {prediction?.status === 'danger' ? 'Critical' : prediction?.status === 'warning' ? 'Warning' : 'Safe'}
          </span>
          <span
            className="inline-flex items-center justify-center text-sm px-4 py-2 rounded-full font-semibold"
            style={{
              color: '#b8860b',
              border: '1px solid rgba(200,168,64,0.4)',
              background: 'rgba(200,168,64,0.12)',
            }}
          >
            +0.3° today
          </span>
        </div>
      </div>
    </div>
  )
}



