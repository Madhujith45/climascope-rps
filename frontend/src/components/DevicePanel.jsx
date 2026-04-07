/**
 * ClimaScope - Device Status Panel
 */
import React, { useState, useEffect } from 'react'
import { getAuthToken } from '../services/auth'

const BASE_URL = import.meta.env.VITE_BACKEND_URL;

function isDeviceOnline(device) {
  if (device?.last_seen) {
    const lastSeen = new Date(device.last_seen).getTime()
    if (Number.isFinite(lastSeen)) {
      return Date.now() - lastSeen <= 60_000
    }
  }
  return device?.is_active !== false
}

function DeviceCard({ device, isSelected, onSelect }) {
  const online = isDeviceOnline(device)
  return (
    <button
      onClick={() => onSelect(isSelected ? '' : device.device_id)}
      className="w-full text-left rounded-xl px-4 py-3 transition-all"
      style={{
        background: isSelected
          ? 'linear-gradient(135deg, rgba(200,168,64,0.12), rgba(200,168,64,0.05)), rgba(30, 35, 20, 0.65)'
          : 'rgba(255,255,255,0.03)',
        border: isSelected
          ? '1px solid rgba(200,168,64,0.4)'
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
              background: online ? 'rgba(34,197,94,0.1)' : 'rgba(160,64,48,0.12)',
              border: `1px solid ${online ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.15)'}`,
              color: online ? '#4a8040' : '#a04030',
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
            <div className="text-sm font-medium text-[var(--text-primary)] leading-none mb-0.5">
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
                background: online ? '#4a8040' : '#a04030',
                boxShadow: online ? '0 0 6px #4a8040' : 'none',
              }}
            />
            <span className="text-xs font-medium" style={{ color: online ? '#4a8040' : '#a04030' }}>
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
        // Try new endpoint first (/api/devices), fallback to old endpoint
        let res = await fetch(`${BASE_URL}/api/devices/list`, { headers: { Authorization: `Bearer ${token}` } })
        if (!res.ok) {
          res = await fetch(`${BASE_URL}/devices/list`, { headers: { Authorization: `Bearer ${token}` } })
        }
        if (!res.ok) return
        const d = await res.json()
        const list = d.devices || []

        // Fallback: if no registered device exists yet, infer one from latest telemetry.
        if (list.length === 0) {
          const latestRes = await fetch(`${BASE_URL}/api/data/latest?n=1`, { headers: { Authorization: `Bearer ${token}` } })
          if (latestRes.ok) {
            const latest = await latestRes.json()
            const latestDoc = Array.isArray(latest) ? latest[0] : latest
            if (latestDoc) {
              const inferredDeviceId = latestDoc.device_id || 'climascope-pi001'
              setDevices([
                {
                  id: inferredDeviceId,
                  device_id: inferredDeviceId,
                  device_name: inferredDeviceId,
                  location: 'Auto-detected',
                  is_active: true,
                  last_seen: latestDoc.timestamp || null,
                },
              ])
              return
            }
          }
        }

        setDevices(list)
      } catch { /* ignore */ }
      finally { setLoading(false) }
    }
    load()
    
    // Refresh every 10 seconds to catch new devices
    const interval = setInterval(load, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="glass-card p-6 flex flex-col" style={{ minHeight: 340 }}>
      <div className="flex items-center gap-3 mb-5">
        <div
          className="flex items-center justify-center rounded-xl"
          style={{ width: 36, height: 36, background: 'rgba(200,168,64,0.12)', border: '1px solid rgba(200,168,64,0.4)', color: '#b8860b' }}
        >
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <rect x="2" y="7" width="20" height="14" rx="2" />
            <path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2" />
          </svg>
        </div>
        <div>
          <div className="text-sm font-semibold text-[var(--text-primary)]">Connected Devices</div>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {devices.filter(d => isDeviceOnline(d)).length} online
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





