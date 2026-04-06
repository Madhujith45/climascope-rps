/**
 * ClimaScope – Sensor Cards Component
 * Displays a grid of four metric cards:
 *   Temperature | Pressure | Gas PPM | MQ2 Voltage
 */

import React from 'react'

const CARDS = [
  {
    key: 'temperature',
    label: 'Temperature',
    unit: '°C',
    icon: '🌡️',
    color: 'from-green-500/20 to-yellow-400/10',
    border: 'border-green-500/40',
    textColor: 'text-green-400',
    barColor: 'bg-green-400',
    min: 25,
    max: 40,
  },
  {
    key: 'pressure',
    label: 'Pressure',
    unit: 'hPa',
    icon: '🌐',
    color: 'from-yellow-400/16 to-green-500/10',
    border: 'border-yellow-400/35',
    textColor: 'text-yellow-400',
    barColor: 'bg-yellow-400',
    min: 980,
    max: 1020,
  },
  {
    key: 'gas_ppm',
    label: 'Gas PPM',
    unit: 'ppm',
    icon: '☁️',
    color: 'from-yellow-400/16 to-green-500/10',
    border: 'border-yellow-400/35',
    textColor: 'text-yellow-400',
    barColor: 'bg-yellow-400',
    min: 0,
    max: 300,
  },
  {
    key: 'mq2_voltage',
    label: 'MQ2 Voltage',
    unit: 'V',
    icon: '⚡',
    color: 'from-green-500/20 to-yellow-400/10',
    border: 'border-green-500/40',
    textColor: 'text-green-400',
    barColor: 'bg-green-400',
    min: 0,
    max: 5,
  },
]

function ProgressBar({ value, min, max, barColor }) {
  const pct = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100))
  return (
    <div className="mt-3 h-1.5 w-full rounded-full bg-gray-700">
      <div
        className={`h-1.5 rounded-full transition-all duration-700 ${barColor}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {CARDS.map((c) => (
        <div
          key={c.key}
          className={`rounded-xl border bg-gradient-to-br p-5 animate-pulse ${c.color} ${c.border}`}
        >
          <div className="h-4 w-24 rounded bg-gray-600" />
          <div className="mt-4 h-8 w-28 rounded bg-gray-600" />
          <div className="mt-3 h-1.5 w-full rounded bg-gray-700" />
        </div>
      ))}
    </div>
  )
}

export default function SensorCards({ data }) {
  if (!data) return <SkeletonGrid />

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {CARDS.map((c) => {
        const raw   = data[c.key]
        const value = raw !== undefined && raw !== null ? Number(raw) : null
        const display = value !== null
          ? value.toFixed(c.key === 'mq2_voltage' ? 3 : 2)
          : '—'

        return (
          <div
            key={c.key}
            className={`rounded-xl border bg-gradient-to-br p-5 transition-all duration-300 hover:scale-[1.02] ${c.color} ${c.border}`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">
                {c.label}
              </span>
              <span className="text-xl">{c.icon}</span>
            </div>
            <div className={`mt-2 text-3xl font-bold font-mono ${c.textColor}`}>
              {display}
              <span className="ml-1 text-base font-normal text-gray-400">{c.unit}</span>
            </div>
            {value !== null && (
              <ProgressBar value={value} min={c.min} max={c.max} barColor={c.barColor} />
            )}
          </div>
        )
      })}
    </div>
  )
}

