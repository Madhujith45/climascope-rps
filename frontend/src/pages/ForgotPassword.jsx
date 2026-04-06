/**
 * ClimaScope - Forgot Password (Premium 3-step OTP flow)
 * Step 1: Enter email → Step 2: Enter OTP (auto-focus boxes) → Step 3: New password
 * Success animation on completion
 */
import React, { useState, useRef, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { forgotPassword, verifyOtp, resetPassword } from '../services/auth'

function Logo() {
  return (
    <div className="flex flex-col items-center mb-8">
      <div
        className="flex items-center justify-center rounded-2xl mb-4"
        style={{ width: 56, height: 56, background: 'linear-gradient(135deg,#b8860b,#9a6f08)', boxShadow: '0 10px 24px rgba(0,0,0,0.35)' }}
      >
        <svg width="26" height="26" fill="none" viewBox="0 0 24 24" stroke="white" strokeWidth={2.5}>
          <path d="M12 2a10 10 0 100 20A10 10 0 0012 2z" /><path d="M12 6v6l4 2" strokeLinecap="round" />
        </svg>
      </div>
    </div>
  )
}

function StepIndicator({ current }) {
  const steps = ['Email', 'Verify OTP', 'New Password']
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {steps.map((s, i) => (
        <React.Fragment key={s}>
          <div className="flex items-center gap-1.5">
            <div
              className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300"
              style={{
                background: i <= current ? 'linear-gradient(135deg,#b8860b,#9a6f08)' : 'rgba(255,255,255,0.06)',
                color: i <= current ? '#fff' : '#8a8060',
                boxShadow: i === current ? '0 0 12px rgba(200,168,64,0.4)' : 'none',
              }}
            >
              {i < current ? 'OK' : i + 1}
            </div>
            <span className="text-xs hidden sm:inline" style={{ color: i <= current ? '#b8860b' : '#8a8060' }}>{s}</span>
          </div>
          {i < 2 && <div className="w-6 h-px" style={{ background: i < current ? '#b8860b' : 'rgba(255,255,255,0.1)' }} />}
        </React.Fragment>
      ))}
    </div>
  )
}

function OTPInput({ value, onChange }) {
  const refs = useRef([])
  const digits = value.padEnd(6, ' ').split('').slice(0, 6)

  const handleChange = (i, val) => {
    const ch = val.replace(/\D/g, '').slice(-1)
    const arr = digits.map(d => d.trim())
    arr[i] = ch
    const joined = arr.join('')
    onChange(joined.trim())
    if (ch && i < 5) refs.current[i + 1]?.focus()
  }

  const handleKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !digits[i].trim() && i > 0) {
      refs.current[i - 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const paste = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    onChange(paste)
    if (paste.length > 0) refs.current[Math.min(paste.length, 5)]?.focus()
  }

  return (
    <div className="flex gap-2 justify-center" onPaste={handlePaste}>
      {[0,1,2,3,4,5].map(i => (
        <input
          key={i}
          ref={el => refs.current[i] = el}
          type="text"
          inputMode="numeric"
          maxLength={1}
          className="w-11 h-13 text-center text-xl font-bold rounded-xl outline-none transition-all duration-200"
          autoFocus={i === 0}
          style={{
            background: digits[i].trim() ? 'rgba(200,168,64,0.12)' : 'rgba(255,255,255,0.05)',
            border: digits[i].trim() ? '1.5px solid rgba(200,168,64,0.5)' : '1.5px solid rgba(138,128,96,0.2)',
            color: '#4a8040',
            height: 52,
          }}
          value={digits[i].trim()}
          onChange={e => handleChange(i, e.target.value)}
          onKeyDown={e => handleKeyDown(i, e)}
        />
      ))}
    </div>
  )
}

export default function ForgotPassword() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0) // 0=email, 1=otp, 2=newpass, 3=success
  const [email, setEmail]           = useState('')
  const [otp, setOtp]               = useState('')
  const [resetToken, setResetToken] = useState('')
  const [newPassword, setNewPassword]   = useState('')
  const [confirmPass, setConfirmPass]   = useState('')
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState('')

  // Step 1 - send OTP
  const handleEmail = async (e) => {
    e.preventDefault()
    setLoading(true); setError('')
    try { await forgotPassword(email); setStep(1) }
    catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  // Step 2 - verify OTP
  const handleOtp = async (e) => {
    e.preventDefault()
    if (otp.length !== 6) { setError('Enter all 6 digits'); return }
    setLoading(true); setError('')
    try {
      const data = await verifyOtp(email, otp)
      setResetToken(data.reset_token)
      setStep(2)
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  // Step 3 - reset password
  const handleReset = async (e) => {
    e.preventDefault()
    if (newPassword !== confirmPass) { setError('Passwords do not match'); return }
    if (newPassword.length < 8) { setError('Password must be at least 8 characters'); return }
    setLoading(true); setError('')
    try {
      await resetPassword(email, newPassword, resetToken)
      setStep(3) // success
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="auth-bg flex items-center justify-center min-h-screen p-4">
      <div className="auth-card w-full max-w-sm p-8 page-in">
        <Logo />
        {step < 3 && <StepIndicator current={step} />}

        {error && (
          <div className="mb-4 rounded-xl px-4 py-3 text-sm"
               style={{ background: 'rgba(160,64,48,0.18)', border: '1px solid rgba(160,64,48,0.35)', color: '#e8b0a6' }}>
            {error}
          </div>
        )}

        {/* -- Step 0: Email ------------------------ */}
        {step === 0 && (
          <form onSubmit={handleEmail} className="flex flex-col gap-4">
            <div className="text-center mb-2">
              <h1 className="text-xl font-bold text-[var(--text-primary)]">Forgot password?</h1>
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>We'll send a 6-digit code to your email</p>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>Email address</label>
              <input className="auth-input" type="email" placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)} required autoFocus />
            </div>
            <button type="submit" className="auth-btn mt-1" disabled={loading}>
              {loading ? 'Sending...' : 'Send OTP'}
            </button>
            <p className="text-center text-xs" style={{ color: 'var(--text-muted)' }}>
              <Link to="/login" className="font-medium hover:opacity-80" style={{ color: '#b8860b' }}>Back to login</Link>
            </p>
          </form>
        )}

        {/* -- Step 1: OTP Input -------------------- */}
        {step === 1 && (
          <form onSubmit={handleOtp} className="flex flex-col gap-4">
            <div className="text-center mb-2">
              <h1 className="text-xl font-bold text-[var(--text-primary)]">Verify OTP</h1>
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                Enter the 6-digit code sent to <strong className="text-[var(--text-primary)]">{email}</strong>
              </p>
            </div>
            <OTPInput value={otp} onChange={setOtp} />
            <button type="submit" className="auth-btn mt-1" disabled={loading || otp.length < 6}>
              {loading ? 'Verifying...' : 'Verify Code'}
            </button>
            <button type="button" className="text-xs text-center" style={{ color: '#b8860b' }}
                    onClick={() => { setStep(0); setOtp(''); setError('') }}>
              Use a different email
            </button>
          </form>
        )}

        {/* -- Step 2: New Password ---------------- */}
        {step === 2 && (
          <form onSubmit={handleReset} className="flex flex-col gap-4">
            <div className="text-center mb-2">
              <h1 className="text-xl font-bold text-[var(--text-primary)]">Set new password</h1>
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Choose a strong password (min 8 chars)</p>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>New password</label>
              <input className="auth-input" type="password" placeholder="********" value={newPassword} onChange={e => setNewPassword(e.target.value)} required autoFocus />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--text-secondary)' }}>Confirm password</label>
              <input className="auth-input" type="password" placeholder="********" value={confirmPass} onChange={e => setConfirmPass(e.target.value)} required />
            </div>
            <button type="submit" className="auth-btn mt-1" disabled={loading}>
              {loading ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        )}

        {/* -- Step 3: Success ----------------------- */}
        {step === 3 && (
          <div className="text-center py-4 slide-up">
            <div className="text-5xl mb-4" style={{ filter: 'drop-shadow(0 0 12px rgba(34,197,94,0.5))' }}>OK</div>
            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">Password Reset!</h2>
            <p className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>Your password has been updated. You can now sign in.</p>
            <button className="auth-btn" onClick={() => navigate('/login')}>
              Go to Login
            </button>
          </div>
        )}
      </div>
    </div>
  )
}




