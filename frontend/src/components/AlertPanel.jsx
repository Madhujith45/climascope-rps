/**
 * ClimaScope - Alert Panel Component
 * Displays real-time alerts with management capabilities
 */

import React, { useState, useEffect } from 'react'
import { getAuthToken } from '../services/auth'

const BASE_URL = import.meta.env.VITE_BACKEND_URL?.replace(/\/$/, '') || ''

function AlertPanel({ className = "" }) {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const token = getAuthToken()
        if (!token) {
          throw new Error('No authentication token found')
        }

        const response = await fetch(`${BASE_URL}/alerts/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          throw new Error('Failed to fetch alerts')
        }

        const data = await response.json()
        setAlerts(data.alerts || [])
        setUnreadCount(data.unread_count || 0)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchAlerts()
  }, [])

  const handleMarkAsRead = async (alertId) => {
    try {
      const token = getAuthToken()
      const response = await fetch(`${BASE_URL}/alerts/${alertId}/read`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        // Update local state
        setAlerts(alerts.map(alert => 
          alert.id === alertId ? { ...alert, is_read: true } : alert
        ))
        setUnreadCount(prev => Math.max(0, prev - 1))
      }
    } catch (err) {
      console.error('Failed to mark alert as read:', err)
    }
  }

  const handleResolveAlert = async (alertId) => {
    try {
      const token = getAuthToken()
      const response = await fetch(`${BASE_URL}/alerts/${alertId}/resolve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        // Update local state
        setAlerts(alerts.map(alert => 
          alert.id === alertId ? { ...alert, is_resolved: true } : alert
        ))
      }
    } catch (err) {
      console.error('Failed to resolve alert:', err)
    }
  }

  const handleDeleteAlert = async (alertId) => {
    try {
      const token = getAuthToken()
      const response = await fetch(`${BASE_URL}/alerts/${alertId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        // Remove from local state
        setAlerts(alerts.filter(alert => alert.id !== alertId))
      }
    } catch (err) {
      console.error('Failed to delete alert:', err)
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      const token = getAuthToken()
      const response = await fetch(`${BASE_URL}/alerts/mark-all-read`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        setAlerts(alerts.map(alert => ({ ...alert, is_read: true })))
        setUnreadCount(0)
      }
    } catch (err) {
      console.error('Failed to mark all alerts as read:', err)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'danger':
        return 'text-red-400 bg-red-950/30 border-red-800/50'
      case 'warning':
        return 'text-yellow-400 bg-yellow-950/30 border-yellow-800/50'
      default:
        return 'text-yellow-400 bg-gray-900/30 border-green-800/50'
    }
  }

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'danger':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'warning':
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.732-2.5L13.732 4c-.77.833-1.964-.833-2.5L4.082 16.5c-.77.833.192 2.5z" />
          </svg>
        )
      default:
        return (
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  if (loading) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
        <div className="flex items-center space-x-2">
          <div className="animate-spin h-4 w-4 border-2 border-green-600 border-t-transparent border-r-transparent border-b-transparent border-l-transparent"></div>
          <span className="text-sm text-gray-500">Loading alerts...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
        <div className="flex items-center space-x-2">
          <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm text-red-500">Failed to load alerts</span>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">Alerts</h3>
        <div className="flex items-center space-x-2">
          {unreadCount > 0 && (
            <span className="bg-red-600 text-[var(--text-primary)] text-xs px-2 py-1 rounded-full">
              {unreadCount} unread
            </span>
          )}
          <button
            onClick={handleMarkAllAsRead}
            className="text-xs text-yellow-400 hover:text-yellow-300"
          >
            Mark All as Read
          </button>
        </div>
      </div>

      {/* Alert List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <svg className="h-12 w-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm">No alerts found</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`border rounded-lg p-4 ${getSeverityColor(alert.severity)} ${
                !alert.is_read ? 'border-opacity-100' : ''
              }`}
            >
              {/* Alert Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getSeverityIcon(alert.severity)}
                  <div>
                    <div className="text-sm font-medium text-[var(--text-primary)] capitalize">
                      {alert.severity}
                    </div>
                    <div className="text-xs text-gray-400">
                      {alert.device_name}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {!alert.is_read && (
                    <button
                      onClick={() => handleMarkAsRead(alert.id)}
                      className="text-xs text-yellow-400 hover:text-yellow-300"
                    >
                      Mark as Read
                    </button>
                  )}
                  <button
                    onClick={() => handleResolveAlert(alert.id)}
                    className="text-xs text-green-400 hover:text-green-300"
                  >
                    {alert.is_resolved ? 'Resolved' : 'Resolve'}
                  </button>
                  <button
                    onClick={() => handleDeleteAlert(alert.id)}
                    className="text-xs text-red-400 hover:text-red-300"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Alert Message */}
              <div className="text-sm text-[var(--text-primary)] mb-2">
                {alert.message}
              </div>

              {/* Alert Metadata */}
              <div className="flex items-center justify-between text-xs text-gray-400">
                <div>
                  {formatTime(alert.created_at)}
                </div>
                <div>
                  {alert.is_resolved && (
                    <span className="text-green-400">
                      Resolved: {formatTime(alert.resolved_at)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default AlertPanel


