/**
 * ClimaScope - Placeholder Page Builder
 */
import React from 'react'

export function PageHeader({ title, subtitle }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-1">{title}</h1>
      <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{subtitle}</p>
    </div>
  )
}


