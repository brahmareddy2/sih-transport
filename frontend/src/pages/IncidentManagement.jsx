/**
 * IncidentManagement — Phase 5
 * Full incident detection, recovery planning, and execution dashboard.
 * Features:
 *  - Active incidents table with severity badges
 *  - SIH demo: Simulate incident (vehicle + type selector)
 *  - Recovery plan generator with ranked comparison table
 *  - One-click approve & execute recovery
 *  - Resolve incident
 *  - Auto-refresh every 15s
 */
import React, { useState, useEffect, useCallback } from 'react'
import useAuthStore from '../store/authStore'
import {
  listIncidents,
  getIncident,
  simulateIncident,
  generateRecovery,
  listRecoveryPlans,
  approveRecoveryPlan,
  resolveIncident,
} from '../services/incidentApi'
import api from '../services/api'

// ── Severity helpers ──────────────────────────────────────────────────────────
const SEVERITY_COLOR = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#f59e0b',
  low:      '#10b981',
}
const STATUS_COLOR = {
  open:         '#ef4444',
  acknowledged: '#f97316',
  in_recovery:  '#6366f1',
  resolved:     '#10b981',
  closed:       '#6b7280',
}
const TYPE_ICON = {
  breakdown:          '🔴',
  tyre_puncture:      '🔧',
  road_closure:       '🚧',
  traffic_jam:        '🚦',
  low_fuel:           '⛽',
  driver_unavailable: '👤',
  accident:           '💥',
  other:              '⚠️',
}
const PLAN_TYPE_LABEL = {
  replace_vehicle:            '🚛 Replace Vehicle',
  replace_vehicle_and_driver: '🚛👤 Replace Vehicle + Driver',
  reroute:                    '🗺️ Reroute',
  fuel_stop:                  '⛽ Fuel Stop',
  delay_only:                 '⏳ Delay Only',
}

function Badge({ text, color, bg }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: '12px',
      fontSize: '0.72rem',
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      color: color || '#fff',
      background: bg || '#374151',
    }}>{text}</span>
  )
}

function ScoreBar({ score }) {
  const pct = Math.min(100, Math.max(0, score || 0))
  const color = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#ef4444'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 8, borderRadius: 4, background: '#1f2937', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 0.4s' }} />
      </div>
      <span style={{ fontSize: '0.78rem', fontWeight: 700, color, minWidth: 32 }}>{pct}</span>
    </div>
  )
}

export default function IncidentManagement() {
  const { accessToken } = useAuthStore()

  // ── State ──────────────────────────────────────────────────────────────────
  const [incidents, setIncidents]           = useState([])
  const [loading, setLoading]               = useState(false)
  const [selectedIncident, setSelected]     = useState(null)
  const [recoveryData, setRecoveryData]     = useState(null)
  const [execResult, setExecResult]         = useState(null)
  const [error, setError]                   = useState(null)
  const [actionLoading, setActionLoading]   = useState(false)
  const [tab, setTab]                       = useState('active') // active | simulate
  const [filterStatus, setFilterStatus]     = useState('')

  // Simulate form state
  const [vehicles, setVehicles]             = useState([])
  const [simVehicleId, setSimVehicleId]     = useState('')
  const [simIncidentType, setSimIncidentType] = useState('breakdown')
  const [simDescription, setSimDescription] = useState('')
  const [simResult, setSimResult]           = useState(null)

  // ── Load data ──────────────────────────────────────────────────────────────
  const loadIncidents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {}
      if (filterStatus) params.status = filterStatus
      const data = await listIncidents(params)
      setIncidents(data.items || [])
    } catch (e) {
      setError('Failed to load incidents: ' + (e.response?.data?.detail || e.message))
    } finally {
      setLoading(false)
    }
  }, [filterStatus])

  const loadVehicles = useCallback(async () => {
    try {
      const res = await api.get('/vehicles?limit=100')
      setVehicles(res.data?.items || res.data || [])
    } catch (e) {
      console.error('Failed to load vehicles', e)
    }
  }, [])

  useEffect(() => {
    loadIncidents()
    loadVehicles()
    const interval = setInterval(loadIncidents, 15000)
    return () => clearInterval(interval)
  }, [loadIncidents, loadVehicles])

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleSelectIncident = async (inc) => {
    setSelected(inc)
    setRecoveryData(null)
    setExecResult(null)
    // Load existing plans
    try {
      const plans = await listRecoveryPlans(inc.id)
      if (plans.plans?.length > 0) setRecoveryData(plans)
    } catch {/* none yet */}
  }

  const handleGenerateRecovery = async () => {
    if (!selectedIncident) return
    setActionLoading(true)
    setError(null)
    try {
      const data = await generateRecovery(selectedIncident.id)
      setRecoveryData(data)
    } catch (e) {
      setError('Recovery generation failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setActionLoading(false)
    }
  }

  const handleApprove = async (planId) => {
    if (!selectedIncident) return
    setActionLoading(true)
    setError(null)
    try {
      const result = await approveRecoveryPlan(selectedIncident.id, planId)
      setExecResult(result)
      await loadIncidents()
      // Refresh selected
      const updated = await getIncident(selectedIncident.id)
      setSelected(updated)
    } catch (e) {
      setError('Approval failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setActionLoading(false)
    }
  }

  const handleResolve = async () => {
    if (!selectedIncident) return
    setActionLoading(true)
    try {
      const updated = await resolveIncident(selectedIncident.id, 'Resolved by operator')
      setSelected(updated)
      await loadIncidents()
      setRecoveryData(null)
      setExecResult(null)
    } catch (e) {
      setError('Resolve failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setActionLoading(false)
    }
  }

  const handleSimulate = async (e) => {
    e.preventDefault()
    if (!simVehicleId) { setError('Select a vehicle first'); return }
    setActionLoading(true)
    setError(null)
    setSimResult(null)
    try {
      const inc = await simulateIncident({
        vehicle_id: simVehicleId,
        incident_type: simIncidentType,
        description: simDescription || undefined,
      })
      setSimResult(inc)
      setTab('active')
      await loadIncidents()
      setSelected(inc)
    } catch (e) {
      setError('Simulation failed: ' + (e.response?.data?.detail || e.message))
    } finally {
      setActionLoading(false)
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', padding: '0 4px' }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, color: '#f1f5f9' }}>
            🚨 Incident Management & Recovery
          </h2>
          <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.85rem' }}>
            Detect, analyze, and recover from fleet incidents in real time
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={loadIncidents}
            className="btn btn-secondary btn-sm"
            disabled={loading}
          >
            {loading ? '⏳' : '🔄'} Refresh
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: '#450a0a', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: '#fca5a5', fontSize: '0.85rem' }}>
          ❌ {error}
          <button onClick={() => setError(null)} style={{ float: 'right', background: 'none', border: 'none', color: '#f87171', cursor: 'pointer' }}>✕</button>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid var(--color-border)' }}>
        {[
          { key: 'active', label: `📋 Active Incidents (${incidents.filter(i => i.status !== 'resolved' && i.status !== 'closed').length})` },
          { key: 'all', label: '📚 All Incidents' },
          { key: 'simulate', label: '🧪 Simulate Incident' },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); if (t.key !== 'simulate') { setFilterStatus(t.key === 'active' ? '' : ''); } }}
            style={{
              padding: '8px 16px',
              background: 'none',
              border: 'none',
              borderBottom: tab === t.key ? '2px solid #6366f1' : '2px solid transparent',
              color: tab === t.key ? '#a5b4fc' : '#64748b',
              fontWeight: tab === t.key ? 700 : 400,
              cursor: 'pointer',
              fontSize: '0.88rem',
              transition: 'all 0.15s',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Simulate Tab ─────────────────────────────────────────────────── */}
      {tab === 'simulate' && (
        <div className="card" style={{ maxWidth: 600 }}>
          <h3 style={{ margin: '0 0 20px', color: '#f1f5f9' }}>🧪 SIH Demo — Simulate Incident</h3>
          <form onSubmit={handleSimulate}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 6, color: '#94a3b8', fontSize: '0.82rem', fontWeight: 600 }}>
                INCIDENT TYPE
              </label>
              <select
                value={simIncidentType}
                onChange={e => setSimIncidentType(e.target.value)}
                style={{ width: '100%', padding: '10px 12px', background: '#1e293b', border: '1px solid var(--color-border)', borderRadius: 8, color: '#f1f5f9', fontSize: '0.9rem' }}
              >
                <option value="breakdown">🔴 Vehicle Breakdown</option>
                <option value="tyre_puncture">🔧 Tyre Puncture</option>
                <option value="road_closure">🚧 Road Closure</option>
                <option value="traffic_jam">🚦 Severe Traffic</option>
                <option value="low_fuel">⛽ Low Fuel</option>
                <option value="driver_unavailable">👤 Driver Unavailable</option>
              </select>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 6, color: '#94a3b8', fontSize: '0.82rem', fontWeight: 600 }}>
                SELECT VEHICLE
              </label>
              <select
                value={simVehicleId}
                onChange={e => setSimVehicleId(e.target.value)}
                style={{ width: '100%', padding: '10px 12px', background: '#1e293b', border: '1px solid var(--color-border)', borderRadius: 8, color: '#f1f5f9', fontSize: '0.9rem' }}
              >
                <option value="">-- Select a vehicle --</option>
                {vehicles.map(v => (
                  <option key={v.id} value={v.id}>
                    {v.registration_number} — {v.vehicle_type} ({v.status})
                  </option>
                ))}
              </select>
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', marginBottom: 6, color: '#94a3b8', fontSize: '0.82rem', fontWeight: 600 }}>
                DESCRIPTION (optional)
              </label>
              <textarea
                value={simDescription}
                onChange={e => setSimDescription(e.target.value)}
                placeholder="e.g. Engine failure detected on NH-48 near Pune"
                rows={3}
                style={{ width: '100%', padding: '10px 12px', background: '#1e293b', border: '1px solid var(--color-border)', borderRadius: 8, color: '#f1f5f9', fontSize: '0.9rem', resize: 'vertical', boxSizing: 'border-box' }}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={actionLoading || !simVehicleId}
            >
              {actionLoading ? '⏳ Simulating...' : '🚨 SIMULATE INCIDENT'}
            </button>
          </form>
          {simResult && (
            <div style={{ marginTop: 20, padding: 16, background: '#0f2d1c', border: '1px solid #16a34a', borderRadius: 8 }}>
              <p style={{ margin: 0, color: '#4ade80', fontWeight: 700 }}>
                ✅ Incident created: {simResult.incident_type?.replace('_', ' ').toUpperCase()}
              </p>
              <p style={{ margin: '4px 0 0', color: '#86efac', fontSize: '0.83rem' }}>
                Vehicle: {simResult.vehicle_registration} | Severity: {simResult.severity?.toUpperCase()} | ID: {simResult.id?.slice(0, 8)}...
              </p>
              <p style={{ margin: '4px 0 0', color: '#86efac', fontSize: '0.83rem' }}>
                Switching to Active Incidents tab — select the new incident to generate recovery plans.
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── Active / All Incidents Tab ────────────────────────────────────── */}
      {(tab === 'active' || tab === 'all') && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

          {/* ── Left: Incidents Table ──────────────────────────────────────── */}
          <div>
            {/* Filter */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              {['', 'open', 'acknowledged', 'in_recovery', 'resolved'].map(s => (
                <button
                  key={s}
                  onClick={() => setFilterStatus(s)}
                  style={{
                    padding: '4px 10px',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    borderRadius: 20,
                    border: '1px solid',
                    borderColor: filterStatus === s ? '#6366f1' : '#334155',
                    background: filterStatus === s ? '#312e81' : 'transparent',
                    color: filterStatus === s ? '#a5b4fc' : '#64748b',
                    cursor: 'pointer',
                  }}
                >
                  {s || 'ALL'}
                </button>
              ))}
            </div>

            {/* Table */}
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: '0.92rem' }}>
                  📋 Incidents ({incidents.length})
                </span>
              </div>
              <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
                {incidents.length === 0 ? (
                  <div style={{ padding: 32, textAlign: 'center', color: '#475569' }}>
                    {loading ? '⏳ Loading...' : '✅ No incidents found'}
                  </div>
                ) : (
                  incidents.map(inc => (
                    <div
                      key={inc.id}
                      onClick={() => handleSelectIncident(inc)}
                      style={{
                        padding: '12px 16px',
                        borderBottom: '1px solid #1e293b',
                        cursor: 'pointer',
                        background: selectedIncident?.id === inc.id ? '#1e1b4b' : 'transparent',
                        transition: 'background 0.15s',
                      }}
                      onMouseEnter={e => { if (selectedIncident?.id !== inc.id) e.currentTarget.style.background = '#0f172a' }}
                      onMouseLeave={e => { if (selectedIncident?.id !== inc.id) e.currentTarget.style.background = 'transparent' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span style={{ fontSize: '1.1rem' }}>{TYPE_ICON[inc.incident_type] || '⚠️'}</span>
                          <span style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '0.9rem' }}>
                            {inc.incident_type?.replace(/_/g, ' ').toUpperCase()}
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <Badge
                            text={inc.severity}
                            bg={SEVERITY_COLOR[inc.severity] + '33'}
                            color={SEVERITY_COLOR[inc.severity]}
                          />
                          <Badge
                            text={inc.status?.replace('_', ' ')}
                            bg={STATUS_COLOR[inc.status] + '33'}
                            color={STATUS_COLOR[inc.status]}
                          />
                        </div>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                        🚛 {inc.vehicle_registration || 'Unknown Vehicle'}
                        {inc.city && ` · 📍 ${inc.city}`}
                        {inc.affected_shipment_count > 0 && ` · 📦 ${inc.affected_shipment_count} shipments`}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: 2 }}>
                        {new Date(inc.reported_at).toLocaleString()}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* ── Right: Incident Detail + Recovery ─────────────────────────── */}
          <div>
            {!selectedIncident ? (
              <div className="card" style={{ textAlign: 'center', padding: 48, color: '#475569' }}>
                <div style={{ fontSize: '3rem', marginBottom: 12 }}>🔍</div>
                <p>Select an incident to view details and generate recovery plans</p>
              </div>
            ) : (
              <>
                {/* Incident Info Card */}
                <div className="card" style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                    <h3 style={{ margin: 0, color: '#f1f5f9', fontSize: '1rem' }}>
                      {TYPE_ICON[selectedIncident.incident_type] || '⚠️'} Incident Detail
                    </h3>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <Badge
                        text={selectedIncident.severity}
                        bg={SEVERITY_COLOR[selectedIncident.severity]}
                        color='#fff'
                      />
                      <Badge
                        text={selectedIncident.status?.replace('_', ' ')}
                        bg={STATUS_COLOR[selectedIncident.status]}
                        color='#fff'
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', fontSize: '0.83rem' }}>
                    {[
                      ['Type', selectedIncident.incident_type?.replace(/_/g, ' ').toUpperCase()],
                      ['Vehicle', selectedIncident.vehicle_registration || '—'],
                      ['Vehicle Type', selectedIncident.vehicle_type || '—'],
                      ['Driver', selectedIncident.driver_name || '—'],
                      ['Route', selectedIncident.route_number || '—'],
                      ['City', selectedIncident.city || '—'],
                      ['Affected Shipments', selectedIncident.affected_shipment_count ?? '—'],
                      ['Recovery Plans', selectedIncident.recovery_plans_count ?? '—'],
                    ].map(([label, val]) => (
                      <div key={label}>
                        <span style={{ color: '#64748b', fontSize: '0.76rem', display: 'block', marginBottom: 2 }}>{label}</span>
                        <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{val}</span>
                      </div>
                    ))}
                  </div>

                  {selectedIncident.description && (
                    <div style={{ marginTop: 12, padding: '8px 12px', background: '#0f172a', borderRadius: 6, color: '#94a3b8', fontSize: '0.82rem' }}>
                      {selectedIncident.description}
                    </div>
                  )}

                  {/* Action buttons */}
                  <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                    {!['resolved', 'closed'].includes(selectedIncident.status) && (
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={handleGenerateRecovery}
                        disabled={actionLoading}
                        style={{ flex: 1 }}
                      >
                        {actionLoading ? '⏳' : '⚡'} Generate Recovery Plans
                      </button>
                    )}
                    {!['resolved', 'closed'].includes(selectedIncident.status) && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={handleResolve}
                        disabled={actionLoading}
                      >
                        ✅ Resolve
                      </button>
                    )}
                  </div>
                </div>

                {/* Execution Result */}
                {execResult && (
                  <div style={{ marginBottom: 16, padding: 16, background: '#0f2d1c', border: '1px solid #16a34a', borderRadius: 8 }}>
                    <p style={{ margin: 0, fontWeight: 700, color: '#4ade80', fontSize: '0.95rem' }}>
                      ✅ Recovery Executed Successfully
                    </p>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px 16px', marginTop: 10, fontSize: '0.82rem', color: '#86efac' }}>
                      <span>New Vehicle: <strong>{execResult.new_vehicle_registration || 'Same/Reroute'}</strong></span>
                      <span>Shipments Updated: <strong>{execResult.shipments_updated}</strong></span>
                      <span>Extra Delay: <strong>{execResult.estimated_delay_min} min</strong></span>
                      <span>Additional Cost: <strong>₹{execResult.additional_cost_inr?.toFixed(0)}</strong></span>
                    </div>
                    <p style={{ margin: '8px 0 0', color: '#4ade80', fontSize: '0.82rem' }}>{execResult.message}</p>
                  </div>
                )}

                {/* Recovery Plans */}
                {recoveryData && recoveryData.plans?.length > 0 && (
                  <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border)' }}>
                      <h3 style={{ margin: 0, color: '#f1f5f9', fontSize: '0.95rem' }}>
                        ⚡ Recovery Options
                      </h3>
                      <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: '0.78rem' }}>
                        Ranked by recovery score — higher = better option
                      </p>
                    </div>
                    <div>
                      {recoveryData.plans.map((plan, idx) => {
                        const isRecommended = plan.id === recoveryData.recommended_plan_id
                        const isApproved = plan.is_approved
                        return (
                          <div
                            key={plan.id}
                            style={{
                              padding: '14px 16px',
                              borderBottom: '1px solid #1e293b',
                              background: isRecommended ? '#1e1b4b' : isApproved ? '#0f2d1c' : 'transparent',
                              borderLeft: isRecommended ? '3px solid #6366f1' : isApproved ? '3px solid #16a34a' : '3px solid transparent',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                              <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                  <span style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '0.9rem' }}>
                                    {PLAN_TYPE_LABEL[plan.plan_type] || plan.plan_type || 'Recovery Option'}
                                  </span>
                                  {isRecommended && <Badge text="⭐ RECOMMENDED" bg="#312e81" color="#a5b4fc" />}
                                  {isApproved && <Badge text="✅ APPROVED" bg="#14532d" color="#4ade80" />}
                                </div>
                                {plan.alternative_vehicle_registration && (
                                  <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: 3 }}>
                                    🚛 {plan.alternative_vehicle_registration} ({plan.alternative_vehicle_type})
                                    {plan.alternative_driver_name && ` · 👤 ${plan.alternative_driver_name}`}
                                  </div>
                                )}
                              </div>
                              <div style={{ textAlign: 'right', minWidth: 90 }}>
                                <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 3 }}>SCORE</div>
                                <ScoreBar score={plan.recovery_score} />
                              </div>
                            </div>

                            {/* Metrics row */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginBottom: 10 }}>
                              {[
                                ['⏱️ Delay', `+${plan.estimated_delay_min ?? 0} min`],
                                ['📍 Extra km', `+${plan.additional_distance_km?.toFixed(0) ?? 0} km`],
                                ['💰 Cost Impact', `₹${plan.cost_impact_inr?.toFixed(0) ?? 0}`],
                                ['🔧 Action', plan.action_type?.replace('_', ' ') || '—'],
                              ].map(([label, val]) => (
                                <div key={label} style={{ background: '#0f172a', borderRadius: 6, padding: '6px 8px', textAlign: 'center' }}>
                                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>{label}</div>
                                  <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '0.82rem' }}>{val}</div>
                                </div>
                              ))}
                            </div>

                            {/* Description */}
                            {plan.plan_description && (
                              <p style={{ margin: '0 0 10px', fontSize: '0.78rem', color: '#94a3b8', lineHeight: 1.5 }}>
                                {plan.plan_description}
                              </p>
                            )}

                            {/* Approve button */}
                            {!isApproved && !['resolved', 'closed'].includes(selectedIncident.status) && (
                              <button
                                className="btn btn-primary btn-sm"
                                onClick={() => handleApprove(plan.id)}
                                disabled={actionLoading}
                                style={{
                                  background: isRecommended ? '#4f46e5' : '#1e293b',
                                  borderColor: isRecommended ? '#4f46e5' : '#334155',
                                }}
                              >
                                {actionLoading ? '⏳ Executing...' : '✅ Approve & Execute This Plan'}
                              </button>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* No plans yet */}
                {(!recoveryData || recoveryData.plans?.length === 0) &&
                  !['resolved', 'closed'].includes(selectedIncident.status) && (
                  <div className="card" style={{ textAlign: 'center', padding: 32, color: '#475569' }}>
                    <div style={{ fontSize: '2rem', marginBottom: 8 }}>⚡</div>
                    <p style={{ margin: 0 }}>Click "Generate Recovery Plans" to find the best resolution options</p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
