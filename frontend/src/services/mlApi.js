/**
 * ML API service — Phase 3 AI/ML endpoints.
 * All functions return the response .data payload directly.
 */
import api from './api'

// ── Training ──────────────────────────────────────────────────

export const trainDemandModel   = () => api.post('/ml/demand/train').then(r => r.data)
export const trainDelayModel    = () => api.post('/ml/delay/train').then(r => r.data)
export const trainVehicleRisk   = () => api.post('/ml/vehicle-risk/train').then(r => r.data)

// ── Demand Forecasting ────────────────────────────────────────

/**
 * @param {string} origin_city
 * @param {string} destination_city
 * @param {string} target_date  YYYY-MM-DD
 */
export const predictDemand = (origin_city, destination_city, target_date) =>
  api.post('/ml/demand/predict', { origin_city, destination_city, target_date }).then(r => r.data)

// ── Delay Risk ────────────────────────────────────────────────

/**
 * @param {string} shipment_id
 * @param {string} vehicle_id
 * @param {number} distance_km
 * @param {number} estimated_duration_min
 */
export const predictDelay = (shipment_id, vehicle_id, distance_km, estimated_duration_min) =>
  api.post('/ml/delay/predict', { shipment_id, vehicle_id, distance_km, estimated_duration_min }).then(r => r.data)

// ── Vehicle Risk ──────────────────────────────────────────────

export const predictVehicleRisk = (vehicle_id) =>
  api.post('/ml/vehicle-risk/predict', { vehicle_id }).then(r => r.data)

// ── Anomaly Detection ─────────────────────────────────────────

export const detectAnomalies = (route_id) =>
  api.post('/ml/anomaly/detect', { route_id }).then(r => r.data)

// ── Registry & Logs ───────────────────────────────────────────

export const getModelRegistry  = () => api.get('/ml/models').then(r => r.data)
export const getPredictionsLog = (limit = 50) => api.get('/ml/predictions', { params: { limit } }).then(r => r.data)
