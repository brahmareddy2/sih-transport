/**
 * Incident Management API Service — Phase 5
 * REST client for incident detection, recovery planning, and execution.
 */
import api from './api'

// ── Incident CRUD ────────────────────────────────────────────────────────────

export const listIncidents = (params = {}) =>
  api.get('/incidents', { params }).then(r => r.data)

export const getIncident = (incidentId) =>
  api.get(`/incidents/${incidentId}`).then(r => r.data)

export const createIncident = (data) =>
  api.post('/incidents', data).then(r => r.data)

// ── SIH Demo: Simulate an incident ──────────────────────────────────────────

export const simulateIncident = (data) =>
  api.post('/incidents/simulate', data).then(r => r.data)

// ── Recovery Planning ────────────────────────────────────────────────────────

export const generateRecovery = (incidentId) =>
  api.post(`/incidents/${incidentId}/recover`).then(r => r.data)

export const listRecoveryPlans = (incidentId) =>
  api.get(`/incidents/${incidentId}/recovery-plans`).then(r => r.data)

export const approveRecoveryPlan = (incidentId, planId, notes = '') =>
  api.post(`/incidents/${incidentId}/recovery-plans/${planId}/approve`, { notes }).then(r => r.data)

// ── Resolve ──────────────────────────────────────────────────────────────────

export const resolveIncident = (incidentId, resolutionNotes = '') =>
  api.post(`/incidents/${incidentId}/resolve`, { resolution_notes: resolutionNotes }).then(r => r.data)
