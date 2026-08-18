import React, { useState, useEffect } from 'react'
import { useI18nStore } from '../../services/i18n'
import DriverFacilities from './DriverFacilities'
import CommunicationModal from './CommunicationModal'
import api from '../../services/api'

export default function DriverAssistant({ onOpenVoice, onPlanTrip }) {
  const { language, t } = useI18nStore()
  const [selectedFacility, setSelectedFacility] = useState('restaurants')
  const [showFacilities, setShowFacilities] = useState(false)
  const [isCommOpen, setIsCommOpen] = useState(false)
  const [contactData, setContactData] = useState(null)

  const [tripData, setTripData] = useState({
    origin: 'Delhi',
    destination: 'Hyderabad',
    distance_km: 1580,
    duration_hours: 26.5,
    eta: 'Tomorrow 06:30 AM',
    fuel_available_l: 180,
    fuel_required_l: 395,
    refuel_city: 'Nagpur',
    toll_cost_inr: 2850,
    fuel_cost_inr: 36735,
    total_cost_inr: 43500,
    status: 'IN TRANSIT',
  })
  const [loadingTrip, setLoadingTrip] = useState(false)

  const fetchActiveTrip = async () => {
    setLoadingTrip(true)
    try {
      const { data } = await api.get('/drivers/active-trip')
      setTripData(data)
    } catch (e) {
      console.error('Failed to load active trip telemetry:', e)
    } finally {
      setLoadingTrip(false)
    }
  }

  useEffect(() => {
    fetchActiveTrip()
  }, [])

  // Offline syncing engine states
  const [syncStatus, setSyncStatus] = useState(navigator.onLine ? 'ONLINE' : 'OFFLINE')
  const [offlineUpdates, setOfflineUpdates] = useState(() => {
    return JSON.parse(localStorage.getItem('pending_driver_updates') || '[]')
  })
  const [newUpdateText, setNewUpdateText] = useState('')
  const [fuelLogged, setFuelLogged] = useState('')

  useEffect(() => {
    const handleOnline = () => {
      triggerSync()
    }
    const handleOffline = () => {
      setSyncStatus('OFFLINE')
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const triggerSync = () => {
    setSyncStatus('SYNCING')
    setTimeout(() => {
      const pending = JSON.parse(localStorage.getItem('pending_driver_updates') || '[]')
      if (pending.length > 0) {
        console.log('Automatically synced driver updates with central database:', pending)
        localStorage.removeItem('pending_driver_updates')
        setOfflineUpdates([])
      }
      setSyncStatus('ONLINE')
    }, 2000)
  }

  const handleToggleConnection = () => {
    if (syncStatus === 'ONLINE' || syncStatus === 'SYNCING') {
      setSyncStatus('OFFLINE')
    } else {
      triggerSync()
    }
  }

  const addOfflineUpdate = (e) => {
    e.preventDefault()
    if (!newUpdateText && !fuelLogged) return

    const newRecord = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      status: newUpdateText || 'Logged Fuel Refill',
      fuel: fuelLogged ? parseFloat(fuelLogged) : null,
    }

    const updated = [...offlineUpdates, newRecord]
    setOfflineUpdates(updated)
    localStorage.setItem('pending_driver_updates', JSON.stringify(updated))

    setNewUpdateText('')
    setFuelLogged('')

    // If simulated status is online, auto-sync immediately
    if (syncStatus === 'ONLINE') {
      triggerSync()
    }
  }

  const handleFacilityClick = (cat) => {
    setSelectedFacility(cat)
    setShowFacilities(true)
  }

  const handleCallDispatch = () => {
    setContactData({
      target_name: 'Central Fleet Control Room',
      location: 'Cargo Pilot Operations Hub',
      phone: '+91 80456 71001',
      disclaimer: 'Demo call mode — connects driver directly to central fleet manager.',
    })
    setIsCommOpen(true)
  }

  const getStatusColor = () => {
    if (syncStatus === 'ONLINE') return '#10b981'
    if (syncStatus === 'SYNCING') return '#3b82f6'
    return '#ef4444'
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
          position: 'relative',
        }}
      >
        {/* Sync Status Badge */}
        <div
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: '#111122',
            border: `1px solid ${getStatusColor()}`,
            borderRadius: 12,
            padding: '6px 12px',
          }}
        >
          <span style={{ height: '8px', width: '8px', borderRadius: '50%', background: getStatusColor(), display: 'inline-block' }} />
          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#fff' }}>{syncStatus}</span>
        </div>

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
            {t('my_trip', 'My Active Trip')}
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
            🟢 {tripData.status}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
          <div style={{ background: '#1c1c34', padding: '14px', borderRadius: 14, border: '1px solid #2d2d48' }}>
            <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>ROUTE</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff', marginTop: '2px' }}>
              {tripData.origin} ➔ {tripData.destination}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#38bdf8', marginTop: '2px' }}>
              Via NH44 ({tripData.distance_km.toLocaleString()} km)
            </div>
          </div>

          <div style={{ background: '#1c1c34', padding: '14px', borderRadius: 14, border: '1px solid #2d2d48' }}>
            <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>ESTIMATED TIME & ARRIVAL</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#34d399', marginTop: '2px' }}>
              {tripData.duration_hours} Hours
            </div>
            <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginTop: '2px' }}>
              ETA: {tripData.eta}
            </div>
          </div>

          <div style={{ background: '#1c1c34', padding: '14px', borderRadius: 14, border: '1px solid #2d2d48' }}>
            <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>DIESEL & FUEL LEVEL</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fbbf24', marginTop: '2px' }}>
              {tripData.fuel_available_l} L Available
            </div>
            <div style={{ fontSize: '0.72rem', color: '#f87171', marginTop: '2px' }}>
              Requires ~{tripData.fuel_required_l} L total (Refuel in {tripData.refuel_city})
            </div>
          </div>

          <div style={{ background: '#1c1c34', padding: '14px', borderRadius: 14, border: '1px solid #2d2d48' }}>
            <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>ESTIMATED TRIP EXPENSE</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#a78bfa', marginTop: '2px' }}>
              ₹{tripData.total_cost_inr.toLocaleString()} Total
            </div>
            <div style={{ fontSize: '0.72rem', color: '#9ca3af', marginTop: '2px' }}>
              Tolls: ₹{tripData.toll_cost_inr.toLocaleString()} • Fuel: ₹{tripData.fuel_cost_inr.toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Offline Log & Sync Panel */}
      <div
        style={{
          background: '#16162a',
          borderRadius: 24,
          padding: '24px',
          border: '1px solid #2d2d48',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff', margin: 0 }}>
            📡 Offline Support & Trip Updates Logger
          </h3>
          <button
            onClick={handleToggleConnection}
            style={{
              padding: '6px 12px',
              borderRadius: 8,
              background: syncStatus === 'OFFLINE' ? '#10b981' : '#ef4444',
              color: '#fff',
              border: 'none',
              fontWeight: 800,
              fontSize: '0.75rem',
              cursor: 'pointer',
            }}
          >
            {syncStatus === 'OFFLINE' ? 'Simulate Go Online 📡' : 'Simulate Go Offline 🔌'}
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
          {/* Submit updates form */}
          <form onSubmit={addOfflineUpdate} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', display: 'block', marginBottom: '4px' }}>
                Quick Update / Status text
              </label>
              <input
                type="text"
                placeholder="e.g. Stopped at Nagpur Dhaba, Stuck in NH44 traffic"
                value={newUpdateText}
                onChange={(e) => setNewUpdateText(e.target.value)}
                style={{ width: '100%', boxSizing: 'border-box', background: '#111122', border: '1px solid #3b3b5c', borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#cbd5e1', display: 'block', marginBottom: '4px' }}>
                Refilled Fuel Log (Litres)
              </label>
              <input
                type="number"
                placeholder="e.g. 100"
                value={fuelLogged}
                onChange={(e) => setFuelLogged(e.target.value)}
                style={{ width: '100%', boxSizing: 'border-box', background: '#111122', border: '1px solid #3b3b5c', borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: '0.85rem' }}
              />
            </div>
            <button
              type="submit"
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: 8,
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: '#fff',
                border: 'none',
                fontWeight: 800,
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
            >
              Log Local Record (Works Offline)
            </button>
          </form>

          {/* Pending updates list */}
          <div style={{ background: '#111122', padding: '14px', borderRadius: 14, border: '1px solid #2d2d48' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#a5b4fc', marginBottom: '8px' }}>
              Pending Local Cache ({offlineUpdates.length})
            </div>
            {offlineUpdates.length === 0 ? (
              <div style={{ fontSize: '0.8rem', color: '#6b7280', textAlign: 'center', padding: '20px 0' }}>
                No pending offline records. All logs synced.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '150px', overflowY: 'auto' }}>
                {offlineUpdates.map((item) => (
                  <div key={item.id} style={{ background: '#1c1c34', padding: '8px 12px', borderRadius: 8, fontSize: '0.75rem', borderLeft: '3px solid #f59e0b' }}>
                    <div style={{ color: '#fff', fontWeight: 700 }}>{item.status}</div>
                    {item.fuel && <div style={{ color: '#fbbf24' }}>⛽ Refuelled: {item.fuel} Litres</div>}
                    <div style={{ fontSize: '0.65rem', color: '#6b7280', marginTop: '2px' }}>Logged at {item.timestamp}</div>
                  </div>
                ))}
              </div>
            )}
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
