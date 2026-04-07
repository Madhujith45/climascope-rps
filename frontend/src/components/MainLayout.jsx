/**
 * ClimaScope – Main Layout
 * Provides the Sidebar, Topbar, Main Content Area with Outlet, and Chatbot
 */
import React, { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import FloatingChatbot from './FloatingChatbot'
import { getCurrentUser, logout } from '../services/auth'

export default function MainLayout() {
  const [selectedDevice, setSelectedDevice] = useState('')
  const user = getCurrentUser()

  const handleLogout = () => {
    logout()
  }

  return (
    <div className="app-shell">
      <div className="app-bg-image" />
      <div className="app-bg-vignette" />

      <div className="relative z-10 flex h-full overflow-hidden">
        {/* ── Left Sidebar ───────────────────────────────────────── */}
        <Sidebar selectedDevice={selectedDevice} onDeviceChange={setSelectedDevice} />

        {/* ── Main Area ──────────────────────────────────────────── */}
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden relative px-4 md:px-6 pt-4">
          <Topbar user={user} selectedDevice={selectedDevice} secondsAgo={null} onLogout={handleLogout} />

          {/* ── Scrollable Content ─────────────────────────────────── */}
          <main className="flex-1 overflow-y-auto page-in relative" style={{ padding: '18px 4px 42px' }}>
            <Outlet context={{ selectedDevice, user }} />
          </main>

          <FloatingChatbot selectedDevice={selectedDevice} />
        </div>
      </div>
    </div>
  )
}

