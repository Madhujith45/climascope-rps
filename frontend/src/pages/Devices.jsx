import React, { useState, useEffect } from 'react'
import { PageHeader } from '../components/PageHeader'
import { getAuthToken } from '../services/auth'
import toast from 'react-hot-toast'

export default function Devices() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const token = getAuthToken()
        const res = await fetch('/devices/list', { headers: { Authorization: `Bearer ${token}` } })
        if (!res.ok) throw new Error('Failed to fetch devices')
        const data = await res.json()
        setDevices(data.devices || [])
      } catch (err) {
        toast.error('Error loading devices')
      } finally {
        setLoading(false)
      }
    }
    fetchDevices()
  }, [])

  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in">
      <PageHeader title="Connected Devices" subtitle="Manage your edge sensors and view their connection status." />
      
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3].map(i => <div key={i} className="skeleton h-32 rounded-2xl" />)}
        </div>
      ) : devices.length === 0 ? (
        <div className="glass-card p-10 flex flex-col items-center justify-center text-center">
          <div className="text-4xl mb-3">📡</div>
          <h3 className="text-lg font-semibold text-white mb-1">No devices found</h3>
          <p className="text-sm text-gray-400">Add a new device to start monitoring.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {devices.map(d => (
            <div key={d.id} className="glass-card p-5 transition-transform hover:-translate-y-1">
              <div className="flex justify-between items-start mb-4">
                <div className="font-semibold text-lg text-white">{d.device_name}</div>
                <div className={`px-2 py-1 rounded text-xs font-bold ${d.is_active ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                  {d.is_active ? 'ONLINE' : 'OFFLINE'}
                </div>
              </div>
              <div className="text-xs space-y-2 text-gray-400">
                <div className="grid grid-cols-2"><span className="font-medium">ID:</span> <span>{d.device_id}</span></div>
                <div className="grid grid-cols-2"><span className="font-medium">Location:</span> <span>{d.location || 'Unassigned'}</span></div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
