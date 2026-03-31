/**
 * ClimaScope – Risk Timeline
 * Past risk → Current risk → Predicted risk
 */
import React, { useMemo } from 'react'

function getRiskLevel(score) {
  if (score >= 80) return { label: 'Low',    color: '#22c55e', pct: 20  }
  if (score >= 50) return { label: 'Medium', color: '#f59e0b', pct: 55  }
  return               { label: 'High',    color: '#ef4444', pct: 90  }
}

export default function RiskTimeline({ prediction, chartData, loading }) {
  const risks = useMemo(() => {
    const current = prediction?.health_score ?? 70
    // Derive past risk from older chart data health heuristic
    const olderTemps = (chartData || []).slice(10, 30)
      .map(r => Number(r?.temperature)).filter(v => !isNaN(v))
    const avgOld = olderTemps.length > 0
      ? olderTemps.reduce((a, b) => a + b, 0) / olderTemps.length
      : 28
    const pastScore = avgOld > 35 || avgOld < 10 ? 40 : avgOld > 32 ? 60 : 85
    // Projected risk: slight shift from current
    const trend = current - pastScore
    const predicted = Math.max(5, Math.min(100, current + trend * 0.5))

    return [
      { label: 'Past',      score: pastScore },
      { label: 'Current',   score: current   },
      { label: 'Predicted', score: predicted  },
    ]
  }, [prediction, chartData])

  if (loading) {
    return <div className="skeleton h-24 rounded-2xl" />
  }

  return (
    <div className="glass-card p-5">
      <div className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>
        Risk Timeline
      </div>

      <div className="flex items-end justify-between gap-2">
        {risks.map((r, i) => {
          const risk = getRiskLevel(r.score)
          const isCurrent = i === 1
          return (
            <div key={r.label} className="flex-1 flex flex-col items-center gap-2">
              {/* Score */}
              <span className="text-xs font-semibold" style={{ color: risk.color }}>
                {risk.label}
              </span>

              {/* Bar */}
              <div className="relative w-full flex justify-center">
                <div className="rounded-lg transition-all duration-700"
                     style={{
                       width: isCurrent ? 40 : 28,
                       height: Math.max(20, risk.pct * 0.6),
                       background: `linear-gradient(180deg, ${risk.color}cc 0%, ${risk.color}44 100%)`,
                       boxShadow: isCurrent ? `0 0 16px ${risk.color}66` : 'none',
                       border: isCurrent ? `1px solid ${risk.color}66` : 'none',
                     }}
                />
              </div>

              {/* Label */}
              <span className="text-xs" style={{ color: i === 2 ? 'var(--text-muted)' : 'var(--text-secondary)', fontStyle: i === 2 ? 'italic' : 'normal' }}>
                {r.label}
              </span>

              {/* Connector dots */}
              {i < 2 && (
                <div className="absolute" style={{ display: 'none' }} />
              )}
            </div>
          )
        })}
      </div>

      {/* Step connector line */}
      <div className="flex items-center gap-0 mt-2">
        {risks.map((r, i) => {
          const risk = getRiskLevel(r.score)
          return (
            <React.Fragment key={i}>
              <div className="flex-1 flex justify-center">
                <div className="w-2 h-2 rounded-full" style={{ background: risk.color, boxShadow: `0 0 6px ${risk.color}` }} />
              </div>
              {i < 2 && (
                <div className="flex-1" style={{ height: 2, background: `linear-gradient(90deg, ${getRiskLevel(risks[i].score).color}66, ${getRiskLevel(risks[i + 1].score).color}66)` }} />
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}
