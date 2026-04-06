/**
 * ClimaScope - Trend Chart with Prediction Line
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
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  } catch {
    return ts
  }
}

function generateForecast(sorted) {
  if (sorted.length < 6) return { labels: [], values: [] }

  const recent = sorted.slice(-10).map((r) => Number(r?.raw?.temperature)).filter((v) => !isNaN(v))
  if (recent.length < 2) return { labels: [], values: [] }

  const n = recent.length
  const xMean = (n - 1) / 2
  const yMean = recent.reduce((a, b) => a + b, 0) / n

  let num = 0
  let den = 0
  for (let i = 0; i < n; i++) {
    num += (i - xMean) * (recent[i] - yMean)
    den += (i - xMean) ** 2
  }

  const slope = den ? num / den : 0
  const intercept = yMean - slope * xMean

  const lastVal = recent[recent.length - 1]
  const lastTime = new Date(sorted[sorted.length - 1]?.timestamp || Date.now())

  const labels = [fmt(lastTime)]
  const values = [lastVal]

  for (let i = 1; i <= 6; i++) {
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
    const realLabels = sorted.map((r) => fmt(r.timestamp))
    const realValues = sorted.map((r) => r?.raw?.temperature ?? null)
    const allLabels = [...realLabels, ...forecast.labels.slice(1)]

    const fLen = Math.max(0, forecast.labels.length - 1)
    const rLen = Math.max(0, realValues.length - 1)

    const realData = [...realValues, ...Array(fLen).fill(null)]
    const predData = realValues.length > 0
      ? [...Array(rLen).fill(null), realValues[realValues.length - 1], ...forecast.values.slice(1)]
      : []

    return {
      labels: allLabels,
      datasets: [
        {
          label: 'Temperature (°C)',
          data: realData,
          borderColor: '#9a6f08',
          backgroundColor: (ctx) => {
            const c = ctx.chart.ctx
            const g = c.createLinearGradient(0, 0, 0, 260)
            g.addColorStop(0, 'rgba(240, 208, 64, 0.15)')
            g.addColorStop(1, 'rgba(240, 208, 64, 0)')
            return g
          },
          borderWidth: 2.5,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: '#9a6f08',
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
          tension: 0.42,
          fill: true,
          spanGaps: true,
        },
        {
          label: 'Forecast',
          data: predData,
          borderColor: '#b8860b',
          borderDash: [6, 4],
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: '#b8860b',
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
        backgroundColor: 'rgba(30, 35, 20, 0.95)',
        titleColor: '#8a8060',
        bodyColor: '#e8e0c8',
        borderColor: 'rgba(200,168,64,0.4)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 10,
        callbacks: {
          label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y != null ? ctx.parsed.y.toFixed(2) : '-'} °C`,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#8a8060', maxTicksLimit: 12, font: { size: 11, family: 'Inter' } },
        grid: { color: 'rgba(138,128,96,0.12)', drawBorder: false },
      },
      y: {
        ticks: { color: '#8a8060', font: { size: 11, family: 'Inter' }, callback: (v) => `${v}` },
        grid: { color: 'rgba(138,128,96,0.10)', drawBorder: false },
      },
    },
  }), [])

  return (
    <div className="glass-card p-5 h-full">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-base font-semibold text-[var(--text-primary)]">Temperature Trend</h3>
          <div className="text-sm" style={{ color: 'var(--text-muted)' }}>Last 24 hours</div>
        </div>
        <span
          className="text-xs px-3 py-1 rounded-full"
          style={{
            background: 'rgba(200, 168, 64, 0.12)',
            border: '1px solid rgba(200,168,64,0.4)',
            color: '#9a6f08',
          }}
        >
          Today
        </span>
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




