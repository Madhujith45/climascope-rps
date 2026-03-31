/**
 * ClimaScope – Historical Data Table
 *
 * Displays paginated sensor readings from GET /api/data/history.
 * Supports device_id filtering and pagination.
 *
 * Props
 * -----
 * records      {object[]}  – array of sensor reading objects
 * total        {number}    – total record count (used for pagination footer)
 * deviceId     {string}    – current device filter value
 * onDeviceChange {fn}      – callback when device filter input changes
 * onPageChange  {fn}       – callback({ limit, offset }) for pagination
 * limit        {number}    – current page size
 * offset       {number}    – current offset
 * loading      {boolean}   – show skeleton rows while fetching
 */

import React from 'react'

const PAGE_SIZES = [25, 50, 100]

function formatTimestamp(ts) {
  try {
    return new Date(ts).toLocaleString(undefined, {
      month:   'short',
      day:     '2-digit',
      hour:    '2-digit',
      minute:  '2-digit',
      second:  '2-digit',
      hour12:  false,
    })
  } catch {
    return ts ?? '—'
  }
}

function fmt(v, decimals = 2) {
  return v !== undefined && v !== null ? Number(v).toFixed(decimals) : '—'
}

function SkeletonRows({ count = 8 }) {
  return Array.from({ length: count }, (_, i) => (
    <tr key={i} className="border-b border-slate-800">
      {[...Array(6)].map((__, j) => (
        <td key={j} className="px-4 py-3">
          <div className="h-4 w-full animate-pulse rounded bg-slate-700" />
        </td>
      ))}
    </tr>
  ))
}

export default function HistoryTable({
  records = [],
  total = 0,
  deviceId = '',
  onDeviceChange,
  onPageChange,
  limit = 25,
  offset = 0,
  loading = false,
}) {
  const currentPage = Math.floor(offset / limit) + 1
  const totalPages  = Math.max(1, Math.ceil(total / limit))

  function goTo(newOffset) {
    onPageChange?.({ limit, offset: Math.max(0, newOffset) })
  }
  function setPageSize(newLimit) {
    onPageChange?.({ limit: Number(newLimit), offset: 0 })
  }

  return (
    <div className="rounded-xl border border-slate-700/60 bg-card overflow-hidden">

      {/* ── Toolbar ──────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-700/60 px-4 py-3">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400">
          History
          {total > 0 && (
            <span className="ml-2 rounded-full bg-slate-700/60 px-2 py-0.5 font-mono text-slate-400">
              {total.toLocaleString()} records
            </span>
          )}
        </h3>

        {/* Device filter */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-500" htmlFor="device-filter">
            Device:
          </label>
          <input
            id="device-filter"
            type="text"
            value={deviceId}
            onChange={(e) => onDeviceChange?.(e.target.value)}
            placeholder="e.g. climascope_001"
            className="w-44 rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5
                       text-xs text-slate-200 placeholder-slate-600
                       focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500/40
                       transition-colors"
          />
          {deviceId && (
            <button
              onClick={() => onDeviceChange?.('')}
              className="rounded-lg border border-slate-600 bg-slate-800 px-2.5 py-1.5
                         text-xs text-slate-400 hover:bg-slate-700 transition-colors"
              title="Clear filter"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* ── Table ────────────────────────────────────────────────────── */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/80 text-xs">
              <th className="px-4 py-3 text-left font-semibold uppercase tracking-widest text-slate-500">
                #
              </th>
              <th className="px-4 py-3 text-left font-semibold uppercase tracking-widest text-slate-500">
                Timestamp
              </th>
              <th className="px-4 py-3 text-left font-semibold uppercase tracking-widest text-slate-500">
                Device
              </th>
              <th className="px-4 py-3 text-right font-semibold uppercase tracking-widest text-orange-500/70">
                Temp (°C)
              </th>
              <th className="px-4 py-3 text-right font-semibold uppercase tracking-widest text-violet-500/70">
                Pressure (hPa)
              </th>
              <th className="px-4 py-3 text-right font-semibold uppercase tracking-widest text-emerald-500/70">
                Gas (ppm)
              </th>
              <th className="px-4 py-3 text-right font-semibold uppercase tracking-widest text-sky-500/70">
                MQ2 (V)
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading ? (
              <SkeletonRows count={limit > 10 ? 8 : limit} />
            ) : records.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-slate-500">
                  {deviceId
                    ? `No records found for device "${deviceId}"`
                    : 'No historical data available yet.'}
                </td>
              </tr>
            ) : (
              records.map((row, idx) => (
                <tr
                  key={row.id ?? idx}
                  className="transition-colors hover:bg-slate-800/40"
                >
                  <td className="px-4 py-3 font-mono text-xs text-slate-600">
                    {offset + idx + 1}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-400 whitespace-nowrap">
                    {formatTimestamp(row.timestamp)}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400 max-w-[140px] truncate" title={row.device_id}>
                    {row.device_id ?? '—'}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-orange-400">
                    {fmt(row.temperature)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-violet-400">
                    {fmt(row.pressure)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-emerald-400">
                    {fmt(row.gas_ppm)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-sky-400">
                    {fmt(row.mq2_voltage, 3)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Pagination footer ─────────────────────────────────────────── */}
      {total > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-700/60 px-4 py-3 text-xs text-slate-500">
          {/* Page info */}
          <span>
            Page {currentPage} of {totalPages}
            &nbsp;·&nbsp;
            {offset + 1}–{Math.min(offset + limit, total)} of {total.toLocaleString()}
          </span>

          {/* Page size chooser */}
          <div className="flex items-center gap-2">
            <label htmlFor="page-size" className="text-slate-500">Rows:</label>
            <select
              id="page-size"
              value={limit}
              onChange={(e) => setPageSize(e.target.value)}
              className="rounded border border-slate-600 bg-slate-800 px-2 py-1
                         text-xs text-slate-300 focus:outline-none focus:border-sky-500"
            >
              {PAGE_SIZES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Prev / Next */}
          <div className="flex items-center gap-1">
            <button
              disabled={offset === 0}
              onClick={() => goTo(offset - limit)}
              className="rounded border border-slate-600 px-3 py-1 hover:bg-slate-800
                         disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              ← Prev
            </button>
            <button
              disabled={offset + limit >= total}
              onClick={() => goTo(offset + limit)}
              className="rounded border border-slate-600 px-3 py-1 hover:bg-slate-800
                         disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
