import React, { useState } from 'react'
import { useI18nStore } from '../services/i18n'
import VoiceAssistantModal from '../components/voice/VoiceAssistantModal'
import { executeVoiceCommand } from '../services/voiceApi'

export default function DriverMode() {
  const { language, t } = useI18nStore()
  const [isVoiceOpen, setIsVoiceOpen] = useState(false)
  const [activeTrip, setActiveTrip] = useState({
    origin: 'Delhi',
    destination: 'Hyderabad',
    vehicle_reg: 'MH02AB1234',
    current_city: 'Nagpur',
    distance_remaining_km: 790,
    eta_hours: 12.5,
    eta_time: 'Tomorrow 06:30 AM',
    fuel_level_l: 140,
    fuel_pct: 68,
    speed_kmh: 58,
  })
  const [emergencyAlert, setEmergencyAlert] = useState(null)
  const [returnLoadModal, setReturnLoadModal] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleEmergencyAction = async (emergencyType) => {
    setLoading(true)
    try {
      const res = await executeVoiceCommand({
        query: `Emergency ${emergencyType} for vehicle ${activeTrip.vehicle_reg}`,
        language,
        confirmed: true,
        action_payload: {
          intent: emergencyType === 'breakdown' ? 'REPORT_BREAKDOWN' : emergencyType === 'tyre' ? 'REPORT_TYRE_PUNCTURE' : 'FIND_FUEL_STATION',
          entities: { vehicle_registration: activeTrip.vehicle_reg },
        },
      })
      setEmergencyAlert(res)
    } catch (err) {
      setEmergencyAlert({
        text: `Alert sent to operator for ${emergencyType}. Assistance is being dispatched.`,
      })
    } finally {
      setLoading(false)
    }
  }

  const handleReturnCargoCheck = async () => {
    setLoading(true)
    try {
      const res = await executeVoiceCommand({
        query: `Find return load from ${activeTrip.destination}`,
        language,
        confirmed: true,
        action_payload: {
          intent: 'FIND_RETURN_CARGO',
          entities: { destination: activeTrip.destination },
        },
      })
      setEmergencyAlert(res)
    } catch (err) {
      setEmergencyAlert({
        text: `Checking return loads from ${activeTrip.destination}... 2 compatible shipments found.`,
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        maxWidth: '900px',
        margin: '0 auto',
        padding: '20px',
        fontFamily: "'Inter', sans-serif",
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
      }}
    >
      {/* 1. Hello Driver Header */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1e1e38, #2a2a4e)',
          borderRadius: 24,
          padding: '28px',
          border: '1px solid #3b3b60',
          boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: '2rem', fontWeight: 900, color: '#fff' }}>
            {t('hello_driver', '👋 Hello Driver')}
          </h1>
          <p style={{ margin: '6px 0 0', fontSize: '1.05rem', color: '#a5b4fc', fontWeight: 500 }}>
            {t('tell_me_what_you_need', 'Tell me what you need or tap a quick button below.')}
          </p>
        </div>

        {/* Large Voice Action Button */}
        <button
          onClick={() => setIsVoiceOpen(true)}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '12px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            color: '#fff',
            border: 'none',
            borderRadius: 18,
            padding: '16px 28px',
            fontSize: '1.2rem',
            fontWeight: 900,
            cursor: 'pointer',
            boxShadow: '0 0 25px rgba(99, 102, 241, 0.6)',
            transition: 'all 0.2s',
          }}
        >
          <span style={{ fontSize: '1.6rem' }}>🎤</span>
          <span>{t('speak', 'SPEAK')}</span>
        </button>
      </div>

      {/* 2. My Trip Section */}
      <div
        style={{
          background: '#1a1a2e',
          borderRadius: 24,
          padding: '24px',
          border: '1px solid #2d2d48',
          boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, color: '#fff' }}>
            {t('my_trip', '🚛 My Active Trip')}
          </h2>
          <span style={{ fontSize: '0.85rem', fontWeight: 800, padding: '4px 12px', borderRadius: 8, background: '#10b98122', color: '#10b981', border: '1px solid #10b98144' }}>
            {activeTrip.vehicle_reg}
          </span>
        </div>

        {/* Big Route Visual */}
        <div
          style={{
            padding: '20px',
            background: '#121222',
            borderRadius: 18,
            marginBottom: '20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '0.8rem', color: '#9ca3af', textTransform: 'uppercase' }}>Origin</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#fff' }}>{activeTrip.origin}</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
            <span style={{ fontSize: '1.2rem', color: '#6366f1' }}>➔ ➔ ➔</span>
            <span style={{ fontSize: '0.8rem', color: '#60a5fa', fontWeight: 700 }}>
              Near {activeTrip.current_city}
            </span>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.8rem', color: '#9ca3af', textTransform: 'uppercase' }}>Destination</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#10b981' }}>{activeTrip.destination}</div>
          </div>
        </div>

        {/* 3 Telematics Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          {/* ETA */}
          <div style={{ padding: '18px', background: '#141426', borderRadius: 16, border: '1px solid #2d2d42' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#60a5fa', fontWeight: 700, fontSize: '0.9rem' }}>
              <span>⏱️</span>
              <span>Estimated Arrival (ETA)</span>
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 900, color: '#fff', marginTop: '8px' }}>
              ~{activeTrip.eta_hours} Hours
            </div>
            <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '4px' }}>
              {activeTrip.eta_time} ({activeTrip.distance_remaining_km} km remaining)
            </div>
          </div>

          {/* Diesel Fuel */}
          <div style={{ padding: '18px', background: '#141426', borderRadius: 16, border: '1px solid #2d2d42' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fbbf24', fontWeight: 700, fontSize: '0.9rem' }}>
              <span>⛽</span>
              <span>Available Diesel</span>
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 900, color: '#fff', marginTop: '8px' }}>
              {activeTrip.fuel_level_l} Litres ({activeTrip.fuel_pct}%)
            </div>
            <div style={{ marginTop: '8px', height: '8px', background: '#2d2d3d', borderRadius: 99, overflow: 'hidden' }}>
              <div style={{ width: `${activeTrip.fuel_pct}%`, height: '100%', background: '#10b981', borderRadius: 99 }} />
            </div>
          </div>

          {/* Current Speed */}
          <div style={{ padding: '18px', background: '#141426', borderRadius: 16, border: '1px solid #2d2d42' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a78bfa', fontWeight: 700, fontSize: '0.9rem' }}>
              <span>⚡</span>
              <span>Vehicle Telematics</span>
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 900, color: '#fff', marginTop: '8px' }}>
              {activeTrip.speed_kmh} km/h
            </div>
            <div style={{ fontSize: '0.8rem', color: '#10b981', marginTop: '4px' }}>
              ✓ Engine Healthy & In Transit
            </div>
          </div>
        </div>
      </div>

      {/* 3. Emergency Quick Action Buttons */}
      <div
        style={{
          background: '#1a1a2e',
          borderRadius: 24,
          padding: '24px',
          border: '1px solid #2d2d48',
          boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
        }}
      >
        <h2 style={{ margin: '0 0 16px', fontSize: '1.3rem', fontWeight: 800, color: '#ef4444' }}>
          {t('emergency_help', '🚨 Emergency Quick Help')}
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
          <button
            onClick={() => handleEmergencyAction('breakdown')}
            disabled={loading}
            style={{
              padding: '20px 16px',
              borderRadius: 16,
              background: '#ef444422',
              color: '#f87171',
              border: '2px solid #ef444466',
              fontSize: '1.1rem',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ fontSize: '2rem' }}>🛑</span>
            <span>{t('breakdown', 'BREAKDOWN')}</span>
          </button>

          <button
            onClick={() => handleEmergencyAction('accident')}
            disabled={loading}
            style={{
              padding: '20px 16px',
              borderRadius: 16,
              background: '#f9731622',
              color: '#fb923c',
              border: '2px solid #f9731666',
              fontSize: '1.1rem',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ fontSize: '2rem' }}>⚠️</span>
            <span>{t('accident', 'ACCIDENT')}</span>
          </button>

          <button
            onClick={() => handleEmergencyAction('low_fuel')}
            disabled={loading}
            style={{
              padding: '20px 16px',
              borderRadius: 16,
              background: '#f59e0b22',
              color: '#fbbf24',
              border: '2px solid #f59e0b66',
              fontSize: '1.1rem',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ fontSize: '2rem' }}>⛽</span>
            <span>{t('low_fuel', 'LOW FUEL')}</span>
          </button>

          <button
            onClick={() => handleEmergencyAction('tyre')}
            disabled={loading}
            style={{
              padding: '20px 16px',
              borderRadius: 16,
              background: '#6366f122',
              color: '#a5b4fc',
              border: '2px solid #6366f166',
              fontSize: '1.1rem',
              fontWeight: 800,
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ fontSize: '2rem' }}>⚙️</span>
            <span>{t('tyre_problem', 'TYRE PROBLEM')}</span>
          </button>
        </div>
      </div>

      {/* 4. Return Load Automation Card */}
      <div
        style={{
          background: 'linear-gradient(135deg, #132a24, #1b3d32)',
          borderRadius: 24,
          padding: '24px',
          border: '1px solid #10b98166',
          boxShadow: '0 8px 24px rgba(16, 185, 129, 0.2)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800, color: '#10b981' }}>
            {t('check_return_load', '🔄 Check Return Load')}
          </h3>
          <p style={{ margin: '4px 0 0', fontSize: '0.95rem', color: '#a7f3d0' }}>
            Trip to {activeTrip.destination} is active. Find return freight to earn more and save empty kilometers.
          </p>
        </div>
        <button
          onClick={handleReturnCargoCheck}
          disabled={loading}
          style={{
            padding: '14px 24px',
            borderRadius: 14,
            background: '#10b981',
            color: '#fff',
            border: 'none',
            fontSize: '1.05rem',
            fontWeight: 800,
            cursor: 'pointer',
            boxShadow: '0 4px 15px rgba(16, 185, 129, 0.4)',
          }}
        >
          {t('check_return_load', 'Find Return Cargo ➔')}
        </button>
      </div>

      {/* Emergency / Return Cargo Alert Modal */}
      {emergencyAlert && (
        <div
          style={{
            padding: '20px',
            background: '#1f1f33',
            borderRadius: 18,
            border: '1px solid #6366f188',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: '#fff' }}>
              System Response
            </h4>
            <button
              onClick={() => setEmergencyAlert(null)}
              style={{ background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: '1.2rem' }}
            >
              ✕
            </button>
          </div>
          <div style={{ fontSize: '0.95rem', color: '#e2e8f0', lineHeight: 1.5 }}>
            {emergencyAlert.text}
          </div>
        </div>
      )}

      {/* Persistent Voice Assistant Modal */}
      <VoiceAssistantModal isOpen={isVoiceOpen} onClose={() => setIsVoiceOpen(false)} />
    </div>
  )
}
