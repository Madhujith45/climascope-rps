/**
 * ClimaScope - Device Selector Component
 * Allows users to select and manage their devices
 */

import React, { useState, useEffect } from 'react'
import { getAuthToken } from '../services/auth'

const BASE_URL = import.meta.env.VITE_BACKEND_URL;

function DeviceSelector({ selectedDevice, onDeviceChange, className = "" }) {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const token = getAuthToken()
        if (!token) {
          throw new Error('No authentication token found')
        }

        let response = await fetch(`${BASE_URL}/api/devices/list`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          response = await fetch(`${BASE_URL}/devices/list`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })
        }

        if (!response.ok) {
          throw new Error('Failed to fetch devices')
        }

        const data = await response.json()
        setDevices(data.devices || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchDevices()
  }, [])

  const handleDeviceChange = (deviceId) => {
    onDeviceChange(deviceId)
  }

  if (loading) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="animate-spin h-4 w-4 border-2 border-green-600 border-t-transparent border-r-transparent border-b-transparent border-l-transparent"></div>
        <span className="text-sm text-gray-500">Loading devices...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-sm text-red-500">Failed to load devices</span>
      </div>
    )
  }

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <svg className="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      
      <select
        value={selectedDevice}
        onChange={(e) => handleDeviceChange(e.target.value)}
        className="block w-full px-3 py-2 border border-gray-700 bg-gray-800 text-[var(--text-primary)] text-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
      >
        <option value="">Select a device</option>
        {devices.map((device) => (
          <option key={device.id} value={device.device_id}>
            {device.device_name} ({device.location || 'No location'})
          </option>
        ))}
      </select>

      {devices.length === 0 && !loading && !error && (
        <span className="text-sm text-gray-500">No devices found</span>
      )}
    </div>
  )
}

export default DeviceSelector


