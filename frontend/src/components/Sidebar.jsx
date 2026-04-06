/**
 * ClimaScope - Sidebar Component
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
        width: 56,
        margin: '14px 0 14px 14px',
        background: '#1a1a1a',
        border: '1px solid rgba(138, 128, 96, 0.2)',
        borderRadius: 16,
        padding: '10px 6px',
        gap: 10,
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.35)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center justify-center mb-4">
        <div
          className="flex items-center justify-center rounded-xl"
          style={{
            width: 38, height: 38,
            background: 'linear-gradient(135deg,#b8860b,#9a6f08)',
            boxShadow: '0 6px 18px rgba(200,168,64,0.28)',
          }}
          title="ClimaScope"
        >
          <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth={2.5}>
            <path d="M12 2a10 10 0 100 20A10 10 0 0012 2z" />
            <path d="M12 6v6l4 2" strokeLinecap="round" />
          </svg>
        </div>
      </div>

      {/* Nav Items */}
      <nav className="flex flex-col items-center gap-2">
        {NAV.map(item => (
          <Link
            key={item.id}
            to={`/${item.id}`}
            className={`sidebar-item ${active === item.id ? 'active' : ''}`}
            style={{
              width: 42,
              height: 42,
              justifyContent: 'center',
              padding: 0,
              borderRadius: 12,
            }}
            title={item.label}
          >
            {item.icon}
            <span className="sr-only">{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* Device Selector */}
      {devices.length > 0 && (
        <div className="mt-auto">
          <select
            value={selectedDevice}
            onChange={e => onDeviceChange(e.target.value)}
            className="w-full rounded-xl text-xs px-2 py-2 outline-none"
            title="Active Device"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
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



