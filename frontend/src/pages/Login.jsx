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

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--color-bg-primary)',
      padding: '20px'
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '420px' }}>
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '8px' }}>
            🚚 Logistics DSS
          </h1>
          <p className="text-sm text-muted">
            AI-Powered Intelligent Transportation Platform
          </p>
        </div>

        {error && (
          <div className="badge badge-danger w-full" style={{ padding: '10px 14px', marginBottom: '20px', borderRadius: 'var(--radius-md)', textTransform: 'none', justifyContent: 'center' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label htmlFor="email">Email Address</label>
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
            <label htmlFor="password">Password</label>
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

          <button type="submit" className="btn btn-primary w-full" style={{ justifyContent: 'center', marginTop: '8px' }} disabled={isLoading}>
            {isLoading ? <span className="spinner" /> : 'Sign In'}
          </button>
        </form>

        <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--color-border)', textAlign: 'center' }}>
          <p className="text-sm text-muted">Phase 1 Demo Credentials</p>
          <code className="font-mono text-sm" style={{ display: 'block', marginTop: '4px', color: 'var(--color-brand-light)' }}>
            admin@logistics.in / Admin@123!
          </code>
        </div>
      </div>
    </div>
  )
}
