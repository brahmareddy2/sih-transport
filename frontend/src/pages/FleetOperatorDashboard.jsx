import React, { useState } from 'react'
import Optimization from './Optimization'
import LiveTracking from './LiveTracking'

export default function FleetOperatorDashboard() {
  const [activeTab, setActiveTab] = useState('optimization')

  return (
    <div style={{ padding: '0px', width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Dynamic Tab Switcher */}
      <div 
        style={{
          display: 'flex',
          gap: '12px',
          padding: '12px 24px',
          background: 'var(--color-bg-secondary)',
          borderBottom: '1px solid var(--color-border)',
          alignItems: 'center',
          boxShadow: 'var(--shadow-glow)',
          zIndex: 10,
        }}
      >
        <button
          onClick={() => setActiveTab('optimization')}
          style={{
            padding: '8px 16px',
            borderRadius: '20px',
            border: activeTab === 'optimization' ? 'none' : '1px solid var(--color-border)',
            background: activeTab === 'optimization' ? 'var(--color-blue-gradient, linear-gradient(135deg, #3b82f6, #1d4ed8))' : 'var(--color-bg-primary)',
            color: activeTab === 'optimization' ? '#fff' : 'var(--color-text-primary)',
            fontWeight: 800,
            cursor: 'pointer',
            fontSize: '0.85rem',
            boxShadow: activeTab === 'optimization' ? '0 4px 15px rgba(59, 130, 246, 0.4)' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          🛰️ Dispatch & Route Optimization
        </button>
        <button
          onClick={() => setActiveTab('tracking')}
          style={{
            padding: '8px 16px',
            borderRadius: '20px',
            border: activeTab === 'tracking' ? 'none' : '1px solid var(--color-border)',
            background: activeTab === 'tracking' ? 'var(--color-blue-gradient, linear-gradient(135deg, #3b82f6, #1d4ed8))' : 'var(--color-bg-primary)',
            color: activeTab === 'tracking' ? '#fff' : 'var(--color-text-primary)',
            fontWeight: 800,
            cursor: 'pointer',
            fontSize: '0.85rem',
            boxShadow: activeTab === 'tracking' ? '0 4px 15px rgba(59, 130, 246, 0.4)' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          📍 Fleet Telematics & GPS Tracking
        </button>
      </div>

      {/* Tab Content Area */}
      <div style={{ flex: 1, position: 'relative' }}>
        {activeTab === 'optimization' ? <Optimization /> : <LiveTracking />}
      </div>
    </div>
  )
}
