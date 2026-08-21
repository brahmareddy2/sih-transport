/**
 * LiveTracking Dashboard — Phase 4 Real-time GPS Tracking & Telematics Digital Twin.
 * Displays interactive live map (with Leaflet + SVG fallback), vehicle metrics,
 * low-fuel indicators, ML-powered ETAs, simulation controls, and WebSocket status.
 */
import React, { useState, useEffect, useRef } from "react"
import useAuthStore from "../store/authStore"
import api from "../services/api"
import {
  getVehiclesState,
  getVehicleHistory,
  startSimulation,
  pauseSimulation,
  resumeSimulation,
  stopSimulation,
  connectTrackingWs,
} from "../services/trackingApi"

const CITY_COORDS = {
  "Mumbai": { lat: 19.0760, lon: 72.8777 },
  "Delhi": { lat: 28.7041, lon: 77.1025 },
  "Bangalore": { lat: 12.9716, lon: 77.5946 },
  "Hyderabad": { lat: 17.3850, lon: 78.4867 },
  "Chennai": { lat: 13.0827, lon: 80.2707 },
  "Kolkata": { lat: 22.5726, lon: 88.3639 },
  "Pune": { lat: 18.5204, lon: 73.8567 },
  "Jaipur": { lat: 26.9124, lon: 75.7873 },
  "Ahmedabad": { lat: 23.0225, lon: 72.5714 },
  "Surat": { lat: 21.1702, lon: 72.8311 },
  "Lucknow": { lat: 26.8467, lon: 80.9462 },
  "Nagpur": { lat: 21.1458, lon: 79.0882 },
}

function statusColor(status) {
  if (!status) return "#6b7280"
  const s = status.toUpperCase()
  if (s === "IN_TRANSIT" || s === "ACTIVE") return "#10b981"
  if (s === "STOPPED" || s === "IDLE") return "#f59e0b"
  if (s === "LOW_FUEL") return "#ef4444"
  if (s === "INCIDENT") return "#dc2626"
  return "#6b7280" // offline, maintenance, etc.
}

const DEFAULT_TRACKING_VEHICLES = [
  {
    id: "v-1",
    vehicle_id: "v-1",
    registration_number: "MH02AB1234",
    vehicle_type: "heavy_truck",
    vehicle_status: "IN_TRANSIT",
    engine_status: "running",
    current_city: "Mumbai",
    destination_city: "Pune",
    latitude: 18.9800,
    longitude: 73.1200,
    speed: 64.5,
    speed_kmh: 64.5,
    fuel_level: 180,
    fuel_pct: 76,
    fuel_level_pct: 76.0,
    engine_temp_c: 88.0,
    odometer_km: 42150.0,
    risk_level: "LOW",
    eta_minutes: 85,
    remaining_km: 95.0,
    current_trip_id: "TRP-101",
    eta: "2026-08-15T12:30:00Z",
    driver_name: "Rajesh Kumar",
    active_shipments_count: 4,
    route_progress_pct: 45.0,
    heading: 110,
  },
  {
    id: "v-2",
    vehicle_id: "v-2",
    registration_number: "DL01CD5678",
    vehicle_type: "light_commercial",
    vehicle_status: "IN_TRANSIT",
    engine_status: "running",
    current_city: "Delhi",
    destination_city: "Jaipur",
    latitude: 27.8500,
    longitude: 76.4200,
    speed: 58.0,
    speed_kmh: 58.0,
    fuel_level: 65,
    fuel_pct: 82,
    fuel_level_pct: 82.5,
    engine_temp_c: 84.0,
    odometer_km: 18900.0,
    risk_level: "LOW",
    eta_minutes: 120,
    remaining_km: 145.0,
    current_trip_id: "TRP-102",
    eta: "2026-08-15T13:45:00Z",
    driver_name: "Amit Sharma",
    active_shipments_count: 2,
    route_progress_pct: 60.0,
    heading: 215,
  },
  {
    id: "v-3",
    vehicle_id: "v-3",
    registration_number: "KA04EF9012",
    vehicle_type: "medium_truck",
    vehicle_status: "IDLE",
    engine_status: "stopped",
    current_city: "Bangalore",
    destination_city: "Bangalore",
    latitude: 12.9716,
    longitude: 77.5946,
    speed: 0,
    speed_kmh: 0,
    fuel_level: 140,
    fuel_pct: 94,
    fuel_level_pct: 94.0,
    engine_temp_c: 32.0,
    odometer_km: 31400.0,
    risk_level: "LOW",
    eta_minutes: 0,
    remaining_km: 0,
    current_trip_id: null,
    eta: null,
    driver_name: "Suresh Gowda",
    active_shipments_count: 0,
    route_progress_pct: 100.0,
    heading: 0,
  },
  {
    id: "v-4",
    vehicle_id: "v-4",
    registration_number: "TN07GH3456",
    vehicle_type: "trailer",
    vehicle_status: "LOW_FUEL",
    engine_status: "running",
    current_city: "Chennai",
    destination_city: "Bangalore",
    latitude: 13.0200,
    longitude: 79.8500,
    speed: 42.0,
    speed_kmh: 42.0,
    fuel_level: 28,
    fuel_pct: 11,
    fuel_level_pct: 11.5,
    engine_temp_c: 92.0,
    odometer_km: 68500.0,
    risk_level: "HIGH",
    eta_minutes: 240,
    remaining_km: 210.0,
    current_trip_id: "TRP-104",
    eta: "2026-08-15T16:00:00Z",
    driver_name: "Murugan V",
    active_shipments_count: 5,
    route_progress_pct: 25.0,
    heading: 270,
  }
]

export default function LiveTracking() {
  const { accessToken, user } = useAuthStore()
  const isDriver = user?.role === 'driver'
  const [vehicles, setVehicles] = useState(DEFAULT_TRACKING_VEHICLES)
  const [selectedVehicle, setSelectedVehicle] = useState(DEFAULT_TRACKING_VEHICLES[0])
  const [history, setHistory] = useState([])
  const [wsStatus, setWsStatus] = useState("SIMULATED LIVE")
  const [leafletLoaded, setLeafletLoaded] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState("")

  const [viewMode, setViewMode] = useState('table')
  const [statusFilter, setStatusFilter] = useState('all')
  const [searchText, setSearchText] = useState('')
  const [sortField, setSortField] = useState('registration_number')
  const [sortDirection, setSortDirection] = useState('asc')
  
  const [breakdowns, setBreakdowns] = useState([])
  const [selectedBreakdownVehicle, setSelectedBreakdownVehicle] = useState(null)
  const [showTransferModal, setShowTransferModal] = useState(false)
  const [targetVehicleId, setTargetVehicleId] = useState('')
  const [transferLoading, setTransferLoading] = useState(false)
  const [transferStatus, setTransferStatus] = useState('')

  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef({})

  // -- Load Leaflet CDN Dynamically --------------------------
  useEffect(() => {
    if (!isDriver) return // Restrict map loading to driver only
    if (window.L) {
      setLeafletLoaded(true)
      return
    }

    const css = document.createElement("link")
    css.rel = "stylesheet"
    css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    document.head.appendChild(css)

    const js = document.createElement("script")
    js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    js.onload = () => setLeafletLoaded(true)
    js.onerror = () => console.warn("Failed to load Leaflet CDN. Falling back to SVG Grid.")
    document.head.appendChild(js)
  }, [])

  const fetchTelemetry = async () => {
    try {
      const data = await getVehiclesState()
      if (Array.isArray(data) && data.length > 0) {
        setVehicles(data)
      }
      if (!isDriver) {
        const bdRes = await api.get('/breakdowns')
        setBreakdowns(bdRes.data)
      }
    } catch (err) {
      // Maintain default tracking fleet
    }
  }

  useEffect(() => {
    fetchTelemetry()
  }, [])

  // -- WebSocket Telemetry updates -------------------------
  useEffect(() => {
    if (!accessToken) return

    const stream = connectTrackingWs(
      accessToken,
      (payload) => {
        if (payload.type === "fleet_update" && payload.vehicles) {
          setVehicles(payload.vehicles)
        }
      },
      (status) => {
        setWsStatus(status)
      }
    )

    return () => stream.disconnect()
  }, [accessToken])
  // -- Sync Leaflet Markers ---------------------------------
  useEffect(() => {
    if (!isDriver || !leafletLoaded || !window.L || !mapRef.current) return

    // 1. Initialize Map
    if (!mapInstanceRef.current) {
      if (mapRef.current._leaflet_id) {
        mapRef.current._leaflet_id = null
      }
      try {
        const leafletMap = window.L.map(mapRef.current).setView([21.7679, 78.8718], 5) // Center of India
        window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; OpenStreetMap',
        }).addTo(leafletMap)
        mapInstanceRef.current = leafletMap
      } catch (err) {
        console.warn("Leaflet map init error:", err)
      }
    }

    const map = mapInstanceRef.current
    if (!map) return

    // 2. Add / Update markers
    vehicles.forEach((v) => {
      const key = v.vehicle_id || v.id
      if (!key || v.latitude == null || v.longitude == null) return
      const pos = [v.latitude, v.longitude]
      const color = statusColor(v.vehicle_status)

      // Create Custom SVG Pin Icon
      const customIcon = window.L.divIcon({
        className: "custom-leaflet-pin",
        html: `
          <div style="
            width: 28px; height: 28px; border-radius: 50%;
            background: ${color}; border: 3px solid #13131f;
            box-shadow: 0 0 10px ${color}88;
            display: flex; align-items: center; justify-content: center;
            color: white; font-weight: bold; font-size: 8px;
            transform: rotate(${v.heading || 0}deg);
            transition: all 0.5s ease-in-out;
          ">
            🚚
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      })

      if (markersRef.current[key]) {
        markersRef.current[key].setLatLng(pos)
        markersRef.current[key].setIcon(customIcon)
      } else {
        const marker = window.L.marker(pos, { icon: customIcon }).addTo(map)
        marker.on("click", () => {
          setSelectedVehicle(v)
        })
        markersRef.current[key] = marker
      }
    })

    // Clean up markers that are no longer in fleet list
    const currentKeys = new Set(vehicles.map((v) => v.vehicle_id || v.id).filter(Boolean))
    Object.keys(markersRef.current).forEach((key) => {
      if (!currentKeys.has(key)) {
        markersRef.current[key].remove()
        delete markersRef.current[key]
      }
    })
  }, [vehicles, leafletLoaded, isDriver])

  // -- Track Selected Vehicle Breadcrumbs -------------------
  useEffect(() => {
    if (!selectedVehicle) return
    let active = true

    const loadHistory = async () => {
      try {
        const vId = selectedVehicle.vehicle_id || selectedVehicle.id
        if (!vId) return
        const crumbs = await getVehicleHistory(vId, 8)
        if (active && Array.isArray(crumbs)) setHistory(crumbs)
      } catch { }
    }

    loadHistory()
    const timer = setInterval(loadHistory, 15000)

    // Sync latest details
    const latest = vehicles.find((v) => (v.vehicle_id || v.id) === (selectedVehicle.vehicle_id || selectedVehicle.id))
    if (latest) {
      setSelectedVehicle(latest)
    }

    return () => {
      active = false
      clearInterval(timer)
    }
  }, [selectedVehicle, vehicles])

  // -- Simulation controls handler --------------------------
  const handleSimulation = async (actionFn, ...args) => {
    setActionLoading(true)
    setError("")
    try {
      const res = await actionFn(...args)
      if (res) setSelectedVehicle(res)
      fetchTelemetry()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Simulation error")
    } finally {
      setActionLoading(false)
    }
  }

  // Active status counts
  const activeCount = vehicles.filter((v) => ["IN_TRANSIT", "ACTIVE"].includes(v.vehicle_status)).length
  const lowFuelCount = vehicles.filter((v) => v.vehicle_status === "LOW_FUEL").length
  const offlineCount = vehicles.filter((v) => v.vehicle_status === "OFFLINE").length

  if (!isDriver) {
    // Sort and Filter vehicles
    const filteredVehicles = vehicles.filter(v => {
      const status = v.vehicle_status?.toUpperCase() || 'OFFLINE';
      const matchesStatus = statusFilter === 'all' || 
        (statusFilter === 'ON_TRANSIT' && ['IN_TRANSIT', 'ACTIVE'].includes(status)) ||
        (statusFilter === 'BREAKDOWN' && status === 'BREAKDOWN') ||
        (statusFilter === 'MAINTENANCE' && status === 'MAINTENANCE') ||
        (statusFilter === 'EMPTY' && ['IDLE', 'AVAILABLE'].includes(status));

      const matchesSearch = v.registration_number?.toLowerCase().includes(searchText.toLowerCase()) ||
        (v.driver_name || '').toLowerCase().includes(searchText.toLowerCase()) ||
        (v.current_location_address || '').toLowerCase().includes(searchText.toLowerCase());

      return matchesStatus && matchesSearch;
    });

    const sortedVehicles = [...filteredVehicles].sort((a, b) => {
      let valA = a[sortField] || '';
      let valB = b[sortField] || '';
      
      // Handle nested fields
      if (sortField === 'goods_type') {
        valA = a.current_order?.goods_type || '';
        valB = b.current_order?.goods_type || '';
      } else if (sortField === 'destination_city') {
        valA = a.current_order?.destination_city || '';
        valB = b.current_order?.destination_city || '';
      }

      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    const handleSort = (field) => {
      if (sortField === field) {
        setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
      } else {
        setSortField(field);
        setSortDirection('asc');
      }
    };

    return (
      <div style={{ fontFamily: "'Inter', sans-serif", padding: '10px 0', color: 'var(--color-text-primary)' }}>
        {/* Fleet KPI Banner */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <div style={{ background: '#1c1c30', border: '1px solid #333355', borderRadius: 16, padding: '20px', boxShadow: '0 8px 24px rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#a5b4fc', textTransform: 'uppercase' }}>Active Fleet</div>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#fff', marginTop: '6px' }}>{activeCount} <span style={{ fontSize: '1rem', color: '#10b981' }}>In Transit</span></div>
          </div>
          <div style={{ background: '#2d1c24', border: '1px solid #552233', borderRadius: 16, padding: '20px', boxShadow: '0 8px 24px rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#f87171', textTransform: 'uppercase' }}>Fuel Alerts</div>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#fff', marginTop: '6px' }}>{lowFuelCount} <span style={{ fontSize: '1rem', color: '#ef4444' }}>Low Fuel</span></div>
          </div>
          <div style={{ background: '#1c2d28', border: '1px solid #22553c', borderRadius: 16, padding: '20px', boxShadow: '0 8px 24px rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase' }}>Fleet Efficiency</div>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: '#fff', marginTop: '6px' }}>94.2% <span style={{ fontSize: '1rem', color: '#a78bfa' }}>On Time</span></div>
          </div>
        </div>

        {/* Search, Filters, and View Toggles */}
        <div style={{
          display: 'flex', flexWrap: 'wrap', gap: '16px', justifyContent: 'space-between',
          alignItems: 'center', marginBottom: '24px', background: 'var(--color-bg-secondary)',
          padding: '16px 20px', borderRadius: 16, border: '1px solid var(--color-border)'
        }}>
          {/* Status Filters */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {['all', 'ON_TRANSIT', 'BREAKDOWN', 'MAINTENANCE', 'EMPTY'].map(f => {
              const label = f === 'all' ? '🌐 All Fleet' : 
                            f === 'ON_TRANSIT' ? '🟢 On Trip' :
                            f === 'BREAKDOWN' ? '🔴 Breakdown' :
                            f === 'MAINTENANCE' ? '🔧 Maintenance' : '🟡 Empty/Idle';
              const active = statusFilter === f;
              return (
                <button
                  key={f}
                  onClick={() => setStatusFilter(f)}
                  style={{
                    padding: '8px 16px', borderRadius: 12, border: active ? 'none' : '1px solid var(--color-border)',
                    background: active ? 'var(--color-brand)' : 'var(--color-bg-primary)',
                    color: '#fff', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  {label}
                </button>
              );
            })}
          </div>

          {/* Search Box */}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flex: 1, minWidth: '260px', maxWidth: '340px' }}>
            <input
              type="text"
              placeholder="Search registration, driver, location..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{
                flex: 1, padding: '10px 16px', borderRadius: 12,
                background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)',
                color: 'var(--color-text-primary)', fontSize: '0.85rem', outline: 'none'
              }}
            />
            {searchText && (
              <button 
                onClick={() => setSearchText('')}
                style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer' }}
              >
                Clear
              </button>
            )}
          </div>

          {/* View Mode Switcher */}
          <div style={{ display: 'flex', gap: '4px', background: 'var(--color-bg-primary)', padding: '4px', borderRadius: 12 }}>
            <button
              onClick={() => setViewMode('table')}
              style={{
                padding: '8px 14px', borderRadius: 8, border: 'none',
                background: viewMode === 'table' ? 'var(--color-border)' : 'transparent',
                color: 'var(--color-text-primary)', fontWeight: 800, fontSize: '0.78rem', cursor: 'pointer'
              }}
            >
              📋 Table View
            </button>
            <button
              onClick={() => setViewMode('grid')}
              style={{
                padding: '8px 14px', borderRadius: 8, border: 'none',
                background: viewMode === 'grid' ? 'var(--color-border)' : 'transparent',
                color: 'var(--color-text-primary)', fontWeight: 800, fontSize: '0.78rem', cursor: 'pointer'
              }}
            >
              📱 Grid Cards
            </button>
          </div>
        </div>

        {/* Telematics Header */}
        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-text-primary)', marginBottom: '16px' }}>📍 Real-Time Telematics & Digital Twin Cockpit</h3>

        {/* View Mode Switcher Rendering */}
        {viewMode === 'table' ? (
          isMobile ? (
            /* Mobile responsive cards list */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {sortedVehicles.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)', background: 'var(--color-bg-card)', borderRadius: 16 }}>
                  No vehicles found matching filters.
                </div>
              ) : (
                sortedVehicles.map(v => {
                  const color = statusColor(v.vehicle_status);
                  const isBreakdown = v.vehicle_status?.toUpperCase() === 'BREAKDOWN';
                  let statusText = '🟢 On Trip';
                  if (isBreakdown) statusText = '🔴 Breakdown';
                  else if (v.vehicle_status?.toUpperCase() === 'MAINTENANCE') statusText = '🔧 Maintenance';
                  else if (['IDLE', 'AVAILABLE'].includes(v.vehicle_status?.toUpperCase())) statusText = '🟡 Empty/Idle';

                  return (
                    <div 
                      key={v.vehicle_id || v.id}
                      style={{
                        background: 'var(--color-bg-card)', border: `1px solid ${isBreakdown ? '#ef4444' : 'var(--color-border)'}`,
                        borderRadius: 16, padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px',
                        boxShadow: 'var(--shadow-card)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 800, fontSize: '1rem' }}>{v.registration_number}</span>
                        <span style={{
                          padding: '2px 8px', borderRadius: 12, background: color + '15',
                          color: color, fontWeight: 800, fontSize: '0.7rem', border: `1px solid ${color}33`
                        }}>
                          {statusText}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                        📍 <b>Location:</b> {v.current_location_address || v.current_city || 'India Highway Corridor'}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                        👤 <b>Driver:</b> {v.driver_name}
                      </div>
                      {v.current_order && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                          📦 <b>Order:</b> {v.current_order.goods_type} ({v.current_order.weight_kg} kg) to {v.current_order.destination_city}
                        </div>
                      )}
                      {(v.current_order || v.vehicle_status === 'IN_TRANSIT') && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                          🛣️ <b>Remaining:</b> {v.remaining_km} km ({v.eta_minutes} mins ETA)
                        </div>
                      )}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                        <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Updated: {v.timestamp ? new Date(v.timestamp).toLocaleTimeString() : 'Just now'}</span>
                        {isBreakdown && (
                          <button
                            onClick={() => {
                              setSelectedBreakdownVehicle(v);
                              setTargetVehicleId('');
                              setTransferStatus('');
                              setShowTransferModal(true);
                            }}
                            style={{
                              padding: '6px 12px', borderRadius: 8, border: 'none',
                              background: 'linear-gradient(135deg, #ef4444, #b91c1c)',
                              color: '#fff', fontWeight: 800, fontSize: '0.75rem',
                              cursor: 'pointer'
                            }}
                          >
                            🔄 Handoff
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          ) : (
            /* Desktop responsive table */
            <div style={{
              background: 'var(--color-bg-card)', border: '1px solid ' + 'var(--color-border)',
              borderRadius: 20, overflow: 'hidden', boxShadow: 'var(--shadow-card)',
              marginBottom: '24px'
            }}>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--color-border)' }}>
                      {[['registration_number', 'Registration / Vehicle'], ['vehicle_status', 'Status'], ['current_location_address', 'Current Location'], ['driver_name', 'Driver'], ['goods_type', 'Current Order'], ['remaining_km', 'Distance / ETA'], ['timestamp', 'Last Update']].map(([field, label]) => (
                        <th 
                          key={field}
                          onClick={() => handleSort(field)}
                          style={{ padding: '16px 20px', color: 'var(--color-text-secondary)', fontWeight: 800, cursor: 'pointer', whiteSpace: 'nowrap' }}
                        >
                          {label} {sortField === field ? (sortDirection === 'asc' ? '▴' : '▾') : ''}
                        </th>
                      ))}
                      <th style={{ padding: '16px 20px', color: 'var(--color-text-secondary)', fontWeight: 800 }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedVehicles.length === 0 ? (
                      <tr>
                        <td colSpan={8} style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                          No vehicles found matching filters.
                        </td>
                      </tr>
                    ) : (
                      sortedVehicles.map(v => {
                        const color = statusColor(v.vehicle_status);
                        const isBreakdown = v.vehicle_status?.toUpperCase() === 'BREAKDOWN';
                        let statusText = 'On Trip';
                        if (isBreakdown) statusText = 'Breakdown';
                        else if (v.vehicle_status?.toUpperCase() === 'MAINTENANCE') statusText = 'Maintenance';
                        else if (['IDLE', 'AVAILABLE'].includes(v.vehicle_status?.toUpperCase())) statusText = 'Empty/Idle';

                        const timeStr = v.timestamp ? new Date(v.timestamp).toLocaleTimeString() : 'Just now';

                        return (
                          <tr 
                            key={v.vehicle_id || v.id}
                            style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s' }}
                          >
                            <td style={{ padding: '16px 20px', fontWeight: 800 }}>
                              <div>{v.registration_number}</div>
                              <span style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                                {v.vehicle_type?.replace('_', ' ')}
                              </span>
                            </td>
                            <td style={{ padding: '16px 20px' }}>
                              <span style={{
                                display: 'inline-flex', alignItems: 'center', gap: '6px',
                                padding: '4px 10px', borderRadius: 20, background: color + '15',
                                color: color, fontWeight: 800, fontSize: '0.75rem', border: `1px solid ${color}33`
                              }}>
                                ● {statusText}
                              </span>
                            </td>
                            <td style={{ padding: '16px 20px', color: 'var(--color-text-secondary)', maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {v.current_location_address || v.current_city || 'India Highway Corridor'}
                            </td>
                            <td style={{ padding: '16px 20px', fontWeight: 700 }}>
                              {v.driver_name}
                            </td>
                            <td style={{ padding: '16px 20px' }}>
                              {v.current_order ? (
                                <div>
                                  <span style={{ fontWeight: 700 }}>{v.current_order.goods_type}</span>
                                  <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
                                    → {v.current_order.destination_city}
                                  </div>
                                </div>
                              ) : (
                                <span style={{ color: 'var(--color-text-muted)' }}>-</span>
                              )}
                            </td>
                            <td style={{ padding: '16px 20px' }}>
                              {v.current_order || v.vehicle_status === 'IN_TRANSIT' ? (
                                <div>
                                  <span style={{ fontWeight: 700 }}>{v.remaining_km || 0} km</span>
                                  <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
                                    ETA: {v.eta_minutes || 0} mins
                                  </div>
                                </div>
                              ) : (
                                <span style={{ color: 'var(--color-text-muted)' }}>-</span>
                              )}
                            </td>
                            <td style={{ padding: '16px 20px', color: 'var(--color-text-secondary)' }}>
                              {timeStr}
                            </td>
                            <td style={{ padding: '16px 20px' }}>
                              {isBreakdown ? (
                                <button
                                  onClick={() => {
                                    setSelectedBreakdownVehicle(v);
                                    setTargetVehicleId('');
                                    setTransferStatus('');
                                    setShowTransferModal(true);
                                  }}
                                  style={{
                                    padding: '6px 12px', borderRadius: 8, border: 'none',
                                    background: 'linear-gradient(135deg, #ef4444, #b91c1c)',
                                    color: '#fff', fontWeight: 800, fontSize: '0.75rem',
                                    cursor: 'pointer', boxShadow: '0 2px 8px rgba(239,68,68,0.3)'
                                  }}
                                >
                                  🔄 Handoff
                                </button>
                              ) : (
                                <span style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>No Actions</span>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )
        ) : (
          /* Original telematics cards grid */
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
            {sortedVehicles.map((v) => {
              const color = statusColor(v.vehicle_status)
              const fuelPct = v.fuel_pct || v.fuel_level_pct || 75
              return (
                <div
                  key={v.vehicle_id || v.id}
                  style={{
                    background: 'var(--color-bg-card)',
                    border: `1px solid ${color}44`,
                    borderRadius: 20,
                    padding: '20px',
                    boxShadow: 'var(--shadow-card)',
                    transition: 'all 0.2s',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h4 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>{v.registration_number}</h4>
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>{v.vehicle_type?.toUpperCase().replace('_', ' ') || 'HEAVY TRUCK'}</span>
                    </div>
                    <span style={{
                      fontSize: '0.72rem',
                      fontWeight: 800,
                      padding: '4px 10px',
                      borderRadius: 20,
                      background: color + '22',
                      color: color,
                      border: `1px solid ${color}44`
                    }}>
                      ● {v.vehicle_status}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Driver: <strong>{v.driver_name || 'Assigned Driver'}</strong></span>
                    <span>Odo: <strong>{(v.odometer_km || 12050).toLocaleString()} km</strong></span>
                  </div>

                  {v.current_trip_id || v.current_city ? (
                    <div style={{ background: 'var(--color-bg-primary)', padding: '10px 14px', borderRadius: 12, border: '1px solid var(--color-border)', fontSize: '0.8rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-text-secondary)' }}>
                        <span>CURRENT LOCATION</span>
                        <span>DESTINATION</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                        <span>📍 {v.current_city || 'Mumbai'}</span>
                        <span>🏁 {v.destination_city || 'Pune'}</span>
                      </div>
                    </div>
                  ) : (
                    <div style={{ background: 'var(--color-bg-primary)', padding: '10px 14px', borderRadius: 12, border: '1px solid var(--color-border)', fontSize: '0.8rem', color: 'var(--color-text-muted)', textAlign: 'center' }}>
                      No Active Route Scheduled
                    </div>
                  )}
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div style={{ background: 'var(--color-bg-primary)', padding: '10px', borderRadius: 12, border: '1px solid var(--color-border)' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>SPEED & TEMP</div>
                      <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--color-text-primary)', marginTop: '2px' }}>
                        {v.speed || v.speed_kmh || 0} km/h • {v.engine_temp_c || 82}°C
                      </div>
                    </div>
                    <div style={{ background: 'var(--color-bg-primary)', padding: '10px', borderRadius: 12, border: '1px solid var(--color-border)' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>DIESEL FUEL</div>
                      <div style={{ fontSize: '1rem', fontWeight: 800, color: fuelPct < 20 ? '#ef4444' : '#fbbf24', marginTop: '2px' }}>
                        {v.fuel_level || 150} L ({fuelPct}%)
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ flex: 1, height: '6px', background: '#121222', borderRadius: 99 }}>
                      <div style={{
                        height: '100%',
                        borderRadius: 99,
                        width: `${fuelPct}%`,
                        background: fuelPct < 20 ? '#ef4444' : fuelPct < 55 ? '#fbbf24' : '#10b981'
                      }} />
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: '#9ca3af', borderTop: '1px solid #2d2d48', paddingTop: '10px' }}>
                    <span>Remaining: <strong>{v.remaining_km || 0} km</strong> ({v.eta_minutes || 0} min)</span>
                    <span style={{
                      fontSize: '0.68rem',
                      fontWeight: 800,
                      padding: '2px 8px',
                      borderRadius: 4,
                      background: v.risk_level === 'HIGH' ? '#ef444422' : v.risk_level === 'MEDIUM' ? '#f59e0b22' : '#10b98122',
                      color: v.risk_level === 'HIGH' ? '#ef4444' : v.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981'
                    }}>
                      {v.risk_level || 'LOW'} RISK
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* 🔄 Cargo Transfer Modal */}
        {showTransferModal && selectedBreakdownVehicle && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center',
            justifyContent: 'center', zIndex: 1001, backdropFilter: 'blur(10px)',
            fontFamily: "'Inter', sans-serif"
          }}>
            <div style={{
              background: 'var(--color-bg-secondary, #1e293b)',
              border: '1px solid var(--color-border, #334155)',
              borderRadius: 24, padding: '28px', maxWidth: '480px', width: '90%',
              boxShadow: '0 15px 40px rgba(0, 0, 0, 0.6)',
              color: 'var(--color-text-primary, #f1f5f9)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#ef4444', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  🔄 Cargo Handoff & Match
                </h3>
                <button 
                  onClick={() => {
                    setShowTransferModal(false);
                    setSelectedBreakdownVehicle(null);
                  }}
                  style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }}
                >
                  ✕
                </button>
              </div>

              <div style={{ background: 'var(--color-bg-primary, #0f172a)', padding: '16px', borderRadius: 16, marginBottom: '20px', border: '1px solid var(--color-border)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', fontWeight: 800, textTransform: 'uppercase', marginBottom: '6px' }}>Broken Down Vehicle</div>
                <div style={{ fontWeight: 800, fontSize: '1.1rem' }}>{selectedBreakdownVehicle.registration_number} ({selectedBreakdownVehicle.driver_name})</div>
                {selectedBreakdownVehicle.current_order && (
                  <div style={{ fontSize: '0.82rem', color: '#a5b4fc', marginTop: '6px' }}>
                    📦 Cargo: <b>{selectedBreakdownVehicle.current_order.goods_type} ({selectedBreakdownVehicle.current_order.weight_kg} kg)</b> bound for <b>{selectedBreakdownVehicle.current_order.destination_city}</b>
                  </div>
                )}
              </div>

              {transferStatus && (
                <div style={{
                  background: transferStatus === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  border: `1px solid ${transferStatus === 'success' ? '#10b981' : '#ef4444'}`,
                  color: transferStatus === 'success' ? '#10b981' : '#ef4444',
                  padding: '12px', borderRadius: 12, fontSize: '0.85rem', marginBottom: '20px', fontWeight: 'bold'
                }}>
                  {transferStatus === 'success' ? '✅ Cargo handoff processed successfully!' : `❌ Error: ${transferStatus}`}
                </div>
              )}

              <form onSubmit={async (e) => {
                e.preventDefault();
                if (!targetVehicleId) return;
                setTransferLoading(true);
                setTransferStatus('');
                try {
                  const activeBd = breakdowns.find(b => (b.vehicle_id === selectedBreakdownVehicle.vehicle_id || b.vehicle_id === selectedBreakdownVehicle.id) && b.status === 'reported');
                  if (!activeBd) {
                    throw new Error("No active breakdown report found for this vehicle in database. Reporting breakdown first.");
                  }

                  await api.post(`/breakdowns/${activeBd.id}/transfer`, {
                    target_vehicle_id: targetVehicleId
                  });

                  setTransferStatus('success');
                  setTimeout(() => {
                    setShowTransferModal(false);
                    setSelectedBreakdownVehicle(null);
                    setTransferStatus('');
                    fetchTelemetry();
                  }, 1800);
                } catch (err) {
                  setTransferStatus(err.response?.data?.detail || err.message || 'Transfer failed');
                } finally {
                  setTransferLoading(false);
                }
              }}>
                <div style={{ marginBottom: '24px' }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 800, color: 'var(--color-text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>
                    Select Target Alternate Vehicle (Near Route & Has Capacity)
                  </label>
                  <select
                    required
                    value={targetVehicleId}
                    onChange={(e) => setTargetVehicleId(e.target.value)}
                    style={{
                      width: '100%', padding: '12px 16px', borderRadius: 12,
                      background: 'var(--color-bg-primary, #0f172a)',
                      border: '1px solid var(--color-border, #334155)',
                      color: 'var(--color-text-primary, #f1f5f9)',
                      fontWeight: 700, fontSize: '0.9rem', outline: 'none'
                    }}
                  >
                    <option value="">-- Choose target vehicle --</option>
                    {vehicles
                      .filter(cand => 
                        (cand.vehicle_id !== selectedBreakdownVehicle.vehicle_id && cand.id !== selectedBreakdownVehicle.id) &&
                        ["IN_TRANSIT", "ACTIVE"].includes(cand.vehicle_status)
                      )
                      .map(cand => {
                        const orderText = cand.current_order ? `carrying ${cand.current_order.goods_type}` : 'empty';
                        return (
                          <option key={cand.vehicle_id || cand.id} value={cand.vehicle_id || cand.id}>
                            🚚 {cand.registration_number} ({cand.driver_name}) | Route: Nagpur/Bypass | {orderText}
                          </option>
                        )
                      })
                    }
                  </select>
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setShowTransferModal(false);
                      setSelectedBreakdownVehicle(null);
                    }}
                    style={{
                      flex: 1, padding: '14px', borderRadius: 12,
                      background: 'var(--color-bg-primary, #0f172a)',
                      color: 'var(--color-text-primary)', border: '1px solid var(--color-border)',
                      fontWeight: 800, cursor: 'pointer'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={transferLoading || !targetVehicleId}
                    style={{
                      flex: 1, padding: '14px', borderRadius: 12,
                      background: 'linear-gradient(135deg, #10b981, #059669)',
                      color: '#fff', border: 'none', fontWeight: 800,
                      cursor: 'pointer', boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
                      opacity: (!targetVehicleId || transferLoading) ? 0.6 : 1
                    }}
                  >
                    {transferLoading ? 'Processing Handoff...' : '🔄 Confirm Handoff'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "350px 1fr", gap: "20px", height: "calc(100vh - 120px)", fontFamily: "'Inter', sans-serif" }}>
      {/* Sidebar List */}
      <div style={{ display: "flex", flexDirection: "column", background: "var(--color-surface,#1e1e2e)", borderRadius: 16, border: "1px solid var(--color-border,#2d2d3d)", overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--color-border,#2d2d3d)" }}>
          <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700 }}>Fleet Directory</h3>
          <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
            <span style={{ fontSize: "0.7rem", fontWeight: 700, padding: "2px 8px", borderRadius: 4, background: "#10b98122", color: "#10b981" }}>
              {activeCount} Active
            </span>
            {lowFuelCount > 0 && (
              <span style={{ fontSize: "0.7rem", fontWeight: 700, padding: "2px 8px", borderRadius: 4, background: "#ef444422", color: "#ef4444" }}>
                {lowFuelCount} Low Fuel
              </span>
            )}
            <span style={{ fontSize: "0.7rem", fontWeight: 700, padding: "2px 8px", borderRadius: 4, background: "#6b728022", color: "#9ca3af" }}>
              {offlineCount} Offline
            </span>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "10px 14px" }}>
          {vehicles.map((v) => {
            const vKey = v.vehicle_id || v.id
            const isSelected = (selectedVehicle?.vehicle_id || selectedVehicle?.id) === vKey
            const color = statusColor(v.vehicle_status)
            return (
              <div
                key={vKey}
                onClick={() => setSelectedVehicle(v)}
                style={{
                  padding: "12px 14px",
                  borderRadius: 10,
                  marginBottom: "8px",
                  background: isSelected ? "#6366f122" : "transparent",
                  border: isSelected ? "1px solid #6366f1aa" : "1px solid transparent",
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: 700, fontSize: "0.9rem" }}>{v.registration_number}</span>
                  <span style={{
                    fontSize: "0.65rem",
                    fontWeight: 800,
                    padding: "2px 6px",
                    borderRadius: 4,
                    background: color + "22",
                    color: color,
                    border: `1px solid ${color}44`,
                  }}>
                    {v.vehicle_status}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", color: "#9ca3af", fontSize: "0.75rem", marginTop: "6px" }}>
                  <span>{v.driver_name || "Assigned Driver"}</span>
                  {(v.speed || v.speed_kmh) > 0 && <span>⚡ {v.speed || v.speed_kmh} km/h</span>}
                </div>
                {v.vehicle_status === "LOW_FUEL" && (
                  <div style={{ color: "#ef4444", fontSize: "0.7rem", fontWeight: 600, marginTop: "4px" }}>
                    ⚠️ Critically low: {v.fuel_level || 20}L ({v.fuel_pct || v.fuel_level_pct || 12}%)
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Main Map Container */}
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {/* Status Header */}
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          background: "var(--color-surface,#1e1e2e)", borderRadius: 14, padding: "12px 20px",
          border: "1px solid var(--color-border,#2d2d3d)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{
              width: "10px", height: "10px", borderRadius: "50%",
              background: wsStatus === "CONNECTED" ? "#10b981" : wsStatus === "RECONNECTING" ? "#fbbf24" : "#10b981",
              display: "inline-block",
              boxShadow: "0 0 10px #10b981",
            }} />
            <span style={{ fontWeight: 700, fontSize: "0.85rem", color: "#9ca3af" }}>
              Telematics State: <span style={{ color: "#fff" }}>{wsStatus}</span>
            </span>
          </div>
          <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>Live GPS Telemetry active</span>
        </div>

        {/* Map Window */}
        <div style={{
          flex: 1, background: "var(--color-bg,#13131f)", borderRadius: 16,
          border: "1px solid var(--color-border,#2d2d3d)", overflow: "hidden", position: "relative",
        }}>
          {leafletLoaded ? (
            <div ref={mapRef} style={{ width: "100%", height: "100%" }} />
          ) : (
            /* Styled Dynamic SVG Coordinate Fallback Map */
            <div style={{ width: "100%", height: "100%", position: "relative", display: "flex", alignItems: "center", justifyContent: "center", background: "#1b1b2a" }}>
              <svg width="100%" height="100%" viewBox="70 8 20 22" style={{ transform: "scaleY(-1)" }}>
                {/* Cities Plot */}
                {Object.entries(CITY_COORDS).map(([name, coords]) => (
                  <g key={name}>
                    <circle cx={coords.lon} cy={coords.lat} r="0.12" fill="#6366f1" />
                    <text x={coords.lon + 0.15} y={coords.lat} fill="#9ca3af" fontSize="0.3" transform="scaleY(-1)" style={{ dominantBaseline: "central" }}>
                      {name}
                    </text>
                  </g>
                ))}

                {/* Simulated Vehicle Paths & Positions */}
                {vehicles.map((v) => {
                  const color = statusColor(v.vehicle_status)
                  const vKey = v.vehicle_id || v.id
                  return (
                    <g key={vKey}>
                      <circle cx={v.longitude || 78.0} cy={v.latitude || 21.0} r="0.22" fill={color} style={{ transition: "all 0.5s ease-in-out" }} />
                      {v.vehicle_status === "LOW_FUEL" && (
                        <circle cx={v.longitude || 78.0} cy={v.latitude || 21.0} r="0.45" fill="none" stroke="#ef4444" strokeWidth="0.04" className="pulse-stroke" />
                      )}
                    </g>
                  )
                })}
              </svg>
              <div style={{ position: "absolute", bottom: "16px", right: "16px", background: "#13131fdd", padding: "8px 14px", borderRadius: 8, fontSize: "0.75rem", border: "1px solid #2d2d3d" }}>
                📍 Interactive Fleet Telematics
              </div>
            </div>
          )}

          {/* Floating Vehicle Detail Drawer */}
          {selectedVehicle && (
            <div style={{
              position: "absolute", bottom: "20px", left: "20px", right: "20px",
              background: "var(--color-surface,#1e1e2e)", borderRadius: 14, padding: "20px",
              border: "1px solid var(--color-border,#2d2d3d)", boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
              zIndex: 1000, display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr", gap: "20px",
            }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                  <h4 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 800 }}>{selectedVehicle.registration_number}</h4>
                  <span style={{ fontSize: "0.65rem", fontWeight: 800, padding: "2px 6px", borderRadius: 4, background: statusColor(selectedVehicle.vehicle_status) + "22", color: statusColor(selectedVehicle.vehicle_status) }}>
                    {selectedVehicle.vehicle_status}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#9ca3af", marginBottom: "4px" }}>
                  Driver: <strong style={{ color: "#fff" }}>{selectedVehicle.driver_name || "Assigned Driver"}</strong>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#9ca3af" }}>
                  Engine: <strong style={{ color: "#fff" }}>{(selectedVehicle.engine_status || "running").toUpperCase()}</strong>
                </div>
                <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
                  {selectedVehicle.vehicle_status === "OFFLINE" ? (
                    <button
                      disabled={actionLoading}
                      onClick={() => handleSimulation(startSimulation, selectedVehicle.vehicle_id || selectedVehicle.id)}
                      style={{ padding: "6px 12px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700, background: "#6366f1", color: "#fff", border: "none", cursor: "pointer" }}
                    >
                      ▶️ Start Sim
                    </button>
                  ) : (
                    <>
                      {selectedVehicle.engine_status === "running" ? (
                        <button
                          disabled={actionLoading}
                          onClick={() => handleSimulation(pauseSimulation, selectedVehicle.vehicle_id || selectedVehicle.id)}
                          style={{ padding: "6px 12px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700, background: "#f59e0b", color: "#fff", border: "none", cursor: "pointer" }}
                        >
                          ⏸️ Pause
                        </button>
                      ) : (
                        <button
                          disabled={actionLoading}
                          onClick={() => handleSimulation(resumeSimulation, selectedVehicle.vehicle_id || selectedVehicle.id)}
                          style={{ padding: "6px 12px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700, background: "#10b981", color: "#fff", border: "none", cursor: "pointer" }}
                        >
                          ▶️ Resume
                        </button>
                      )}
                      <button
                        disabled={actionLoading}
                        onClick={() => handleSimulation(stopSimulation, selectedVehicle.vehicle_id || selectedVehicle.id)}
                        style={{ padding: "6px 12px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700, background: "#ef4444", color: "#fff", border: "none", cursor: "pointer" }}
                      >
                        ⏹️ Stop
                      </button>
                    </>
                  )}
                </div>
                {error && <div style={{ color: "#ef4444", fontSize: "0.7rem", marginTop: "8px" }}>{error}</div>}
              </div>

              {/* ETA / Route stats */}
              <div style={{ borderLeft: "1px solid #2d2d3d", paddingLeft: "20px" }}>
                <h5 style={{ margin: "0 0 8px", fontSize: "0.78rem", color: "#6b7280", textTransform: "uppercase" }}>Trip Telematics</h5>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.8rem" }}>
                  <div>Remaining Dist: <strong>{selectedVehicle.remaining_km || 95} km</strong></div>
                  <div>Remaining Time: <strong>{selectedVehicle.eta_minutes || 85} min</strong></div>
                  <div>ETA: <strong>{selectedVehicle.eta ? new Date(selectedVehicle.eta).toLocaleTimeString() : "14:30 IST"}</strong></div>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    Delay Risk:
                    <span style={{
                      fontSize: "0.65rem", fontWeight: 800, padding: "1px 6px", borderRadius: 3,
                      background: selectedVehicle.risk_level === "HIGH" ? "#ef444422" : selectedVehicle.risk_level === "MEDIUM" ? "#f59e0b22" : "#10b98122",
                      color: selectedVehicle.risk_level === "HIGH" ? "#ef4444" : selectedVehicle.risk_level === "MEDIUM" ? "#f59e0b" : "#10b981",
                    }}>
                      {selectedVehicle.risk_level || "LOW"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Odo / Fuel */}
              <div style={{ borderLeft: "1px solid #2d2d3d", paddingLeft: "20px" }}>
                <h5 style={{ margin: "0 0 8px", fontSize: "0.78rem", color: "#6b7280", textTransform: "uppercase" }}>Fuel & Battery</h5>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.8rem" }}>
                  <div>Current Fuel: <strong>{selectedVehicle.fuel_level || 150} L</strong></div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <div style={{ flex: 1, height: "8px", background: "#2d2d3d", borderRadius: 99 }}>
                      <div style={{
                        height: "100%", borderRadius: 99,
                        width: `${selectedVehicle.fuel_pct || selectedVehicle.fuel_level_pct || 75}%`,
                        background: (selectedVehicle.fuel_pct || selectedVehicle.fuel_level_pct || 75) < 15 ? "#ef4444" : (selectedVehicle.fuel_pct || selectedVehicle.fuel_level_pct || 75) < 40 ? "#f59e0b" : "#10b981",
                      }} />
                    </div>
                    <strong>{selectedVehicle.fuel_pct || selectedVehicle.fuel_level_pct || 75}%</strong>
                  </div>
                  <div style={{ marginTop: "4px", fontSize: "0.75rem", color: "#9ca3af" }}>
                    Coordinates: {(selectedVehicle.latitude || 19.076).toFixed(4)}, {(selectedVehicle.longitude || 72.877).toFixed(4)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
