/**
 * Analytics, What-If Simulation, and Notifications API Service — Phase 7
 */
import api from './api'

// ── Analytics ────────────────────────────────────────────────────────────────

export const getDashboardOverview = () =>
  api.get('/analytics/dashboard').then(r => r.data)

export const getCostTrends = () =>
  api.get('/analytics/cost-trends').then(r => r.data)

export const getActualVsPredicted = () =>
  api.get('/analytics/actual-vs-predicted').then(r => r.data)

// ── What-If Simulation ───────────────────────────────────────────────────────

export const getWhatIfScenarios = () =>
  api.get('/what-if/scenarios').then(r => r.data)

export const runWhatIfSimulation = (data) =>
  api.post('/what-if/simulate', data).then(r => r.data)

// ── Notifications ─────────────────────────────────────────────────────────────

export const listNotifications = (params = {}) =>
  api.get('/notifications', { params }).then(r => r.data)

export const getUnreadNotificationCount = () =>
  api.get('/notifications/unread-count').then(r => r.data)

export const markNotificationRead = (notificationId) =>
  api.post(`/notifications/${notificationId}/read`).then(r => r.data)

export const markAllNotificationsRead = () =>
  api.post('/notifications/mark-all-read').then(r => r.data)

// ── System Diagnostics ───────────────────────────────────────────────────────

export const getSystemStats = () =>
  api.get('/admin/system-stats').then(r => r.data)
