/**
 * ClimaScope - Environmental Stability Score (Centerpiece)
 * Circular progress + dynamic explanation + color animation
 */
import React, { useMemo } from 'react'

function getLabel(score) {
  if (score >= 80) return { text: 'Stable',            color: '#4a8040', glow: 'rgba(34,197,94,0.2)' }
  if (score >= 50) return { text: 'Slightly Unstable', color: '#9a6f08', glow: 'rgba(184,134,11,0.25)' }
  return               { text: 'Critical',             color: '#a04030', glow: 'rgba(160,64,48,0.35)' }
}

function getExplanation(score, prediction, data) {
  if (!data || !prediction) return 'Analyzing environmental conditions...'
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
    if (!isNaN(temp) && temp > 32) return `Slightly unstable - temperature at ${temp.toFixed(1)}°C is above comfort zone.`
    if (!isNaN(gas) && gas > 150) return `Slightly unstable - gas levels at ${gas.toFixed(0)} ppm approaching threshold.`
    return 'Some parameters are approaching warning thresholds.'
  }
  return 'Critical - multiple environmental parameters exceed safe limits. Immediate attention required.'
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
      className="glass-card-static p-7 h-full flex flex-col items-center justify-center gap-3"
      style={{ boxShadow: `0 0 40px ${glow}`, borderColor: `${color}22`, background: `radial-gradient(ellipse at center, ${glow} 0%, transparent 70%), var(--bg-card)` }}
    >
      <div className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-primary)' }}>
        Stability Score
      </div>
      <div className="text-sm -mt-2" style={{ color: 'var(--text-muted)' }}>
        Environmental health
      </div>

      {/* Circular Progress Ring */}
      <div className="relative flex items-center justify-center my-2" style={{ width: 150, height: 150 }}>
        {/* Outer glow pulse */}
        <div className="absolute inset-0 rounded-full" style={{
          background: `radial-gradient(circle, ${color}18 0%, transparent 70%)`,
          animation: 'pulse-dot 3s ease-in-out infinite',
        }} />
        <svg width="150" height="150" viewBox="0 0 150 150">
          <circle cx="75" cy="75" r={R} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="11" />
          <circle cx="75" cy="75" r={R} fill="none" stroke={color} strokeWidth="11"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            style={{
              transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1), stroke 0.4s ease',
              transform: 'rotate(-90deg)', transformOrigin: '50% 50%',
              filter: `drop-shadow(0 0 12px ${color}dd)`,
            }}
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className="text-5xl font-bold metric-value" style={{ color, lineHeight: 1 }}>
            {Math.round(score)}
          </span>
          <span className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>/100</span>
        </div>
      </div>

      <div className="font-semibold text-lg text-center" style={{ color }}>{text}</div>

      <div className="grid grid-cols-3 gap-2 w-full mt-2">
        {[
          { title: 'TEMPERATURE', value: score >= 80 ? 'Optimal' : score >= 50 ? 'Watch' : 'Critical' },
          { title: 'HUMIDITY', value: score >= 80 ? 'Balanced' : score >= 50 ? 'Moderate' : 'Unstable' },
          { title: 'AIR QUALITY', value: score >= 80 ? 'Clean' : score >= 50 ? 'Elevated' : 'Hazard' },
        ].map((tag) => (
          <div
            key={tag.title}
            className="rounded-2xl px-3 py-2 text-center"
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.1)',
            }}
          >
            <div className="text-xs font-semibold tracking-wider" style={{ color: 'var(--text-muted)' }}>{tag.title}</div>
            <div className="text-xl font-semibold mt-1" style={{ color: 'var(--text-primary)' }}>{tag.value}</div>
          </div>
        ))}
      </div>
    </div>
  )
}



