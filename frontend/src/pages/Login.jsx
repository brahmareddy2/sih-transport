import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import { LANGUAGES, useI18nStore } from '../services/i18n'
import { ROLE_HOME_PATH } from '../services/constants'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
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
        background: 'linear-gradient(135deg, #0a0a18 0%, #131326 50%, #0a0a18 100%)',
        padding: '24px',
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '580px',
          background: '#16162a',
          border: '1px solid #2d2d48',
          borderRadius: 24,
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
          padding: '36px',
        }}
      >
        {/* 1. Language Selector Header */}
        <div style={{ marginBottom: '24px', padding: '16px', background: '#1c1c34', borderRadius: 18, border: '1px solid #333355' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#a5b4fc', marginBottom: '6px', textAlign: 'center' }}>
            {t('select_language_title', '🌐 Choose Your Preferred Language')}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '12px', textAlign: 'center' }}>
            {t('select_language_sub', 'The application and Voice Assistant will operate in your chosen language.')}
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' }}>
            {LANGUAGES.map((lang) => {
              const isSelected = language === lang.code
              return (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => setLanguage(lang.code)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: 10,
                    background: isSelected ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : '#121222',
                    color: isSelected ? '#fff' : '#cbd5e1',
                    border: isSelected ? '1px solid #a5b4fc' : '1px solid #2d2d42',
                    fontSize: '0.85rem',
                    fontWeight: 800,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    boxShadow: isSelected ? '0 0 15px rgba(99, 102, 241, 0.4)' : 'none',
                    transition: 'all 0.2s',
                  }}
                >
                  <span>{lang.flag}</span>
                  <span>{lang.native}</span>
                  {lang.code !== 'en' && <span style={{ fontSize: '0.7rem', opacity: 0.8 }}>({lang.name})</span>}
                </button>
              )
            })}
          </div>
        </div>

        {/* 2. Portal Title */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.6rem',
              boxShadow: '0 0 25px rgba(99, 102, 241, 0.5)',
              marginBottom: '10px',
            }}
          >
            🚚
          </div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 900, color: '#fff', margin: 0 }}>
            {t('login_portal_title', 'Logistics DSS Portal')}
          </h1>
          <p style={{ fontSize: '0.85rem', color: '#9ca3af', margin: '4px 0 0' }}>
            {t('login_portal_sub', 'AI-Powered Multi-Vehicle Logistics Decision Support System')}
          </p>
        </div>

        {error && (
          <div
            style={{
              background: '#ef444422',
              color: '#f87171',
              border: '1px solid #ef444466',
              padding: '12px 16px',
              borderRadius: 12,
              marginBottom: '20px',
              fontSize: '0.85rem',
              fontWeight: 600,
              textAlign: 'center',
            }}
          >
            {error}
          </div>
        )}

        {/* 3. Single-Click Instant Login (5 Roles) */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 800, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              {t('single_click_login', '⚡ 1-Click Instant Sign In / Login')}
            </span>
            <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>
              {t('no_typing_needed', 'Tap your role to enter')}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
            {DEMO_ROLES.slice(0, 4).map((r) => (
              <button
                key={r.role}
                type="button"
                onClick={() => handleQuickLogin(r.email, r.pass)}
                disabled={isLoading}
                style={{
                  padding: '12px 14px',
                  borderRadius: 14,
                  background: '#1c1c34',
                  border: `1px solid ${r.color}44`,
                  color: '#fff',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  textAlign: 'left',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = `${r.color}18`
                  e.currentTarget.style.borderColor = r.color
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = '#1c1c34'
                  e.currentTarget.style.borderColor = `${r.color}44`
                }}
              >
                <span style={{ fontSize: '1.4rem' }}>{r.icon}</span>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '0.9rem', color: '#fff' }}>{t(r.labelKey, r.role)}</div>
                  <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>{r.email}</div>
                </div>
              </button>
            ))}
          </div>

          {/* Customer full width */}
          <button
            type="button"
            onClick={() => handleQuickLogin(DEMO_ROLES[4].email, DEMO_ROLES[4].pass)}
            disabled={isLoading}
            style={{
              width: '100%',
              marginTop: '10px',
              padding: '12px 14px',
              borderRadius: 14,
              background: '#1c1c34',
              border: `1px solid ${DEMO_ROLES[4].color}44`,
              color: '#fff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              textAlign: 'left',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = `${DEMO_ROLES[4].color}18`
              e.currentTarget.style.borderColor = DEMO_ROLES[4].color
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#1c1c34'
              e.currentTarget.style.borderColor = `${DEMO_ROLES[4].color}44`
            }}
          >
            <span style={{ fontSize: '1.4rem' }}>{DEMO_ROLES[4].icon}</span>
            <div>
              <div style={{ fontWeight: 800, fontSize: '0.9rem', color: '#fff' }}>{t(DEMO_ROLES[4].labelKey, 'Customer')}</div>
              <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>{DEMO_ROLES[4].email}</div>
            </div>
          </button>
        </div>

        {/* Divider */}
        <div style={{ position: 'relative', textAlign: 'center', margin: '22px 0' }}>
          <div style={{ height: '1px', background: '#2d2d48', width: '100%' }} />
          <span
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: '#16162a',
              padding: '0 14px',
              fontSize: '0.72rem',
              fontWeight: 800,
              color: '#6b7280',
              textTransform: 'uppercase',
            }}
          >
            {t('or_enter_credentials', 'OR ENTER CREDENTIALS')}
          </span>
        </div>

        {/* 4. Manual Credentials Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label htmlFor="email" style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '6px' }}>
              {t('email_label', 'Email Address')}
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@logistics.in"
              required
              style={{
                width: '100%',
                boxSizing: 'border-box',
                background: '#111122',
                border: '1px solid #3b3b5c',
                borderRadius: 12,
                padding: '12px 16px',
                color: '#fff',
                fontSize: '0.9rem',
                outline: 'none',
              }}
            />
          </div>

          <div>
            <label htmlFor="password" style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '6px' }}>
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
                borderRadius: 12,
                padding: '12px 16px',
                color: '#fff',
                fontSize: '0.9rem',
                outline: 'none',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: 12,
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              color: '#fff',
              border: 'none',
              fontWeight: 800,
              fontSize: '1rem',
              cursor: 'pointer',
              boxShadow: '0 4px 20px rgba(99, 102, 241, 0.4)',
              marginTop: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            {isLoading ? 'Authenticating...' : t('sign_in_btn', 'Sign In / Log In ➔')}
          </button>
        </form>
      </div>
    </div>
  )
}
