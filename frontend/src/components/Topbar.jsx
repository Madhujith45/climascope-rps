/**
 * ClimaScope - Top Navigation Bar
 */
import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getAuthToken } from '../services/auth'

const BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function Topbar({ user, selectedDevice, secondsAgo, onLogout }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const [isLive, setIsLive] = useState(false)
  const [statusText, setStatusText] = useState('Offline')
  const menuRef = useRef(null)

  const initials = user?.full_name
    ? user.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
    : (user?.email?.[0] || 'U').toUpperCase()

  // Close drop down on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuRef])

  useEffect(() => {
    const checkLive = async () => {
      try {
        const token = getAuthToken()
        if (!token) {
          setIsLive(false)
          setStatusText('Offline')
          return
        }

        let res = await fetch(`${BASE_URL}/api/devices/list`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) {
          res = await fetch(`${BASE_URL}/devices/list`, {
            headers: { Authorization: `Bearer ${token}` },
          })
        }
        if (!res.ok) throw new Error('device status fetch failed')

        const payload = await res.json()
        const devices = payload?.devices || []
        const activeDeviceId = selectedDevice || 'climascope-pi001'
        const target = devices.find((d) => d.device_id === activeDeviceId) || devices[0]

        if (!target) {
          setIsLive(false)
          setStatusText('Offline')
          return
        }

        const lastSeen = target?.last_seen ? new Date(target.last_seen) : null
        const ageMs = lastSeen && !Number.isNaN(lastSeen.getTime())
          ? Date.now() - lastSeen.getTime()
          : Number.POSITIVE_INFINITY
        const live = (target?.status === 'online') || (Number.isFinite(ageMs) && ageMs <= 60_000)
        setIsLive(live)

        if (!live) {
          setStatusText('Offline')
        } else {
          const ageSec = Number.isFinite(ageMs) ? Math.max(0, Math.floor(ageMs / 1000)) : 0
          setStatusText(ageSec <= 5 ? 'Live' : `${ageSec}s ago`)
        }
      } catch {
        setIsLive(false)
        setStatusText('Offline')
      }
    }

    checkLive()
    const id = setInterval(checkLive, 10_000)
    return () => clearInterval(id)
  }, [selectedDevice])

  return (
    <header
      className="flex items-center justify-between shrink-0 rounded-3xl"
      style={{
        height: 68,
        padding: '0 16px 0 18px',
        border: '1px solid rgba(138, 128, 96, 0.2)',
        background: 'linear-gradient(135deg, rgba(200,168,64,0.14), rgba(200,168,64,0.06)), rgba(30, 35, 20, 0.65)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        boxShadow: '0 10px 24px rgba(0,0,0,0.22), 0 0 30px rgba(200,168,64,0.16)',
        zIndex: 50,
      }}
    >
      {/* Left: brand */}
      <div className="flex items-center gap-3">
        <div
          className="flex items-center justify-center rounded-xl"
          style={{
            width: 34,
            height: 34,
            background: 'rgba(200,168,64,0.14)',
            border: '1px solid rgba(200,168,64,0.28)',
            color: '#b8860b',
          }}
        >
          <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path d="M12 3l7 4v5c0 5-3.5 7.5-7 9-3.5-1.5-7-4-7-9V7l7-4z" />
          </svg>
        </div>
        <div className="font-semibold text-2xl leading-none text-[var(--text-primary)] tracking-tight">ClimaScope</div>
        <span
          className="text-xs px-2 py-0.5 rounded-full font-semibold"
          style={{
            color: 'var(--highlight)',
            background: 'rgba(200, 168, 64, 0.12)',
            border: '1px solid rgba(200,168,64,0.3)',
          }}
        >
          LIVE
        </span>
      </div>

      {/* Right: status + avatar */}
      <div className="flex items-center gap-4">
        {/* Live status */}
        <div className="flex items-center gap-2">
          <span
            className="pulse-dot inline-block rounded-full"
            style={{
              width: 8,
              height: 8,
              background: isLive ? '#4a8040' : '#a04030',
              boxShadow: isLive ? '0 0 8px #4a8040' : '0 0 8px #a04030',
            }}
          />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>     
            {statusText}
          </span>
        </div>

        {/* Bell */}
        <button
          className="flex items-center justify-center rounded-xl transition-colors hidden sm:flex"
          style={{ width: 38, height: 38, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
          title="Notifications (active alerts)"
        >
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="#8a8060" strokeWidth={2}>
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </button>

        {/* Avatar / Dropdown menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 rounded-xl px-3 py-1.5 transition-colors hover:opacity-80"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
            title="Profile Menu"
          >
            <div
              className="flex items-center justify-center rounded-lg text-xs font-bold text-[var(--text-primary)]"
              style={{
                width: 28, height: 28,
                background: 'linear-gradient(135deg,#b8860b,#9a6f08)',
                fontSize: 11,
              }}
            >
              {initials}
            </div>
            <span className="text-sm text-[var(--text-primary)] hidden sm:block">
              {user?.full_name || user?.email?.split('@')[0] || 'User'}
            </span>
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="#8a8060" strokeWidth={2}>
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          {/* Dropdown Content */}
          {menuOpen && (
            <div className="absolute right-0 mt-2 w-48 rounded-xl overflow-hidden shadow-2xl fade-in"
                 style={{ background: 'rgba(30,35,20,0.92)', border: '1px solid rgba(138,128,96,0.2)', backdropFilter: 'blur(16px)' }}>
              
              <div className="px-4 py-3 border-b border-white/5">
                <p className="text-sm text-[var(--text-primary)] font-medium truncate">{user?.full_name || 'User'}</p>
                <p className="text-xs text-gray-400 truncate">{user?.email}</p>
              </div>
              
              <div className="py-1">
                <Link
                  to="/settings"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:bg-white/5 hover:text-[var(--text-primary)] transition-colors"
                >
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
                  </svg>
                  Profile & Settings
                </Link>
                
                <button
                  onClick={() => {
                    setMenuOpen(false)
                    onLogout()
                  }}
                  className="w-full flex items-center justify-start gap-2 px-4 py-2 text-sm text-red-400 hover:bg-white/5 transition-colors"
                >
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />    
                    <polyline points="16 17 21 12 16 7" />
                    <line x1="21" y1="12" x2="9" y2="12" />
                  </svg>
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}




