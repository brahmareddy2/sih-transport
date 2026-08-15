/**
 * ReturnCargo — Phase 6
 * Return Cargo Matching and Empty-Kilometer Reduction Dashboard.
 * Features:
 *  - Top KPI cards: Empty-KM reduction, % reduction, fuel savings, net benefit
 *  - Vehicles eligible for return cargo (away from home depot)
 *  - Ranked compatible return cargo matches with 0–100 matching scores
 *  - Compatibility breakdown (Weight, Volume, Refrigeration, Hazmat, Detour)
 *  - One-click Approve & Generate Return Route
 *  - Reject with reason
 *  - Live analytics & auto-refresh
 */
import React, { useState, useEffect, useCallback } from 'react'
import useAuthStore from '../store/authStore'
import {
  getReturnOpportunities,
  searchReturnCargo,
  listReturnCargoMatches,
  getMatchesForVehicle,
  approveReturnMatch,
  rejectReturnMatch,
  getReturnCargoAnalytics,
} from '../services/returnCargoApi'

function ScorePill({ score }) {
  const s = Math.min(100, Math.max(0, score || 0))
  const color = s >= 75 ? '#10b981' : s >= 45 ? '#f59e0b' : '#ef4444'
  const bg = s >= 75 ? '#064e3b' : s >= 45 ? '#451a03' : '#450a0a'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ width: 44, height: 6, borderRadius: 3, background: '#1f2937', overflow: 'hidden' }}>
        <div style={{ width: `${s}%`, height: '100%', background: color }} />
      </div>
      <span style={{ fontSize: '0.8rem', fontWeight: 800, color, background: bg, padding: '2px 6px', borderRadius: 4 }}>
        {s.toFixed(1)}
      </span>
    </div>
  )
}

function StatusBadge({ status }) {
  const styles = {
    approved: { bg: '#064e3b', color: '#34d399', label: 'APPROVED' },
    rejected: { bg: '#450a0a', color: '#f87171', label: 'REJECTED' },
    pending:  { bg: '#1e1b4b', color: '#a5b4fc', label: 'PENDING MATCH' },
  }
  const st = styles[status] || { bg: '#1f2937', color: '#9ca3af', label: status?.toUpperCase() || 'UNKNOWN' }
  return (
    <span style={{
      fontSize: '0.72rem',
      fontWeight: 700,
      padding: '3px 8px',
      borderRadius: 12,
      background: st.bg,
      color: st.color,
      letterSpacing: '0.04em',
    }}>
      {st.label}
    </span>
  )
}

export default function ReturnCargo() {
  const { user } = useAuthStore()

  // ── State ──────────────────────────────────────────────────────────────────
  const [opportunities, setOpportunities]   = useState([])
  const [matches, setMatches]               = useState([])
  const [analytics, setAnalytics]           = useState(null)
  const [selectedVehicle, setSelectedVehicle] = useState(null)
  const [selectedMatch, setSelectedMatch]   = useState(null)
  const [statusFilter, setStatusFilter]     = useState('')
  const [loading, setLoading]               = useState(false)
  const [actionLoading, setActionLoading]   = useState(false)
  const [error, setError]                   = useState(null)
  const [successMsg, setSuccessMsg]         = useState(null)
  const [rejectModalOpen, setRejectModalOpen] = useState(false)
  const [rejectReason, setRejectReason]     = useState('')
  const [rejectingMatchId, setRejectingMatchId] = useState(null)

  // ── Data Fetching ──────────────────────────────────────────────────────────
  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [opps, anRes, matchList] = await Promise.all([
        getReturnOpportunities(),
        getReturnCargoAnalytics(),
        listReturnCargoMatches(statusFilter ? { status: statusFilter } : {}),
      ])
      setOpportunities(opps || [])
      setAnalytics(anRes || null)
      setMatches(matchList?.items || [])
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Failed to load return cargo data')
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    loadData()
    const timer = setInterval(loadData, 20000)
    return () => clearInterval(timer)
  }, [loadData])

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleSelectVehicle = async (veh) => {
    setSelectedVehicle(veh)
    setActionLoading(true)
    setError(null)
    try {
      const res = await getMatchesForVehicle(veh.vehicle_id)
      setMatches(res?.items || [])
      if (res?.items?.length > 0) {
        setSelectedMatch(res.items[0])
      }
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleScanAllVehicles = async () => {
    setActionLoading(true)
    setError(null)
    try {
      const res = await searchReturnCargo({})
      setMatches(res?.items || [])
      await loadData()
      setSuccessMsg(`Scan completed: ${res?.total || 0} return cargo opportunities evaluated.`)
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleApprove = async (matchId) => {
    setActionLoading(true)
    setError(null)
    setSuccessMsg(null)
    try {
      const res = await approveReturnMatch(matchId, 'Approved via Operator Console')
      setSuccessMsg(res.message || 'Return route generated successfully!')
      await loadData()
      if (selectedVehicle) {
        const refreshed = await getMatchesForVehicle(selectedVehicle.vehicle_id)
        setMatches(refreshed?.items || [])
      }
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Approval failed')
    } finally {
      setActionLoading(false)
    }
  }

  const openRejectDialog = (matchId) => {
    setRejectingMatchId(matchId)
    setRejectReason('')
    setRejectModalOpen(true)
  }

  const handleConfirmReject = async () => {
    if (!rejectReason.trim()) return
    setActionLoading(true)
    setRejectModalOpen(false)
    try {
      await rejectReturnMatch(rejectingMatchId, rejectReason)
      setSuccessMsg('Match rejected.')
      await loadData()
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Rejection failed')
    } finally {
      setActionLoading(false)
      setRejectingMatchId(null)
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', paddingBottom: 32 }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.45rem', fontWeight: 800, color: '#f1f5f9' }}>
            🔄 Return Cargo Matching & Empty-KM Reduction
          </h2>
          <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.85rem' }}>
            Intelligent return shipment assignment to eliminate deadhead empty miles and optimize reverse logistics.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={handleScanAllVehicles}
            className="btn btn-primary btn-sm"
            disabled={actionLoading}
            style={{ background: '#4f46e5' }}
          >
            {actionLoading ? '⚡ Scanning...' : '🔍 Scan Fleet for Return Cargo'}
          </button>
          <button
            onClick={loadData}
            className="btn btn-secondary btn-sm"
            disabled={loading}
          >
            {loading ? '⏳' : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {/* Feedback Banners */}
      {error && (
        <div style={{ background: '#450a0a', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: '#fca5a5', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between' }}>
          <span>❌ {error}</span>
          <button onClick={() => setError(null)} style={{ background: 'none', border: 'none', color: '#fca5a5', cursor: 'pointer' }}>✕</button>
        </div>
      )}
      {successMsg && (
        <div style={{ background: '#064e3b', border: '1px solid #10b981', borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: '#6ee7b7', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between' }}>
          <span>✅ {successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} style={{ background: 'none', border: 'none', color: '#6ee7b7', cursor: 'pointer' }}>✕</button>
        </div>
      )}

      {/* ── KPI Metric Cards ──────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 22 }}>
        <div className="card" style={{ padding: '14px 16px', borderTop: '3px solid #10b981' }}>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Empty KM Reduced</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#34d399', marginTop: 4 }}>
            {analytics?.total_empty_km_reduced?.toLocaleString() ?? '0'} <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>km</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#6ee7b7', marginTop: 3 }}>
            🎯 {analytics?.overall_reduction_pct ?? 0}% overall reduction
          </div>
        </div>

        <div className="card" style={{ padding: '14px 16px', borderTop: '3px solid #6366f1' }}>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Fuel Saved</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#a5b4fc', marginTop: 4 }}>
            {analytics?.total_fuel_saved_l?.toLocaleString() ?? '0'} <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>L</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#818cf8', marginTop: 3 }}>
            ⛽ ₹{analytics?.total_fuel_saved_inr?.toLocaleString() ?? '0'} saved
          </div>
        </div>

        <div className="card" style={{ padding: '14px 16px', borderTop: '3px solid #f59e0b' }}>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Net Economic Benefit</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fcd34d', marginTop: 4 }}>
            ₹{analytics?.total_net_benefit_inr?.toLocaleString() ?? '0'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#fbbf24', marginTop: 3 }}>
            💰 Revenue - Detour Costs
          </div>
        </div>

        <div className="card" style={{ padding: '14px 16px', borderTop: '3px solid #3b82f6' }}>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Approved Return Trips</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#93c5fd', marginTop: 4 }}>
            {analytics?.total_approved_matches ?? 0} <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>routes</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#60a5fa', marginTop: 3 }}>
            📦 {analytics?.total_matches_generated ?? 0} matches evaluated
          </div>
        </div>

        <div className="card" style={{ padding: '14px 16px', borderTop: '3px solid #ec4899' }}>
          <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Avg Matching Score</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f472b6', marginTop: 4 }}>
            {analytics?.average_match_score ?? 0} <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>/ 100</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#f472b6', marginTop: 3 }}>
            ⭐ Deterministic business ranking
          </div>
        </div>
      </div>

      {/* ── Main Layout: Vehicles on Left, Matches on Right ──────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 18 }}>

        {/* ── Left Column: Vehicle Return Opportunities ───────────────────── */}
        <div>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: '0.9rem' }}>
                🚛 Eligible Vehicles ({opportunities.length})
              </span>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Away from Base</span>
            </div>
            <div style={{ maxHeight: '68vh', overflowY: 'auto' }}>
              {opportunities.length === 0 ? (
                <div style={{ padding: 24, textAlign: 'center', color: '#64748b', fontSize: '0.85rem' }}>
                  No vehicles currently waiting for return cargo.
                </div>
              ) : (
                opportunities.map(veh => {
                  const isSelected = selectedVehicle?.vehicle_id === veh.vehicle_id
                  return (
                    <div
                      key={veh.vehicle_id}
                      onClick={() => handleSelectVehicle(veh)}
                      style={{
                        padding: '12px 14px',
                        borderBottom: '1px solid #1e293b',
                        cursor: 'pointer',
                        background: isSelected ? '#1e1b4b' : 'transparent',
                        borderLeft: isSelected ? '3px solid #6366f1' : '3px solid transparent',
                        transition: 'background 0.15s',
                      }}
                      onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = '#0f172a' }}
                      onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '0.88rem' }}>
                            {veh.registration_number}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 2 }}>
                            {veh.vehicle_type} · Cap: {veh.capacity_weight_kg}kg
                          </div>
                        </div>
                        {veh.available_matches_count > 0 ? (
                          <span style={{ fontSize: '0.7rem', fontWeight: 700, background: '#064e3b', color: '#34d399', padding: '2px 6px', borderRadius: 10 }}>
                            {veh.available_matches_count} matches
                          </span>
                        ) : (
                          <span style={{ fontSize: '0.7rem', color: '#64748b' }}>0 matches</span>
                        )}
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, fontSize: '0.75rem', color: '#64748b' }}>
                        <span>📍 {veh.current_city} → 🏠 {veh.home_depot_city}</span>
                        <span style={{ fontWeight: 600, color: '#f87171' }}>{veh.potential_empty_km} km empty</span>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>

        {/* ── Right Column: Ranked Return Cargo Matches ───────────────────── */}
        <div>
          {/* Filter Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', gap: 6 }}>
              {[
                { key: '', label: 'All Matches' },
                { key: 'pending', label: 'Pending Approval' },
                { key: 'approved', label: 'Approved Routes' },
                { key: 'rejected', label: 'Rejected' },
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setStatusFilter(tab.key)}
                  style={{
                    padding: '5px 12px',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    borderRadius: 16,
                    border: '1px solid',
                    borderColor: statusFilter === tab.key ? '#6366f1' : '#334155',
                    background: statusFilter === tab.key ? '#312e81' : 'transparent',
                    color: statusFilter === tab.key ? '#a5b4fc' : '#94a3b8',
                    cursor: 'pointer',
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            {selectedVehicle && (
              <button
                onClick={() => { setSelectedVehicle(null); loadData(); }}
                style={{ fontSize: '0.75rem', color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Clear vehicle filter ({selectedVehicle.registration_number}) ✕
              </button>
            )}
          </div>

          {/* Matches List */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: '0.9rem' }}>
                📋 Ranked Return Cargo Recommendations ({matches.length})
              </span>
              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>Sorted by Score & Empty-KM Reduction</span>
            </div>

            <div style={{ maxHeight: '68vh', overflowY: 'auto' }}>
              {matches.length === 0 ? (
                <div style={{ padding: 48, textAlign: 'center', color: '#64748b' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>📦</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>No return cargo matches found for this filter.</div>
                  <div style={{ fontSize: '0.78rem', color: '#475569', marginTop: 4 }}>
                    Click "Scan Fleet for Return Cargo" to search all available return shipments.
                  </div>
                </div>
              ) : (
                matches.map((m, idx) => {
                  const isApproved = m.status === 'approved'
                  const isPending = m.status === 'pending'
                  return (
                    <div
                      key={m.id}
                      style={{
                        padding: '16px 18px',
                        borderBottom: '1px solid #1e293b',
                        background: isApproved ? '#022c22' : idx === 0 && isPending ? '#13112c' : 'transparent',
                        borderLeft: isApproved ? '4px solid #10b981' : idx === 0 && isPending ? '4px solid #6366f1' : '4px solid transparent',
                        transition: 'background 0.15s',
                      }}
                    >
                      {/* Top Row: Shipment info & score */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontWeight: 800, color: '#f1f5f9', fontSize: '0.95rem' }}>
                              📦 {m.shipment_number || 'Shipment'}
                            </span>
                            <span style={{ fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600 }}>
                              {m.origin_city} ➔ {m.destination_city}
                            </span>
                            <StatusBadge status={m.status} />
                            {idx === 0 && isPending && (
                              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#a5b4fc', background: '#312e81', padding: '2px 6px', borderRadius: 4 }}>
                                ⭐ BEST MATCH
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: 4 }}>
                            🚛 Assigned to: <strong>{m.vehicle_registration || 'Vehicle'}</strong> ({m.vehicle_type}) · Cargo: {m.shipment_weight_kg}kg ({m.shipment_goods_type || 'General'})
                          </div>
                        </div>

                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 2 }}>MATCH SCORE</div>
                          <ScorePill score={m.match_score} />
                        </div>
                      </div>

                      {/* Middle: Math & Comparison Metrics Row */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8, margin: '12px 0', background: '#0f172a', borderRadius: 8, padding: '10px 12px' }}>
                        <div>
                          <div style={{ fontSize: '0.68rem', color: '#64748b' }}>DEADHEAD BEFORE</div>
                          <div style={{ fontWeight: 700, color: '#f87171', fontSize: '0.85rem' }}>{m.empty_km_before} km</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.68rem', color: '#64748b' }}>DEADHEAD AFTER</div>
                          <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '0.85rem' }}>{m.empty_km_after} km</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.68rem', color: '#64748b' }}>EMPTY KM SAVED</div>
                          <div style={{ fontWeight: 800, color: '#34d399', fontSize: '0.85rem' }}>
                            -{m.empty_km_reduced} km ({m.empty_km_reduction_pct}%)
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.68rem', color: '#64748b' }}>TRIP DETOUR</div>
                          <div style={{ fontWeight: 700, color: '#cbd5e1', fontSize: '0.85rem' }}>+{m.detour_distance_km} km</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.68rem', color: '#64748b' }}>NET BENEFIT</div>
                          <div style={{ fontWeight: 800, color: '#fcd34d', fontSize: '0.85rem' }}>+₹{m.net_benefit_inr}</div>
                        </div>
                      </div>

                      {/* Compatibility Checklist Badges */}
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12, fontSize: '0.72rem' }}>
                        <span style={{ background: '#1e293b', color: '#94a3b8', padding: '2px 8px', borderRadius: 4 }}>
                          ⚖️ Weight: {m.shipment_weight_kg}kg / {m.vehicle_capacity_weight_kg}kg
                        </span>
                        <span style={{ background: '#1e293b', color: '#94a3b8', padding: '2px 8px', borderRadius: 4 }}>
                          ⛽ Fuel Added: +{m.additional_fuel_l}L (₹{m.additional_fuel_cost_inr})
                        </span>
                        <span style={{ background: '#1e293b', color: '#94a3b8', padding: '2px 8px', borderRadius: 4 }}>
                          💰 Freight Revenue: ₹{m.estimated_revenue_inr}
                        </span>
                        {m.is_refrigerated && (
                          <span style={{ background: '#0284c7', color: '#e0f2fe', padding: '2px 8px', borderRadius: 4 }}>
                            ❄️ Refrigerated
                          </span>
                        )}
                        {m.is_hazardous && (
                          <span style={{ background: '#b45309', color: '#fef3c7', padding: '2px 8px', borderRadius: 4 }}>
                            ☣️ Hazmat
                          </span>
                        )}
                      </div>

                      {/* Action Buttons */}
                      {isPending && (
                        <div style={{ display: 'flex', gap: 10 }}>
                          <button
                            onClick={() => handleApprove(m.id)}
                            className="btn btn-primary btn-sm"
                            disabled={actionLoading}
                            style={{ background: '#4f46e5', fontWeight: 700 }}
                          >
                            {actionLoading ? '⏳ Generating Route...' : '⚡ Approve & Generate Return Route'}
                          </button>
                          <button
                            onClick={() => openRejectDialog(m.id)}
                            className="btn btn-secondary btn-sm"
                            disabled={actionLoading}
                            style={{ color: '#f87171' }}
                          >
                            ✕ Reject
                          </button>
                        </div>
                      )}

                      {isApproved && (
                        <div style={{ fontSize: '0.8rem', color: '#34d399', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span>✅ Return route activated</span>
                          {m.return_route_id && (
                            <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
                              (Route ID: {m.return_route_id.slice(0, 8)}...)
                            </span>
                          )}
                        </div>
                      )}

                      {m.status === 'rejected' && m.rejection_reason && (
                        <div style={{ fontSize: '0.78rem', color: '#f87171' }}>
                          Reason: {m.rejection_reason}
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Rejection Dialog Modal ────────────────────────────────────────── */}
      {rejectModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.75)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 999,
        }}>
          <div className="card" style={{ maxWidth: 450, width: '100%', padding: 24 }}>
            <h3 style={{ margin: '0 0 12px', color: '#f1f5f9' }}>Reject Return Cargo Match</h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: '0 0 16px' }}>
              Please specify the reason for rejecting this return shipment assignment:
            </p>
            <textarea
              value={rejectReason}
              onChange={e => setRejectReason(e.target.value)}
              placeholder="e.g. Driver rest period required, shipper schedule mismatch..."
              rows={3}
              style={{
                width: '100%',
                padding: '8px 12px',
                background: '#1e293b',
                border: '1px solid var(--color-border)',
                borderRadius: 6,
                color: '#f1f5f9',
                fontSize: '0.85rem',
                marginBottom: 16,
                boxSizing: 'border-box',
              }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                onClick={() => setRejectModalOpen(false)}
                className="btn btn-secondary btn-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReject}
                className="btn btn-primary btn-sm"
                disabled={!rejectReason.trim() || actionLoading}
                style={{ background: '#ef4444' }}
              >
                {actionLoading ? 'Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
