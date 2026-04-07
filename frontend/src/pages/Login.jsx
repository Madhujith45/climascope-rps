/**
 * ClimaScope - Premium Login Page
 */
import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login, googleLogin } from '../services/auth'
import ClimaScopeLogo from '../components/ClimaScopeLogo'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '906868526107-uibbhqhhssf687lafkh9dr6bj6fn1rim.apps.googleusercontent.com'

export default function Login() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ identifier: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [googleReady, setGoogleReady] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await login(form)
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Invalid login credentials')
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => {
    const clientId = GOOGLE_CLIENT_ID
    if (!clientId) {
      setGoogleReady(false)
      return
    }

    const scriptId = 'google-identity-services'
    const existingScript = document.getElementById(scriptId)

    const initGoogle = () => {
      if (!window.google?.accounts?.id) return

      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
          if (!response?.credential) {
            setError('Google login did not return a credential token')
            return
          }
          setLoading(true)
          setError('')
          try {
            const data = await googleLogin(response.credential)
            localStorage.setItem('token', data.access_token)
            localStorage.setItem('user', JSON.stringify(data.user))
            navigate('/dashboard')
          } catch (err) {
            setError(err.message || 'Google login failed')
          } finally {
            setLoading(false)
          }
        },
      })

      const googleBtn = document.getElementById('google-signin-button')
      if (googleBtn) {
        googleBtn.innerHTML = ''
        window.google.accounts.id.renderButton(googleBtn, {
          theme: 'outline',
          size: 'large',
          width: 320,
          text: 'continue_with',
          shape: 'pill',
        })
      }
      setGoogleReady(true)
    }

    if (existingScript) {
      initGoogle()
      return
    }

    const script = document.createElement('script')
    script.id = scriptId
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = initGoogle
    script.onerror = () => setError('Failed to load Google sign-in library')
    document.head.appendChild(script)
  }, [navigate])

  return (
    <div className="auth-bg auth-bg-login flex items-center justify-center md:justify-end min-h-screen p-4 md:pr-14 lg:pr-20">
      <div className="auth-card auth-card-login w-full max-w-md p-8 fade-in">
        <div className="mb-7 flex items-center justify-between">
          <ClimaScopeLogo size={42} showWordmark={true} />
          <span className="rounded-full px-2.5 py-1 text-xs font-semibold" style={{ color: '#9a6f08', background: 'rgba(184,134,11,0.14)', border: '1px solid rgba(184,134,11,0.3)' }}>
            Live Monitoring
          </span>
        </div>

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Welcome back</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Access your continuous climate intelligence workspace.</p>
        </div>

        {error && (
          <div className="mb-4 rounded-xl px-4 py-3 text-sm"
               style={{ background: 'rgba(160,64,48,0.18)', border: '1px solid rgba(160,64,48,0.35)', color: '#e8b0a6' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>
              Email or phone number
            </label>
            <input
              id="login-identifier"
              className="auth-input"
              type="text"
              placeholder="you@example.com or +91XXXXXXXXXX"
              value={form.identifier}
              onChange={e => setForm(f => ({ ...f, identifier: e.target.value }))}
              required
              autoComplete="username"
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
                style={{ color: '#b8860b' }}
              >
                Forgot password?
              </Link>
            </div>
            <input
              id="login-password"
              className="auth-input"
              type="password"
              placeholder="********"
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
            style={{
              background: 'linear-gradient(135deg, #d6a214, #bc8808)',
              color: '#151507',
              boxShadow: '0 12px 26px rgba(214,162,20,0.34)',
            }}
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="white" strokeWidth="4" />
                  <path className="opacity-75" fill="white" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                Signing in...
              </span>
            ) : 'Sign in'}
          </button>

          <div className="my-1 flex items-center gap-2">
            <div className="h-px flex-1" style={{ background: 'rgba(255,255,255,0.12)' }} />
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>or</span>
            <div className="h-px flex-1" style={{ background: 'rgba(255,255,255,0.12)' }} />
          </div>

          <div className="flex justify-center">
            <div id="google-signin-button" />
          </div>
          {!googleReady && (
            <p className="text-center text-xs" style={{ color: 'var(--text-muted)' }}>
              Google sign-in requires the frontend build to have a valid Google Client ID.
            </p>
          )}
        </form>

        <p className="text-center text-xs mt-6" style={{ color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/signup" className="font-medium hover:opacity-80" style={{ color: '#b8860b' }}>
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}




