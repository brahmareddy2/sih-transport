import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useI18nStore } from '../services/i18n'
import api from '../services/api'

export default function Signup() {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark')

  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-theme')
    } else {
      document.body.classList.remove('light-theme')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [requestedRole, setRequestedRole] = useState('driver')
  const [prefLang, setPrefLang] = useState('en')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const [validationError, setValidationError] = useState('')
  const [apiError, setApiError] = useState('')
  const [successMsg, setSuccessMsg] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { t } = useI18nStore()
  const navigate = useNavigate()

  const handleSignupSubmit = async (e) => {
    e.preventDefault()
    setValidationError('')
    setApiError('')
    setSuccessMsg('')

    // Client-side validations
    if (!fullName.trim() || !email.trim() || !password || !confirmPassword) {
      setValidationError('Please fill in all required fields.')
      return
    }

    // Basic email format check
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      setValidationError('Please enter a valid email address.')
      return
    }

    // Password length check
    if (password.length < 6) {
      setValidationError('Password must be at least 6 characters long.')
      return
    }

    // Confirm password check
    if (password !== confirmPassword) {
      setValidationError('Passwords do not match.')
      return
    }

    setIsSubmitting(true)
    try {
      const { data } = await api.post('/auth/signup', {
        full_name: fullName,
        email: email,
        password: password,
        phone: phone || null,
        preferred_language: prefLang,
        organization_name: organizationName || null,
        role: requestedRole,
      })

      if (requestedRole === 'admin') {
        setSuccessMsg('Administrator account created! It is currently pending approval. Redirecting to login page...')
      } else {
        setSuccessMsg('Account created successfully! Redirecting to login page...')
      }

      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login')
      }, 3000)
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Registration failed. Please check your inputs.'
      setApiError(errMsg)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-bg-primary)',
        padding: '16px',
        fontFamily: "'Inter', sans-serif",
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Theme Mode Toggle Button */}
      <button
        type="button"
        onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          cursor: 'pointer',
          fontSize: '1.2rem',
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: 'var(--shadow-glow)',
          zIndex: 999,
          color: 'var(--color-text-primary)',
        }}
        title={theme === 'light' ? 'Switch to Night Mode (Dark)' : 'Switch to Day Mode (Light)'}
      >
        {theme === 'light' ? '🌙' : '☀️'}
      </button>

      {/* Subtle background watermark logo */}
      <img
        src="/logo.png"
        alt="Watermark"
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%) rotate(-10deg)',
          width: '70%',
          maxWidth: '500px',
          opacity: 0.04,
          pointerEvents: 'none',
          zIndex: 1,
        }}
      />

      <div
        style={{
          width: '100%',
          maxWidth: '520px',
          background: 'var(--color-bg-secondary)',
          border: '1px solid var(--color-border)',
          borderRadius: 24,
          boxShadow: 'var(--shadow-card)',
          padding: '24px',
          zIndex: 2,
          position: 'relative',
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Portal Title & Branding */}
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              marginBottom: '6px',
            }}
          >
            <img src="/logo.png" alt="Cargo Pilot Logo" style={{ height: '36px', objectFit: 'contain' }} />
            <h1 style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--color-text-primary)', margin: 0, letterSpacing: '0.04em' }}>
              {t('signup_portal_title', 'CARGO PILOT')}
            </h1>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', margin: '2px 0 0', fontWeight: 500 }}>
            Create Your Intelligent Logistics Account
          </p>
        </div>

        {/* Error/Success Banners */}
        {(validationError || apiError) && (
          <div
            style={{
              background: '#ef444422',
              color: '#f87171',
              border: '1px solid #ef444466',
              padding: '10px 14px',
              borderRadius: 10,
              marginBottom: '16px',
              fontSize: '0.8rem',
              fontWeight: 600,
              textAlign: 'center',
            }}
          >
            {validationError || apiError}
          </div>
        )}

        {successMsg && (
          <div
            style={{
              background: '#10b98122',
              color: '#34d399',
              border: '1px solid #10b98166',
              padding: '10px 14px',
              borderRadius: 10,
              marginBottom: '16px',
              fontSize: '0.8rem',
              fontWeight: 600,
              textAlign: 'center',
            }}
          >
            {successMsg}
          </div>
        )}

        {/* Signup Form */}
        <form onSubmit={handleSignupSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
                Full Name *
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ravi Kumar"
                required
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  padding: '10px 12px',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.8rem',
                  outline: 'none',
                }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
                Email Address *
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ravi@cargo.in"
                required
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  padding: '10px 12px',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.8rem',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
                Mobile Number
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 99988 87776"
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  padding: '10px 12px',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.8rem',
                  outline: 'none',
                }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
                Organization/Company
              </label>
              <input
                type="text"
                value={organizationName}
                onChange={(e) => setOrganizationName(e.target.value)}
                placeholder="GMR Logistics"
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  padding: '10px 12px',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.8rem',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
                Preferred Language
              </label>
              <select
                value={prefLang}
                onChange={(e) => setPrefLang(e.target.value)}
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  padding: '10px 12px',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.8rem',
                  outline: 'none',
                }}
              >
                <option value="en">English</option>
                <option value="te">తెలుగు (Telugu)</option>
                <option value="hi">हिन्दी (Hindi)</option>
                <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                <option value="mr">मराठी (Marathi)</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
                Requested Security Role
              </label>
              <select
                value={requestedRole}
                onChange={(e) => setRequestedRole(e.target.value)}
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  padding: '10px 12px',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.8rem',
                  outline: 'none',
                }}
              >
                <option value="driver">🚛 Driver (Mobile Cockpit)</option>
                <option value="fleet_operator">👨‍✈️ Fleet Operator</option>
                <option value="customer">📦 Enterprise Customer (Shipment Track)</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
                Password *
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min 6 chars"
                required
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  padding: '10px 12px',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.8rem',
                  outline: 'none',
                }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
                Confirm Password *
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Match password"
                required
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8,
                  padding: '10px 12px',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.8rem',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              width: '100%',
              padding: '12px',
              borderRadius: 10,
              background: 'linear-gradient(135deg, #10b981, #059669)',
              color: '#fff',
              border: 'none',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)',
              marginTop: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {isSubmitting ? 'Processing...' : 'Register New Account ➔'}
          </button>
        </form>

        {/* Link back to Login */}
        <div style={{ textAlign: 'center', marginTop: '18px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
            Already have an account?{' '}
          </span>
          <Link
            to="/login"
            style={{
              fontSize: '0.8rem',
              color: 'var(--color-purple)',
              textDecoration: 'none',
              fontWeight: 800,
              transition: 'opacity 0.2s',
            }}
            onMouseEnter={(e) => (e.target.style.opacity = 0.8)}
            onMouseLeave={(e) => (e.target.style.opacity = 1)}
          >
            Log In
          </Link>
        </div>
      </div>
    </div>
  )
}
