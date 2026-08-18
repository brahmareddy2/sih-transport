import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import { LANGUAGES, useI18nStore } from '../services/i18n'
import { ROLE_HOME_PATH } from '../services/constants'
import api from '../services/api'

export default function Login() {
  const [isSignup, setIsSignup] = useState(false)
  
  // Login form fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  
  // Signup form fields
  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [requestedRole, setRequestedRole] = useState('driver')
  const [prefLang, setPrefLang] = useState('en')
  const [signupPassword, setSignupPassword] = useState('')
  const [signupSuccessMsg, setSignupSuccessMsg] = useState('')

  const { login, isLoading, error, clearError } = useAuthStore()
  const { language, setLanguage, t } = useI18nStore()
  const navigate = useNavigate()

  const DEMO_ROLES = [
    { role: 'admin', labelKey: 'role_admin', email: 'admin@logistics.in', pass: 'Admin@123!', icon: '👑', color: '#8b5cf6' },
    { role: 'operator', labelKey: 'role_operator', email: 'operator@logistics.in', pass: 'Operator@123!', icon: '⚡', color: '#3b82f6' },
    { role: 'fleet_manager', labelKey: 'role_fleet', email: 'fleet@logistics.in', pass: 'Fleet@123!', icon: '🚛', color: '#06b6d4' },
    { role: 'driver', labelKey: 'role_driver', email: 'driver@logistics.in', pass: 'Driver@123!', icon: '📍', color: '#10b981' },
    { role: 'customer', labelKey: 'role_customer', email: 'customer@logistics.in', pass: 'Customer@123!', icon: '📦', color: '#f59e0b' },
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    setSignupSuccessMsg('')
    const result = await login(email, password)
    if (result.success) {
      const dest = ROLE_HOME_PATH[result.role] || '/home'
      navigate(dest)
    }
  }

  const handleSignupSubmit = async (e) => {
    e.preventDefault()
    clearError()
    setSignupSuccessMsg('')
    try {
      const { data } = await api.post('/auth/signup', {
        full_name: fullName,
        email: email,
        password: signupPassword,
        phone: phone || null,
        preferred_language: prefLang,
        organization_name: organizationName || null,
        role: requestedRole,
      })

      if (requestedRole === 'admin') {
        setSignupSuccessMsg('Administrator account created! It is currently pending approval. Please contact a system administrator to activate it.')
      } else {
        setSignupSuccessMsg('Registration successful! Please login with your credentials.')
        // Fill login email and switch to login tab
        setIsSignup(false)
        setPassword('')
      }
    } catch (err) {
      const errMsg = err.response?.data?.detail || 'Registration failed. Please check your inputs.'
      useAuthStore.setState({ error: errMsg })
    }
  }

  const handleQuickLogin = async (demoEmail, demoPassword) => {
    setEmail(demoEmail)
    setPassword(demoPassword)
    clearError()
    setSignupSuccessMsg('')
    const result = await login(demoEmail, demoPassword)
    if (result.success) {
      const dest = ROLE_HOME_PATH[result.role] || '/home'
      navigate(dest)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0a0a18 0%, #131326 50%, #0a0a18 100%)',
        padding: '16px',
        fontFamily: "'Inter', sans-serif",
        position: 'relative',
        overflow: 'hidden',
      }}
    >
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
          background: '#16162aee',
          border: '1px solid #2d2d48',
          borderRadius: 24,
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
          padding: '24px',
          zIndex: 2,
          position: 'relative',
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Language Selector Header */}
        <div style={{ marginBottom: '20px', padding: '12px', background: '#1c1c34', borderRadius: 14, border: '1px solid #333355' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#a5b4fc', marginBottom: '6px', textAlign: 'center' }}>
            {t('select_language_title', '🌐 Choose Your Preferred Language')}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center' }}>
            {LANGUAGES.map((lang) => {
              const isSelected = language === lang.code
              return (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => setLanguage(lang.code)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 8,
                    background: isSelected ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : '#121222',
                    color: isSelected ? '#fff' : '#cbd5e1',
                    border: isSelected ? '1px solid #a5b4fc' : '1px solid #2d2d42',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    boxShadow: isSelected ? '0 0 10px rgba(99, 102, 241, 0.4)' : 'none',
                    transition: 'all 0.2s',
                  }}
                >
                  <span>{lang.flag}</span>
                  <span>{lang.native}</span>
                </button>
              )
            })}
          </div>
        </div>

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
            <h1 style={{ fontSize: '1.8rem', fontWeight: 900, color: '#fff', margin: 0, letterSpacing: '0.04em' }}>
              {t('login_portal_title', 'CARGO PILOT')}
            </h1>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#9ca3af', margin: '2px 0 0', fontWeight: 500 }}>
            {t('login_portal_sub', 'Your Intelligent Logistics Co-Pilot')}
          </p>
        </div>

        {/* Tab Toggle: Login vs Signup */}
        <div
          style={{
            display: 'flex',
            background: '#111122',
            padding: '4px',
            borderRadius: 12,
            marginBottom: '20px',
            border: '1px solid #2d2d44',
          }}
        >
          <button
            type="button"
            onClick={() => { setIsSignup(false); clearError(); setSignupSuccessMsg(''); }}
            style={{
              flex: 1,
              padding: '10px',
              borderRadius: 8,
              background: !isSignup ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent',
              color: '#fff',
              border: 'none',
              fontWeight: 800,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {t('login_tab', 'Login')}
          </button>
          <button
            type="button"
            onClick={() => { setIsSignup(true); clearError(); setSignupSuccessMsg(''); }}
            style={{
              flex: 1,
              padding: '10px',
              borderRadius: 8,
              background: isSignup ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent',
              color: '#fff',
              border: 'none',
              fontWeight: 800,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            {t('signup_tab', 'Create Account')}
          </button>
        </div>

        {error && (
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
            {error}
          </div>
        )}

        {signupSuccessMsg && (
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
            {signupSuccessMsg}
          </div>
        )}

        {!isSignup ? (
          /* LOGIN FLOW */
          <>
            {/* Quick Demo Logins */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {t('single_click_login', '⚡ 1-Click Instant Sign In / Login')}
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', marginBottom: '8px' }}>
                {DEMO_ROLES.slice(0, 4).map((r) => (
                  <button
                    key={r.role}
                    type="button"
                    onClick={() => handleQuickLogin(r.email, r.pass)}
                    disabled={isLoading}
                    style={{
                      padding: '10px',
                      borderRadius: 10,
                      background: '#1c1c34',
                      border: `1px solid ${r.color}33`,
                      color: '#fff',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      textAlign: 'left',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = `${r.color}15`
                      e.currentTarget.style.borderColor = r.color
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = '#1c1c34'
                      e.currentTarget.style.borderColor = `${r.color}33`
                    }}
                  >
                    <span style={{ fontSize: '1.2rem' }}>{r.icon}</span>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontWeight: 800, fontSize: '0.8rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {t(r.labelKey, r.role.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()))}
                      </div>
                      <div style={{ fontSize: '0.65rem', color: '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.email}</div>
                    </div>
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={() => handleQuickLogin(DEMO_ROLES[4].email, DEMO_ROLES[4].pass)}
                disabled={isLoading}
                style={{
                  width: '100%',
                  padding: '10px',
                  borderRadius: 10,
                  background: '#1c1c34',
                  border: `1px solid ${DEMO_ROLES[4].color}33`,
                  color: '#fff',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  textAlign: 'left',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = `${DEMO_ROLES[4].color}15`
                  e.currentTarget.style.borderColor = DEMO_ROLES[4].color
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = '#1c1c34'
                  e.currentTarget.style.borderColor = `${DEMO_ROLES[4].color}33`
                }}
              >
                <span style={{ fontSize: '1.2rem' }}>{DEMO_ROLES[4].icon}</span>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '0.8rem' }}>{t(DEMO_ROLES[4].labelKey, 'Customer')}</div>
                  <div style={{ fontSize: '0.65rem', color: '#9ca3af' }}>{DEMO_ROLES[4].email}</div>
                </div>
              </button>
            </div>

            {/* Divider */}
            <div style={{ position: 'relative', textAlign: 'center', margin: '18px 0' }}>
              <div style={{ height: '1px', background: '#2d2d48', width: '100%' }} />
              <span style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', background: '#16162a', padding: '0 10px', fontSize: '0.65rem', fontWeight: 800, color: '#6b7280', textTransform: 'uppercase' }}>
                {t('or_enter_credentials', 'OR ENTER CREDENTIALS')}
              </span>
            </div>

            {/* Credentials Form */}
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label htmlFor="email" style={{ fontSize: '0.78rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '4px' }}>
                  {t('email_label', 'Email Address')}
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  required
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    background: '#111122',
                    border: '1px solid #3b3b5c',
                    borderRadius: 10,
                    padding: '10px 14px',
                    color: '#fff',
                    fontSize: '0.85rem',
                    outline: 'none',
                  }}
                />
              </div>

              <div>
                <label htmlFor="password" style={{ fontSize: '0.78rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '4px' }}>
                  {t('password_label', 'Password')}
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    background: '#111122',
                    border: '1px solid #3b3b5c',
                    borderRadius: 10,
                    padding: '10px 14px',
                    color: '#fff',
                    fontSize: '0.85rem',
                    outline: 'none',
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: 10,
                  background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 800,
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)',
                  marginTop: '8px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {isLoading ? 'Authenticating...' : t('sign_in_btn', 'Sign In / Log In ➔')}
              </button>
            </form>
          </>
        ) : (
          /* SIGNUP FLOW */
          <form onSubmit={handleSignupSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '4px' }}>
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Ravi Kumar"
                  required
                  style={{ width: '100%', boxSizing: 'border-box', background: '#111122', border: '1px solid #3b3b5c', borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '4px' }}>
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ravi@cargo.in"
                  required
                  style={{ width: '100%', boxSizing: 'border-box', background: '#111122', border: '1px solid #3b3b5c', borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '4px' }}>
                  Mobile Number
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 99988 87776"
                  style={{ width: '100%', boxSizing: 'border-box', background: '#111122', border: '1px solid #3b3b5c', borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '4px' }}>
                  Password
                </label>
                <input
                  type="password"
                  value={signupPassword}
                  onChange={(e) => setSignupPassword(e.target.value)}
                  placeholder="Minimum 6 chars"
                  required
                  style={{ width: '100%', boxSizing: 'border-box', background: '#111122', border: '1px solid #3b3b5c', borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '4px' }}>
                  Organization/Company
                </label>
                <input
                  type="text"
                  value={organizationName}
                  onChange={(e) => setOrganizationName(e.target.value)}
                  placeholder="GMR Logistics"
                  style={{ width: '100%', boxSizing: 'border-box', background: '#111122', border: '1px solid #3b3b5c', borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '4px' }}>
                  Preferred Language
                </label>
                <select
                  value={prefLang}
                  onChange={(e) => setPrefLang(e.target.value)}
                  style={{ width: '100%', boxSizing: 'border-box', background: '#111122', border: '1px solid #3b3b5c', borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
                >
                  <option value="en">English</option>
                  <option value="te">తెలుగు (Telugu)</option>
                  <option value="hi">हिन्दी (Hindi)</option>
                  <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                  <option value="mr">मराठी (Marathi)</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '4px' }}>
                Requested Security Role
              </label>
              <select
                value={requestedRole}
                onChange={(e) => setRequestedRole(e.target.value)}
                style={{ width: '100%', boxSizing: 'border-box', background: '#111122', border: '1px solid #3b3b5c', borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: '0.8rem', outline: 'none' }}
              >
                <option value="driver">🚛 Driver (Mobile Cockpit)</option>
                <option value="operator">⚡ Logistics Operator (VRP Optimization)</option>
                <option value="fleet_manager">👨‍✈️ Fleet & Maintenance Manager</option>
                <option value="customer">📦 Enterprise Customer (Shipment Track)</option>
                <option value="admin">👑 Platform Administrator (Approval Required)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: 8,
                background: 'linear-gradient(135deg, #10b981, #059669)',
                color: '#fff',
                border: 'none',
                fontWeight: 800,
                fontSize: '0.85rem',
                cursor: 'pointer',
                boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)',
                marginTop: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {isLoading ? 'Processing...' : 'Register New Account ➔'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
