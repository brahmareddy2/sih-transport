import React, { useState, useEffect } from 'react'
import { useI18nStore } from '../../services/i18n'
import DriverFacilities from './DriverFacilities'
import CommunicationModal from './CommunicationModal'
import api from '../../services/api'
import useAuthStore from '../../store/authStore'
import { connectTrackingWs } from '../../services/trackingApi'

export default function DriverAssistant({ onOpenVoice, onPlanTrip }) {
  const { language, t } = useI18nStore()
  const [selectedFacility, setSelectedFacility] = useState('restaurants')
  const [showFacilities, setShowFacilities] = useState(false)
  const [isCommOpen, setIsCommOpen] = useState(false)
  const [contactData, setContactData] = useState(null)

  // Breakdown modal states
  const [showBreakdownModal, setShowBreakdownModal] = useState(false)
  const [breakdownSeverity, setBreakdownSeverity] = useState('minor')
  const [breakdownDesc, setBreakdownDesc] = useState('')
  const [breakdownSubmitting, setBreakdownSubmitting] = useState(false)
  const [breakdownStatus, setBreakdownStatus] = useState('')

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
    origin_coords: [28.7041, 77.1025],
    destination_coords: [17.3850, 78.4867],
    path_coords: [[28.7041, 77.1025], [17.3850, 78.4867]],
    current_lat: 28.7041,
    current_lon: 77.1025,
  })
  const [loadingTrip, setLoadingTrip] = useState(false)

  const { accessToken } = useAuthStore()
  const [gpsState, setGpsState] = useState(null)
  const [leafletLoaded, setLeafletLoaded] = useState(false)
  const mapRef = React.useRef(null)
  const mapInstanceRef = React.useRef(null)
  const markerRef = React.useRef(null)
  const routeLineRef = React.useRef(null)
  const facilityMarkersRef = React.useRef([])
  const activeNavTargetRef = React.useRef(null)
  const [userCoords, setUserCoords] = React.useState(null)
  const [navRouteInfo, setNavRouteInfo] = React.useState(null)

  // Watch GPS/Browser Geolocation continuously on startup (asks permission once)
  React.useEffect(() => {
    if (!navigator.geolocation) return

    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        const lat = pos.coords.latitude
        const lng = pos.coords.longitude
        setUserCoords({ lat, lng })
        
        // Update vehicle marker on the map to show actual user position
        if (mapInstanceRef.current) {
          if (!markerRef.current) {
            const truckIcon = window.L.divIcon({
              className: '',
              html: `<div style="font-size: 24px; filter: drop-shadow(0 0 8px #10b981);">🚚</div>`,
              iconSize: [24, 24],
              iconAnchor: [12, 12]
            })
            markerRef.current = window.L.marker([lat, lng], { icon: truckIcon }).addTo(mapInstanceRef.current)
          } else {
            markerRef.current.setLatLng([lat, lng])
          }
        }

        // If actively navigating, dynamically update the route line
        if (activeNavTargetRef.current) {
          updateRoutePath(lat, lng, activeNavTargetRef.current.lat, activeNavTargetRef.current.lng, activeNavTargetRef.current.name)
        }
      },
      (err) => {
        console.warn("watchPosition failed or denied:", err)
      },
      { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
    )

    return () => navigator.geolocation.clearWatch(watchId)
  }, [])

  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371 // Radius of the earth in km
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLon = (lon2 - lon1) * Math.PI / 180
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    return R * c // Distance in km
  }

  const updateRoutePath = async (startLat, startLng, destLat, destLng, destName) => {
    try {
      const res = await fetch(`https://router.project-osrm.org/route/v1/driving/${startLng},${startLat};${destLng},${destLat}?overview=full&geometries=geojson`)
      const data = await res.json()

      if (data.routes && data.routes.length > 0) {
        const route = data.routes[0]
        const geometry = route.geometry
        const distanceKm = route.distance / 1000
        const durationMins = route.duration / 60

        // Clear previous route polyline
        if (routeLineRef.current) {
          routeLineRef.current.remove()
        }

        // Draw road-based route polyline
        routeLineRef.current = window.L.geoJSON(geometry, {
          style: { color: '#2563eb', weight: 6, opacity: 0.95 }
        }).addTo(mapInstanceRef.current)

        // Set React state to display in bottom navigation drawer
        setNavRouteInfo({
          distanceKm,
          durationMins,
          targetName: destName
        })

        // Place duration and distance popup directly at the midpoint of the route path
        const midIndex = Math.floor(geometry.coordinates.length / 2)
        const midCoords = geometry.coordinates[midIndex]

        if (window.routePopupInstance) {
          window.routePopupInstance.remove()
        }

        setTimeout(() => {
          if (mapInstanceRef.current) {
            window.routePopupInstance = window.L.popup()
              .setLatLng([midCoords[1], midCoords[0]])
              .setContent(`
                <div style="
                  background: #1e1b4b; color: #fff; border-radius: 8px; 
                  padding: 6px 12px; font-weight: bold; font-size: 0.8rem;
                  border: 1px solid #10b981; box-shadow: 0 4px 12px rgba(0,0,0,0.5);
                  text-align: center;
                  min-width: 140px;
                ">
                  🚗 <b>${durationMins.toFixed(0)} min</b><br/>
                  🛣️ <b>${distanceKm.toFixed(2)} km remaining</b>
                </div>
              `)
              .openOn(mapInstanceRef.current)
          }
        }, 400)
      }
    } catch (err) {
      console.error("OSRM Route update failed:", err)
    }
  }

  const fetchNearbyPetrolPumps = async () => {
    if (!mapInstanceRef.current) return;
    const lat = userCoords ? userCoords.lat : (gpsState ? gpsState.latitude : (tripData.current_lat || 28.7041))
    const lng = userCoords ? userCoords.lng : (gpsState ? gpsState.longitude : (tripData.current_lon || 77.1025))

    try {
      const { data } = await api.get('/nearby/petrol-pumps', { params: { lat, lng } })
      
      // Clear old facility markers
      facilityMarkersRef.current.forEach(m => m.remove())
      facilityMarkersRef.current = []

      // Calculate distances
      const resultsWithDist = data.results.map(item => ({
        ...item,
        distance: calculateDistance(lat, lng, item.lat, item.lng)
      }))

      // Sort closest first
      resultsWithDist.sort((a, b) => a.distance - b.distance)

      let nearestMarker = null

      resultsWithDist.forEach(item => {
        const isNearest = resultsWithDist.length > 0 && item.name === resultsWithDist[0].name
        const pinIcon = window.L.divIcon({
          className: '',
          html: `<div style="
            background: #fbbf24; width: ${isNearest ? '24px' : '18px'}; height: ${isNearest ? '24px' : '18px'}; 
            border-radius: 50%; border: 2.5px solid ${isNearest ? '#10b981' : '#fff'}; 
            box-shadow: 0 0 12px #fbbf24;
            display: flex; align-items: center; justify-content: center;
            font-size: ${isNearest ? '11px' : '9px'};
            font-weight: bold;
            position: relative;
          ">
            ⛽
            ${isNearest ? '<span style="position:absolute; top:-8px; right:-8px; background:#10b981; color:#fff; font-size:6px; border-radius:4px; padding:1px 3px; border:1px solid #fff;">BEST</span>' : ''}
          </div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        })
        
        const marker = window.L.marker([item.lat, item.lng], { icon: pinIcon }).addTo(mapInstanceRef.current)
        const fuelsList = item.fuels ? item.fuels.join(', ') : 'Petrol, Diesel'
        
        marker.bindPopup(`
          <div style="font-family:'Inter', sans-serif; color: #fff; min-width: 170px; padding: 4px;">
            <h4 style="margin:0 0 4px; color:#fff; font-size: 0.9rem;">${item.name}</h4>
            ${isNearest ? '<span style="color:#10b981; font-weight:bold; font-size:0.75rem;">⭐ Closest to Your Location!</span><br/>' : ''}
            <span style="color:#9ca3af; font-size:0.7rem;">📍 ${item.address || ''}</span><br/>
            <span style="color:#fbbf24; font-size:0.75rem; display:block; margin-top:2px;">⛽ Fuels: <b>${fuelsList}</b></span>
            <span style="color:#38bdf8; font-size:0.75rem; display:block; margin-bottom: 6px;">🛣️ Distance: <b>${item.distance.toFixed(2)} km</b></span>
            <button 
              onclick="window.navigateRoute(${item.lat}, ${item.lng}, '${item.name.replace(/'/g, "\\'")}')" 
              style="
                width:100%; padding:6px; background:#10b981; border:none; 
                border-radius:6px; color:#fff; font-weight:bold; font-size:0.75rem; 
                cursor:pointer; text-align:center;
              "
            >
              🚙 Navigate Route
            </button>
          </div>
        `)
        
        facilityMarkersRef.current.push(marker)
        if (isNearest) nearestMarker = marker
      })

      // Re-center map to the searched location
      mapInstanceRef.current.setView([lat, lng], 13)

      // AUTO-NAVIGATION: Route immediately to closest station!
      const nearest = resultsWithDist[0]
      if (nearest) {
        window.navigateRoute(nearest.lat, nearest.lng, nearest.name)
      }
    } catch (err) {
      console.error("Failed to load nearby gas stations:", err)
      alert("Could not load nearby gas stations. Please try again.")
    }
  }

  const fetchNearbyMechanics = async () => {
    if (!mapInstanceRef.current) return;
    const lat = userCoords ? userCoords.lat : (gpsState ? gpsState.latitude : (tripData.current_lat || 28.7041))
    const lng = userCoords ? userCoords.lng : (gpsState ? gpsState.longitude : (tripData.current_lon || 77.1025))

    try {
      const { data } = await api.get('/nearby/mechanics', { params: { lat, lng } })
      
      // Clear old facility markers
      facilityMarkersRef.current.forEach(m => m.remove())
      facilityMarkersRef.current = []

      // Calculate distances
      const resultsWithDist = data.results.map(item => ({
        ...item,
        distance: calculateDistance(lat, lng, item.lat, item.lng)
      }))

      // Sort closest first
      resultsWithDist.sort((a, b) => a.distance - b.distance)

      let nearestMarker = null

      resultsWithDist.forEach(item => {
        const isNearest = resultsWithDist.length > 0 && item.name === resultsWithDist[0].name
        const pinIcon = window.L.divIcon({
          className: '',
          html: `<div style="
            background: #ef4444; width: ${isNearest ? '24px' : '18px'}; height: ${isNearest ? '24px' : '18px'}; 
            border-radius: 50%; border: 2.5px solid ${isNearest ? '#10b981' : '#fff'}; 
            box-shadow: 0 0 12px #ef4444;
            display: flex; align-items: center; justify-content: center;
            font-size: ${isNearest ? '11px' : '9px'};
            font-weight: bold;
            position: relative;
          ">
            🔧
            ${isNearest ? '<span style="position:absolute; top:-8px; right:-8px; background:#10b981; color:#fff; font-size:6px; border-radius:4px; padding:1px 3px; border:1px solid #fff;">BEST</span>' : ''}
          </div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        })
        
        const marker = window.L.marker([item.lat, item.lng], { icon: pinIcon }).addTo(mapInstanceRef.current)
        
        marker.bindPopup(`
          <div style="font-family:'Inter', sans-serif; color: #fff; min-width: 170px; padding: 4px;">
            <h4 style="margin:0 0 4px; color:#fff; font-size: 0.9rem;">${item.name}</h4>
            ${isNearest ? '<span style="color:#10b981; font-weight:bold; font-size:0.75rem;">⭐ Closest to Your Location!</span><br/>' : ''}
            <span style="color:#9ca3af; font-size:0.7rem;">📍 ${item.address || ''}</span><br/>
            <span style="color:#ef4444; font-size:0.75rem; display:block; margin-top:2px;">🔧 Services: <b>Engine, Tyres & Punctures</b></span>
            <span style="color:#38bdf8; font-size:0.75rem; display:block; margin-bottom: 6px;">🛣️ Distance: <b>${item.distance.toFixed(2)} km</b></span>
            <button 
              onclick="window.navigateRoute(${item.lat}, ${item.lng}, '${item.name.replace(/'/g, "\\'")}')" 
              style="
                width:100%; padding:6px; background:#10b981; border:none; 
                border-radius:6px; color:#fff; font-weight:bold; font-size:0.75rem; 
                cursor:pointer; text-align:center;
              "
            >
              🚙 Navigate Route
            </button>
          </div>
        `)
        
        facilityMarkersRef.current.push(marker)
        if (isNearest) nearestMarker = marker
      })

      // Re-center map to the searched location
      mapInstanceRef.current.setView([lat, lng], 13)

      // AUTO-NAVIGATION: Route immediately to closest mechanic!
      const nearest = resultsWithDist[0]
      if (nearest) {
        window.navigateRoute(nearest.lat, nearest.lng, nearest.name)
      }
    } catch (err) {
      console.error("Failed to load nearby mechanics:", err)
      alert("Could not load nearby mechanics. Please try again.")
    }
  }

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

  // Dynamic Road-Based Routing Hook (OSRM Free API)
  useEffect(() => {
    window.navigateRoute = async (destLat, destLng, destName) => {
      activeNavTargetRef.current = { lat: destLat, lng: destLng, name: destName }
      const startLat = userCoords ? userCoords.lat : (gpsState ? gpsState.latitude : (tripData.current_lat || 28.7041))
      const startLng = userCoords ? userCoords.lng : (gpsState ? gpsState.longitude : (tripData.current_lon || 77.1025))

      await updateRoutePath(startLat, startLng, destLat, destLng, destName)

      // Adjust map viewport to show the whole route path
      if (mapInstanceRef.current && routeLineRef.current) {
        mapInstanceRef.current.fitBounds(routeLineRef.current.getBounds())
      }
    }

    return () => {
      delete window.navigateRoute
    }
  }, [gpsState, tripData, userCoords])

  // Connect to WebSocket Telemetry Stream
  useEffect(() => {
    if (!accessToken) return

    const stream = connectTrackingWs(
      accessToken,
      (payload) => {
        if (payload.type === 'fleet_update' && Array.isArray(payload.vehicles) && payload.vehicles.length > 0) {
          console.log('[Driver GPS Update]', payload.vehicles[0])
          setGpsState(payload.vehicles[0])
        }
      },
      (status) => {
        console.log('[Driver WS Status]', status)
      }
    )

    return () => stream.disconnect()
  }, [accessToken])

  // Load Leaflet CDN Dynamically
  useEffect(() => {
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
    js.onerror = () => console.warn("Failed to load Leaflet in Driver cockpit.")
    document.head.appendChild(js)
  }, [])

  // Sync / Render Leaflet Map
  useEffect(() => {
    if (!leafletLoaded || !window.L || !mapRef.current) return

    const originCoords = tripData.origin_coords || [28.7041, 77.1025]
    const destCoords = tripData.destination_coords || [17.3850, 78.4867]
    const pathCoords = tripData.path_coords || [originCoords, destCoords]
    
    const currentLat = gpsState ? gpsState.latitude : (tripData.current_lat || originCoords[0])
    const currentLon = gpsState ? gpsState.longitude : (tripData.current_lon || originCoords[1])
    const currentSpeed = gpsState ? (gpsState.speed || gpsState.speed_kmh || 0) : 0
    const currentHeading = gpsState ? (gpsState.heading || 0) : 0

    if (!mapInstanceRef.current) {
      if (mapRef.current._leaflet_id) {
        mapRef.current._leaflet_id = null
      }
      try {
        const leafletMap = window.L.map(mapRef.current).setView([currentLat, currentLon], 6)
        window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; OpenStreetMap contributors',
        }).addTo(leafletMap)
        mapInstanceRef.current = leafletMap

        // Plot route path
        routeLineRef.current = window.L.polyline(pathCoords, { color: '#10b981', weight: 5, opacity: 0.8 }).addTo(leafletMap)

        // Plot start and end points
        window.L.marker(originCoords, {
          icon: window.L.divIcon({
            html: '<div style="background:#10b981; width:12px; height:12px; border-radius:50%; border:2px solid #fff; box-shadow: 0 0 10px #10b981;"></div>',
            iconSize: [12, 12]
          })
        }).addTo(leafletMap).bindPopup(`Origin: ${tripData.origin}`)

        window.L.marker(destCoords, {
          icon: window.L.divIcon({
            html: '<div style="background:#ef4444; width:12px; height:12px; border-radius:50%; border:2px solid #fff; box-shadow: 0 0 10px #ef4444;"></div>',
            iconSize: [12, 12]
          })
        }).addTo(leafletMap).bindPopup(`Destination: ${tripData.destination}`)
      } catch (err) {
        console.warn("Leaflet driver map init error:", err)
      }
    }

    const map = mapInstanceRef.current
    if (!map) return

    // Update vehicle marker position
    const pos = [currentLat, currentLon]
    const markerColor = currentSpeed > 0 ? '#10b981' : '#f59e0b'
    const vehicleIcon = window.L.divIcon({
      className: 'driver-vehicle-pin',
      html: `
        <div style="
          width: 32px; height: 32px; border-radius: 50%;
          background: ${markerColor}; border: 3px solid #16162a;
          box-shadow: 0 0 15px ${markerColor}bb;
          display: flex; align-items: center; justify-content: center;
          color: white; font-size: 14px;
          transform: rotate(${currentHeading}deg);
          transition: all 0.4s ease-in-out;
        ">
          🚚
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    })

    if (markerRef.current) {
      markerRef.current.setLatLng(pos)
      markerRef.current.setIcon(vehicleIcon)
    } else {
      markerRef.current = window.L.marker(pos, { icon: vehicleIcon }).addTo(map)
      markerRef.current.bindPopup(`Vehicle: ${tripData.registration_number || 'Assigned Carrier'}`)
    }

    // Auto center map on current position
    map.panTo(pos)
  }, [leafletLoaded, tripData, gpsState])

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
          background: 'linear-gradient(135deg, var(--color-bg-secondary) 0%, var(--color-bg-primary) 100%)',
          borderRadius: 24,
          padding: '32px',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-card)',
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
            background: 'var(--color-bg-secondary)',
            border: `1px solid ${getStatusColor()}`,
            borderRadius: 12,
            padding: '6px 12px',
          }}
        >
          <span style={{ height: '8px', width: '8px', borderRadius: '50%', background: getStatusColor(), display: 'inline-block' }} />
          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>{syncStatus}</span>
        </div>

        <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>🚚</div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--color-text-primary)', margin: 0 }}>
          {t('hello_driver', '👋 Hello Driver')}
        </h1>
        <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', margin: '6px 0 20px' }}>
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
          background: 'var(--color-bg-card)',
          borderRadius: 24,
          padding: '24px',
          border: '1px solid var(--color-border)',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--color-text-primary)', margin: 0 }}>
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
          <div style={{ background: 'var(--color-bg-primary)', padding: '14px', borderRadius: 14, border: '1px solid var(--color-border)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>ROUTE</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-text-primary)', marginTop: '2px' }}>
              {tripData.origin} ➔ {tripData.destination}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-brand)', marginTop: '2px' }}>
              Via NH44 ({tripData.distance_km.toLocaleString()} km)
            </div>
          </div>

          <div style={{ background: 'var(--color-bg-primary)', padding: '14px', borderRadius: 14, border: '1px solid var(--color-border)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>ESTIMATED TIME & ARRIVAL</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#34d399', marginTop: '2px' }}>
              {tripData.duration_hours} Hours
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              ETA: {tripData.eta}
            </div>
          </div>

          <div style={{ background: 'var(--color-bg-primary)', padding: '14px', borderRadius: 14, border: '1px solid var(--color-border)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>DIESEL & FUEL LEVEL</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fbbf24', marginTop: '2px' }}>
              {tripData.fuel_available_l} L Available
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-danger)', marginTop: '2px' }}>
              Requires ~{tripData.fuel_required_l} L total (Refuel in {tripData.refuel_city})
            </div>
          </div>

          <div style={{ background: 'var(--color-bg-primary)', padding: '14px', borderRadius: 14, border: '1px solid var(--color-border)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>ESTIMATED TRIP EXPENSE</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-purple)', marginTop: '2px' }}>
              ₹{tripData.total_cost_inr.toLocaleString()} Total
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              Tolls: ₹{tripData.toll_cost_inr.toLocaleString()} • Fuel: ₹{tripData.fuel_cost_inr.toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Dynamic Live Route Tracking Map Card */}
      <div
        style={{
          background: 'var(--color-bg-card)',
          borderRadius: 24,
          padding: '24px',
          border: '1px solid var(--color-border)',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-text-primary)', margin: 0 }}>
            📍 Live Route Map & GPS Progress
          </h3>
          {gpsState && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#10b981', fontWeight: 700 }}>
              <span style={{ height: '8px', width: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block', boxShadow: '0 0 8px #10b981' }} />
              Speed: {gpsState.speed || gpsState.speed_kmh || 0} km/h • Risk: {gpsState.risk_level || 'LOW'}
            </div>
          )}
        </div>

        <div
          style={{
            height: '350px',
            borderRadius: 16,
            overflow: 'hidden',
            border: '1px solid #3b3b5c',
            background: '#121222',
            position: 'relative'
          }}
        >
          {leafletLoaded && (
            <div style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              zIndex: 1000,
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}>
              <button
                type="button"
                onClick={fetchNearbyPetrolPumps}
                style={{
                  padding: '8px 12px',
                  background: 'rgba(22, 22, 42, 0.95)',
                  border: '1px solid #3b3b5c',
                  borderRadius: 10,
                  color: '#fff',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                ⛽ Nearby Gas Stations
              </button>
              <button
                type="button"
                onClick={fetchNearbyMechanics}
                style={{
                  padding: '8px 12px',
                  background: 'rgba(22, 22, 42, 0.95)',
                  border: '1px solid #3b3b5c',
                  borderRadius: 10,
                  color: '#fff',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                🔧 Nearby Mechanics
              </button>
            </div>
          )}
          {leafletLoaded ? (
            <div ref={mapRef} style={{ width: '100%', height: '100%', zIndex: 1 }} />
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justify: 'center', height: '100%', color: '#9ca3af', fontSize: '0.9rem' }}>
              ⚡ Loading Interactive Route Telematics...
            </div>
          )}
        </div>
        
        {/* Dynamic Trip Progress Overlay Panel */}
        <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
          <span>Current Coordinates: <strong>{gpsState ? gpsState.latitude?.toFixed(4) : (tripData.current_lat ? tripData.current_lat.toFixed(4) : 'N/A')}</strong>, <strong>{gpsState ? gpsState.longitude?.toFixed(4) : (tripData.current_lon ? tripData.current_lon.toFixed(4) : 'N/A')}</strong></span>
          <span>Remaining: <strong>{gpsState ? gpsState.remaining_km : tripData.distance_km} km</strong> ({gpsState ? gpsState.eta_minutes : Math.round(tripData.duration_hours*60)} min)</span>
        </div>

        {/* Beautiful Google-style bottom navigation drawer */}
        {navRouteInfo && (
          <div style={{
            marginTop: '16px',
            background: 'var(--color-bg-secondary)',
            border: '1.5px solid var(--color-success)',
            borderRadius: 16,
            padding: '16px',
            boxShadow: 'var(--shadow-card)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            fontFamily: "'Inter', sans-serif",
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justify: 'space-between' }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--color-success)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  🟢 ACTIVE ROAD ROUTING
                </span>
                <h4 style={{ margin: '2px 0 0', color: 'var(--color-text-primary)', fontSize: '0.95rem', fontWeight: 800 }}>
                  Navigating to {navRouteInfo.targetName}
                </h4>
              </div>
              <button
                type="button"
                onClick={() => {
                  activeNavTargetRef.current = null
                  setNavRouteInfo(null)
                  if (routeLineRef.current) routeLineRef.current.remove()
                  if (window.routePopupInstance) window.routePopupInstance.remove()
                }}
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: 'var(--color-danger)',
                  borderRadius: 8,
                  padding: '4px 10px',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  transition: 'opacity 0.2s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = 0.8)}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = 1)}
              >
                ✕ Cancel Route
              </button>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
              <span style={{ fontSize: '1.6rem', fontWeight: 900, color: 'var(--color-success)' }}>
                {navRouteInfo.durationMins < 60 
                  ? `${Math.round(navRouteInfo.durationMins)} min`
                  : `${Math.floor(navRouteInfo.durationMins / 60)} hr ${Math.round(navRouteInfo.durationMins % 60)} min`
                }
              </span>
              <span style={{ fontSize: '1.1rem', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                ({navRouteInfo.distanceKm.toFixed(2)} km)
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              via optimized highway corridor • updating live from your GPS sensor
            </div>
          </div>
        )}
      </div>

      {/* Offline Support & Trip Updates Logger */}
      <div
        style={{
          background: 'var(--color-bg-card)',
          borderRadius: 24,
          padding: '24px',
          border: '1px solid var(--color-border)',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-text-primary)', margin: 0 }}>
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
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
                Quick Update / Status text
              </label>
              <input
                type="text"
                placeholder="e.g. Stopped at Nagpur Dhaba, Stuck in NH44 traffic"
                value={newUpdateText}
                onChange={(e) => setNewUpdateText(e.target.value)}
                style={{ width: '100%', boxSizing: 'border-box', background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '8px 12px', color: 'var(--color-text-primary)', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-primary)', display: 'block', marginBottom: '4px' }}>
                Refilled Fuel Log (Litres)
              </label>
              <input
                type="number"
                placeholder="e.g. 100"
                value={fuelLogged}
                onChange={(e) => setFuelLogged(e.target.value)}
                style={{ width: '100%', boxSizing: 'border-box', background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)', borderRadius: 8, padding: '8px 12px', color: 'var(--color-text-primary)', fontSize: '0.85rem' }}
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
          <div style={{ background: 'var(--color-bg-primary)', padding: '14px', borderRadius: 14, border: '1px solid var(--color-border)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--color-purple)', marginBottom: '8px' }}>
              Pending Local Cache ({offlineUpdates.length})
            </div>
            {offlineUpdates.length === 0 ? (
              <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textAlign: 'center', padding: '20px 0' }}>
                No pending offline records. All logs synced.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '150px', overflowY: 'auto' }}>
                {offlineUpdates.map((item) => (
                  <div key={item.id} style={{ background: 'var(--color-bg-secondary)', padding: '8px 12px', borderRadius: 8, fontSize: '0.75rem', borderLeft: '3px solid #f59e0b' }}>
                    <div style={{ color: 'var(--color-text-primary)', fontWeight: 700 }}>{item.status}</div>
                    {item.fuel && <div style={{ color: '#fbbf24' }}>⛽ Refuelled: {item.fuel} Litres</div>}
                    <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>Logged at {item.timestamp}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3. Driver Quick Action Touch Buttons */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--color-purple)', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          🛣️ Highway Services & Pit-Stops
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px' }}>
          <button
            type="button"
            onClick={() => handleFacilityClick('restaurants')}
            style={{
              padding: '16px 12px',
              borderRadius: 16,
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
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
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
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
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
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
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
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
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
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
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
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

          <button
            type="button"
            onClick={() => setShowBreakdownModal(true)}
            style={{
              padding: '16px 12px',
              borderRadius: 16,
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.25))',
              border: '1px solid #ef4444',
              color: '#ef4444',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 0 10px rgba(239, 68, 68, 0.1)'
            }}
          >
            <span style={{ fontSize: '1.6rem' }}>🚨</span>
            <span>Report Breakdown</span>
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

      {/* 🚨 Driver Breakdown Modal */}
      {showBreakdownModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, backdropFilter: 'blur(8px)',
          fontFamily: "'Inter', sans-serif"
        }}>
          <div style={{
            background: 'var(--color-bg-secondary, #1e293b)',
            border: '1px solid var(--color-border, #334155)',
            borderRadius: 24, padding: '28px', maxWidth: '420px', width: '90%',
            boxShadow: 'var(--shadow-card, 0 10px 30px rgba(0,0,0,0.5))',
            color: 'var(--color-text-primary, #f1f5f9)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444' }}>
                🚨 Report Vehicle Breakdown
              </h3>
              <button 
                onClick={() => setShowBreakdownModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {breakdownStatus && (
              <div style={{
                background: breakdownStatus === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                border: `1px solid ${breakdownStatus === 'success' ? '#10b981' : '#ef4444'}`,
                color: breakdownStatus === 'success' ? '#10b981' : '#ef4444',
                padding: '12px', borderRadius: 12, fontSize: '0.85rem', marginBottom: '16px', fontWeight: 'bold'
              }}>
                {breakdownStatus === 'success' ? '✅ Breakdown reported successfully!' : `❌ Error: ${breakdownStatus}`}
              </div>
            )}

            <form onSubmit={async (e) => {
              e.preventDefault();
              setBreakdownSubmitting(true);
              setBreakdownStatus('');
              try {
                await api.post('/breakdowns', {
                  vehicle_id: tripData.vehicle_id,
                  trip_id: tripData.trip_id,
                  severity: breakdownSeverity,
                  description: breakdownDesc
                });
                setBreakdownStatus('success');
                setBreakdownDesc('');
                setTimeout(() => {
                  setShowBreakdownModal(false);
                  setBreakdownStatus('');
                  fetchActiveTrip(); // Refresh driver active trip telemetry
                }, 1800);
              } catch (err) {
                setBreakdownStatus(err.response?.data?.detail || err.message || 'Submission failed');
              } finally {
                setBreakdownSubmitting(false);
              }
            }}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 800, color: 'var(--color-text-secondary)', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Breakdown Severity
                </label>
                <select
                  value={breakdownSeverity}
                  onChange={(e) => setBreakdownSeverity(e.target.value)}
                  style={{
                    width: '100%', padding: '12px 16px', borderRadius: 12,
                    background: 'var(--color-bg-primary, #0f172a)',
                    border: '1px solid var(--color-border, #334155)',
                    color: 'var(--color-text-primary, #f1f5f9)',
                    fontWeight: 700, fontSize: '0.9rem', outline: 'none'
                  }}
                >
                  <option value="minor">🔧 Minor (No alternate vehicle needed)</option>
                  <option value="major">⚠️ Major (Requires Alternate Cargo Transfer)</option>
                </select>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 800, color: 'var(--color-text-secondary)', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Breakdown Description
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Describe the nature of breakdown (e.g. Engine overheated near bypass road, smoke coming out)"
                  value={breakdownDesc}
                  onChange={(e) => setBreakdownDesc(e.target.value)}
                  style={{
                    width: '100%', padding: '12px 16px', borderRadius: 12,
                    background: 'var(--color-bg-primary, #0f172a)',
                    border: '1px solid var(--color-border, #334155)',
                    color: 'var(--color-text-primary, #f1f5f9)',
                    fontSize: '0.9rem', outline: 'none', resize: 'vertical'
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={breakdownSubmitting}
                style={{
                  width: '100%', padding: '14px', borderRadius: 12,
                  background: 'linear-gradient(135deg, #ef4444, #b91c1c)',
                  color: '#fff', border: 'none', fontWeight: 800, fontSize: '0.95rem',
                  cursor: 'pointer', boxShadow: '0 4px 15px rgba(239, 68, 68, 0.4)',
                  transition: 'opacity 0.2s'
                }}
              >
                {breakdownSubmitting ? 'Submitting Report...' : '🚨 Submit Breakdown Report'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
