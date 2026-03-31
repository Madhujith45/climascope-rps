/**
 * ClimaScope – Alerts Section (card-based, premium)
 */
import React, { useState, useEffect } from 'react'
import { getAuthToken } from '../services/auth'

const SEV = {
  danger:  { color: '#ef4444', bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.2)',  strip: '#ef4444', label: 'Critical' },
  warning: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', strip: '#f59e0b', label: 'Warning'  },
  info:    { color: '#60a5fa', bg: 'rgba(96,165,250,0.08)',  border: 'rgba(96,165,250,0.2)', strip: '#60a5fa', label: 'Info'     },
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
  const [alerts,      setAlerts]      = useState([])
  const [loading,     setLoading]     = useState(true)
  const [unread,      setUnread]      = useState(0)

  useEffect(() => {
    const load = async () => {
      try {
        const token = getAuthToken()
        const res = await fetch('/alerts/', { headers: { Authorization: `Bearer ${token}` } })
        if (!res.ok) throw new Error()
        const d = await res.json()
        setAlerts(d.alerts || [])
        setUnread(d.unread_count || 0)
      } catch { /* ignore */ }
      finally { setLoading(false) }
    }

    load()

    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [])

  const handleRead = async (id) => {
    const token = getAuthToken()
    await fetch(`/alerts/${id}/read`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a))
    setUnread(p => Math.max(0, p - 1))
  }

  const handleResolve = async (id) => {
    const token = getAuthToken()
    await fetch(`/alerts/${id}/resolve`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_resolved: true } : a))
  }

  const handleMarkAll = async () => {
    const token = getAuthToken()
    await fetch('/alerts/mark-all-read', { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    setAlerts(prev => prev.map(a => ({ ...a, is_read: true })))
    setUnread(0)
  }

  return (
    <div className="glass-card p-6 flex flex-col" style={{ minHeight: 340 }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center rounded-xl"
            style={{ width: 36, height: 36, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}
          >
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </div>
          <div>
            <div className="text-sm font-semibold text-white">Active Alerts</div>
            {unread > 0 && (
              <div className="text-xs" style={{ color: '#ef4444' }}>{unread} unread</div>
            )}
          </div>
        </div>
        {unread > 0 && (
          <button
            className="text-xs font-medium transition-opacity hover:opacity-70"
            style={{ color: '#60a5fa' }}
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
        ) : alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-8"
               style={{ color: 'var(--text-muted)' }}>
            <svg width="36" height="36" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} className="mb-3 opacity-40">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm">All clear — no active alerts</p>
          </div>
        ) : (
          alerts.map(alert => {
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
                          {alert.device_name}
                        </span>
                      </div>
                      <p className="text-xs leading-relaxed text-white truncate">{alert.message}</p>
                      <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                        {timeAgo(alert.created_at)}
                      </p>
                    </div>

                    <div className="flex flex-col gap-1 shrink-0">
                      {!alert.is_read && (
                        <button
                          className="text-xs hover:opacity-70 transition-opacity"
                          style={{ color: '#60a5fa' }}
                          onClick={() => handleRead(alert.id)}
                        >
                          Read
                        </button>
                      )}
                      {!alert.is_resolved && (
                        <button
                          className="text-xs hover:opacity-70 transition-opacity"
                          style={{ color: '#22c55e' }}
                          onClick={() => handleResolve(alert.id)}
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
    </div>
  )
}
