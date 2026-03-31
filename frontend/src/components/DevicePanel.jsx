/**
 * ClimaScope – Device Status Panel
 */
import React, { useState, useEffect } from 'react'
import { getAuthToken } from '../services/auth'

function DeviceCard({ device, isSelected, onSelect }) {
  const online = device.is_active !== false
  return (
    <button
      onClick={() => onSelect(isSelected ? '' : device.device_id)}
      className="w-full text-left rounded-xl px-4 py-3 transition-all"
      style={{
        background: isSelected
          ? 'linear-gradient(135deg, rgba(20,184,166,0.15), rgba(59,130,246,0.10))'
          : 'rgba(255,255,255,0.03)',
        border: isSelected
          ? '1px solid rgba(20,184,166,0.3)'
          : '1px solid rgba(255,255,255,0.05)',
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Device icon */}
          <div
            className="flex items-center justify-center rounded-lg"
            style={{
              width: 34, height: 34,
              background: online ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.08)',
              border: `1px solid ${online ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.15)'}`,
              color: online ? '#22c55e' : '#ef4444',
            }}
          >
            <svg width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <rect x="2" y="7" width="20" height="14" rx="2" />
              <path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
              <line x1="12" y1="12" x2="12" y2="16" />
              <line x1="10" y1="14" x2="14" y2="14" />
            </svg>
          </div>

          <div>
            <div className="text-sm font-medium text-white leading-none mb-0.5">
              {device.device_name || device.device_id}
            </div>
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
              {device.location || 'No location'}
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{
                background: online ? '#22c55e' : '#ef4444',
                boxShadow: online ? '0 0 6px #22c55e' : 'none',
              }}
            />
            <span className="text-xs font-medium" style={{ color: online ? '#22c55e' : '#ef4444' }}>
              {online ? 'Online' : 'Offline'}
            </span>
          </div>
          {device.last_seen && (
            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
              {new Date(device.last_seen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          )}
        </div>
      </div>
    </button>
  )
}

export default function DevicePanel({ selectedDevice, onDeviceChange }) {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const token = getAuthToken()
        const res = await fetch('/devices/list', { headers: { Authorization: `Bearer ${token}` } })
        if (!res.ok) return
        const d = await res.json()
        setDevices(d.devices || [])
      } catch { /* ignore */ }
      finally { setLoading(false) }
    }
    load()
  }, [])

  return (
    <div className="glass-card p-6 flex flex-col" style={{ minHeight: 340 }}>
      <div className="flex items-center gap-3 mb-5">
        <div
          className="flex items-center justify-center rounded-xl"
          style={{ width: 36, height: 36, background: 'rgba(96,165,250,0.1)', border: '1px solid rgba(96,165,250,0.2)', color: '#60a5fa' }}
        >
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <rect x="2" y="7" width="20" height="14" rx="2" />
            <path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
          </svg>
        </div>
        <div>
          <div className="text-sm font-semibold text-white">Connected Devices</div>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {devices.filter(d => d.is_active !== false).length} online
          </div>
        </div>
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto">
        {loading ? (
          [1,2,3].map(i => <div key={i} className="skeleton h-16 rounded-xl" />)
        ) : devices.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-8"
               style={{ color: 'var(--text-muted)' }}>
            <svg width="36" height="36" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} className="mb-3 opacity-40">
              <rect x="2" y="7" width="20" height="14" rx="2" />
              <path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
            </svg>
            <p className="text-sm">No devices registered</p>
          </div>
        ) : (
          devices.map(d => (
            <DeviceCard
              key={d.id || d.device_id}
              device={d}
              isSelected={selectedDevice === d.device_id}
              onSelect={onDeviceChange}
            />
          ))
        )}
      </div>
    </div>
  )
}
