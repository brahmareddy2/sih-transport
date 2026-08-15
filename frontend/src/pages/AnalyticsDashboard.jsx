/**
 * AnalyticsDashboard — Phase 7
 * Executive Logistics Intelligence, Cost & Performance Trends,
 * and Actual vs ML-Predicted Accuracy Dashboard.
 */
import React, { useState, useEffect } from 'react'
import {
  getDashboardOverview,
  getCostTrends,
  getActualVsPredicted,
} from '../services/analyticsApi'

export default function AnalyticsDashboard() {
  const [overview, setOverview] = useState(null)
  const [costTrends, setCostTrends] = useState([])
  const [actVsPred, setActVsPred] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [ov, ct, avp] = await Promise.all([
          getDashboardOverview(),
          getCostTrends(),
          getActualVsPredicted(),
        ])
        setOverview(ov)
        setCostTrends(ct?.items || [])
        setActVsPred(avp)
      } catch (e) {
        setError(e.response?.data?.detail || e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>⏳ Loading Analytics Intelligence...</div>
  }

  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', paddingBottom: 32 }}>

      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ margin: 0, fontSize: '1.45rem', fontWeight: 800, color: '#f1f5f9' }}>
          📈 Enterprise Logistics Analytics & AI Evaluation
        </h2>
        <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.85rem' }}>
          Real-time PostgreSQL telemetry, historical operational trends, and ML prediction accuracy validation.
        </p>
      </div>

      {error && (
        <div style={{ background: '#450a0a', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: '#fca5a5', fontSize: '0.85rem' }}>
          ❌ {error}
        </div>
      )}

      {/* ── Top Key Metric Tiles ──────────────────────────────────────────── */}
      {overview && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 22 }}>
          <div className="card" style={{ padding: '14px 16px', borderTop: '3px solid #6366f1' }}>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Total Logistics Cost</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#a5b4fc', marginTop: 4 }}>
              ₹{overview.total_logistics_cost_inr?.toLocaleString() ?? '0'}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#818cf8', marginTop: 3 }}>
              ⛽ Fuel: ₹{overview.total_fuel_cost_inr?.toLocaleString() ?? '0'}
            </div>
          </div>

          <div className="card" style={{ padding: '14px 16px', borderTop: '3px solid #10b981' }}>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Empty KM Eliminated</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#34d399', marginTop: 4 }}>
              {overview.empty_km_reduced?.toLocaleString() ?? '0'} <span style={{ fontSize: '0.85rem' }}>km</span>
            </div>
            <div style={{ fontSize: '0.72rem', color: '#6ee7b7', marginTop: 3 }}>
              🎯 {overview.empty_km_reduction_pct}% total reduction
            </div>
          </div>

          <div className="card" style={{ padding: '14px 16px', borderTop: '3px solid #f59e0b' }}>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>On-Time Delivery Rate</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fcd34d', marginTop: 4 }}>
              {overview.on_time_delivery_pct}%
            </div>
            <div style={{ fontSize: '0.72rem', color: '#fbbf24', marginTop: 3 }}>
              📦 {overview.delivered_shipments} delivered · {overview.delayed_shipments} delayed
            </div>
          </div>

          <div className="card" style={{ padding: '14px 16px', borderTop: '3px solid #ec4899' }}>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Fleet Utilization</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f472b6', marginTop: 4 }}>
              {overview.avg_vehicle_utilization_pct}%
            </div>
            <div style={{ fontSize: '0.72rem', color: '#f472b6', marginTop: 3 }}>
              🚛 {overview.in_transit_vehicles} in transit / {overview.total_vehicles} total
            </div>
          </div>
        </div>
      )}

      {/* ── Cost Breakdown & Historical Routes Table ──────────────────────── */}
      <div className="card" style={{ marginBottom: 22, padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '0.95rem', color: '#f1f5f9' }}>
            💰 Route Cost Distribution & Distance Breakdown
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Latest Completed Routes</span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#0f172a', borderBottom: '1px solid #1e293b', color: '#94a3b8' }}>
                <th style={{ padding: '10px 14px' }}>Route Number</th>
                <th style={{ padding: '10px 14px' }}>Distance</th>
                <th style={{ padding: '10px 14px' }}>Fuel Cost</th>
                <th style={{ padding: '10px 14px' }}>Toll Cost</th>
                <th style={{ padding: '10px 14px' }}>Driver Wage</th>
                <th style={{ padding: '10px 14px' }}>Total Cost</th>
                <th style={{ padding: '10px 14px' }}>Date</th>
              </tr>
            </thead>
            <tbody>
              {costTrends.map((ct, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #1e293b' }}>
                  <td style={{ padding: '10px 14px', fontWeight: 700, color: '#e2e8f0' }}>{ct.route_number}</td>
                  <td style={{ padding: '10px 14px', color: '#cbd5e1' }}>{ct.distance_km} km</td>
                  <td style={{ padding: '10px 14px', color: '#a5b4fc' }}>₹{ct.fuel_cost_inr}</td>
                  <td style={{ padding: '10px 14px', color: '#fcd34d' }}>₹{ct.toll_cost_inr}</td>
                  <td style={{ padding: '10px 14px', color: '#94a3b8' }}>₹{ct.driver_cost_inr}</td>
                  <td style={{ padding: '10px 14px', fontWeight: 800, color: '#34d399' }}>₹{ct.total_cost_inr}</td>
                  <td style={{ padding: '10px 14px', color: '#64748b' }}>{ct.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Actual vs Predicted Intelligence ──────────────────────────────── */}
      {actVsPred && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>

          {/* Left: ETA Prediction Accuracy */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--color-border)' }}>
              <h3 style={{ margin: 0, fontSize: '0.95rem', color: '#f1f5f9' }}>
                ⏱️ Predicted ETA vs Actual Delivery Duration
              </h3>
              <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.75rem' }}>
                Evaluates ML transit duration models against completed trip logs
              </p>
            </div>
            <div style={{ maxHeight: 300, overflowY: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ background: '#0f172a', color: '#94a3b8', borderBottom: '1px solid #1e293b' }}>
                    <th style={{ padding: '8px 12px' }}>Corridor</th>
                    <th style={{ padding: '8px 12px' }}>Predicted</th>
                    <th style={{ padding: '8px 12px' }}>Actual</th>
                    <th style={{ padding: '8px 12px' }}>Variance</th>
                    <th style={{ padding: '8px 12px' }}>Accuracy</th>
                  </tr>
                </thead>
                <tbody>
                  {actVsPred.eta_comparisons?.map((eta, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '8px 12px', color: '#e2e8f0', fontWeight: 600 }}>
                        {eta.origin_city} ➔ {eta.destination_city}
                      </td>
                      <td style={{ padding: '8px 12px', color: '#94a3b8' }}>{eta.predicted_duration_min} min</td>
                      <td style={{ padding: '8px 12px', color: '#cbd5e1' }}>{eta.actual_duration_min} min</td>
                      <td style={{ padding: '8px 12px', color: eta.error_min <= 20 ? '#34d399' : '#f87171', fontWeight: 700 }}>
                        ±{eta.error_min} min
                      </td>
                      <td style={{ padding: '8px 12px', color: '#34d399', fontWeight: 800 }}>
                        {eta.accuracy_pct}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right: Demand Forecast vs Real Shipments */}
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--color-border)' }}>
              <h3 style={{ margin: 0, fontSize: '0.95rem', color: '#f1f5f9' }}>
                📊 Demand Forecast Accuracy & AI Reliability
              </h3>
              <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.75rem' }}>
                Ridge & LightGBM forecast performance across Indian state corridors
              </p>
            </div>
            <div style={{ padding: 16 }}>
              {actVsPred.demand_comparisons?.slice(0, 3).map((dem, i) => (
                <div key={i} style={{ marginBottom: 12, paddingBottom: 10, borderBottom: '1px solid #1e293b' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 700, color: '#e2e8f0' }}>
                    <span>{dem.corridor}</span>
                    <span style={{ color: '#a5b4fc' }}>Confidence: {dem.confidence_band}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#94a3b8', marginTop: 4 }}>
                    <span>Predicted: <strong>{dem.predicted_shipments}</strong> orders</span>
                    <span>Actual: <strong>{dem.actual_shipments}</strong> orders</span>
                    <span style={{ color: dem.variance === 0 ? '#34d399' : '#fbbf24' }}>
                      Variance: {dem.variance > 0 ? `+${dem.variance}` : dem.variance}
                    </span>
                  </div>
                </div>
              ))}

              {/* AI Risk Model Summary */}
              {actVsPred.delay_risk_accuracy && (
                <div style={{ background: '#0f172a', borderRadius: 6, padding: '10px 12px', marginTop: 8 }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', marginBottom: 4 }}>
                    ⚡ Delay Classifier Early Warning Score
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, textAlign: 'center', fontSize: '0.75rem' }}>
                    <div>
                      <span style={{ color: '#64748b', display: 'block' }}>Precision</span>
                      <strong style={{ color: '#34d399' }}>{actVsPred.delay_risk_accuracy.precision_score * 100}%</strong>
                    </div>
                    <div>
                      <span style={{ color: '#64748b', display: 'block' }}>Recall</span>
                      <strong style={{ color: '#34d399' }}>{actVsPred.delay_risk_accuracy.recall_score * 100}%</strong>
                    </div>
                    <div>
                      <span style={{ color: '#64748b', display: 'block' }}>Early Warning</span>
                      <strong style={{ color: '#38bdf8' }}>{actVsPred.delay_risk_accuracy.early_warning_rate_pct}%</strong>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
