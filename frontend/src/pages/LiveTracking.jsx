/**
 * LiveTracking Dashboard — Phase 4 Real-time GPS Tracking & Telematics Digital Twin.
 * Displays interactive live map (with Leaflet + SVG fallback), vehicle metrics,
 * low-fuel indicators, ML-powered ETAs, simulation controls, and WebSocket status.
 */
import React, { useState, useEffect, useRef } from "react"
import useAuthStore from "../store/authStore"
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

export default function LiveTracking() {
  const { accessToken } = useAuthStore()
  const [vehicles, setVehicles] = useState([])
  const [selectedVehicle, setSelectedVehicle] = useState(null)
  const [history, setHistory] = useState([])
  const [wsStatus, setWsStatus] = useState("OFFLINE")
  const [leafletLoaded, setLeafletLoaded] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState("")

  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef({})

  // -- Load Leaflet CDN Dynamically --------------------------
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
    js.onerror = () => console.warn("Failed to load Leaflet CDN. Falling back to SVG Grid.")
    document.head.appendChild(js)
  }, [])

  // -- Initialize REST state ------------------------------
  const fetchTelemetry = async () => {
    try {
      const data = await getVehiclesState()
      setVehicles(data)
    } catch (err) {
      console.error("Failed fetching telemetry list:", err)
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
    if (!leafletLoaded || !window.L || !mapRef.current) return

    // 1. Initialize Map
    if (!mapInstanceRef.current) {
      const leafletMap = window.L.map(mapRef.current).setView([21.7679, 78.8718], 5) // Center of India
      window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(leafletMap)
      mapInstanceRef.current = leafletMap
    }

    const map = mapInstanceRef.current

    // 2. Add / Update markers
    vehicles.forEach((v) => {
      const key = v.vehicle_id
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
            ?
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
    const currentKeys = new Set(vehicles.map((v) => v.vehicle_id))
    Object.keys(markersRef.current).forEach((key) => {
      if (!currentKeys.has(key)) {
        markersRef.current[key].remove()
        delete markersRef.current[key]
      }
    })
  }, [vehicles, leafletLoaded])

  // -- Track Selected Vehicle Breadcrumbs -------------------
  useEffect(() => {
    if (!selectedVehicle) return
    let active = true

    const loadHistory = async () => {
      try {
        const crumbs = await getVehicleHistory(selectedVehicle.vehicle_id, 8)
        if (active) setHistory(crumbs)
      } catch {}
    }

    loadHistory()
    const timer = setInterval(loadHistory, 15000)

    // Sync latest details
    const latest = vehicles.find((v) => v.vehicle_id === selectedVehicle.vehicle_id)
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
      setSelectedVehicle(res)
      fetchTelemetry()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setActionLoading(false)
    }
  }

  // Active status counts
  const activeCount = vehicles.filter((v) => ["IN_TRANSIT", "ACTIVE"].includes(v.vehicle_status)).length
  const lowFuelCount = vehicles.filter((v) => v.vehicle_status === "LOW_FUEL").length
  const offlineCount = vehicles.filter((v) => v.vehicle_status === "OFFLINE").length

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
            const isSelected = selectedVehicle?.vehicle_id === v.vehicle_id
            const color = statusColor(v.vehicle_status)
            return (
              <div
                key={v.vehicle_id}
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
                  <span>{v.driver_name}</span>
                  {v.speed > 0 && <span>? {v.speed} km/h</span>}
                </div>
                {v.vehicle_status === "LOW_FUEL" && (
                  <div style={{ color: "#ef4444", fontSize: "0.7rem", fontWeight: 600, marginTop: "4px" }}>
                    ?? Critically low: {v.fuel_level}L ({v.fuel_pct}%)
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
              background: wsStatus === "CONNECTED" ? "#10b981" : wsStatus === "RECONNECTING" ? "#fbbf24" : "#ef4444",
              display: "inline-block",
              boxShadow: wsStatus === "CONNECTED" ? "0 0 10px #10b981" : "none",
            }} />
            <span style={{ fontWeight: 700, fontSize: "0.85rem", color: "#9ca3af" }}>
              WebSocket State: <span style={{ color: "#fff" }}>{wsStatus}</span>
            </span>
          </div>
          <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>Updates broadcast every 3s</span>
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
            <div style={{ width: "100%", height: "100%", position: "relative", display: "flex", alignItems: "center", justifyItems: "center", background: "#1b1b2a" }}>
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
                  return (
                    <g key={v.vehicle_id}>
                      <circle cx={v.longitude} cy={v.latitude} r="0.22" fill={color} style={{ transition: "all 0.5s ease-in-out" }} />
                      {v.vehicle_status === "LOW_FUEL" && (
                        <circle cx={v.longitude} cy={v.latitude} r="0.45" fill="none" stroke="#ef4444" strokeWidth="0.04" className="pulse-stroke" />
                      )}
                    </g>
                  )
                })}
              </svg>
              <div style={{ position: "absolute", bottom: "16px", right: "16px", background: "#13131fdd", padding: "8px 14px", borderRadius: 8, fontSize: "0.75rem", border: "1px solid #2d2d3d" }}>
                ?? Offline Fallback: SVG Coordinate Twin
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
                  Driver: <strong style={{ color: "#fff" }}>{selectedVehicle.driver_name}</strong>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#9ca3af" }}>
                  Engine: <strong style={{ color: "#fff" }}>{selectedVehicle.engine_status.toUpperCase()}</strong>
                </div>
                <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
                  {selectedVehicle.vehicle_status === "OFFLINE" ? (
                    <button
                      disabled={actionLoading}
                      onClick={() => handleSimulation(startSimulation, selectedVehicle.vehicle_id)}
                      style={{ padding: "6px 12px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700, background: "#6366f1", color: "#fff", border: "none", cursor: "pointer" }}
                    >
                      ?? Start Sim
                    </button>
                  ) : (
                    <>
                      {selectedVehicle.engine_status === "running" ? (
                        <button
                          disabled={actionLoading}
                          onClick={() => handleSimulation(pauseSimulation, selectedVehicle.vehicle_id)}
                          style={{ padding: "6px 12px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700, background: "#f59e0b", color: "#fff", border: "none", cursor: "pointer" }}
                        >
                          ?? Pause
                        </button>
                      ) : (
                        <button
                          disabled={actionLoading}
                          onClick={() => handleSimulation(resumeSimulation, selectedVehicle.vehicle_id)}
                          style={{ padding: "6px 12px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700, background: "#10b981", color: "#fff", border: "none", cursor: "pointer" }}
                        >
                          ?? Resume
                        </button>
                      )}
                      <button
                        disabled={actionLoading}
                        onClick={() => handleSimulation(stopSimulation, selectedVehicle.vehicle_id)}
                        style={{ padding: "6px 12px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 700, background: "#ef4444", color: "#fff", border: "none", cursor: "pointer" }}
                      >
                        ?? Stop
                      </button>
                    </>
                  )}
                </div>
                {error && <div style={{ color: "#ef4444", fontSize: "0.7rem", marginTop: "8px" }}>{error}</div>}
              </div>

              {/* ETA / Route stats */}
              <div style={{ borderLeft: "1px solid #2d2d3d", paddingLeft: "20px" }}>
                <h5 style={{ margin: "0 0 8px", fontSize: "0.78rem", color: "#6b7280", textTransform: "uppercase" }}>Trip Telematics</h5>
                {selectedVehicle.current_trip_id ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.8rem" }}>
                    <div>Remaining Dist: <strong>{selectedVehicle.remaining_km} km</strong></div>
                    <div>Remaining Time: <strong>{selectedVehicle.eta_minutes} min</strong></div>
                    <div>ETA: <strong>{selectedVehicle.eta ? new Date(selectedVehicle.eta).toLocaleTimeString() : "—"}</strong></div>
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
                ) : (
                  <div style={{ color: "#6b7280", fontSize: "0.8rem" }}>No active trip assigned to this vehicle.</div>
                )}
              </div>

              {/* Odo / Fuel */}
              <div style={{ borderLeft: "1px solid #2d2d3d", paddingLeft: "20px" }}>
                <h5 style={{ margin: "0 0 8px", fontSize: "0.78rem", color: "#6b7280", textTransform: "uppercase" }}>Fuel & Battery</h5>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.8rem" }}>
                  <div>Current Fuel: <strong>{selectedVehicle.fuel_level} L</strong></div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <div style={{ flex: 1, height: "8px", background: "#2d2d3d", borderRadius: 99 }}>
                      <div style={{
                        height: "100%", borderRadius: 99,
                        width: `${selectedVehicle.fuel_pct}%`,
                        background: selectedVehicle.fuel_pct < 15 ? "#ef4444" : selectedVehicle.fuel_pct < 40 ? "#f59e0b" : "#10b981",
                      }} />
                    </div>
                    <strong>{selectedVehicle.fuel_pct}%</strong>
                  </div>
                  <div style={{ marginTop: "4px", fontSize: "0.75rem", color: "#9ca3af" }}>
                    Coordinates: {selectedVehicle.latitude.toFixed(4)}, {selectedVehicle.longitude.toFixed(4)}
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
