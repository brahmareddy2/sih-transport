import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import { useI18nStore } from '../services/i18n'
import VoiceAssistantModal from '../components/voice/VoiceAssistantModal'
import UniversalSearchBar from '../components/common/UniversalSearchBar'
import api from '../services/api'

export default function RoleHome() {
  const { user } = useAuthStore()
  const { language, t } = useI18nStore()
  const navigate = useNavigate()
  const [isVoiceOpen, setIsVoiceOpen] = useState(false)
  const [initialVoiceQuery, setInitialVoiceQuery] = useState('')
  const [pendingUsers, setPendingUsers] = useState([])
  const [loadingUsers, setLoadingUsers] = useState(false)

  const role = user?.role || 'fleet_operator'

  useEffect(() => {
    if (role === 'admin') {
      fetchPendingUsers()
    }
  }, [role])

  const fetchPendingUsers = async () => {
    setLoadingUsers(true)
    try {
      const { data } = await api.get('/admin/pending-users')
      setPendingUsers(data || [])
    } catch (e) {
      console.error('Error fetching pending users:', e)
    } finally {
      setLoadingUsers(false)
    }
  }

  const handleApprove = async (userId) => {
    try {
      await api.post(`/admin/approve-user/${userId}`)
      fetchPendingUsers()
    } catch (e) {
      alert('Failed to approve user account.')
    }
  }

  const handleSearchSubmit = (query) => {
    setInitialVoiceQuery(query)
    setIsVoiceOpen(true)
  }

  // Role-Specific Action Tiles Configuration
  const ROLE_TILES = {
    driver: [
      { icon: '🎤', title: 'ASK VOICE ASSISTANT', desc: 'Speak to plan trips, check fuel, or report issues', action: () => { setInitialVoiceQuery(''); setIsVoiceOpen(true); }, accent: '#6366f1', hero: true },
      { icon: '🚛', title: 'MY ACTIVE TRIP', desc: 'View current route, destination, and remaining hours', path: '/driver-mode', accent: '#10b981' },
      { icon: '📍', title: 'LIVE GPS LOCATION', desc: 'Monitor vehicle speed, coordinates & telematics', path: '/driver-mode', accent: '#06b6d4' },
      { icon: '⛽', title: 'DIESEL & BUNKERING', desc: 'Check fuel level and nearest highway fuel stations', path: '/driver-mode', accent: '#f59e0b' },
      { icon: '🚨', title: 'EMERGENCY HELP', desc: 'Instant breakdown, accident & puncture response', path: '/driver-mode', accent: '#ef4444' },
      { icon: '🔄', title: 'RETURN LOADS', desc: 'Find return cargo to eliminate empty return miles', path: '/return-cargo', accent: '#8b5cf6' },
    ],
    fleet_operator: [
      { icon: '🎤', title: 'ASK CARGO PILOT', desc: 'Voice query for fleet status, delayed shipments, fuel expenses', action: () => { setInitialVoiceQuery(''); setIsVoiceOpen(true); }, accent: '#6366f1', hero: true },
      { icon: '🛣️', title: 'ROUTE OPTIMIZATION', desc: 'Google OR-Tools solver with capacity & time window constraints', path: '/fleet-operator', accent: '#3b82f6' },
      { icon: '🚛', title: 'FLEET TELEMATICS & GPS', desc: 'Real-time vehicle health, speed, and fuel consumption', path: '/fleet-operator', accent: '#10b981' },
      { icon: '🔄', title: 'RETURN CARGO / BACKHAUL', desc: 'Backhaul matches to reduce empty-km and save fuel', path: '/return-cargo', accent: '#8b5cf6' },
      { icon: '🚨', title: 'INCIDENTS & RECOVERY', desc: 'Simulate disruptions and review multi-criteria recovery plans', path: '/incidents', accent: '#ef4444' },
      { icon: '💰', title: 'COST & FUEL ANALYTICS', desc: 'Operational expense breakdown and fuel cost optimization', path: '/analytics', accent: '#f59e0b' },
      { icon: '⚡', title: 'WHAT-IF SIMULATOR', desc: '9 contingency disruption scenarios with before/after matrix', path: '/what-if', accent: '#06b6d4' },
      { icon: '🤖', title: 'AI MODEL REGISTRY', desc: 'Demand forecasting, delay risk classifier, and ANN diagnostics', path: '/ml', accent: '#ec4899' },
    ],
    customer: [
      { icon: '🎤', title: 'TRACK BY VOICE', desc: 'Ask: "Where is my shipment?" or "When will it arrive?"', action: () => { setInitialVoiceQuery(''); setIsVoiceOpen(true); }, accent: '#6366f1', hero: true },
      { icon: '📦', title: 'MY SHIPMENTS', desc: 'View active orders, weight, origin, and destination', path: '/analytics', accent: '#10b981' },
      { icon: '📍', title: 'LIVE GPS TRACKING', desc: 'Visual interactive tracking of your freight consignment', path: '/tracking', accent: '#06b6d4' },
      { icon: '⏱️', title: 'DELIVERY ETA & SLA', desc: 'On-time delivery performance and arrival estimates', path: '/analytics', accent: '#f59e0b' },
      { icon: '☎️', title: 'OPERATOR SUPPORT', desc: 'Direct priority assistance for urgent consignment routing', path: '/incidents', accent: '#ec4899' },
    ],
    admin: [
      { icon: '🎤', title: 'EXECUTIVE VOICE ASSISTANT', desc: 'System-wide voice query for fleet metrics, costs, and audit logs', action: () => { setInitialVoiceQuery(''); setIsVoiceOpen(true); }, accent: '#6366f1', hero: true },
      { icon: '📊', title: 'EXECUTIVE OVERVIEW', desc: 'Fleet KPIs, cost savings, active incidents, and SLA metrics', path: '/analytics', accent: '#10b981' },
      { icon: '🚛', title: 'FLEET & GPS TRACKING', desc: 'Active real-time map, fuel gauges, and simulation controls', path: '/tracking', accent: '#06b6d4' },
      { icon: '🧠', title: 'OR-TOOLS OPTIMIZATION', desc: 'Capacity, time windows, and multi-vehicle route optimization', path: '/operator', accent: '#3b82f6' },
      { icon: '🚨', title: 'INCIDENT & DISRUPTION DSS', desc: 'Ranked recovery plans and automated rerouting protocols', path: '/incidents', accent: '#ef4444' },
      { icon: '🤖', title: 'MACHINE LEARNING & ANOMALIES', desc: 'Demand forecasting, delay classifier, and model health', path: '/ml', accent: '#ec4899' },
    ],
  }

  const tiles = ROLE_TILES[role] || ROLE_TILES.fleet_operator

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '24px', fontFamily: "'Inter', sans-serif" }}>
      {/* 1. Large Universal Search Bar with embedded mic */}
      <UniversalSearchBar
        onSearch={handleSearchSubmit}
        onOpenVoice={() => {
          setInitialVoiceQuery('')
          setIsVoiceOpen(true)
        }}
      />

      {/* 2. Welcome Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #18182e, #222240)',
          borderRadius: 24,
          padding: '30px',
          border: '1px solid #3b3b5c',
          boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
          marginBottom: '28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px',
        }}
      >
        <div>
          <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: 1 }}>
            {role.toUpperCase()} COCKPIT
          </div>
          <h1 style={{ margin: '6px 0 0', fontSize: '2rem', fontWeight: 900, color: '#fff' }}>
            Welcome back, {user?.full_name || 'User'}
          </h1>
          <p style={{ margin: '6px 0 0', color: '#9ca3af', fontSize: '1rem' }}>
            Choose a quick action below, search above, or press Speak to use the universal assistant.
          </p>
        </div>

        <button
          onClick={() => {
            setInitialVoiceQuery('')
            setIsVoiceOpen(true)
          }}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '12px',
            background: 'linear-gradient(135deg, #6366f1, #a855f7)',
            color: '#fff',
            border: 'none',
            borderRadius: 18,
            padding: '16px 28px',
            fontSize: '1.2rem',
            fontWeight: 900,
            cursor: 'pointer',
            boxShadow: '0 0 30px rgba(99, 102, 241, 0.5)',
            transition: 'all 0.2s',
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>🎤</span>
          <span>{t('speak', 'SPEAK')}</span>
        </button>
      </div>

      {/* 3. Pending User Approvals Panel (Admin Only) */}
      {role === 'admin' && pendingUsers.length > 0 && (
        <div
          style={{
            background: '#1a102f',
            border: '1px solid #7c3aed66',
            borderRadius: 20,
            padding: '20px',
            marginBottom: '28px',
            boxShadow: '0 8px 24px rgba(124, 58, 237, 0.15)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f3e8ff', margin: 0 }}>
              🛡️ Pending Security Role Approvals ({pendingUsers.length})
            </h2>
            <button
              onClick={fetchPendingUsers}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#c084fc',
                fontWeight: 700,
                cursor: 'pointer',
                fontSize: '0.85rem',
              }}
            >
              🔄 Refresh
            </button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {pendingUsers.map((pUser) => (
              <div
                key={pUser.id}
                style={{
                  background: '#110b21',
                  border: '1px solid #332554',
                  borderRadius: 12,
                  padding: '14px 18px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '12px',
                }}
              >
                <div>
                  <div style={{ fontWeight: 800, color: '#fff', fontSize: '0.95rem' }}>
                    {pUser.full_name}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '2px' }}>
                    Email: <span style={{ color: '#e9d5ff' }}>{pUser.email}</span> | Org: <span style={{ color: '#e9d5ff' }}>{pUser.organization_name || 'N/A'}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', marginTop: '4px' }}>
                    Requested Role:{' '}
                    <span style={{ color: '#f472b6', fontWeight: 800, textTransform: 'uppercase' }}>
                      {pUser.role.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => handleApprove(pUser.id)}
                  style={{
                    background: 'linear-gradient(135deg, #10b981, #059669)',
                    border: 'none',
                    color: '#fff',
                    borderRadius: 8,
                    padding: '8px 16px',
                    fontWeight: 800,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.03)')}
                  onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
                >
                  Approve Account ✓
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4. Action Tiles Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '18px' }}>
        {tiles.map((tile, idx) => (
          <div
            key={idx}
            onClick={() => {
              if (tile.action) tile.action()
              else if (tile.path) navigate(tile.path)
            }}
            style={{
              padding: '24px',
              borderRadius: 20,
              background: 'var(--color-bg-card)',
              border: `1px solid ${tile.accent}33`,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transition: 'all 0.2s ease-in-out',
              boxShadow: 'var(--shadow-card)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.borderColor = tile.accent
              e.currentTarget.style.boxShadow = `0 12px 30px ${tile.accent}22`
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.borderColor = `${tile.accent}33`
              e.currentTarget.style.boxShadow = 'var(--shadow-card)'
            }}
          >
            <div>
              <div style={{ fontSize: '2.5rem', marginBottom: '14px' }}>{tile.icon}</div>
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>
                {tile.title}
              </h3>
              <p style={{ margin: '8px 0 0', color: 'var(--color-text-secondary)', fontSize: '0.9rem', lineHeight: 1.4 }}>
                {tile.desc}
              </p>
            </div>
            <div style={{ marginTop: '20px', display: 'flex', alignItems: 'center', gap: '6px', color: tile.accent, fontWeight: 800, fontSize: '0.85rem' }}>
              <span>OPEN NOW</span>
              <span>➔</span>
            </div>
          </div>
        ))}
      </div>

      {/* Voice Assistant Modal */}
      <VoiceAssistantModal
        isOpen={isVoiceOpen}
        onClose={() => {
          setIsVoiceOpen(false)
          setInitialVoiceQuery('')
        }}
        initialQuery={initialVoiceQuery}
      />
    </div>
  )
}
