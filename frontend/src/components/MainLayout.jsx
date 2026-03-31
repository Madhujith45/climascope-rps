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
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-base)' }}>
      {/* ── Left Sidebar ───────────────────────────────────────── */}
      <Sidebar selectedDevice={selectedDevice} onDeviceChange={setSelectedDevice} />

      {/* ── Main Area ──────────────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden relative">
        <Topbar user={user} secondsAgo={null} onLogout={handleLogout} />

        {/* ── Scrollable Content ─────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto page-in relative" style={{ padding: '24px 28px 40px' }}>
          <Outlet context={{ selectedDevice, user }} />
        </main>

        <FloatingChatbot selectedDevice={selectedDevice} />
      </div>
    </div>
  )
}
