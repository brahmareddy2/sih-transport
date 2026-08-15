import React, { useState } from 'react'
import { useI18nStore } from '../../services/i18n'
import DriverFacilities from './DriverFacilities'
import CommunicationModal from './CommunicationModal'

export default function DriverAssistant({ onOpenVoice, onPlanTrip }) {
  const { language, t } = useI18nStore()
  const [selectedFacility, setSelectedFacility] = useState('restaurants')
  const [showFacilities, setShowFacilities] = useState(false)
  const [isCommOpen, setIsCommOpen] = useState(false)
  const [contactData, setContactData] = useState(null)

  const handleFacilityClick = (cat) => {
    setSelectedFacility(cat)
    setShowFacilities(true)
  }

  const handleCallDispatch = () => {
    setContactData({
      target_name: 'Central Fleet Control Room',
      location: 'Logistics DSS Operations Hub',
      phone: '+91 80456 71001',
      disclaimer: 'Demo call mode — connects driver directly to central fleet manager.',
    })
    setIsCommOpen(true)
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', fontFamily: "'Inter', sans-serif" }}>
      {/* 1. Header Greeting & Voice Hero Button */}
      <div
        style={{
          background: 'linear-gradient(135deg, #181832 0%, #1e1b4b 100%)',
          borderRadius: 24,
          padding: '32px',
          border: '1px solid #3b3b5c',
          boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
          textAlign: 'center',
          marginBottom: '24px',
        }}
      >
        <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>🚚</div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 900, color: '#fff', margin: 0 }}>
          {t('hello_driver', '👋 Hello Driver')}
        </h1>
        <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: '6px 0 20px' }}>
          {t('tell_me_what_you_need', 'Tell me what you need or tap a quick button below.')}
        </p>

        {/* Hero Mic Button */}
        <button
          type="button"
          onClick={onOpenVoice}
          style={{
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            border: 'none',
            borderRadius: 50,
            padding: '16px 36px',
            color: '#fff',
            fontSize: '1.2rem',
            fontWeight: 800,
            cursor: 'pointer',
            boxShadow: '0 0 35px rgba(16, 185, 129, 0.5)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '12px',
            transition: 'transform 0.2s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'scale(1.05)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        >
          <span style={{ fontSize: '1.5rem' }}>🎤</span>
          <span>{t('speak', 'Speak / మాట్లాడండి / बोलें')}</span>
        </button>
      </div>

      {/* 2. My Active Trip Telemetry Card */}
      <div
        style={{
          background: '#16162a',
          borderRadius: 24,
          padding: '24px',
          border: '1px solid #2d2d48',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fff', margin: 0 }}>
            {t('my_trip', '🚛 My Active Trip')}
          </h2>
          <span
            style={{
              background: '#10b98122',
              color: '#34d399',
              padding: '6px 12px',
              borderRadius: 20,
              fontSize: '0.8rem',
              fontWeight: 700,
            }}
          >
            🟢 IN TRANSIT
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
          <div style={{ background: '#1c1c34', padding: '14px', borderRadius: 14, border: '1px solid #2d2d48' }}>
            <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>ROUTE</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff', marginTop: '2px' }}>Delhi ➔ Hyderabad</div>
            <div style={{ fontSize: '0.72rem', color: '#38bdf8', marginTop: '2px' }}>Via NH44 & NH48 (1,580 km)</div>
          </div>

          <div style={{ background: '#1c1c34', padding: '14px', borderRadius: 14, border: '1px solid #2d2d48' }}>
            <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>ESTIMATED TIME & ARRIVAL</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#34d399', marginTop: '2px' }}>26.5 Hours</div>
            <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginTop: '2px' }}>ETA: Tomorrow 06:30 AM</div>
          </div>

          <div style={{ background: '#1c1c34', padding: '14px', borderRadius: 14, border: '1px solid #2d2d48' }}>
            <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>DIESEL & FUEL LEVEL</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fbbf24', marginTop: '2px' }}>180 L Available</div>
            <div style={{ fontSize: '0.72rem', color: '#f87171', marginTop: '2px' }}>Requires ~395 L total (Refuel in Nagpur)</div>
          </div>

          <div style={{ background: '#1c1c34', padding: '14px', borderRadius: 14, border: '1px solid #2d2d48' }}>
            <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>ESTIMATED TRIP EXPENSE</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#a78bfa', marginTop: '2px' }}>₹43,500 Total</div>
            <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginTop: '2px' }}>Tolls: ₹2,850 • Fuel: ₹36,735</div>
          </div>
        </div>
      </div>

      {/* 3. Driver Quick Action Touch Buttons */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#a5b4fc', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          🛣️ Highway Services & Pit-Stops
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px' }}>
          <button
            type="button"
            onClick={() => handleFacilityClick('restaurants')}
            style={{
              padding: '16px 12px',
              borderRadius: 16,
              background: '#1c1c34',
              border: '1px solid #3b3b5c',
              color: '#fff',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span style={{ fontSize: '1.6rem' }}>🍛</span>
            <span>{t('trip.food', 'Food & Dhabas')}</span>
          </button>

          <button
            type="button"
            onClick={() => handleFacilityClick('parking')}
            style={{
              padding: '16px 12px',
              borderRadius: 16,
              background: '#1c1c34',
              border: '1px solid #3b3b5c',
              color: '#fff',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span style={{ fontSize: '1.6rem' }}>🅿️</span>
            <span>{t('trip.parking', 'Free Parking')}</span>
          </button>

          <button
            type="button"
            onClick={() => handleFacilityClick('restrooms')}
            style={{
              padding: '16px 12px',
              borderRadius: 16,
              background: '#1c1c34',
              border: '1px solid #3b3b5c',
              color: '#fff',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span style={{ fontSize: '1.6rem' }}>🚻</span>
            <span>{t('trip.restroom', 'Restrooms')}</span>
          </button>

          <button
            type="button"
            onClick={() => handleFacilityClick('fuel_stations')}
            style={{
              padding: '16px 12px',
              borderRadius: 16,
              background: '#1c1c34',
              border: '1px solid #3b3b5c',
              color: '#fff',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span style={{ fontSize: '1.6rem' }}>⛽</span>
            <span>{t('trip.fuel_stops', 'Diesel Bunkers')}</span>
          </button>

          <button
            type="button"
            onClick={() => handleFacilityClick('puncture_shops')}
            style={{
              padding: '16px 12px',
              borderRadius: 16,
              background: '#1c1c34',
              border: '1px solid #f8717144',
              color: '#fff',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span style={{ fontSize: '1.6rem' }}>⚙️</span>
            <span>{t('trip.puncture', 'Puncture Help')}</span>
          </button>

          <button
            type="button"
            onClick={handleCallDispatch}
            style={{
              padding: '16px 12px',
              borderRadius: 16,
              background: '#1c1c34',
              border: '1px solid #10b98144',
              color: '#fff',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span style={{ fontSize: '1.6rem' }}>📞</span>
            <span>{t('trip.contact', 'Call Dispatch')}</span>
          </button>
        </div>
      </div>

      {/* 4. Facilities Explorer */}
      {showFacilities && (
        <DriverFacilities defaultCategory={selectedFacility} />
      )}

      {/* Safe Contact Bridge Modal */}
      <CommunicationModal
        isOpen={isCommOpen}
        onClose={() => setIsCommOpen(false)}
        contactData={contactData}
      />
    </div>
  )
}
