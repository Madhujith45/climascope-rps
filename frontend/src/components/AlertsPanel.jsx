/**
 * ClimaScope – Alerts Panel Component
 * Displays the most recent MODERATE and HIGH risk events.
 */

import React from 'react'

const LEVEL_STYLES = {
  MODERATE: {
    badge: 'bg-moderate/20 text-moderate border-moderate/40',
    dot:   'bg-moderate',
    row:   'border-moderate/20 hover:bg-moderate/5',
  },
  HIGH: {
    badge: 'bg-high/20 text-high border-high/40',
    dot:   'bg-high',
    row:   'border-high/20 hover:bg-high/5',
  },
}

function formatTimestamp(ts) {
  try {
    return new Date(ts).toLocaleString(undefined, {
      month: 'short', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false,
    })
  } catch {
    return ts
  }
}

export default function AlertsPanel({ alerts, loading }) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-16 animate-pulse rounded-lg bg-slate-800" />
        ))}
      </div>
    )
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 py-10 text-slate-500">
        <span className="text-3xl">✅</span>
        <p className="mt-2 text-sm">No alerts – system operating normally</p>
      </div>
    )
  }

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
      {alerts.map((alert) => {
        const styles = LEVEL_STYLES[alert.risk_level] || LEVEL_STYLES.MODERATE
        const reasons = alert.risk_reason ? alert.risk_reason.split(';') : []

        return (
          <div
            key={alert.id}
            className={`rounded-lg border p-3 transition-colors ${styles.row}`}
          >
            <div className="flex items-center justify-between gap-2">
              {/* Level badge */}
              <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-bold ${styles.badge}`}>
                <span className={`h-1.5 w-1.5 rounded-full ${styles.dot}`} />
                {alert.risk_level}
              </span>

              {/* Score pill */}
              <span className="rounded bg-slate-700/60 px-2 py-0.5 font-mono text-xs text-slate-300">
                Score: {alert.risk_score}
              </span>

              {/* Anomaly flag */}
              {alert.anomaly_flag && (
                <span className="rounded bg-yellow-900/40 px-2 py-0.5 text-xs text-yellow-400 border border-yellow-700/40">
                  ⚠ ANOMALY
                </span>
              )}

              {/* Timestamp */}
              <span className="ml-auto text-xs text-slate-500 shrink-0">
                {formatTimestamp(alert.timestamp)}
              </span>
            </div>

            {/* Reasons list */}
            {reasons.length > 0 && (
              <ul className="mt-1.5 space-y-0.5">
                {reasons.map((r, i) => (
                  <li key={i} className="text-xs text-slate-400 pl-4 relative before:absolute before:left-1 before:top-1.5 before:h-1 before:w-1 before:rounded-full before:bg-slate-600">
                    {r.trim()}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )
      })}
    </div>
  )
}
