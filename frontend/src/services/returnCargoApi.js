/**
 * Return Cargo & Empty-Kilometer Reduction API Service — Phase 6
 * REST client for return cargo matching, ranking, approval, and savings analytics.
 */
import api from './api'

// ── Search & Opportunities ───────────────────────────────────────────────────

export const getReturnOpportunities = () =>
  api.get('/return-cargo/opportunities').then(r => r.data)

export const searchReturnCargo = (data = {}) =>
  api.post('/return-cargo', data).then(r => r.data)

export const listReturnCargoMatches = (params = {}) =>
  api.get('/return-cargo', { params }).then(r => r.data)

export const getReturnCargoMatch = (matchId) =>
  api.get(`/return-cargo/${matchId}`).then(r => r.data)

export const getMatchesForVehicle = (vehicleId, params = {}) =>
  api.get(`/return-cargo/matches/${vehicleId}`, { params }).then(r => r.data)

// ── Actions ──────────────────────────────────────────────────────────────────

export const refreshReturnMatch = (matchId) =>
  api.post(`/return-cargo/${matchId}/match`).then(r => r.data)

export const approveReturnMatch = (matchId, notes = '') =>
  api.post(`/return-cargo/matches/${matchId}/approve`, { notes }).then(r => r.data)

export const rejectReturnMatch = (matchId, rejectionReason) =>
  api.post(`/return-cargo/matches/${matchId}/reject`, { rejection_reason: rejectionReason }).then(r => r.data)

// ── Analytics ────────────────────────────────────────────────────────────────

export const getReturnCargoAnalytics = () =>
  api.get('/return-cargo/analytics').then(r => r.data)
