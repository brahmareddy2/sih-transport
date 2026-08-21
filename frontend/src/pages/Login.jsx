import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import { LANGUAGES, useI18nStore } from '../services/i18n'
import { ROLE_HOME_PATH } from '../services/constants'
import api from '../services/api'

export default function Login() {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark')

  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-theme')
    } else {
      document.body.classList.remove('light-theme')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  // Login form fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const { login, isLoading, error, clearError } = useAuthStore()
  const { language, setLanguage, t } = useI18nStore()
  const navigate = useNavigate()

  const DEMO_ROLES = [
    { role: 'admin', labelKey: 'role_admin', email: 'admin@logistics.in', pass: 'Admin@123!', icon: '👑', color: '#8b5cf6' },
    { role: 'fleet_operator', labelKey: 'role_fleet_operator', email: 'operator@logistics.in', pass: 'Operator@123!', icon: '⚡', color: '#3b82f6' },
    { role: 'driver', labelKey: 'role_driver', email: 'driver@logistics.in', pass: 'Driver@123!', icon: '📍', color: '#10b981' },
    { role: 'customer', labelKey: 'role_customer', email: 'customer@logistics.in', pass: 'Customer@123!', icon: '📦', color: '#f59e0b' },
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    const result = await login(email, password)
    if (result.success) {
      const dest = ROLE_HOME_PATH[result.role] || '/home'
      navigate(dest)
    }
  }

  const handleQuickLogin = async (demoEmail, demoPassword) => {
    setEmail(demoEmail)
    setPassword(demoPassword)
    clearError()
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
        {/* Language Selector Header */}
        <div style={{ marginBottom: '20px', padding: '12px', background: 'var(--color-bg-hover)', borderRadius: 14, border: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--color-purple)', marginBottom: '6px', textAlign: 'center' }}>
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
                    background: isSelected ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'var(--color-bg-primary)',
                    color: isSelected ? '#fff' : 'var(--color-text-secondary)',
                    border: isSelected ? '1px solid var(--color-purple)' : '1px solid var(--color-border)',
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
            <h1 style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--color-text-primary)', margin: 0, letterSpacing: '0.04em' }}>
              {t('login_portal_title', 'CARGO PILOT')}
            </h1>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', margin: '2px 0 0', fontWeight: 500 }}>
            {t('login_portal_sub', 'Your Intelligent Logistics Co-Pilot')}
          </p>
        </div>

        {/* Tab Toggle: Login vs Signup */}
        <div
          style={{
            display: 'flex',
            background: 'var(--color-bg-primary)',
            padding: '4px',
            borderRadius: 12,
            marginBottom: '20px',
            border: '1px solid var(--color-border)',
          }}
        >
          <button
            type="button"
            style={{
              flex: 1,
              padding: '10px',
              borderRadius: 8,
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
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
            onClick={() => navigate('/signup')}
            style={{
              flex: 1,
              padding: '10px',
              borderRadius: 8,
              background: 'transparent',
              color: 'var(--color-text-secondary)',
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

        {/* LOGIN FLOW */}
        <>
          {/* Quick Demo Logins */}
          {import.meta.env.VITE_ENABLE_DEV_LOGIN === 'true' && (
            <>
              <div style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 800, color: 'var(--color-purple)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    {t('single_click_login', '⚡ 1-Click Instant Sign In / Login')}
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', marginBottom: '8px' }}>
                  {DEMO_ROLES.map((r) => (
                    <button
                      key={r.role}
                      type="button"
                      onClick={() => handleQuickLogin(r.email, r.pass)}
                      disabled={isLoading}
                      style={{
                        padding: '10px',
                        borderRadius: 10,
                        background: 'var(--color-bg-primary)',
                        border: `1px solid ${r.color}33`,
                        color: 'var(--color-text-primary)',
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
                        e.currentTarget.style.background = 'var(--color-bg-primary)'
                        e.currentTarget.style.borderColor = `${r.color}33`
                      }}
                    >
                      <span style={{ fontSize: '1.2rem' }}>{r.icon}</span>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 800, fontSize: '0.8rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {t(r.labelKey, r.role.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()))}
                        </div>
                        <div style={{ fontSize: '0.65rem', color: 'var(--color-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.email}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Divider */}
              <div style={{ position: 'relative', textAlign: 'center', margin: '18px 0' }}>
                <div style={{ height: '1px', background: 'var(--color-border)', width: '100%' }} />
                <span style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', background: 'var(--color-bg-secondary)', padding: '0 10px', fontSize: '0.65rem', fontWeight: 800, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                  {t('or_enter_credentials', 'OR ENTER CREDENTIALS')}
                </span>
              </div>
            </>
          )}

          {/* Credentials Form */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <label htmlFor="email" style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
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
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 10,
                  padding: '10px 14px',
                  color: 'var(--color-text-primary)',
                  fontSize: '0.85rem',
                  outline: 'none',
                }}
              />
            </div>

            <div>
              <label htmlFor="password" style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
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
                  background: 'var(--color-bg-primary)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 10,
                  padding: '10px 14px',
                  color: 'var(--color-text-primary)',
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

          {/* Don't have an account? Sign up link */}
          <div style={{ textAlign: 'center', marginTop: '18px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
              Don't have an account?{' '}
            </span>
            <button
              type="button"
              onClick={() => navigate('/signup')}
              style={{
                background: 'none',
                border: 'none',
                padding: 0,
                fontSize: '0.8rem',
                color: 'var(--color-purple)',
                cursor: 'pointer',
                fontWeight: 800,
                transition: 'opacity 0.2s',
              }}
              onMouseEnter={(e) => (e.target.style.opacity = 0.8)}
              onMouseLeave={(e) => (e.target.style.opacity = 1)}
            >
              Sign Up
            </button>
          </div>
        </>
      </div>
    </div>
  )
}
