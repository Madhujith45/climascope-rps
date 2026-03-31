/**
 * ClimaScope – Top Navigation Bar
 */
import React, { useState } from 'react'

export default function Topbar({ user, secondsAgo, onLogout }) {
  const [searchVal, setSearchVal] = useState('')

  const initials = user?.full_name
    ? user.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
    : (user?.email?.[0] || 'U').toUpperCase()

  return (
    <header
      className="flex items-center justify-between shrink-0"
      style={{
        height: 64,
        padding: '0 28px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        background: 'rgba(8,13,20,0.8)',
        backdropFilter: 'blur(12px)',
        zIndex: 10,
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
          className="flex items-center justify-center rounded-xl transition-colors"
          style={{ width: 36, height: 36, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.07)' }}
          title="Notifications"
        >
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="#94a3b8" strokeWidth={2}>
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </button>

        {/* Avatar / logout */}
        <button
          onClick={onLogout}
          className="flex items-center gap-2 rounded-xl px-3 py-1.5 transition-colors hover:opacity-80"
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.07)' }}
          title="Click to logout"
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
      </div>
    </header>
  )
}
