import React, { useState, useEffect } from 'react'
import Optimization from './Optimization'
import LiveTracking from './LiveTracking'
import api from '../services/api'

export default function FleetOperatorDashboard() {
  const [activeTab, setActiveTab] = useState('optimization')

  // Orders Tab State
  const [pendingOrders, setPendingOrders] = useState([])
  const [availableVehicles, setAvailableVehicles] = useState([])
  const [availableDrivers, setAvailableDrivers] = useState([])
  const [loadingOrders, setLoadingOrders] = useState(false)
  const [actionMessage, setActionMessage] = useState('')
  const [selectedVehicle, setSelectedVehicle] = useState({})
  const [selectedDriver, setSelectedDriver] = useState({})

  // Financial Tab State
  const [financialData, setFinancialData] = useState(null)
  const [loadingFinancials, setLoadingFinancials] = useState(false)
  const [financialError, setFinancialError] = useState('')

  const loadPendingData = async () => {
    setLoadingOrders(true)
    setActionMessage('')
    try {
      const [ordersRes, vehiclesRes, driversRes] = await Promise.all([
        api.get('/shipments/pending'),
        api.get('/vehicles/available'),
        api.get('/drivers/available'),
      ])
      
      const orders = ordersRes.data?.items || []
      const vehicles = vehiclesRes.data?.items || []
      const drivers = driversRes.data?.items || []
      
      setPendingOrders(orders)
      setAvailableVehicles(vehicles)
      setAvailableDrivers(drivers)

      // Initialize dropdown selections
      const firstVeh = vehicles[0]?.id || ''
      const firstDrv = drivers[0]?.id || ''
      
      const initialVeh = {}
      const initialDrv = {}
      orders.forEach(o => {
        initialVeh[o.id] = firstVeh
        initialDrv[o.id] = firstDrv
      })
      setSelectedVehicle(initialVeh)
      setSelectedDriver(initialDrv)
    } catch (err) {
      console.error('Failed to load fleet operator pending assignment data:', err)
    } finally {
      setLoadingOrders(false)
    }
  }

  const loadFinancialData = async () => {
    setLoadingFinancials(true)
    setFinancialError('')
    try {
      const { data } = await api.get('/fleet-operator/financial-summary')
      setFinancialData(data)
    } catch (err) {
      console.error('Failed to fetch financial summary:', err)
      setFinancialError('Failed to retrieve fleet financial metrics.')
    } finally {
      setLoadingFinancials(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'orders') {
      loadPendingData()
    } else if (activeTab === 'financials') {
      loadFinancialData()
    }
  }, [activeTab])

  // Fetch pending count on startup for notification label
  useEffect(() => {
    const fetchPendingCountOnly = async () => {
      try {
        const { data } = await api.get('/shipments/pending')
        if (data?.items) {
          setPendingOrders(data.items)
        }
      } catch {}
    }
    fetchPendingCountOnly()
  }, [])

  const handleAssignOrder = async (shipmentId) => {
    const vId = selectedVehicle[shipmentId]
    const dId = selectedDriver[shipmentId]
    
    if (!vId || !dId) {
      setActionMessage('❌ Please select both an available vehicle and a driver.')
      return
    }

    setActionMessage('')
    try {
      await api.post(`/shipments/${shipmentId}/assign`, {
        vehicle_id: vId,
        driver_id: dId
      })
      setActionMessage('🎉 Consignment trip assigned and marked in-transit successfully!')
      // Refresh
      setTimeout(() => {
        loadPendingData()
      }, 1500)
    } catch (err) {
      console.error('Failed to assign shipment:', err)
      setActionMessage(`❌ Assignment failed: ${err.response?.data?.detail || 'Database validation error.'}`)
    }
  }

  const handleVehChange = (shipmentId, val) => {
    setSelectedVehicle(prev => ({ ...prev, [shipmentId]: val }))
  }

  const handleDrvChange = (shipmentId, val) => {
    setSelectedDriver(prev => ({ ...prev, [shipmentId]: val }))
  }

  return (
    <div style={{ padding: '0px', width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Dynamic Tab Switcher */}
      <div 
        style={{
          display: 'flex',
          gap: '12px',
          padding: '12px 24px',
          background: 'var(--color-bg-secondary)',
          borderBottom: '1px solid var(--color-border)',
          alignItems: 'center',
          boxShadow: 'var(--shadow-glow)',
          zIndex: 10,
          flexWrap: 'wrap'
        }}
      >
        <button
          onClick={() => setActiveTab('optimization')}
          style={{
            padding: '8px 16px',
            borderRadius: '20px',
            border: activeTab === 'optimization' ? 'none' : '1px solid var(--color-border)',
            background: activeTab === 'optimization' ? 'var(--color-blue-gradient, linear-gradient(135deg, #3b82f6, #1d4ed8))' : 'var(--color-bg-primary)',
            color: activeTab === 'optimization' ? '#fff' : 'var(--color-text-primary)',
            fontWeight: 800,
            cursor: 'pointer',
            fontSize: '0.85rem',
            boxShadow: activeTab === 'optimization' ? '0 4px 15px rgba(59, 130, 246, 0.4)' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          🛰️ Dispatch & Route Optimization
        </button>
        <button
          onClick={() => setActiveTab('tracking')}
          style={{
            padding: '8px 16px',
            borderRadius: '20px',
            border: activeTab === 'tracking' ? 'none' : '1px solid var(--color-border)',
            background: activeTab === 'tracking' ? 'var(--color-blue-gradient, linear-gradient(135deg, #3b82f6, #1d4ed8))' : 'var(--color-bg-primary)',
            color: activeTab === 'tracking' ? '#fff' : 'var(--color-text-primary)',
            fontWeight: 800,
            cursor: 'pointer',
            fontSize: '0.85rem',
            boxShadow: activeTab === 'tracking' ? '0 4px 15px rgba(59, 130, 246, 0.4)' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          📍 Fleet Telematics & GPS Tracking
        </button>
        <button
          onClick={() => setActiveTab('orders')}
          style={{
            padding: '8px 16px',
            borderRadius: '20px',
            border: activeTab === 'orders' ? 'none' : '1px solid var(--color-border)',
            background: activeTab === 'orders' ? 'var(--color-blue-gradient, linear-gradient(135deg, #3b82f6, #1d4ed8))' : 'var(--color-bg-primary)',
            color: activeTab === 'orders' ? '#fff' : 'var(--color-text-primary)',
            fontWeight: 800,
            cursor: 'pointer',
            fontSize: '0.85rem',
            boxShadow: activeTab === 'orders' ? '0 4px 15px rgba(59, 130, 246, 0.4)' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          📦 Customer Booking Orders ({pendingOrders.length})
        </button>
        <button
          onClick={() => setActiveTab('financials')}
          style={{
            padding: '8px 16px',
            borderRadius: '20px',
            border: activeTab === 'financials' ? 'none' : '1px solid var(--color-border)',
            background: activeTab === 'financials' ? 'var(--color-blue-gradient, linear-gradient(135deg, #3b82f6, #1d4ed8))' : 'var(--color-bg-primary)',
            color: activeTab === 'financials' ? '#fff' : 'var(--color-text-primary)',
            fontWeight: 800,
            cursor: 'pointer',
            fontSize: '0.85rem',
            boxShadow: activeTab === 'financials' ? '0 4px 15px rgba(59, 130, 246, 0.4)' : 'none',
            transition: 'all 0.2s ease',
          }}
        >
          💰 Financial Summary
        </button>
      </div>

      {/* Tab Content Area */}
      <div style={{ flex: 1, position: 'relative', padding: (activeTab === 'orders' || activeTab === 'financials') ? '20px' : '0px' }}>
        {activeTab === 'optimization' && <Optimization />}
        {activeTab === 'tracking' && <LiveTracking />}
        
        {activeTab === 'orders' && (
          <div style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 800, color: '#f1f5f9' }}>
                  📦 Pending Consignment Orders & Dispatch Assignment
                </h2>
                <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.85rem' }}>
                  Verify unassigned customer bookings, match with idle/empty trucks, and assign drivers.
                </p>
              </div>
              <button
                onClick={loadPendingData}
                style={{ padding: '8px 14px', background: '#1e293b', border: '1px solid var(--color-border)', borderRadius: 8, color: '#fff', fontSize: '0.75rem', fontWeight: 'bold', cursor: 'pointer' }}
              >
                🔄 Refresh Lists
              </button>
            </div>

            {actionMessage && (
              <div style={{
                background: actionMessage.startsWith('❌') ? '#450a0a' : '#064e3b',
                border: '1px solid ' + (actionMessage.startsWith('❌') ? '#ef4444' : '#10b981'),
                borderRadius: 10, padding: '12px 16px', marginBottom: 20, color: '#fff', fontSize: '0.85rem', fontWeight: 700
              }}>
                {actionMessage}
              </div>
            )}

            {loadingOrders ? (
              <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
                Loading pending orders and empty vehicles...
              </div>
            ) : pendingOrders.length === 0 ? (
              <div className="card" style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
                🎉 No pending customer consignment orders to dispatch!
              </div>
            ) : (
              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ background: '#0f172a', borderBottom: '1px solid #1e293b', color: '#94a3b8' }}>
                        <th style={{ padding: '12px 16px' }}>Order Info</th>
                        <th style={{ padding: '12px 16px' }}>Origin Point</th>
                        <th style={{ padding: '12px 16px' }}>Destination Point</th>
                        <th style={{ padding: '12px 16px' }}>Weight / Cargo</th>
                        <th style={{ padding: '12px 16px' }}>Available Fleet Vehicles & Drivers</th>
                        <th style={{ padding: '12px 16px', textAlign: 'center' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pendingOrders.map(o => (
                        <tr key={o.id} style={{ borderBottom: '1px solid #1e293b' }}>
                          <td style={{ padding: '16px', fontWeight: 800, color: '#fff' }}>
                            <div>{o.shipment_number}</div>
                            <span style={{
                              padding: '2px 6px', borderRadius: 4, fontSize: '0.65rem',
                              background: o.priority === 'urgent' || o.priority === 'high' ? '#ef444422' : '#fbbf2422',
                              color: o.priority === 'urgent' || o.priority === 'high' ? '#f87171' : '#fcd34d',
                              border: `1px solid ${o.priority === 'urgent' || o.priority === 'high' ? '#ef444444' : '#fbbf2444'}`,
                              display: 'inline-block', marginTop: 4, textTransform: 'uppercase'
                            }}>
                              {o.priority}
                            </span>
                          </td>
                          <td style={{ padding: '16px', color: '#cbd5e1' }}>
                            <div style={{ fontWeight: 600 }}>{o.origin_city}</div>
                            <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>{o.origin_address}</div>
                          </td>
                          <td style={{ padding: '16px', color: '#cbd5e1' }}>
                            <div style={{ fontWeight: 600 }}>{o.destination_city}</div>
                            <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>{o.destination_address}</div>
                          </td>
                          <td style={{ padding: '16px', color: '#cbd5e1' }}>
                            <div style={{ fontWeight: 700, color: '#fbbf24' }}>{o.weight_kg} kg</div>
                            <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 2 }}>{o.goods_type}</div>
                          </td>
                          <td style={{ padding: '16px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                              <div>
                                <span style={{ display: 'block', fontSize: '0.65rem', color: '#94a3b8', marginBottom: 3 }}>Vehicle (Empty/Idle):</span>
                                <select
                                  value={selectedVehicle[o.id] || ''}
                                  onChange={(e) => handleVehChange(o.id, e.target.value)}
                                  style={{
                                    width: '100%', minWidth: 200, padding: '6px', borderRadius: 6,
                                    background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)',
                                    color: '#fff', fontSize: '0.78rem'
                                  }}
                                >
                                  {availableVehicles.length === 0 ? (
                                    <option value="">No Empty/Idle Trucks Available</option>
                                  ) : (
                                    availableVehicles.map(v => (
                                      <option key={v.id} value={v.id}>{v.registration_number} ({v.vehicle_type})</option>
                                    ))
                                  )}
                                </select>
                              </div>
                              <div>
                                <span style={{ display: 'block', fontSize: '0.65rem', color: '#94a3b8', marginBottom: 3 }}>Driver (Available):</span>
                                <select
                                  value={selectedDriver[o.id] || ''}
                                  onChange={(e) => handleDrvChange(o.id, e.target.value)}
                                  style={{
                                    width: '100%', minWidth: 200, padding: '6px', borderRadius: 6,
                                    background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)',
                                    color: '#fff', fontSize: '0.78rem'
                                  }}
                                >
                                  {availableDrivers.length === 0 ? (
                                    <option value="">No Available Drivers</option>
                                  ) : (
                                    availableDrivers.map(d => (
                                      <option key={d.id} value={d.id}>{d.full_name} ({d.phone || 'No Phone'})</option>
                                    ))
                                  )}
                                </select>
                              </div>
                            </div>
                          </td>
                          <td style={{ padding: '16px', textAlign: 'center' }}>
                            <button
                              onClick={() => handleAssignOrder(o.id)}
                              disabled={availableVehicles.length === 0 || availableDrivers.length === 0}
                              style={{
                                padding: '8px 14px', background: 'linear-gradient(135deg, #10b981, #059669)',
                                border: 'none', borderRadius: 8, color: '#fff', fontWeight: 'bold', fontSize: '0.75rem',
                                cursor: 'pointer', opacity: (availableVehicles.length === 0 || availableDrivers.length === 0) ? 0.5 : 1,
                                boxShadow: '0 4px 10px rgba(16, 185, 129, 0.25)'
                              }}
                            >
                              🚚 Confirm & Dispatch
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'financials' && (
          <div style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.35rem', fontWeight: 800, color: '#f1f5f9' }}>
                  💰 Fleet Financial Summary & Costing
                </h2>
                <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.85rem' }}>
                  Review real-time freight margins, itemized logistics costs, and per-vehicle profit analyses.
                </p>
              </div>
              <button
                onClick={loadFinancialData}
                style={{ padding: '8px 14px', background: '#1e293b', border: '1px solid var(--color-border)', borderRadius: 8, color: '#fff', fontSize: '0.75rem', fontWeight: 'bold', cursor: 'pointer' }}
              >
                🔄 Refresh Financials
              </button>
            </div>

            {financialError && (
              <div style={{ background: '#450a0a', border: '1px solid #ef4444', borderRadius: 10, padding: '12px', color: '#fca5a5', marginBottom: 16 }}>
                ⚠️ {financialError}
              </div>
            )}

            {loadingFinancials ? (
              <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
                Fetching operational cost statements and vehicle margins...
              </div>
            ) : !financialData ? (
              <div style={{ padding: 40, textAlign: 'center', color: '#94a3b8' }}>
                No active routes with cost summaries recorded.
              </div>
            ) : (
              <div>
                {/* Metric Cards Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 22 }}>
                  <div className="card" style={{ borderTop: '3px solid #38bdf8', padding: '14px 16px' }}>
                    <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Fleet Revenue</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#e2e8f0', marginTop: 4 }}>
                      ₹{financialData.total_revenue?.toLocaleString()}
                    </div>
                  </div>
                  <div className="card" style={{ borderTop: '3px solid #fbbf24', padding: '14px 16px' }}>
                    <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Operating Cost</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#e2e8f0', marginTop: 4 }}>
                      ₹{financialData.total_cost?.toLocaleString()}
                    </div>
                  </div>
                  <div className="card" style={{ borderTop: '3px solid #10b981', padding: '14px 16px' }}>
                    <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Net Margin</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#34d399', marginTop: 4 }}>
                      ₹{financialData.net_margin?.toLocaleString()}
                    </div>
                  </div>
                  <div className="card" style={{ borderTop: '3px solid #8b5cf6', padding: '14px 16px' }}>
                    <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Profit Margin</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#c084fc', marginTop: 4 }}>
                      {financialData.profit_margin_pct}%
                    </div>
                  </div>
                  <div className="card" style={{ borderTop: '3px solid #ec4899', padding: '14px 16px' }}>
                    <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>Avg Cost per KM</div>
                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f472b6', marginTop: 4 }}>
                      ₹{financialData.avg_cost_per_km} <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>/ km</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '0.8fr 1.2fr', gap: 20 }}>
                  {/* Left: Itemized Cost Breakdown */}
                  <div className="card" style={{ padding: 20 }}>
                    <h3 style={{ marginTop: 0, marginBottom: 16, fontSize: '0.95rem', color: '#f1f5f9' }}>
                      📊 Itemized Expense Share
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: 4 }}>
                          <span>⛽ Fuel Cost</span>
                          <strong>₹{financialData.cost_breakdown?.fuel_cost?.toLocaleString()}</strong>
                        </div>
                        <div style={{ width: '100%', height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{
                            width: `${(financialData.cost_breakdown?.fuel_cost / financialData.total_cost) * 100}%`,
                            height: '100%', background: '#fbbf24'
                          }} />
                        </div>
                      </div>

                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: 4 }}>
                          <span>🛣️ Toll Gate Cost</span>
                          <strong>₹{financialData.cost_breakdown?.toll_cost?.toLocaleString()}</strong>
                        </div>
                        <div style={{ width: '100%', height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{
                            width: `${(financialData.cost_breakdown?.toll_cost / financialData.total_cost) * 100}%`,
                            height: '100%', background: '#38bdf8'
                          }} />
                        </div>
                      </div>

                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: 4 }}>
                          <span>👔 Driver Allowances</span>
                          <strong>₹{financialData.cost_breakdown?.driver_wages?.toLocaleString()}</strong>
                        </div>
                        <div style={{ width: '100%', height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{
                            width: `${(financialData.cost_breakdown?.driver_wages / financialData.total_cost) * 100}%`,
                            height: '100%', background: '#ec4899'
                          }} />
                        </div>
                      </div>

                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#cbd5e1', marginBottom: 4 }}>
                          <span>⚙️ Depot & Other Overheads</span>
                          <strong>₹{financialData.cost_breakdown?.overhead_costs?.toLocaleString()}</strong>
                        </div>
                        <div style={{ width: '100%', height: 6, background: 'rgba(255,255,255,0.05)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{
                            width: `${(financialData.cost_breakdown?.overhead_costs / financialData.total_cost) * 100}%`,
                            height: '100%', background: '#a5b4fc'
                          }} />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right: Per-Vehicle Performance report */}
                  <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--color-border)' }}>
                      <h3 style={{ margin: 0, fontSize: '0.95rem', color: '#f1f5f9' }}>
                        🚛 Per-Vehicle Operational Cost & Margin Report
                      </h3>
                    </div>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                        <thead>
                          <tr style={{ background: '#0f172a', borderBottom: '1px solid #1e293b', color: '#94a3b8' }}>
                            <th style={{ padding: '10px 14px' }}>Vehicle Number</th>
                            <th style={{ padding: '10px 14px' }}>Trips</th>
                            <th style={{ padding: '10px 14px' }}>Distance</th>
                            <th style={{ padding: '10px 14px' }}>Total Cost</th>
                            <th style={{ padding: '10px 14px' }}>Total Revenue</th>
                            <th style={{ padding: '10px 14px' }}>Profit Margin</th>
                          </tr>
                        </thead>
                        <tbody>
                          {financialData.vehicle_report?.map((vh, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid #1e293b' }}>
                              <td style={{ padding: '10px 14px', fontWeight: 800, color: '#fff' }}>{vh.registration_number}</td>
                              <td style={{ padding: '10px 14px', color: '#cbd5e1' }}>{vh.trips_count}</td>
                              <td style={{ padding: '10px 14px', color: '#94a3b8' }}>{vh.distance_km} km</td>
                              <td style={{ padding: '10px 14px', color: '#fca5a5' }}>₹{vh.total_cost?.toLocaleString()}</td>
                              <td style={{ padding: '10px 14px', color: '#a7f3d0' }}>₹{vh.total_revenue?.toLocaleString()}</td>
                              <td style={{ padding: '10px 14px', color: vh.profit_margin_pct >= 20 ? '#10b981' : '#f59e0b', fontWeight: 800 }}>
                                {vh.profit_margin_pct}% Margins
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
