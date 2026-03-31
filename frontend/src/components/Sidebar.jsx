/**
 * ClimaScope – Sidebar Component
 */
import React, { useState, useEffect } from 'react'
import { getAuthToken } from '../services/auth'

const NAV = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: (
      <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
    ),
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: (
      <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
  },
  {
    id: 'devices',
    label: 'Devices',
    icon: (
      <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <rect x="2" y="7" width="20" height="14" rx="2" />
        <path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
      </svg>
    ),
  },
  {
    id: 'alerts',
    label: 'Alerts',
    icon: (
      <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
    ),
  },
  {
    id: 'reports',
    label: 'Reports',
    icon: (
      <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: (
      <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
      </svg>
    ),
  },
]

import { useLocation, Link } from 'react-router-dom'

export default function Sidebar({ selectedDevice, onDeviceChange }) {
  const location = useLocation()
  const active = location.pathname.substring(1) || 'dashboard'
  const [devices, setDevices] = useState([])

  useEffect(() => {
    const load = async () => {
      try {
        const token = getAuthToken()
        const res = await fetch('/devices/list', { headers: { Authorization: `Bearer ${token}` } })
        if (!res.ok) return
        const d = await res.json()
        setDevices(d.devices || [])
      } catch { /* ignore */ }
    }
    load()
  }, [])

  return (
    <aside
      className="flex flex-col shrink-0"
      style={{
        width: 220,
        background: 'rgba(10,16,26,0.95)',
        borderRight: '1px solid rgba(255,255,255,0.05)',
        padding: '20px 12px',
        gap: 8,
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-2 mb-6">
        <div
          className="flex items-center justify-center rounded-xl"
          style={{
            width: 36, height: 36,
            background: 'linear-gradient(135deg,#14b8a6,#3b82f6)',
            boxShadow: '0 4px 16px rgba(20,184,166,0.35)',
          }}
        >
          <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth={2.5}>
            <path d="M12 2a10 10 0 100 20A10 10 0 0012 2z" />
            <path d="M12 6v6l4 2" strokeLinecap="round" />
          </svg>
        </div>
        <div>
          <div className="font-bold text-white text-sm leading-none">ClimaScope</div>
          <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>AI Intelligence</div>
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex flex-col gap-1">
        {NAV.map(item => (
          <Link
            key={item.id}
            to={`/${item.id}`}
            className={`sidebar-item w-full text-left ${active === item.id ? 'active' : ''}`}
          >
            {item.icon}
            {item.label}
          </Link>
        ))}
      </nav>

      {/* Device Selector */}
      {devices.length > 0 && (
        <div className="mt-auto">
          <div className="text-xs font-semibold uppercase tracking-widest mb-2 px-2"
               style={{ color: 'var(--text-muted)' }}>
            Active Device
          </div>
          <select
            value={selectedDevice}
            onChange={e => onDeviceChange(e.target.value)}
            className="w-full rounded-xl text-sm px-3 py-2.5 outline-none"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
              color: 'var(--text-primary)',
            }}
          >
            <option value="">All devices</option>
            {devices.map(d => (
              <option key={d.id} value={d.device_id}>{d.device_name}</option>
            ))}
          </select>
        </div>
      )}
    </aside>
  )
}
