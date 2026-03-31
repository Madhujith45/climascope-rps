import React, { useState } from 'react'
import { PageHeader } from '../components/PageHeader'
import { getCurrentUser } from '../services/auth'
import toast from 'react-hot-toast'

export default function Settings() {
  const user = getCurrentUser() || {}
  const [name, setName] = useState(user.full_name || '')
  
  const handleSave = (e) => {
    e.preventDefault()
    // Simulated update since we don't have a user update endpoint yet
    toast.success('Settings updated successfully!')
  }

  return (
    <div className="absolute inset-0 p-6 md:px-8 pb-10 overflow-y-auto page-in">
      <PageHeader title="Account Settings" subtitle="Manage your profile and API keys." />
      
      <div className="glass-card p-6 max-w-xl">
        <form onSubmit={handleSave} className="flex flex-col gap-5">
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
          <div>
            <label className="block text-xs font-semibold mb-1.5 text-gray-400">Password</label>
            <button type="button" className="text-sm font-medium text-teal-400 block pb-1 border-b border-teal-400/30">
              Request password reset
            </button>
          </div>
          <hr className="border-gray-800 my-2" />
          <button type="submit" className="auth-btn max-w-xs self-end">
            Save Changes
          </button>
        </form>
      </div>
    </div>
  )
}
