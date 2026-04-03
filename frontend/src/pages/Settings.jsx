import React, { useState, useEffect } from 'react'
import { PageHeader } from '../components/PageHeader'
import { getCurrentUser, getAuthToken } from '../services/auth'
import toast from 'react-hot-toast'

export default function Settings() {
  const user = getCurrentUser() || {}
  const [name, setName] = useState(user.full_name || '')
  
  // Extract country and specific phone
  const defaultCode = '+91'
  let dbCode = '+91'
  let dbPhone = ''
  
  if (user.phone) {
    const match = user.phone.match(/^(\+\d{1,4})(.*)$/)
    if (match) {
      dbCode = match[1]
      dbPhone = match[2]
    } else {
      dbPhone = user.phone
    }
  }

  const [countryCode, setCountryCode] = useState(dbCode)
  const [phone, setPhone] = useState(dbPhone)
  
  const [alertMode, setAlertMode] = useState(user.alert_mode || 'email')
  const [alertsEnabled, setAlertsEnabled] = useState(user.alerts_enabled !== false)
  const [loading, setLoading] = useState(false)
  const [fetching, setFetching] = useState(true)

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setFetching(true)
        const token = getAuthToken()
        const res = await fetch('/auth/verify', {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (res.ok) {
          const data = await res.json()
          if (data.user) {
            setName(data.user.full_name || '')
            setAlertMode(data.user.alert_mode || 'email')
            setAlertsEnabled(data.user.alerts_enabled !== false)
            if (data.user.phone) {
              const match = data.user.phone.match(/^(\+\d{1,4})(.*)$/)
              if (match) {
                setCountryCode(match[1])
                setPhone(match[2])
              } else {
                setPhone(data.user.phone)
              }
            }
          }
        }
      } catch (err) {
        console.error("Failed to fetch user settings", err)
      } finally {
        setFetching(false)
      }
    }
    fetchSettings()
  }, [])

  const handleSave = async (e) => {
    e.preventDefault()

    const finalPhone = phone.trim() ? `${countryCode}${phone.trim()}` : ''

    if (["sms", "both"].includes(alertMode)) {
      if (!finalPhone) {
        toast.error('Phone number required for SMS alerts')
        return
      }
      if (!finalPhone.match(/^\+[1-9]\d{4,14}$/)) {
        toast.error('Invalid phone format. Please provide a valid phone number.')
        return
      }
    }

    try {
      setLoading(true)
      const token = getAuthToken()
      const res = await fetch('/auth/me/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          full_name: name,
          phone: finalPhone || null,
          alert_mode: alertMode,
          alerts_enabled: alertsEnabled
        })
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to update settings')
      }

      toast.success('Settings updated successfully!')

      // Attempt to refresh local user copy
      const verifyRes = await fetch('/auth/verify', {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (verifyRes.ok) {
        const data = await verifyRes.json()
        localStorage.setItem('climascope_user', JSON.stringify(data.user))      
        window.dispatchEvent(new Event('storage')) // Trigger auth update       
      }

    } catch (err) {
      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (fetching) {
    return <div className="p-8 text-slate-400">Loading settings...</div>        
  }

  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in">
      <PageHeader title="Account Settings" subtitle="Manage your profile, alerts, and API keys." />

      <div className="glass-card p-6 max-w-xl">
        <form onSubmit={handleSave} className="flex flex-col gap-6">

          <div className="flex flex-col gap-5">
            <h3 className="text-sm font-semibold border-b border-gray-800 pb-2 text-teal-400">Profile Information</h3>

            <div>
              <label className="block text-xs font-semibold mb-1.5 text-gray-400">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="auth-input bg-opacity-20 bg-slate-800"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold mb-1.5 text-gray-400">Email Address</label>
              <input
                type="email"
                value={user.email || ''}
                disabled
                className="auth-input opacity-60 cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Email cannot be changed.</p>
            </div>

          </div>

          <div className="flex flex-col gap-5 mt-2">
            <h3 className="text-sm font-semibold border-b border-gray-800 pb-2 text-teal-400">Alert Preferences</h3>

            <div className="flex items-center justify-between bg-slate-800/40 p-4 rounded-xl border border-white/5">
              <div>
                <div className="text-sm font-medium text-white">Enable Alerts</div>
                <div className="text-xs text-gray-400 mt-0.5">Receive notifications for anomalies or high risk scores.</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={alertsEnabled}
                  onChange={e => setAlertsEnabled(e.target.checked)}
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-teal-500"></div>
              </label>
            </div>

            <div className={`transition-opacity duration-300 ${!alertsEnabled ? 'opacity-50 pointer-events-none' : ''}`}>
              <label className="block text-xs font-semibold mb-1.5 text-gray-400">Alert Mode</label>
              <select
                value={alertMode}
                onChange={e => setAlertMode(e.target.value)}
                disabled={!alertsEnabled}
                className="auth-input bg-opacity-20 bg-slate-800 w-full"        
              >
                <option value="email">Email Only</option>
                <option value="sms">SMS Only</option>
                <option value="both">Both Email & SMS</option>
              </select>
            </div>

            <div className={`transition-opacity duration-300 ${!alertsEnabled ? 'opacity-50 pointer-events-none' : ''}`}>
              <label className="block text-xs font-semibold mb-1.5 text-gray-400">Phone Number (Optional)</label>
              
              <div className="flex gap-2">
                <select
                  value={countryCode}
                  onChange={e => setCountryCode(e.target.value)}
                  disabled={!alertsEnabled}
                  className="auth-input bg-opacity-20 bg-slate-800 w-32"
                >
                  <option value="+1">+1 (US)</option>
                  <option value="+44">+44 (UK)</option>
                  <option value="+61">+61 (AU)</option>
                  <option value="+91">+91 (IN)</option>
                </select>
                <input
                  type="tel"
                  placeholder="Enter phone number"
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  disabled={!alertsEnabled}
                  className="auth-input bg-opacity-20 bg-slate-800 flex-1"
                />
              </div>

              <p className="text-xs text-gray-500 mt-1">Required if SMS receiving is enabled.</p>
              {["sms", "both"].includes(alertMode) && !phone && (
                <p className="text-xs text-amber-500 mt-1 font-medium">?? Warning: Phone number is required for SMS alerts</p>
              )}
            </div>

          </div>

          <hr className="border-gray-800 my-2" />
          <button type="submit" disabled={loading} className={`auth-btn max-w-xs self-end ${loading ? 'opacity-70 cursor-wait' : ''}`}>
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </div>
    </div>
  )
}
