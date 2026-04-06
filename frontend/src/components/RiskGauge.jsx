/**
 * ClimaScope - Circular Risk Gauge Component
 * SVG-based gauge that renders a 0-100 arc coloured by risk level.
 */

import React from 'react'

// Risk level thresholds (must match edge processing engine)
const LEVELS = {
  SAFE:     { label: 'SAFE',     color: '#4a8040', bg: 'bg-safe/20',     border: 'border-safe/40',     text: 'text-safe'     },
  MODERATE: { label: 'MODERATE', color: '#b8860b', bg: 'bg-moderate/20', border: 'border-moderate/40', text: 'text-moderate' },
  HIGH:     { label: 'HIGH',     color: '#a04030', bg: 'bg-high/20',      border: 'border-high/40',     text: 'text-high',    pulse: true },
}

function getLevel(score) {
  if (score <= 30)  return LEVELS.SAFE
  if (score <= 65)  return LEVELS.MODERATE
  return LEVELS.HIGH
}

/**
 * Compute the SVG arc path for a given percentage fill on a circular track.
 * cx, cy - centre; r - radius; pct - 0-100
 */
function describeArc(cx, cy, r, pct) {
  const startAngle = -220   // degrees from positive x-axis (clockwise)
  const totalSweep = 260    // total arc degrees
  const endAngle   = startAngle + (totalSweep * Math.min(pct, 99.99) / 100)

  const toRad = (deg) => (deg * Math.PI) / 180
  const x1 = cx + r * Math.cos(toRad(startAngle))
  const y1 = cy + r * Math.sin(toRad(startAngle))
  const x2 = cx + r * Math.cos(toRad(endAngle))
  const y2 = cy + r * Math.sin(toRad(endAngle))
  const largeArc = endAngle - startAngle > 180 ? 1 : 0

  return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`
}

export default function RiskGauge({ score, riskLevel, anomalyFlag, riskReason }) {
  const safeScore = score !== undefined && score !== null ? Math.max(0, Math.min(100, score)) : 0
  const level = getLevel(safeScore)
  const displayLevel = riskLevel ? LEVELS[riskLevel] || level : level
  const arcPath = describeArc(80, 80, 60, safeScore)

  // Track arc (grey background)
  const trackPath = describeArc(80, 80, 60, 99.99)

  return (
    <div className={`rounded-xl border p-5 flex flex-col items-center ${displayLevel.bg} ${displayLevel.border}`}>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-gray-400">
        Risk Score
      </h3>

      {/* SVG Gauge */}
      <div className="relative">
        <svg viewBox="0 0 160 160" className="w-44 h-44">
          {/* Shadow filter */}
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Track */}
          <path
            d={trackPath}
            fill="none"
            stroke="#334155"
            strokeWidth="12"
            strokeLinecap="round"
          />

          {/* Value arc */}
          <path
            d={arcPath}
            fill="none"
            stroke={displayLevel.color}
            strokeWidth="12"
            strokeLinecap="round"
            filter="url(#glow)"
            style={{ transition: 'stroke-dashoffset 0.8s ease' }}
          />

          {/* Centre text */}
          <text
            x="80"
            y="76"
            textAnchor="middle"
            dominantBaseline="middle"
            fill={displayLevel.color}
            fontSize="28"
            fontWeight="bold"
            fontFamily="monospace"
          >
            {safeScore}
          </text>
          <text
            x="80"
            y="98"
            textAnchor="middle"
            fill="#8a8060"
            fontSize="9"
            letterSpacing="2"
          >
            / 100
          </text>
        </svg>
      </div>

      {/* Level badge */}
      <div
        className={`mt-2 flex items-center gap-2 rounded-full px-4 py-1 text-sm font-bold border
          ${displayLevel.bg} ${displayLevel.border} ${displayLevel.text}
          ${displayLevel.pulse ? 'risk-pulse' : ''}`}
      >
        <span
          className="inline-block h-2 w-2 rounded-full"
          style={{ background: displayLevel.color }}
        />
        {displayLevel.label}
        {anomalyFlag && (
          <span className="ml-1 text-xs font-normal text-yellow-400">WARNING ANOMALY</span>
        )}
      </div>

      {/* Reason */}
      {riskReason && (
        <p className="mt-3 text-center text-xs text-gray-400 leading-relaxed px-2 max-w-xs">
          {riskReason.split(';')[0]}
        </p>
      )}
    </div>
  )
}




