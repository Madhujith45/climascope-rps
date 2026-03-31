/**
 * ClimaScope – Premium Login Page
 */
import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../services/auth'

export default function Login() {
  const navigate = useNavigate()
  const [form,    setForm]    = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await login(form)
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user',  JSON.stringify(data.user))
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Invalid login credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-bg flex items-center justify-center min-h-screen p-4">
      <div className="auth-card w-full max-w-sm p-8 fade-in">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div
            className="flex items-center justify-center rounded-2xl mb-4"
            style={{
              width: 56, height: 56,
              background: 'linear-gradient(135deg,#14b8a6,#3b82f6)',
              boxShadow: '0 8px 24px rgba(20,184,166,0.4)',
            }}
          >
            <svg width="26" height="26" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth={2.5}>
              <path d="M12 2a10 10 0 100 20A10 10 0 0012 2z" />
              <path d="M12 6v6l4 2" strokeLinecap="round" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-white">Welcome back</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            Sign in to ClimaScope
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-xl px-4 py-3 text-sm"
               style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>
              Email address
            </label>
            <input
              id="login-email"
              className="auth-input"
              type="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              required
              autoComplete="email"
            />
          </div>
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>
                Password
              </label>
              <Link
                to="/forgot-password"
                className="text-xs hover:opacity-80 transition-opacity"
                style={{ color: '#2dd4bf' }}
              >
                Forgot password?
              </Link>
            </div>
            <input
              id="login-password"
              className="auth-input"
              type="password"
              placeholder="••••••••"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required
              autoComplete="current-password"
            />
          </div>

          <button
            id="login-submit"
            type="submit"
            className="auth-btn mt-2"
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="white" strokeWidth="4" />
                  <path className="opacity-75" fill="white" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                Signing in…
              </span>
            ) : 'Sign in'}
          </button>
        </form>

        <p className="text-center text-xs mt-6" style={{ color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/signup" className="font-medium hover:opacity-80" style={{ color: '#2dd4bf' }}>
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}
