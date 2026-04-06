/**
 * ClimaScope - Line Charts Component
 * Three auto-updating time-series charts using react-chartjs-2:
 *   Temperature vs Time | Pressure vs Time | Gas PPM vs Time
 */

import React, { useMemo } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const CHART_DEFS = [
  {
    key:   'temperature',
    label: 'Temperature',
    unit:  '°C',
    color: 'rgba(251,146,60,1)',
    fill:  'rgba(251,146,60,0.08)',
  },
  {
    key:   'pressure',
    label: 'Pressure',
    unit:  'hPa',
    color: 'rgba(167,139,250,1)',
    fill:  'rgba(167,139,250,0.08)',
  },
  {
    key:   'gas_ppm',
    label: 'Gas PPM',
    unit:  'ppm',
    color: 'rgba(52,211,153,1)',
    fill:  'rgba(52,211,153,0.08)',
  },
]

function formatTime(ts) {
  try {
    const d = new Date(ts)
    return [
      d.getHours().toString().padStart(2, '0'),
      d.getMinutes().toString().padStart(2, '0'),
      d.getSeconds().toString().padStart(2, '0'),
    ].join(':')
  } catch {
    return ts
  }
}

function buildDataset(records, def) {
  return {
    labels: records.map((r) => formatTime(r.timestamp)),
    datasets: [
      {
        label: `${def.label} (${def.unit})`,
        data: records.map((r) => r[def.key] ?? null),
        borderColor: def.color,
        backgroundColor: def.fill,
        borderWidth: 2,
        pointRadius: 2,
        pointHoverRadius: 5,
        tension: 0.35,
        fill: true,
        spanGaps: true,
      },
    ],
  }
}

function makeOptions(unit) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#8a8060',
        bodyColor: '#e2e8f0',
        borderColor: '#334155',
        borderWidth: 1,
        callbacks: {
          label: (ctx) =>
            ` ${ctx.parsed.y != null ? ctx.parsed.y.toFixed(2) : 'N/A'} ${unit}`,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#8a8060', maxTicksLimit: 8, font: { size: 10 } },
        grid:  { color: '#1e293b' },
      },
      y: {
        ticks: { color: '#8a8060', font: { size: 10 } },
        grid:  { color: '#1e2d45' },
      },
    },
  }
}

function ChartCard({ def, records }) {
  const chartData = useMemo(() => buildDataset(records, def), [records, def])
  const options   = useMemo(() => makeOptions(def.unit), [def.unit])

  return (
    <div className="rounded-xl border border-gray-700/60 bg-card p-4">
      <div className="mb-2 flex items-center gap-2">
        <span
          className="inline-block h-2.5 w-2.5 rounded-full"
          style={{ background: def.color }}
        />
        <h4 className="text-xs font-semibold uppercase tracking-widest text-gray-400">
          {def.label}
        </h4>
        <span className="ml-auto text-xs text-gray-600">{def.unit}</span>
      </div>
      <div className="h-44">
        <Line data={chartData} options={options} />
      </div>
    </div>
  )
}

export default function Charts({ records }) {
  // Display oldest → newest left to right
  const sorted = useMemo(
    () => (records ? [...records].reverse() : []),
    [records]
  )

  if (!records || records.length === 0) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {CHART_DEFS.map((d) => (
          <div
            key={d.key}
            className="h-64 rounded-xl border border-gray-700/60 bg-card animate-pulse"
          />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {CHART_DEFS.map((d) => (
        <ChartCard key={d.key} def={d} records={sorted} />
      ))}
    </div>
  )
}


