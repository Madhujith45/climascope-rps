/**
 * ClimaScope - System Status Block (SAFE / WARNING / CRITICAL)
 */
import React from 'react'

const STATUS_CONFIG = {
  normal: {
    label:   'SAFE',
    subtext: 'All environmental parameters within normal range.',
    color:   '#4a8040',
    glow:    'rgba(16,185,129,0.25)',
    bg:      'rgba(16,185,129,0.08)',
    border:  'rgba(16,185,129,0.25)',
    icon: (
      <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  warning: {
    label:   'WARNING',
    subtext: 'Sensor readings approaching threshold limits. Monitor closely.',
    color:   '#b8860b',
    glow:    'rgba(251,146,60,0.25)',
    bg:      'rgba(251,146,60,0.08)',
    border:  'rgba(251,146,60,0.25)',
    icon: (
      <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
    ),
  },
  danger: {
    label:   'CRITICAL',
    subtext: 'Critical environmental conditions detected. Immediate action required.',
    color:   '#a04030',
    glow:    'rgba(160,64,48,0.35)',
    bg:      'rgba(160,64,48,0.12)',
    border:  'rgba(160,64,48,0.35)',
    icon: (
      <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>
    ),
  },
}

export default function StatusBlock({ prediction, loading }) {
  if (loading) {
    return (
      <div className="glass-card-static p-6 h-full">
        <div className="skeleton w-32 h-4 rounded mb-4" />
        <div className="skeleton w-48 h-10 rounded mb-3" />
        <div className="skeleton w-full h-3 rounded" />
      </div>
    )
  }

  const status = prediction?.status || 'normal'
  const cfg    = STATUS_CONFIG[status] || STATUS_CONFIG.normal

  return (
    <div
      className="glass-card-static p-6 h-full"
      style={{
        background: `radial-gradient(ellipse 80% 60% at 20% 50%, ${cfg.glow} 0%, transparent 60%), rgba(13,21,32,0.85)`,
        borderColor: cfg.border,
      }}
    >
      <div className="text-xs font-semibold uppercase tracking-widest mb-4"
           style={{ color: 'var(--text-muted)' }}>
        System Status
      </div>

      <div className="flex items-center gap-4 mb-4">
        {/* Animated ring */}
        <div className="relative flex items-center justify-center" style={{ width: 64, height: 64 }}>
          <span
            className="absolute rounded-full animate-pulse-ring"
            style={{
              inset: 0,
              background: `${cfg.color}22`,
              borderRadius: '50%',
            }}
          />
          <div
            className="relative flex items-center justify-center rounded-full"
            style={{
              width: 56, height: 56,
              background: cfg.bg,
              border: `2px solid ${cfg.border}`,
              color: cfg.color,
              boxShadow: `0 0 20px ${cfg.glow}`,
            }}
          >
            {cfg.icon}
          </div>
        </div>

        <div>
          <div
            className="text-4xl font-bold tracking-wide"
            style={{ color: cfg.color, textShadow: `0 0 30px ${cfg.color}55` }}
          >
            {cfg.label}
          </div>
          {prediction?.confidence != null && (
            <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
              AI confidence: {Math.round(prediction.confidence * 100)}%
            </div>
          )}
        </div>
      </div>

      <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.6 }}>
        {cfg.subtext}
      </p>

      {prediction?.anomaly && (
        <div className="mt-4 flex items-center gap-2 rounded-xl px-3 py-2"
             style={{ background: 'rgba(160,64,48,0.18)', border: '1px solid rgba(160,64,48,0.35)' }}>
          <span style={{ color: '#a04030', fontSize: 13 }}>WARNING Anomaly detected by ML model</span>
        </div>
      )}
    </div>
  )
}




