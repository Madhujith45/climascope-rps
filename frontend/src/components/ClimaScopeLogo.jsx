import React from 'react'

export default function ClimaScopeLogo({ size = 44, showWordmark = true }) {
  return (
    <div className="flex items-center gap-2" aria-label="ClimaScope logo">
      <svg width={size} height={size} viewBox="0 0 64 64" fill="none" role="img">
        <defs>
          <linearGradient id="csGold" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#b8860b" />
            <stop offset="100%" stopColor="#9a6f08" />
          </linearGradient>
          <linearGradient id="csGreen" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#3f6d36" />
            <stop offset="100%" stopColor="#2e5427" />
          </linearGradient>
        </defs>
        <circle cx="32" cy="32" r="28" stroke="url(#csGold)" strokeWidth="4" fill="rgba(255,255,255,0.02)" />
        <path d="M10 33c5-6 12-10 22-10 9 0 15 3 22 8" stroke="url(#csGreen)" strokeWidth="5" strokeLinecap="round" />
        <path d="M18 41c5-4 10-6 16-6 8 0 14 3 20 7" stroke="url(#csGold)" strokeWidth="4" strokeLinecap="round" opacity="0.9" />
        <circle cx="46" cy="18" r="3" fill="#b8860b" />
      </svg>
      {showWordmark && (
        <span className="text-xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
          ClimaScope
        </span>
      )}
    </div>
  )
}
