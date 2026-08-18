import React, { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

import { useI18nStore } from '../services/i18n'
import { fetchTripPlan } from '../services/voiceApi'
import UniversalAssistant from '../components/common/UniversalAssistant'

// Fix Leaflet Default Marker Icons in React/Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Custom Pin Factory
const createCustomIcon = (emoji, bgColor = '#6366f1') => {
  return L.divIcon({
    className: 'custom-leaflet-icon',
    html: `
      <div style="
        background: ${bgColor};
        color: #fff;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        border: 2px solid #fff;
      ">
        ${emoji}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  })
}

export default function TripPlanner() {
  const { language, t } = useI18nStore()
  const location = useLocation()
  const navigate = useNavigate()

  const [origin, setOrigin] = useState('Delhi')
  const [destination, setDestination] = useState('Hyderabad')
  const [currentFuel, setCurrentFuel] = useState(150)
  const [foodBudget, setFoodBudget] = useState(400)
  const [selectedRouteId, setSelectedRouteId] = useState('best_route')
  const [loading, setLoading] = useState(false)
  const [tripData, setTripData] = useState(null)
  const [showReturnModal, setShowReturnModal] = useState(false)
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  // Load initial plan or fetch
  useEffect(() => {
    const passedPlan = location.state?.initialPlan
    if (passedPlan && passedPlan.coordinates) {
      setTripData(passedPlan)
      if (passedPlan.origin) setOrigin(passedPlan.origin)
      if (passedPlan.destination) setDestination(passedPlan.destination)
    } else {
      loadTripData('Delhi', 'Hyderabad', 150, 400)
    }
  }, [location.state])

  const loadTripData = async (orig, dest, fuel, food) => {
    setLoading(true)
    try {
      const res = await fetchTripPlan({
        origin: orig,
        destination: dest,
        current_fuel_l: fuel,
        food_budget_inr: food,
        language,
      })
      if (res && res.data) {
        setTripData(res.data)
      }
    } catch (err) {
      console.error('Failed to load trip plan:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRecalculate = (e) => {
    e?.preventDefault?.()
    loadTripData(origin, destination, Number(currentFuel), Number(foodBudget))
  }

  const handleRouteSelect = (route) => {
    setSelectedRouteId(route.id)
    if (tripData) {
      setTripData({
        ...tripData,
        distance_km: route.distance_km,
        duration_hours: route.duration_hours,
        fuel_cost_inr: route.fuel_cost_inr,
        toll_cost_inr: route.toll_cost_inr,
        total_cost_inr: route.total_cost_inr,
      })
    }
  }

  const defaultCoords = [
    [28.6139, 77.2090], [27.1767, 78.0081], [26.2183, 78.1828],
    [25.4484, 78.5685], [21.1458, 79.0882], [19.6641, 78.5320], [17.3850, 78.4867]
  ]

  const routeCoords = tripData?.coordinates?.length ? tripData.coordinates : defaultCoords
  const mapCenter = [23.5, 78.5]

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px', minHeight: '100vh', background: 'var(--color-bg-primary, #0c0c16)', color: '#fff', fontFamily: "'Inter', sans-serif" }}>
      {/* Top Header & Search Bar */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', background: 'linear-gradient(135deg, #1b1b32, #111122)', padding: '24px', borderRadius: 20, border: '1px solid #2d2d48', boxShadow: '0 8px 30px rgba(0,0,0,0.5)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.8rem' }}>🗺️</span>
              <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 900, background: 'linear-gradient(to right, #60a5fa, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                {origin.toUpperCase()} ➔ {destination.toUpperCase()} {t('trip_plan', 'Trip Planner')}
              </h1>
            </div>
            <p style={{ margin: '4px 0 0', color: '#9ca3af', fontSize: '0.9rem' }}>
              {tripData?.corridor_name || 'NH44 North-South National Highway Freight Corridor'}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setShowReturnModal(true)}
              style={{
                padding: '8px 16px',
                borderRadius: 10,
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: '#fff',
                border: 'none',
                fontWeight: 800,
                fontSize: '0.85rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span>🔄</span>
              <span>{t('check_return_load', 'Return Load Match')}</span>
            </button>
            <button
              onClick={() => window.print()}
              style={{
                padding: '8px 14px',
                borderRadius: 10,
                background: '#232338',
                color: '#e2e8f0',
                border: '1px solid #3b3b54',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              🖨️ Print Plan
            </button>
          </div>
        </div>

        {/* Global Universal Voice + Search Assistant */}
        <UniversalAssistant
          placeholder={language === 'te' ? 'ట్రిప్ ప్లాన్ లేదా మార్గాన్ని మార్చండి... ఉదా: ముంబై నుండి పూణే' : 'Ask anything or change trip... e.g. Mumbai to Pune, find dhabas...'}
          onResult={(res) => {
            if (res?.data) {
              setTripData(res.data)
              if (res.data.origin) setOrigin(res.data.origin)
              if (res.data.destination) setDestination(res.data.destination)
            }
          }}
        />
      </div>

      {/* Main Grid: Left Route Summary + Right Interactive Map */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'minmax(340px, 1.2fr) minmax(360px, 1.8fr)', gap: '24px' }}>
        {/* LEFT COLUMN: KPI Metrics, Fuel, Tolls, Food, Total Cost */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* 1. Distance & Driving Duration Card */}
          <div style={{ background: '#16162a', padding: '20px', borderRadius: 18, border: '1px solid #2d2d44', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            <div style={{ background: '#111122', padding: '14px', borderRadius: 12, textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', textTransform: 'uppercase', fontWeight: 700 }}>Total Distance</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#60a5fa', marginTop: '4px' }}>
                {tripData?.distance_km ?? 1580} km
              </div>
            </div>
            <div style={{ background: '#111122', padding: '14px', borderRadius: 12, textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', textTransform: 'uppercase', fontWeight: 700 }}>Driving Time</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#34d399', marginTop: '4px' }}>
                ~{tripData?.duration_hours ?? 26.5} hrs
              </div>
            </div>
            <div style={{ background: '#111122', padding: '14px', borderRadius: 12, textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', textTransform: 'uppercase', fontWeight: 700 }}>Trip Duration</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#a78bfa', marginTop: '4px' }}>
                ~{tripData?.duration_days ?? 2.0} days
              </div>
            </div>
          </div>

          {/* 2. Route Options (Best, Fastest, Lowest Cost) */}
          <div style={{ background: '#16162a', padding: '20px', borderRadius: 18, border: '1px solid #2d2d44' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '1.05rem', fontWeight: 800 }}>
              🛣️ Route Options Comparison
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {(tripData?.route_options || [
                { id: 'best_route', name: 'Best Route (NH44 Main Freight Corridor)', distance_km: 1580, duration_hours: 26.5, total_cost_inr: 43500 },
                { id: 'fastest_route', name: 'Fastest Route (Expressway Bypass)', distance_km: 1620, duration_hours: 24.0, total_cost_inr: 45000 },
                { id: 'lowest_cost_route', name: 'Lowest Cost Route (Economy NH)', distance_km: 1550, duration_hours: 29.0, total_cost_inr: 40800 },
              ]).map((rt) => {
                const isSelected = selectedRouteId === rt.id
                return (
                  <div
                    key={rt.id}
                    onClick={() => handleRouteSelect(rt)}
                    style={{
                      padding: '14px 16px',
                      borderRadius: 12,
                      background: isSelected ? '#6366f122' : '#111122',
                      border: isSelected ? '2px solid #6366f1' : '1px solid #2e2e46',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 800, color: isSelected ? '#a5b4fc' : '#fff', fontSize: '0.95rem' }}>
                        {rt.name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '2px' }}>
                        {rt.distance_km} km • ~{rt.duration_hours} hrs
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 800, color: '#10b981', fontSize: '1rem' }}>
                        ₹{rt.total_cost_inr?.toLocaleString?.()}
                      </div>
                      <span style={{ fontSize: '0.7rem', padding: '2px 6px', borderRadius: 4, background: isSelected ? '#6366f1' : '#27273a', color: '#fff' }}>
                        {isSelected ? '✓ Selected' : 'Select'}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* 3. Fuel Calculation Card */}
          <div style={{ background: '#16162a', padding: '20px', borderRadius: 18, border: '1px solid #2d2d44' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: '#fbbf24' }}>
                ⛽ Fuel Consumption & Cost Calculator
              </h3>
              <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>@ ₹95.0/L Diesel</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#e2e8f0', marginBottom: '6px' }}>
                  <span>Current Available Fuel:</span>
                  <strong style={{ color: '#fbbf24' }}>{currentFuel} Litres</strong>
                </label>
                <input
                  type="range"
                  min="0"
                  max="400"
                  step="10"
                  value={currentFuel}
                  onChange={(e) => {
                    setCurrentFuel(Number(e.target.value))
                    handleRecalculate()
                  }}
                  style={{ width: '100%', accentColor: '#fbbf24' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginTop: '6px' }}>
                <div style={{ background: '#111122', padding: '10px', borderRadius: 10, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Total Required</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff' }}>
                    {tripData?.fuel_required_l ?? 395} L
                  </div>
                </div>
                <div style={{ background: '#111122', padding: '10px', borderRadius: 10, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>To Purchase</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fbbf24' }}>
                    {Math.max(0, (tripData?.fuel_required_l ?? 395) - currentFuel)} L
                  </div>
                </div>
                <div style={{ background: '#111122', padding: '10px', borderRadius: 10, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Fuel Cost</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#10b981' }}>
                    ₹{(tripData?.fuel_cost_inr ?? 37525).toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 4. Toll Cost Breakdown Card */}
          <div style={{ background: '#16162a', padding: '20px', borderRadius: 18, border: '1px solid #2d2d44' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800 }}>
                🛣️ Toll Cost Breakdown
              </h3>
              <div style={{ fontSize: '1.1rem', fontWeight: 900, color: '#60a5fa' }}>
                ₹{(tripData?.toll_cost_inr ?? 2850).toLocaleString()}
              </div>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#fbbf24', marginBottom: '12px' }}>
              * Estimated — actual FASTag toll may vary based on truck axle classification.
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '180px', overflowY: 'auto' }}>
              {(tripData?.toll_plazas || [
                { name: 'Yamuna Expressway Toll Gate', location: 'Agra Section', cost_inr: 620 },
                { name: 'Gwalior Bypass Toll Plaza', location: 'NH44 Mile 320', cost_inr: 340 },
                { name: 'Babina Toll Plaza', location: 'Jhansi Section', cost_inr: 280 },
                { name: 'Nagpur Outer Ring Toll', location: 'Nagpur Hub', cost_inr: 480 },
                { name: 'Pimpalgaon Toll Plaza', location: 'Border Point', cost_inr: 380 },
                { name: 'Medchal Toll Plaza', location: 'Hyderabad Entrance', cost_inr: 450 },
              ]).map((t, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '8px 12px',
                    background: '#111122',
                    borderRadius: 8,
                    fontSize: '0.85rem',
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 700, color: '#e2e8f0' }}>{t.name}</span>
                    <span style={{ fontSize: '0.75rem', color: '#9ca3af', marginLeft: '6px' }}>({t.location})</span>
                  </div>
                  <strong style={{ color: '#60a5fa' }}>₹{t.cost_inr}</strong>
                </div>
              ))}
            </div>
          </div>

          {/* 5. Food & Driver Meals Calculator */}
          <div style={{ background: '#16162a', padding: '20px', borderRadius: 18, border: '1px solid #2d2d44' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: '#f472b6' }}>
                🍛 Food & Daily Allowance
              </h3>
              <div style={{ fontSize: '1.1rem', fontWeight: 900, color: '#f472b6' }}>
                ₹{(tripData?.food_cost_inr ?? 800).toLocaleString()}
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#9ca3af' }}>
                <span>Daily Breakdown: Breakfast ₹100 • Lunch ₹150 • Dinner ₹150</span>
                <span>= ₹400 / day</span>
              </div>
              <div>
                <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: '#e2e8f0', marginBottom: '4px' }}>
                  <span>Daily Meal Allowance Budget:</span>
                  <strong style={{ color: '#f472b6' }}>₹{foodBudget} / day</strong>
                </label>
                <input
                  type="range"
                  min="200"
                  max="1000"
                  step="50"
                  value={foodBudget}
                  onChange={(e) => {
                    setFoodBudget(Number(e.target.value))
                    handleRecalculate()
                  }}
                  style={{ width: '100%', accentColor: '#f472b6' }}
                />
              </div>
            </div>
          </div>

          {/* 6. Total Cost Summary & Financial ROI */}
          <div style={{ background: 'linear-gradient(135deg, #1e1e38, #18182c)', padding: '24px', borderRadius: 20, border: '1px solid #10b98155', boxShadow: '0 0 30px rgba(16, 185, 129, 0.15)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #2d2d48', paddingBottom: '12px', marginBottom: '14px' }}>
              <div>
                <div style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 800, textTransform: 'uppercase' }}>
                  Total Estimated Trip Cost
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 900, color: '#10b981', marginTop: '2px' }}>
                  ₹{(tripData?.total_cost_inr ?? 43500).toLocaleString()}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Expected Arrival (ETA):</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#fff', marginTop: '2px' }}>
                  {tripData?.eta_timestamp || 'Tomorrow at 18:30 PM'}
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
              <div style={{ background: '#111122', padding: '10px 14px', borderRadius: 10 }}>
                <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Cost Per Km:</div>
                <strong style={{ color: '#fff', fontSize: '1rem' }}>₹{tripData?.cost_per_km_inr ?? 27.53} / km</strong>
              </div>
              <div style={{ background: '#111122', padding: '10px 14px', borderRadius: 10 }}>
                <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Cost Per Day:</div>
                <strong style={{ color: '#fff', fontSize: '1rem' }}>₹{tripData?.cost_per_day_inr ?? 21750} / day</strong>
              </div>
              <div style={{ background: '#111122', padding: '10px 14px', borderRadius: 10 }}>
                <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Estimated Revenue:</div>
                <strong style={{ color: '#60a5fa', fontSize: '1rem' }}>₹{(tripData?.est_freight_revenue_inr ?? 65000).toLocaleString()}</strong>
              </div>
              <div style={{ background: '#10b98118', padding: '10px 14px', borderRadius: 10, border: '1px solid #10b98144' }}>
                <div style={{ fontSize: '0.75rem', color: '#10b981' }}>Estimated Net Profit:</div>
                <strong style={{ color: '#10b981', fontSize: '1.1rem' }}>₹{(tripData?.est_net_profit_inr ?? 21500).toLocaleString()}</strong>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Interactive Leaflet Route Map + POI Tabs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ background: '#16162a', padding: '16px', borderRadius: 18, border: '1px solid #2d2d44', height: '620px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.2rem' }}>📍</span>
                <span style={{ fontWeight: 800, fontSize: '1rem', color: '#fff' }}>Interactive Freight Route Map (Leaflet + OpenStreetMap)</span>
              </div>
              <div style={{ display: 'flex', gap: '6px', fontSize: '0.75rem', color: '#9ca3af' }}>
                <span>🚩 Origin</span> • <span>🏁 Dest</span> • <span>⛽ Fuel</span> • <span>🍛 Dhaba</span> • <span>⚙️ Mechanic</span>
              </div>
            </div>

            <div style={{ flex: 1, borderRadius: 14, overflow: 'hidden', border: '1px solid #2d2d44' }}>
              <MapContainer
                center={mapCenter}
                zoom={5}
                style={{ width: '100%', height: '100%' }}
                scrollWheelZoom={true}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {/* Route Polyline */}
                <Polyline
                  positions={routeCoords}
                  color="#6366f1"
                  weight={5}
                  opacity={0.85}
                  dashArray="0"
                />

                {/* Origin Marker */}
                {routeCoords[0] && (
                  <Marker position={routeCoords[0]} icon={createCustomIcon('🚩', '#10b981')}>
                    <Popup>
                      <strong>Origin: {origin}</strong><br />
                      Trip Start Point
                    </Popup>
                  </Marker>
                )}

                {/* Destination Marker */}
                {routeCoords[routeCoords.length - 1] && (
                  <Marker position={routeCoords[routeCoords.length - 1]} icon={createCustomIcon('🏁', '#ef4444')}>
                    <Popup>
                      <strong>Destination: {destination}</strong><br />
                      Delivery Hub & Unloading Bay
                    </Popup>
                  </Marker>
                )}

                {/* Toll Plazas */}
                {(tripData?.toll_plazas || []).filter(t => t.lat && t.lng).map((t, i) => (
                  <Marker key={`toll-${i}`} position={[t.lat, t.lng]} icon={createCustomIcon('🛣️', '#3b82f6')}>
                    <Popup>
                      <strong>{t.name}</strong><br />
                      Location: {t.location}<br />
                      FASTag Fee: ₹{t.cost_inr}
                    </Popup>
                  </Marker>
                ))}

                {/* Fuel Stations */}
                {(tripData?.fuel_stations || []).filter(f => f.lat && f.lng).map((f, i) => (
                  <Marker key={`fuel-${i}`} position={[f.lat, f.lng]} icon={createCustomIcon('⛽', '#f59e0b')}>
                    <Popup>
                      <strong>{f.name}</strong><br />
                      {f.highway}<br />
                      Diesel: ₹{f.price_per_litre}/L • Truck Bay: Yes
                    </Popup>
                  </Marker>
                ))}

                {/* Restaurants */}
                {(tripData?.restaurants || []).filter(r => r.lat && r.lng).map((r, i) => (
                  <Marker key={`rest-${i}`} position={[r.lat, r.lng]} icon={createCustomIcon('🍛', '#ec4899')}>
                    <Popup>
                      <strong>{r.name}</strong><br />
                      {r.cuisine}<br />
                      Cost: {r.avg_cost} • ⭐ {r.rating}
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </div>

          {/* Highway Facilities Quick Access */}
          <div style={{ background: '#16162a', padding: '20px', borderRadius: 18, border: '1px solid #2d2d44' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: '1.05rem', fontWeight: 800, color: '#a5b4fc' }}>
              🛠️ Highway Amenities & Emergency Contacts Along Route
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              {(tripData?.puncture_shops || [
                { name: 'Om Sai 24/7 Heavy Truck Puncture Repair', phone: '+91 98234 56789', distance_km: 1.8, status: 'OPEN 24/7' },
                { name: 'Nagpur Highway Mobile Mechanic', phone: '+91 97654 32109', distance_km: 3.2, status: 'OPEN 24/7' },
              ]).map((s, idx) => (
                <div key={idx} style={{ background: '#111122', padding: '12px', borderRadius: 10, border: '1px solid #ef444433' }}>
                  <div style={{ fontWeight: 800, fontSize: '0.85rem', color: '#fff' }}>{s.name}</div>
                  <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '2px' }}>📍 {s.distance_km} km away • {s.status}</div>
                  <a
                    href={`tel:${s.phone.replace(/\s+/g, '')}`}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      marginTop: '8px',
                      background: '#10b981',
                      color: '#fff',
                      padding: '4px 10px',
                      borderRadius: 6,
                      fontSize: '0.75rem',
                      fontWeight: 800,
                      textDecoration: 'none',
                    }}
                  >
                    📞 Call: {s.phone}
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Return Cargo Reminder Modal */}
      {showReturnModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.8)',
            zIndex: 99999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '16px',
          }}
          onClick={() => setShowReturnModal(false)}
        >
          <div
            style={{
              background: '#1a1a2e',
              border: '1px solid #6366f1',
              borderRadius: 20,
              padding: '24px',
              maxWidth: '500px',
              width: '100%',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.8rem' }}>🔄</span>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>Return Shipment Backhaul Match</h3>
                <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Reduce Empty Kilometers & Maximize Truck Profit</span>
              </div>
            </div>
            <p style={{ color: '#e2e8f0', fontSize: '0.95rem', lineHeight: 1.5, margin: 0 }}>
              4–5 hours before arriving at <strong>{destination}</strong>: Would you like to automatically search and accept return cargo back to {origin}?
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <button
                onClick={() => navigate('/return-cargo')}
                style={{
                  padding: '12px',
                  borderRadius: 10,
                  background: 'linear-gradient(135deg, #10b981, #059669)',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 800,
                  cursor: 'pointer',
                }}
              >
                ✓ YES — Find Return Load
              </button>
              <button
                onClick={() => setShowReturnModal(false)}
                style={{
                  padding: '12px',
                  borderRadius: 10,
                  background: '#2d2d3d',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 800,
                  cursor: 'pointer',
                }}
              >
                ✕ Not Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
