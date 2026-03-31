/**
 * ClimaScope – Trend Chart with Prediction Line
 * Solid line = real data, dashed line = 30-min forecast
 */
import React, { useMemo } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

function fmt(ts) {
  try {
    const d = new Date(ts)
    return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`
  } catch { return ts }
}

function generateForecast(sorted) {
  if (sorted.length < 6) return { labels: [], values: [] }
  const recent = sorted.slice(-10).map(r => Number(r.temperature)).filter(v => !isNaN(v))
  if (recent.length < 2) return { labels: [], values: [] }
  // Simple linear regression for naive forecast
  const n = recent.length
  const xMean = (n - 1) / 2
  const yMean = recent.reduce((a, b) => a + b, 0) / n
  let num = 0, den = 0
  for (let i = 0; i < n; i++) { num += (i - xMean) * (recent[i] - yMean); den += (i - xMean) ** 2 }
  const slope = den ? num / den : 0
  const intercept = yMean - slope * xMean

  const lastVal = recent[recent.length - 1]
  const lastTime = new Date(sorted[sorted.length - 1]?.timestamp || Date.now())
  const labels = []
  const values = [lastVal] // start from last real point for a connected look
  labels.push(fmt(lastTime))
  for (let i = 1; i <= 6; i++) { // 6 x 5min = 30 min
    const t = new Date(lastTime.getTime() + i * 5 * 60000)
    labels.push(fmt(t))
    values.push(parseFloat((intercept + slope * (n - 1 + i)).toFixed(2)))
  }
  return { labels, values }
}

export default function TrendChart({ data, loading }) {
  const sorted = useMemo(() => (data ? [...data].reverse() : []), [data])
  const forecast = useMemo(() => generateForecast(sorted), [sorted])

  const chartData = useMemo(() => {
    const realLabels = sorted.map(r => fmt(r.timestamp))
    const realValues = sorted.map(r => r.temperature ?? null)
    const allLabels = [...realLabels, ...forecast.labels.slice(1)] // skip first (duplicate)
    
    const fLen = Math.max(0, forecast.labels.length - 1)
    const rLen = Math.max(0, realValues.length - 1)
    
    const realData  = [...realValues, ...Array(fLen).fill(null)]
    const predData  = realValues.length > 0
      ? [...Array(rLen).fill(null), realValues[realValues.length - 1], ...forecast.values.slice(1)]
      : []

    return {
      labels: allLabels,
      datasets: [
        {
          label: 'Temperature (°C)',
          data: realData,
          borderColor: '#14b8a6',
          backgroundColor: (ctx) => {
            const c = ctx.chart.ctx; const g = c.createLinearGradient(0, 0, 0, 260)
            g.addColorStop(0, 'rgba(20,184,166,0.18)'); g.addColorStop(1, 'rgba(20,184,166,0.0)'); return g
          },
          borderWidth: 2.5,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: '#14b8a6',
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
          tension: 0.42,
          fill: true,
          spanGaps: true,
        },
        {
          label: 'Forecast',
          data: predData,
          borderColor: '#14b8a6',
          borderDash: [6, 4],
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: '#2dd4bf',
          tension: 0.3,
          fill: false,
          spanGaps: false,
        },
      ],
    }
  }, [sorted, forecast])

  const options = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 500 },
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(13,21,32,0.95)',
        titleColor: '#94a3b8', bodyColor: '#2dd4bf',
        borderColor: 'rgba(20,184,166,0.3)', borderWidth: 1,
        padding: 12, cornerRadius: 10,
        callbacks: { label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y != null ? ctx.parsed.y.toFixed(2) : '—'} °C` },
      },
    },
    scales: {
      x: { ticks: { color: '#4b6282', maxTicksLimit: 12, font: { size: 11, family: 'Inter' } }, grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false } },
      y: { ticks: { color: '#4b6282', font: { size: 11, family: 'Inter' }, callback: v => `${v}°` }, grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false } },
    },
  }), [])

  return (
    <div className="glass-card p-6 h-full">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-sm font-semibold text-white">Temperature Trend</h3>
          <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Last {sorted.length} readings + 30-min forecast
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-4 h-0.5 rounded-full" style={{ background: '#14b8a6' }} />
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Live</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-4 h-0.5 rounded-full" style={{ background: '#14b8a6', borderTop: '1px dashed #14b8a6', opacity: 0.6 }} />
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Forecast</span>
          </div>
        </div>
      </div>

      {loading || !data || data.length === 0 ? (
        <div className="skeleton w-full rounded-xl" style={{ height: 220 }} />
      ) : (
        <div style={{ height: 220 }}>
          <Line data={chartData} options={options} />
        </div>
      )}
    </div>
  )
}
