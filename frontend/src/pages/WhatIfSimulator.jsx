/**
 * WhatIfSimulator — Phase 7
 * Interactive sandbox What-If simulation dashboard for operational contingency planning.
 * Features:
 *  - 9 disruption & operational scenarios
 *  - Vehicle selection & custom override parameters (delay, detour, payload)
 *  - Side-by-side BEFORE vs AFTER metric comparison grid
 *  - Explainable optimization & recovery recommendation plan
 */
import React, { useState, useEffect } from 'react'
import api from '../services/api'
import { getWhatIfScenarios, runWhatIfSimulation } from '../services/analyticsApi'

const SCENARIO_ICONS = {
  heavy_traffic: '🚦',
  breakdown: '🔴',
  tyre_puncture: '🔧',
  road_closure: '🚧',
  low_fuel: '⛽',
  driver_unavailable: '👤',
  urgent_shipment: '⚡',
  additional_shipment: '📦',
  vehicle_unavailable: '🚛',
}

export default function WhatIfSimulator() {
  const [scenarios, setScenarios] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [selectedScenario, setSelectedScenario] = useState('heavy_traffic')
  const [selectedVehicleId, setSelectedVehicleId] = useState('')
  const [extraDelay, setExtraDelay] = useState('')
  const [detourKm, setDetourKm] = useState('')
  const [extraWeight, setExtraWeight] = useState('')
  const [loading, setLoading] = useState(false)
  const [simResult, setSimResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function init() {
      try {
        const [scenList, vehRes] = await Promise.all([
          getWhatIfScenarios(),
          api.get('/vehicles?limit=50'),
        ])
        setScenarios(scenList || [])
        setVehicles(vehRes.data?.items || vehRes.data || [])
        if (vehRes.data?.items?.length > 0) {
          setSelectedVehicleId(vehRes.data.items[0].id)
        }
      } catch (e) {
        console.error('Failed to init What-If simulator', e)
      }
    }
    init()
  }, [])

  // Auto-run simulation on initial load once vehicle is available
  useEffect(() => {
    if (selectedVehicleId && !simResult) {
      handleSimulate('heavy_traffic', selectedVehicleId)
    }
  }, [selectedVehicleId])

  const handleSimulate = async (scenType = selectedScenario, vehId = selectedVehicleId) => {
    setLoading(true)
    setError(null)
    try {
      const payload = {
        scenario_type: scenType,
        vehicle_id: vehId || undefined,
        extra_delay_min: extraDelay ? parseInt(extraDelay, 10) : undefined,
        detour_km: detourKm ? parseFloat(detourKm) : undefined,
        additional_weight_kg: extraWeight ? parseFloat(extraWeight) : undefined,
      }
      const res = await runWhatIfSimulation(payload)
      setSimResult(res)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Simulation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', paddingBottom: 32 }}>

      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ margin: 0, fontSize: '1.45rem', fontWeight: 800, color: '#f1f5f9' }}>
          ⚡ What-If Scenario Simulation & Contingency Analyzer
        </h2>
        <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.85rem' }}>
          Sandbox decision support to model disruptions, urgent orders, and breakdowns before executing in the field.
        </p>
      </div>

      {error && (
        <div style={{ background: '#450a0a', border: '1px solid #ef4444', borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: '#fca5a5', fontSize: '0.85rem' }}>
          ❌ {error}
        </div>
      )}

      {/* ── Scenario Selection Grid ───────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10, marginBottom: 20 }}>
        {scenarios.map(scen => {
          const isSelected = selectedScenario === scen.type
          const icon = SCENARIO_ICONS[scen.type] || '⚡'
          return (
            <button
              key={scen.type}
              onClick={() => {
                setSelectedScenario(scen.type)
                handleSimulate(scen.type, selectedVehicleId)
              }}
              style={{
                padding: '12px 14px',
                borderRadius: 8,
                border: '1px solid',
                borderColor: isSelected ? '#6366f1' : '#334155',
                background: isSelected ? '#312e81' : '#1e293b',
                color: isSelected ? '#ffffff' : '#cbd5e1',
                cursor: 'pointer',
                textAlign: 'left',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                transition: 'all 0.15s',
              }}
            >
              <span style={{ fontSize: '1.3rem' }}>{icon}</span>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.82rem' }}>{scen.title}</div>
                <div style={{ fontSize: '0.68rem', color: isSelected ? '#c7d2fe' : '#64748b', textTransform: 'capitalize' }}>
                  {scen.category}
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* ── Configuration Parameters Bar ──────────────────────────────────── */}
      <div className="card" style={{ padding: '14px 18px', marginBottom: 20, background: '#0f172a' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: 4 }}>
              TARGET VEHICLE
            </label>
            <select
              value={selectedVehicleId}
              onChange={e => {
                setSelectedVehicleId(e.target.value)
                handleSimulate(selectedScenario, e.target.value)
              }}
              style={{ width: '100%', padding: '8px 10px', background: '#1e293b', border: '1px solid var(--color-border)', borderRadius: 6, color: '#f1f5f9', fontSize: '0.85rem' }}
            >
              {vehicles.map(v => (
                <option key={v.id} value={v.id}>
                  {v.registration_number} — {v.vehicle_type} ({v.current_city || 'Mumbai'})
                </option>
              ))}
            </select>
          </div>

          <div style={{ width: 140 }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: 4 }}>
              EXTRA DELAY (MIN)
            </label>
            <input
              type="number"
              value={extraDelay}
              onChange={e => setExtraDelay(e.target.value)}
              placeholder="Auto / Default"
              style={{ width: '100%', padding: '8px 10px', background: '#1e293b', border: '1px solid var(--color-border)', borderRadius: 6, color: '#f1f5f9', fontSize: '0.85rem', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ width: 140 }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: 4 }}>
              DETOUR DISTANCE (KM)
            </label>
            <input
              type="number"
              value={detourKm}
              onChange={e => setDetourKm(e.target.value)}
              placeholder="Auto / Default"
              style={{ width: '100%', padding: '8px 10px', background: '#1e293b', border: '1px solid var(--color-border)', borderRadius: 6, color: '#f1f5f9', fontSize: '0.85rem', boxSizing: 'border-box' }}
            />
          </div>

          <div style={{ width: 150 }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: 4 }}>
              ADDED WEIGHT (KG)
            </label>
            <input
              type="number"
              value={extraWeight}
              onChange={e => setExtraWeight(e.target.value)}
              placeholder="Auto / Default"
              style={{ width: '100%', padding: '8px 10px', background: '#1e293b', border: '1px solid var(--color-border)', borderRadius: 6, color: '#f1f5f9', fontSize: '0.85rem', boxSizing: 'border-box' }}
            />
          </div>

          <button
            onClick={() => handleSimulate()}
            className="btn btn-primary"
            disabled={loading}
            style={{ padding: '8px 18px', background: '#4f46e5', fontWeight: 700 }}
          >
            {loading ? '⏳ Simulating...' : '🚀 Run Simulation'}
          </button>
        </div>
      </div>

      {/* ── Simulation Results: Before vs After ───────────────────────────── */}
      {simResult && (
        <div>
          {/* Header Info */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <div>
              <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f1f5f9' }}>
                {simResult.scenario_title}
              </span>
              <span style={{ marginLeft: 10, fontSize: '0.8rem', color: '#94a3b8' }}>
                Vehicle: <strong>{simResult.target_vehicle_registration}</strong> · Route: {simResult.target_route_number}
              </span>
            </div>
            <span style={{ fontSize: '0.75rem', background: '#312e81', color: '#a5b4fc', padding: '3px 10px', borderRadius: 12, fontWeight: 700 }}>
              SANDBOX MODE (NO PROD WRITE)
            </span>
          </div>

          {/* Metric Comparison Tiles */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 20 }}>
            {Object.entries(simResult.metrics || {}).map(([key, m]) => {
              const deltaColor = m.is_favorable ? '#34d399' : '#f87171'
              const deltaPrefix = m.delta > 0 ? '+' : ''
              return (
                <div key={key} className="card" style={{ padding: '12px 16px', background: '#1e293b' }}>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>
                    {m.metric_name}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 6 }}>
                    <div>
                      <span style={{ fontSize: '0.72rem', color: '#64748b', display: 'block' }}>BEFORE</span>
                      <span style={{ fontSize: '1.1rem', fontWeight: 700, color: '#cbd5e1' }}>
                        {m.before} <span style={{ fontSize: '0.75rem' }}>{m.unit}</span>
                      </span>
                    </div>

                    <div style={{ fontSize: '1.2rem', color: '#64748b' }}>➔</div>

                    <div>
                      <span style={{ fontSize: '0.72rem', color: '#64748b', display: 'block' }}>AFTER</span>
                      <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f1f5f9' }}>
                        {m.after} <span style={{ fontSize: '0.75rem' }}>{m.unit}</span>
                      </span>
                    </div>
                  </div>

                  <div style={{ marginTop: 8, paddingTop: 6, borderTop: '1px solid #334155', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                    <span style={{ color: '#64748b' }}>Variance Delta:</span>
                    <span style={{ fontWeight: 700, color: deltaColor }}>
                      {deltaPrefix}{m.delta} {m.unit} ({deltaPrefix}{m.delta_pct}%)
                    </span>
                  </div>
                </div>
              )
            })}
          </div>

          {/* ── Explainable Optimization Plan Card ─────────────────────────── */}
          <div className="card" style={{ borderLeft: '4px solid #6366f1', background: '#111827' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <span style={{ fontSize: '1.2rem' }}>💡</span>
              <h3 style={{ margin: 0, fontSize: '1rem', color: '#f1f5f9' }}>
                Recommended Recovery Plan: {simResult.recommended_action}
              </h3>
            </div>
            <p style={{ margin: '0 0 12px', fontSize: '0.82rem', color: '#94a3b8' }}>
              {simResult.description}
            </p>

            <div style={{ background: '#1e293b', borderRadius: 6, padding: '12px 14px' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#a5b4fc', marginBottom: 8, textTransform: 'uppercase' }}>
                Optimization Action Steps:
              </div>
              <ul style={{ margin: 0, paddingLeft: 20, color: '#e2e8f0', fontSize: '0.83rem', lineHeight: 1.6 }}>
                {simResult.action_steps?.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
