/**
 * ClimaScope – Premium Signup Page
 */
import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { signup, login } from '../services/auth'

export default function Signup() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '', phone: '', countryCode: '+91' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (form.password !== form.confirm) {
      setError('Passwords do not match')
      return
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    const finalPhone = form.phone.trim() ? `${form.countryCode}${form.phone.trim()}` : ''

    if (finalPhone) {
      const phoneRegex = /^\+[1-9]\d{4,14}$/
      if (!phoneRegex.test(finalPhone)) {
        setError('Enter a valid phone number')
        return
      }
    }

    setLoading(true)
    setError('')

    try {
      const payload = {
        email: form.email,
        password: form.password,
        full_name: form.full_name
      }
      if (finalPhone) {
        payload.phone = finalPhone
      }

      await signup(payload)
      const data = await login({ email: form.email, password: form.password })  
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user',  JSON.stringify(data.user))
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.')
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
          <h1 className="text-xl font-bold text-white">Create account</h1>      
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Start monitoring your environment</p>
        </div>

        {error && (
          <div className="mb-4 rounded-xl px-4 py-3 text-sm"
               style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#fca5a5' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {[
            { id:'signup-name',     label:'Full name',       type:'text',     key:'full_name', placeholder:'Jane Smith'        },
            { id:'signup-email',    label:'Email address',   type:'email',    key:'email',     placeholder:'you@example.com'   },
            { id:'signup-password', label:'Password',        type:'password', key:'password',  placeholder:'Min 8 characters'  },
            { id:'signup-confirm',  label:'Confirm password',type:'password', key:'confirm',   placeholder:'Repeat password'   },
          ].map(f => (
            <div key={f.key}>
              <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>
                {f.label}
              </label>
              <input
                id={f.id}
                className="auth-input"
                type={f.type}
                placeholder={f.placeholder}
                value={form[f.key]}
                onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                required={f.key !== 'full_name'}
              />
            </div>
          ))}

          {/* New Phone Split Input */}
          <div>
            <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>
              Phone Number (Optional)
            </label>
            <div className="flex flex-col gap-2">
              <div className="flex gap-2">
                <select
                  value={form.countryCode}
                  onChange={e => setForm(prev => ({ ...prev, countryCode: e.target.value }))}
                  className="auth-input w-[100px]"
                >
                  <option value="+1">+1 (US)</option>
                  <option value="+44">+44 (UK)</option>
                  <option value="+61">+61 (AU)</option>
                  <option value="+91">+91 (IN)</option>
                </select>
                <input
                  id="signup-phone"
                  className="auth-input flex-1"
                  type="tel"
                  placeholder="Enter phone number"
                  value={form.phone}
                  onChange={e => setForm(prev => ({ ...prev, phone: e.target.value.replace(/\D/g, '') }))}
                />
              </div>
              <p className="text-[10px] mt-1" style={{ color: 'var(--text-muted)' }}>
                Optional – required only for SMS alerts
              </p>
            </div>
          </div>

          <button id="signup-submit" type="submit" className="auth-btn mt-2" disabled={loading}>
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="white" strokeWidth="4" />
                  <path className="opacity-75" fill="white" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                </svg>
                Creating account…
              </span>
            ) : 'Create account'}
          </button>
        </form>

        <p className="text-center text-xs mt-6" style={{ color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <Link to="/login" className="font-medium hover:opacity-80" style={{ color: '#2dd4bf' }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
