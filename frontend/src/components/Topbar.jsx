/**
 * ClimaScope – Top Navigation Bar
 */
import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'

export default function Topbar({ user, secondsAgo, onLogout }) {
  const [searchVal, setSearchVal] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
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

  return (
    <header
      className="flex items-center justify-between shrink-0"
      style={{
        height: 64,
        padding: '0 28px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        background: 'rgba(8,13,20,0.8)',
        backdropFilter: 'blur(12px)',
        zIndex: 50,
      }}
    >
      {/* Left: page title */}
      <div>
        <h1 className="text-base font-semibold text-white leading-none">Environmental Overview</h1>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>   
          Real-time AI microclimate intelligence
        </p>
      </div>

      {/* Center: Search */}
      <div className="relative hidden md:block">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2"
          width="14" height="14" fill="none" viewBox="0 0 24 24"
          stroke="#4b6282" strokeWidth={2.5}
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          className="search-input"
          placeholder="Search metrics, devices…"
          value={searchVal}
          onChange={e => setSearchVal(e.target.value)}
        />
      </div>

      {/* Right: status + avatar */}
      <div className="flex items-center gap-4">
        {/* Live status */}
        <div className="flex items-center gap-2">
          <span
            className="pulse-dot inline-block rounded-full"
            style={{ width: 7, height: 7, background: '#22c55e', boxShadow: '0 0 6px #22c55e' }}
          />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>     
            {secondsAgo <= 5 ? 'Live' : `${secondsAgo}s ago`}
          </span>
        </div>

        {/* Bell */}
        <button
          className="flex items-center justify-center rounded-xl transition-colors hidden sm:flex"
          style={{ width: 36, height: 36, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.07)' }}
          title="Notifications"
        >
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" strokeWidth={2}>
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </button>

        {/* Avatar / Dropdown menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 rounded-xl px-3 py-1.5 transition-colors hover:opacity-80"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.07)' }}
            title="Profile Menu"
          >
            <div
              className="flex items-center justify-center rounded-lg text-xs font-bold text-white"
              style={{
                width: 28, height: 28,
                background: 'linear-gradient(135deg,#14b8a6,#3b82f6)',
                fontSize: 11,
              }}
            >
              {initials}
            </div>
            <span className="text-sm text-white hidden sm:block">
              {user?.full_name || user?.email?.split('@')[0] || 'User'}
            </span>
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" strokeWidth={2}>
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          {/* Dropdown Content */}
          {menuOpen && (
            <div className="absolute right-0 mt-2 w-48 rounded-xl overflow-hidden shadow-2xl fade-in"
                 style={{ background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(255,255,255,0.1)', backdropFilter: 'blur(16px)' }}>
              
              <div className="px-4 py-3 border-b border-white/5">
                <p className="text-sm text-white font-medium truncate">{user?.full_name || 'User'}</p>
                <p className="text-xs text-gray-400 truncate">{user?.email}</p>
              </div>
              
              <div className="py-1">
                <Link
                  to="/settings"
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:bg-white/5 hover:text-white transition-colors"
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
