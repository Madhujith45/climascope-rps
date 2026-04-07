import React, { useState, useEffect } from 'react'
import { PageHeader } from '../components/PageHeader'
import { getAuthToken } from '../services/auth'
import toast from 'react-hot-toast'

const BASE_URL = import.meta.env.VITE_BACKEND_URL?.replace(/\/$/, '') || ''

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const token = getAuthToken()
        const res = await fetch(`${BASE_URL}/alerts/?limit=20`, { headers: { Authorization: `Bearer ${token}` } })
        if (!res.ok) throw new Error('Failed to fetch alerts')
        const data = await res.json()
        setAlerts(data.alerts || [])
      } catch (err) {
        toast.error('Error loading alerts')
      } finally {
        setLoading(false)
      }
    }
    fetchAlerts()
  }, [])

  const fmt = (iso) => new Date(iso).toLocaleString()

  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in">
      <PageHeader title="System Alerts" subtitle="Recent anomalies and warning conditions detected across your devices." />
      
      {loading ? (
        <div className="space-y-4">
          {[1,2,3,4].map(i => <div key={i} className="skeleton h-20 rounded-xl" />)}
        </div>
      ) : alerts.length === 0 ? (
        <div className="glass-card p-10 flex flex-col items-center justify-center text-center">
          <div className="text-4xl mb-3">OK</div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-1">No alerts!</h3>
          <p className="text-sm text-gray-400">Your systems are operating normally.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map(a => (
            <div key={a.id} className="glass-card flex p-4 items-center gap-4 alert-strip-danger">
              <div className="text-2xl">{a.severity === 'danger' || a.severity === 'critical' || a.severity === 'high' ? 'ALERT' : 'WARNING'}</div>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-baseline mb-1">
                  <h4 className="font-semibold text-[var(--text-primary)] truncate">{a.message || 'Anomaly Detected'}</h4>
                  <span className="text-xs text-gray-400 whitespace-nowrap ml-4">{fmt(a.created_at)}</span>
                </div>
                <p className="text-xs text-gray-400">
                  <span className="text-yellow-300 font-medium">Device: {a.device_id}</span>
                  {a.alert_type && ` | Type: ${a.alert_type.toUpperCase()}`}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}


