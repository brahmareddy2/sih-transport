import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import { ROLE_HOME_PATH } from '../services/constants'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login, isLoading, error, clearError } = useAuthStore()
  const navigate = useNavigate()

  const DEMO_ROLES = [
    { role: 'admin', label: 'Admin', email: 'admin@logistics.in', pass: 'Admin@123!', icon: '👑', color: '#8b5cf6', desc: 'Full System Control & Analytics' },
    { role: 'operator', label: 'Operator', email: 'operator@logistics.in', pass: 'Operator@123!', icon: '⚡', color: '#3b82f6', desc: 'OR-Tools Routing & Consolidation' },
    { role: 'fleet_manager', label: 'Fleet Manager', email: 'fleet@logistics.in', pass: 'Fleet@123!', icon: '🚛', color: '#06b6d4', desc: 'Vehicle Telematics & Return Cargo' },
    { role: 'driver', label: 'Driver', email: 'driver@logistics.in', pass: 'Driver@123!', icon: '📍', color: '#10b981', desc: 'Simple Voice Cockpit & My Trip' },
    { role: 'customer', label: 'Customer', email: 'customer@logistics.in', pass: 'Customer@123!', icon: '📦', color: '#f59e0b', desc: 'Live Consignment Tracking' },
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
        background: 'linear-gradient(135deg, #0d0d1a 0%, #151528 50%, #0d0d1a 100%)',
        padding: '24px',
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '560px',
          background: '#16162a',
          border: '1px solid #2d2d48',
          borderRadius: 24,
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
          padding: '36px',
        }}
      >
        {/* App Title Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.8rem',
              boxShadow: '0 0 25px rgba(99, 102, 241, 0.5)',
              marginBottom: '12px',
            }}
          >
            🚚
          </div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 900, color: '#fff', margin: 0 }}>
            Logistics DSS Portal
          </h1>
          <p style={{ fontSize: '0.9rem', color: '#9ca3af', margin: '6px 0 0' }}>
            AI-Powered Multi-Vehicle Logistics Decision Support System
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
              lineHeight: 1.4,
              textAlign: 'center',
            }}
          >
            {error}
          </div>
        )}

        {/* 1. Single-Click Instant Login (5 Roles) */}
        <div style={{ marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 800, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              ⚡ 1-Click Instant Sign In / Login
            </span>
            <span style={{ fontSize: '0.72rem', color: '#6b7280' }}>No typing required</span>
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
                  <div style={{ fontWeight: 800, fontSize: '0.9rem', color: '#fff' }}>{r.label}</div>
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
              <div style={{ fontWeight: 800, fontSize: '0.9rem', color: '#fff' }}>{DEMO_ROLES[4].label}</div>
              <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>{DEMO_ROLES[4].email}</div>
            </div>
          </button>
        </div>

        {/* Divider */}
        <div style={{ position: 'relative', textAlign: 'center', margin: '24px 0' }}>
          <div style={{ height: '1px', background: '#2d2d48', width: '100%' }} />
          <span
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: '#16162a',
              padding: '0 14px',
              fontSize: '0.75rem',
              fontWeight: 700,
              color: '#6b7280',
              textTransform: 'uppercase',
            }}
          >
            OR ENTER CREDENTIALS
          </span>
        </div>

        {/* 2. Manual Credentials Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label htmlFor="email" style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e2e8f0', display: 'block', marginBottom: '6px' }}>
              Email Address
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
              Password
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
              marginTop: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            {isLoading ? 'Authenticating...' : 'Sign In / Log In ➔'}
          </button>
        </form>
      </div>
    </div>
  )
}
