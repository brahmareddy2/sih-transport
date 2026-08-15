import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useI18nStore } from '../services/i18n'
import VoiceAssistantModal from '../components/voice/VoiceAssistantModal'

export default function RoleHome() {
  const { user } = useAuthStore()
  const { language, t } = useI18nStore()
  const navigate = useNavigate()
  const [isVoiceOpen, setIsVoiceOpen] = useState(false)

  const role = user?.role || 'operator'

  // Role-Specific Action Tiles Configuration
  const ROLE_TILES = {
    driver: [
      { icon: '🎤', title: 'ASK VOICE ASSISTANT', desc: 'Speak to plan trips, check fuel, or report issues', action: () => setIsVoiceOpen(true), accent: '#6366f1', hero: true },
      { icon: '🚛', title: 'MY ACTIVE TRIP', desc: 'View current route, destination, and remaining hours', path: '/driver-mode', accent: '#10b981' },
      { icon: '📍', title: 'LIVE GPS LOCATION', desc: 'Monitor vehicle speed, coordinates & telematics', path: '/tracking', accent: '#06b6d4' },
      { icon: '⛽', title: 'DIESEL & BUNKERING', desc: 'Check fuel level and nearest highway fuel stations', path: '/driver-mode', accent: '#f59e0b' },
      { icon: '🚨', title: 'EMERGENCY HELP', desc: 'Instant breakdown, accident & puncture response', path: '/driver-mode', accent: '#ef4444' },
      { icon: '🔄', title: 'RETURN LOADS', desc: 'Find return cargo to eliminate empty return miles', path: '/return-cargo', accent: '#8b5cf6' },
    ],
    operator: [
      { icon: '🎤', title: 'ASK LOGISTICS DSS', desc: 'Voice query for fleet status, delayed shipments, bottlenecks', action: () => setIsVoiceOpen(true), accent: '#6366f1', hero: true },
      { icon: '🚛', title: 'FLEET DIRECTORY', desc: 'Manage 50 active vehicles and drivers across India', path: '/tracking', accent: '#10b981' },
      { icon: '📦', title: 'SHIPMENTS & CONSOLIDATION', desc: 'Multi-order load consolidation and capacity planning', path: '/operator', accent: '#06b6d4' },
      { icon: '🛣️', title: 'ROUTE OPTIMIZATION', desc: 'Google OR-Tools CVRPTW solver with 5 preset scenarios', path: '/operator', accent: '#3b82f6' },
      { icon: '🚨', title: 'INCIDENTS & RECOVERY', desc: 'Simulate disruptions and review multi-criteria recovery plans', path: '/incidents', accent: '#ef4444' },
      { icon: '🔄', title: 'RETURN CARGO MATCHING', desc: 'Backhaul matches to reduce empty kilometers', path: '/return-cargo', accent: '#8b5cf6' },
    ],
    fleet_manager: [
      { icon: '🎤', title: 'ASK FLEET ASSISTANT', desc: 'Query available vehicles, fuel expenses, and driver safety', action: () => setIsVoiceOpen(true), accent: '#6366f1', hero: true },
      { icon: '🚛', title: 'ACTIVE FLEET TELEMATICS', desc: 'Real-time vehicle health, speed, and fuel consumption', path: '/tracking', accent: '#10b981' },
      { icon: '💰', title: 'COST & FUEL ANALYTICS', desc: 'Operational expense breakdown and fuel cost optimization', path: '/analytics', accent: '#f59e0b' },
      { icon: '🔄', title: 'RETURN CARGO / BACKHAUL', desc: '36.2% empty-km reduction with high-score freight matching', path: '/return-cargo', accent: '#8b5cf6' },
      { icon: '⚡', title: 'WHAT-IF SIMULATOR', desc: '9 contingency disruption scenarios with before/after matrix', path: '/what-if', accent: '#06b6d4' },
      { icon: '🤖', title: 'AI MODEL REGISTRY', desc: 'Demand forecasting, delay risk classifier, and ANN diagnostics', path: '/ml', accent: '#ec4899' },
    ],
    customer: [
      { icon: '🎤', title: 'TRACK BY VOICE', desc: 'Ask: "Where is my shipment?" or "When will it arrive?"', action: () => setIsVoiceOpen(true), accent: '#6366f1', hero: true },
      { icon: '📦', title: 'MY SHIPMENTS', desc: 'View active orders, weight, origin, and destination', path: '/analytics', accent: '#10b981' },
      { icon: '📍', title: 'LIVE GPS TRACKING', desc: 'Visual interactive tracking of your freight consignment', path: '/tracking', accent: '#06b6d4' },
      { icon: '⏱️', title: 'DELIVERY ETA & SLA', desc: 'On-time delivery performance and arrival estimates', path: '/analytics', accent: '#f59e0b' },
      { icon: '☎️', title: 'OPERATOR SUPPORT', desc: 'Direct priority assistance for urgent consignment routing', path: '/incidents', accent: '#ec4899' },
    ],
    admin: [
      { icon: '🎤', title: 'EXECUTIVE VOICE ASSISTANT', desc: 'System-wide voice query for fleet metrics, costs, and audit logs', action: () => setIsVoiceOpen(true), accent: '#6366f1', hero: true },
      { icon: '📊', title: 'EXECUTIVE OVERVIEW', desc: 'Fleet KPIs, cost savings, active incidents, and SLA metrics', path: '/admin', accent: '#10b981' },
      { icon: '🚛', title: 'FLEET & GPS TRACKING', desc: '50-vehicle real-time map, fuel gauges, and simulation controls', path: '/tracking', accent: '#06b6d4' },
      { icon: '🧠', title: 'OR-TOOLS OPTIMIZATION', desc: 'Capacity, time windows, and multi-vehicle route optimization', path: '/operator', accent: '#3b82f6' },
      { icon: '🚨', title: 'INCIDENT & DISRUPTION DSS', desc: 'Ranked recovery plans and automated rerouting protocols', path: '/incidents', accent: '#ef4444' },
      { icon: '🤖', title: 'MACHINE LEARNING & ANOMALIES', desc: 'Demand forecasting, delay classifier, and model health', path: '/ml', accent: '#ec4899' },
    ],
  }

  const tiles = ROLE_TILES[role] || ROLE_TILES.operator

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '24px', fontFamily: "'Inter', sans-serif" }}>
      {/* Welcome Banner */}
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
            {role.toUpperCase()} PORTAL
          </div>
          <h1 style={{ margin: '6px 0 0', fontSize: '2rem', fontWeight: 900, color: '#fff' }}>
            Welcome back, {user?.full_name || 'User'}
          </h1>
          <p style={{ margin: '6px 0 0', color: '#9ca3af', fontSize: '1rem' }}>
            Choose a quick action below or press Speak to use the universal voice assistant.
          </p>
        </div>

        <button
          onClick={() => setIsVoiceOpen(true)}
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
            boxShadow: '0 0 25px rgba(99, 102, 241, 0.5)',
            transition: 'all 0.2s',
          }}
        >
          <span style={{ fontSize: '1.6rem' }}>🎤</span>
          <span>{t('speak', 'SPEAK')}</span>
        </button>
      </div>

      {/* Role Action Tiles Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {tiles.map((tile, i) => (
          <div
            key={i}
            onClick={() => (tile.action ? tile.action() : tile.path ? navigate(tile.path) : null)}
            style={{
              padding: '24px',
              borderRadius: 20,
              background: tile.hero ? 'linear-gradient(135deg, #252545, #303058)' : '#19192b',
              border: `1px solid ${tile.hero ? '#6366f1aa' : '#2d2d42'}`,
              boxShadow: tile.hero ? '0 10px 30px rgba(99, 102, 241, 0.25)' : '0 6px 20px rgba(0,0,0,0.25)',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              transition: 'all 0.2s ease-in-out',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.borderColor = tile.accent
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.borderColor = tile.hero ? '#6366f1aa' : '#2d2d42'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '2.2rem' }}>{tile.icon}</span>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  padding: '3px 10px',
                  borderRadius: 6,
                  background: `${tile.accent}22`,
                  color: tile.accent,
                  border: `1px solid ${tile.accent}44`,
                }}
              >
                OPEN ➔
              </span>
            </div>

            <div>
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>
                {tile.title}
              </h3>
              <p style={{ margin: '6px 0 0', fontSize: '0.88rem', color: '#9ca3af', lineHeight: 1.4 }}>
                {tile.desc}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Voice Assistant Modal */}
      <VoiceAssistantModal isOpen={isVoiceOpen} onClose={() => setIsVoiceOpen(false)} />
    </div>
  )
}
