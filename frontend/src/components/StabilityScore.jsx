/**
 * ClimaScope – Environmental Stability Score (Centerpiece)
 * Circular progress + dynamic explanation + color animation
 */
import React, { useMemo } from 'react'

function getLabel(score) {
  if (score >= 80) return { text: 'Stable',            color: '#22c55e', glow: 'rgba(34,197,94,0.2)' }
  if (score >= 50) return { text: 'Slightly Unstable', color: '#f59e0b', glow: 'rgba(245,158,11,0.2)' }
  return               { text: 'Critical',             color: '#ef4444', glow: 'rgba(239,68,68,0.2)' }
}

function getExplanation(score, prediction, data) {
  if (!data || !prediction) return 'Analyzing environmental conditions…'
  const temp = Number(data.temperature)
  const gas  = Number(data.gas_ppm)

  if (score >= 80) {
    const reasons = []
    if (!isNaN(temp) && temp > 15 && temp < 35) reasons.push('temperature is in safe range')
    if (!isNaN(gas) && gas < 200) reasons.push('gas levels are nominal')
    if (!prediction.anomaly) reasons.push('no anomalies detected')
    return `Stable because ${reasons.join(', ')}.`
  }
  if (score >= 50) {
    if (!isNaN(temp) && temp > 32) return `Slightly unstable — temperature at ${temp.toFixed(1)}°C is above comfort zone.`
    if (!isNaN(gas) && gas > 150) return `Slightly unstable — gas levels at ${gas.toFixed(0)} ppm approaching threshold.`
    return 'Some parameters are approaching warning thresholds.'
  }
  return 'Critical — multiple environmental parameters exceed safe limits. Immediate attention required.'
}

export default function StabilityScore({ prediction, data, loading }) {
  const score = prediction?.health_score ?? 0
  const { text, color, glow } = getLabel(score)
  const explanation = useMemo(() => getExplanation(score, prediction, data), [score, prediction, data])

  const R = 52
  const CIRCUMFERENCE = 2 * Math.PI * R
  const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE

  if (loading) {
    return (
      <div className="glass-card-static p-6 h-full flex flex-col items-center justify-center gap-4">
        <div className="skeleton w-28 h-28 rounded-full" />
        <div className="skeleton w-32 h-4 rounded" />
        <div className="skeleton w-48 h-3 rounded" />
      </div>
    )
  }

  return (
    <div
      className="glass-card-static p-6 h-full flex flex-col items-center justify-center gap-2"
      style={{ boxShadow: `0 0 40px ${glow}`, borderColor: `${color}22` }}
    >
      <div className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
        Stability Score
      </div>

      {/* Circular Progress Ring */}
      <div className="relative flex items-center justify-center my-2" style={{ width: 140, height: 140 }}>
        {/* Outer glow pulse */}
        <div className="absolute inset-0 rounded-full" style={{
          background: `radial-gradient(circle, ${color}11 0%, transparent 70%)`,
          animation: 'pulse-dot 3s ease-in-out infinite',
        }} />
        <svg width="140" height="140" viewBox="0 0 140 140">
          <circle cx="70" cy="70" r={R} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
          <circle cx="70" cy="70" r={R} fill="none" stroke={color} strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            style={{
              transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1), stroke 0.4s ease',
              transform: 'rotate(-90deg)', transformOrigin: '50% 50%',
              filter: `drop-shadow(0 0 10px ${color}aa)`,
            }}
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className="text-4xl font-bold metric-value" style={{ color, lineHeight: 1 }}>
            {Math.round(score)}
          </span>
          <span className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>/100</span>
        </div>
      </div>

      <div className="font-semibold text-lg" style={{ color }}>{text}</div>

      {/* Explanation */}
      <p className="text-xs text-center leading-relaxed"
         style={{ color: 'var(--text-secondary)', maxWidth: 220 }}>
        {explanation}
      </p>
    </div>
  )
}
