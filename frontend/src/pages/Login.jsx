import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import { ROLE_HOME_PATH } from '../services/constants'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login, isLoading, error, clearError } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    const result = await login(email, password)
    if (result.success) {
      const dest = ROLE_HOME_PATH[result.role] || '/'
      navigate(dest)
    }
  }

  const handleQuickLogin = (demoEmail, demoPassword) => {
    setEmail(demoEmail)
    setPassword(demoPassword)
    clearError()
    login(demoEmail, demoPassword).then((result) => {
      if (result.success) {
        const dest = ROLE_HOME_PATH[result.role] || '/'
        navigate(dest)
      }
    })
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--color-bg-primary)',
      padding: '20px'
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '460px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h1 style={{ fontSize: '1.6rem', fontWeight: '700', marginBottom: '6px' }}>
            🚚 Logistics DSS
          </h1>
          <p className="text-sm text-muted">
            AI-Powered Intelligent Transportation Platform
          </p>
        </div>

        {error && (
          <div className="badge badge-danger w-full" style={{ padding: '12px 14px', marginBottom: '18px', borderRadius: 'var(--radius-md)', textTransform: 'none', justifyContent: 'center', lineHeight: '1.4' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label htmlFor="email" style={{ fontSize: '0.85rem', fontWeight: '600' }}>Email Address</label>
            <input
              id="email"
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operator@logistics.in"
              required
            />
          </div>

          <div>
            <label htmlFor="password" style={{ fontSize: '0.85rem', fontWeight: '600' }}>Password</label>
            <input
              id="password"
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button type="submit" className="btn btn-primary w-full" style={{ justifyContent: 'center', marginTop: '6px' }} disabled={isLoading}>
            {isLoading ? <span className="spinner" /> : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--color-border)' }}>
          <p className="text-xs text-muted" style={{ textAlign: 'center', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            ⚡ Single-Click Demo Sign In
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleQuickLogin('admin@logistics.in', 'Admin@123!')}
              disabled={isLoading}
              style={{ justifyContent: 'center', fontSize: '0.8rem' }}
            >
              👑 Admin
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleQuickLogin('operator@logistics.in', 'Operator@123!')}
              disabled={isLoading}
              style={{ justifyContent: 'center', fontSize: '0.8rem' }}
            >
              ⚡ Operator
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleQuickLogin('fleet@logistics.in', 'Fleet@123!')}
              disabled={isLoading}
              style={{ justifyContent: 'center', fontSize: '0.8rem' }}
            >
              🚛 Fleet Mgr
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => handleQuickLogin('driver@logistics.in', 'Driver@123!')}
              disabled={isLoading}
              style={{ justifyContent: 'center', fontSize: '0.8rem' }}
            >
              📍 Driver
            </button>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm w-full"
            onClick={() => handleQuickLogin('customer@logistics.in', 'Customer@123!')}
            disabled={isLoading}
            style={{ justifyContent: 'center', fontSize: '0.8rem', marginTop: '8px' }}
          >
            📦 Enterprise Customer
          </button>
        </div>
      </div>
    </div>
  )
}
