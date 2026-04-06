/**
 * ClimaScope - Alerts Section (card-based, premium)
 */
import React, { useState, useEffect } from 'react'
import { getAuthToken } from '../services/auth'

const MAX_VISIBLE_ALERTS = 5

const SEV = {
  danger:  { color: '#a04030', bg: 'rgba(160,64,48,0.12)',  border: 'rgba(160,64,48,0.35)',  strip: '#a04030', label: 'Critical' },
  warning: { color: '#b8860b', bg: 'rgba(249,115,22,0.08)', border: 'rgba(249,115,22,0.2)', strip: '#b8860b', label: 'Warning'  },
  info:    { color: 'rgba(255,255,255,0.75)', bg: 'rgba(255,255,255,0.06)',  border: 'rgba(138, 128, 96, 0.2)', strip: 'rgba(255,255,255,0.7)', label: 'Info'     },
}

function timeAgo(ts) {
  const diff = Date.now() - new Date(ts).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

export default function AlertsSection() {
  const REFRESH_MS = 10_000
  const [alerts,      setAlerts]      = useState([])
  const [loading,     setLoading]     = useState(true)
  const [showAll,     setShowAll]     = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const token = getAuthToken()
        const res = await fetch('/alerts/?limit=100', { headers: { Authorization: `Bearer ${token}` } })
        if (!res.ok) throw new Error()
        const d = await res.json()
        setAlerts(d.alerts || [])
      } catch { /* ignore */ }
      finally { setLoading(false) }
    }

    load()

    const id = setInterval(load, REFRESH_MS)
    return () => clearInterval(id)
  }, [REFRESH_MS])

  const activeGroupedAlerts = React.useMemo(() => {
    const unresolved = alerts.filter((a) => !a.is_resolved)
    const grouped = new Map()

    unresolved.forEach((alert) => {
      const key = `${alert.device_id || 'unknown'}|${alert.severity}|${alert.message}`
      const current = grouped.get(key)
      if (!current) {
        grouped.set(key, {
          ...alert,
          ids: [alert.id],
          count: 1,
        })
        return
      }

      current.ids.push(alert.id)
      current.count += 1
      if (new Date(alert.created_at).getTime() > new Date(current.created_at).getTime()) {
        current.created_at = alert.created_at
        current.id = alert.id
      }
      if (!alert.is_read) current.is_read = false
    })

    return Array.from(grouped.values()).sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  }, [alerts])

  const visibleAlerts = showAll
    ? activeGroupedAlerts
    : activeGroupedAlerts.slice(0, MAX_VISIBLE_ALERTS)

  const hiddenCount = Math.max(0, activeGroupedAlerts.length - MAX_VISIBLE_ALERTS)
  const activeUnread = alerts.filter((a) => !a.is_resolved && !a.is_read).length

  const handleRead = async (ids) => {
    const token = getAuthToken()
    await Promise.all(ids.map((id) =>
      fetch(`/alerts/${id}/read`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    ))
    setAlerts(prev => prev.map(a => ids.includes(a.id) ? { ...a, is_read: true } : a))
  }

  const handleResolve = async (ids) => {
    const token = getAuthToken()
    await Promise.all(ids.map((id) =>
      fetch(`/alerts/${id}/resolve`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    ))
    setAlerts(prev => prev.map(a => ids.includes(a.id) ? { ...a, is_resolved: true } : a))
  }

  const handleMarkAll = async () => {
    const token = getAuthToken()
    await fetch('/alerts/mark-all-read', { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    setAlerts(prev => prev.map(a => ({ ...a, is_read: true })))
  }

  return (
    <div className="glass-card p-6 flex flex-col" style={{ minHeight: 340 }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center rounded-xl"
            style={{ width: 36, height: 36, background: 'rgba(160,64,48,0.18)', border: '1px solid rgba(160,64,48,0.35)', color: '#a04030' }}
          >
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </div>
          <div>
            <div className="text-sm font-semibold text-[var(--text-primary)]">Active Alerts</div>
            {activeUnread > 0 && (
              <div className="text-xs" style={{ color: '#a04030' }}>{activeUnread} unread</div>
            )}
            <div className="text-[11px] mt-0.5" style={{ color: 'var(--text-muted)' }}>
              Shows unresolved risk events from connected devices.
            </div>
          </div>
        </div>
        {activeUnread > 0 && (
          <button
            className="text-xs font-medium transition-opacity hover:opacity-70"
            style={{ color: '#b8860b' }}
            onClick={handleMarkAll}
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Alert List */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {loading ? (
          [1,2,3].map(i => <div key={i} className="skeleton h-16 rounded-xl" />)
        ) : activeGroupedAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-8"
               style={{ color: 'var(--text-muted)' }}>
            <svg width="36" height="36" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} className="mb-3 opacity-40">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm">All clear - no active alerts</p>
          </div>
        ) : (
          visibleAlerts.map(alert => {
            const cfg = SEV[alert.severity] || SEV.info
            return (
              <div
                key={alert.id}
                className="relative rounded-xl overflow-hidden transition-opacity"
                style={{
                  background: cfg.bg,
                  border: `1px solid ${cfg.border}`,
                  opacity: alert.is_resolved ? 0.5 : 1,
                  paddingLeft: 0,
                }}
              >
                {/* Severity strip */}
                <div
                  style={{
                    position: 'absolute', left: 0, top: 0, bottom: 0, width: 3,
                    background: cfg.strip,
                    boxShadow: `0 0 8px ${cfg.strip}88`,
                  }}
                />
                <div className="px-4 py-3 pl-5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-semibold uppercase" style={{ color: cfg.color }}>
                          {cfg.label}
                        </span>
                        {!alert.is_read && (
                          <span
                            className="inline-block w-1.5 h-1.5 rounded-full"
                            style={{ background: cfg.color }}
                          />
                        )}
                        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                          {String(alert.device_name || '').toLowerCase().includes('unknown')
                            ? 'ClimaScope Pi'
                            : alert.device_name}
                        </span>
                      </div>
                      <p className="text-xs leading-relaxed text-[var(--text-primary)] truncate">{alert.message}</p>
                      {alert.count > 1 && (
                        <p className="text-[11px] mt-1" style={{ color: cfg.color }}>
                          Repeated {alert.count} times
                        </p>
                      )}
                      <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                        {timeAgo(alert.created_at)}
                      </p>
                    </div>

                    <div className="flex flex-col gap-1 shrink-0">
                      {!alert.is_read && (
                        <button
                          className="text-xs hover:opacity-70 transition-opacity"
                          style={{ color: '#b8860b' }}
                          onClick={() => handleRead(alert.ids || [alert.id])}
                        >
                          Read
                        </button>
                      )}
                      {!alert.is_resolved && (
                        <button
                          className="text-xs hover:opacity-70 transition-opacity"
                          style={{ color: '#4a8040' }}
                          onClick={() => handleResolve(alert.ids || [alert.id])}
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {!loading && hiddenCount > 0 && (
        <button
          className="mt-3 text-xs font-medium self-start hover:opacity-80"
          style={{ color: '#b8860b' }}
          onClick={() => setShowAll((prev) => !prev)}
        >
          {showAll ? 'Show fewer alerts' : `Show ${hiddenCount} more alerts`}
        </button>
      )}
    </div>
  )
}




