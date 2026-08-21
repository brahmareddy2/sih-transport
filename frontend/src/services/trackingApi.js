/**
 * Tracking API service — Phase 4 Live Fleet Tracking endpoints.
 * Provides REST calls and WebSocket connection establishment.
 */
import api from './api'

// ── REST API calls ──────────────────────────────────────────

export const getVehiclesState = () =>
  api.get('/tracking/vehicles').then(r => r.data)

export const getVehicleState = (vehicleId) =>
  api.get(`/tracking/vehicles/${vehicleId}`).then(r => r.data)

export const getVehicleHistory = (vehicleId, limit = 100) =>
  api.get(`/tracking/vehicles/${vehicleId}/history`, { params: { limit } }).then(r => r.data)

export const getTripHistory = (tripId, limit = 500) =>
  api.get(`/tracking/trips/${tripId}/location-history`, { params: { limit } }).then(r => r.data)

// ── Simulation Controls ──────────────────────────────────────

export const startSimulation = (vehicleId, routeId = null) =>
  api.post('/tracking/simulate/start', { vehicle_id: vehicleId, route_id: routeId, action: 'start' }).then(r => r.data)

export const pauseSimulation = (vehicleId) =>
  api.post('/tracking/simulate/pause', { vehicle_id: vehicleId, action: 'pause' }).then(r => r.data)

export const resumeSimulation = (vehicleId) =>
  api.post('/tracking/simulate/resume', { vehicle_id: vehicleId, action: 'resume' }).then(r => r.data)

export const stopSimulation = (vehicleId) =>
  api.post('/tracking/simulate/stop', { vehicle_id: vehicleId, action: 'stop' }).then(r => r.data)

// ── WebSocket Helper ──────────────────────────────────────────

/**
 * Establish a real-time WebSocket connection to receive automatic telemetry updates.
 * Includes auto-reconnect fallback mechanism.
 * 
 * @param {string} token - JWT Access Token
 * @param {function} onMessage - Callback for parsed message payloads
 * @param {function} onStatusChange - Callback indicating connection status ('CONNECTED' | 'RECONNECTING' | 'OFFLINE')
 */
export function connectTrackingWs(token, onMessage, onStatusChange) {
  const getSmartTrackingBaseUrl = () => {
    const envVal = import.meta.env.VITE_API_BASE_URL || ''
    if (envVal) return envVal.replace(/\/+$/, '')
    const host = window.location.hostname
    if (
      host === 'localhost' ||
      host === '127.0.0.1' ||
      host === '0.0.0.0' ||
      host.endsWith('.loca.lt') ||
      host.endsWith('.ngrok.io') ||
      host.endsWith('.ngrok-free.app') ||
      host.endsWith('.lhr.life') ||
      host.includes('tunnel')
    ) {
      return ''
    }
    return 'http://localhost:8000'
  }

  const BASE_URL = getSmartTrackingBaseUrl()
  
  // Format WS URL
  let wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  let wsUrl = ''
  if (BASE_URL.startsWith('http')) {
    wsUrl = BASE_URL.replace(/^http/, 'ws') + '/api/v1/tracking/ws?token=' + encodeURIComponent(token)
  } else {
    // Relative fallback
    wsUrl = `${wsProto}//${window.location.host}/api/v1/tracking/ws?token=${encodeURIComponent(token)}`
  }

  let ws = null
  let reconnectTimer = null
  let isClosedIntentionally = false

  function connect() {
    if (isClosedIntentionally) return

    onStatusChange('RECONNECTING')
    loggerInfo('Establishing WebSocket telemetry stream...')

    try {
      ws = new WebSocket(wsUrl)
    } catch (err) {
      loggerError('WebSocket instantiation failed:', err)
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      onStatusChange('CONNECTED')
      loggerInfo('WebSocket telemetry stream active.')
    }

    ws.onmessage = (event) => {
      try {
        if (event.data === 'pong') return
        const payload = JSON.parse(event.data)
        onMessage(payload)
      } catch (err) {
        loggerError('Failed parsing WebSocket message:', err)
      }
    }

    ws.onclose = (event) => {
      if (isClosedIntentionally) {
        onStatusChange('OFFLINE')
        return
      }
      loggerError('WebSocket disconnected. Status code:', event.code)
      scheduleReconnect()
    }

    ws.onerror = (err) => {
      loggerError('WebSocket stream error occurred:', err)
    }
  }

  function scheduleReconnect() {
    onStatusChange('OFFLINE')
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      connect()
    }, 4000) // reconnect retry interval (4 seconds)
  }

  function loggerInfo(msg) {
    console.log(`%c[WS INFO] ${msg}`, 'color: #818cf8; font-weight: bold')
  }

  function loggerError(msg, extra = '') {
    console.error(`[WS ERROR] ${msg}`, extra)
  }

  // Trigger initial connection
  connect()

  // Return destructor
  return {
    disconnect: () => {
      isClosedIntentionally = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      if (ws) {
        try {
          ws.close()
        } catch {}
      }
      onStatusChange('OFFLINE')
    }
  }
}
