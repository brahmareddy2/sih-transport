import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
import Login from './pages/Login'
import Optimization from './pages/Optimization'
import MlDashboard from './pages/MlDashboard'
import LiveTracking from './pages/LiveTracking'
import IncidentManagement from './pages/IncidentManagement'
import ReturnCargo from './pages/ReturnCargo'
import WhatIfSimulator from './pages/WhatIfSimulator'
import AnalyticsDashboard from './pages/AnalyticsDashboard'
import ProtectedRoute from './components/auth/ProtectedRoute'
import useAuthStore from './store/authStore'
import { ROLES } from './services/constants'
import { getUnreadNotificationCount } from './services/analyticsApi'

// Layout for authenticated routes
function DashboardLayout({ title, roleLabel, children }) {
  const { user, logout } = useAuthStore()
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    async function checkNotifs() {
      try {
        const res = await getUnreadNotificationCount()
        setUnreadCount(res?.unread_count || 0)
      } catch (e) {
        // silent
      }
    }
    checkNotifs()
    const timer = setInterval(checkNotifs, 10000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div style={{ padding: '20px', maxWidth: '1440px', margin: '0 auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid var(--color-border)', paddingBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: '700', margin: 0 }}>{title}</h1>
          <p className="text-muted" style={{ fontSize: '0.875rem', margin: '4px 0 0' }}>
            Role: <span className="badge badge-info">{roleLabel}</span> | Logged in as: {user?.email}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <Link to="/operator" className="btn btn-secondary btn-sm" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>
            🛰️ Optimization
          </Link>
          <Link to="/ml" className="btn btn-secondary btn-sm" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>
            📊 AI/ML
          </Link>
          <Link to="/tracking" className="btn btn-secondary btn-sm" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>
            🚛 GPS Tracking
          </Link>
          <Link to="/incidents" className="btn btn-secondary btn-sm" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>
            🚨 Incidents
          </Link>
          <Link to="/return-cargo" className="btn btn-secondary btn-sm" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>
            🔄 Return Cargo
          </Link>
          <Link to="/what-if" className="btn btn-primary btn-sm" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', background: '#4f46e5' }}>
            ⚡ What-If
          </Link>
          <Link to="/analytics" className="btn btn-primary btn-sm" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', background: '#059669' }}>
            📈 Analytics
          </Link>
          {unreadCount > 0 && (
            <span style={{ background: '#ef4444', color: '#fff', fontSize: '0.75rem', fontWeight: 800, padding: '4px 8px', borderRadius: 12 }}>
              🔔 {unreadCount}
            </span>
          )}
          <button onClick={logout} className="btn btn-secondary btn-sm" style={{ marginLeft: '6px' }}>Sign Out</button>
        </div>
      </header>

      <div>
        {children || (
          <div className="card">
            <h3>Operational Dashboard</h3>
            <p className="mt-4" style={{ color: 'var(--color-text-secondary)' }}>
              Logistics DSS Fleet portal fully configured with Real-time GPS Tracking, OR-Tools optimization, Return Cargo Matching, and AI models.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const { accessToken, fetchProfile } = useAuthStore()

  useEffect(() => {
    if (accessToken) {
      fetchProfile()
    }
  }, [accessToken, fetchProfile])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        {/* Protected Routes */}
        <Route element={<ProtectedRoute allowedRoles={[ROLES.ADMIN]} />}>
          <Route path="/admin" element={
            <DashboardLayout title="Admin Console" roleLabel="Administrator">
              <Optimization />
            </DashboardLayout>
          } />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={[ROLES.OPERATOR, ROLES.ADMIN]} />}>
          <Route path="/operator" element={
            <DashboardLayout title="Operator Dashboard" roleLabel="Logistics Operator">
              <Optimization />
            </DashboardLayout>
          } />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={[ROLES.OPERATOR, ROLES.ADMIN]} />}>
          <Route path="/ml" element={
            <DashboardLayout title="AI/ML Intelligence" roleLabel="AI Analyst">
              <MlDashboard />
            </DashboardLayout>
          } />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={[ROLES.OPERATOR, ROLES.FLEET_MANAGER, ROLES.ADMIN]} />}>
          <Route path="/tracking" element={
            <DashboardLayout title="Live Fleet Tracking" roleLabel="Fleet Manager">
              <LiveTracking />
            </DashboardLayout>
          } />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={[ROLES.OPERATOR, ROLES.FLEET_MANAGER, ROLES.ADMIN]} />}>
          <Route path="/incidents" element={
            <DashboardLayout title="Incident Management" roleLabel="Operator">
              <IncidentManagement />
            </DashboardLayout>
          } />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={[ROLES.OPERATOR, ROLES.FLEET_MANAGER, ROLES.ADMIN]} />}>
          <Route path="/return-cargo" element={
            <DashboardLayout title="Return Cargo & Empty-KM Reduction" roleLabel="Operator">
              <ReturnCargo />
            </DashboardLayout>
          } />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={[ROLES.OPERATOR, ROLES.FLEET_MANAGER, ROLES.ADMIN]} />}>
          <Route path="/what-if" element={
            <DashboardLayout title="What-If Contingency Simulator" roleLabel="Operator">
              <WhatIfSimulator />
            </DashboardLayout>
          } />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={[ROLES.OPERATOR, ROLES.FLEET_MANAGER, ROLES.ADMIN]} />}>
          <Route path="/analytics" element={
            <DashboardLayout title="Enterprise Analytics & Performance" roleLabel="Operator">
              <AnalyticsDashboard />
            </DashboardLayout>
          } />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={[ROLES.FLEET_MANAGER, ROLES.ADMIN]} />}>
          <Route path="/fleet" element={<DashboardLayout title="Fleet Management" roleLabel="Fleet Manager" />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={[ROLES.DRIVER, ROLES.ADMIN]} />}>
          <Route path="/driver" element={<DashboardLayout title="Driver Console" roleLabel="Driver" />} />
        </Route>

        <Route element={<ProtectedRoute allowedRoles={[ROLES.CUSTOMER, ROLES.ADMIN]} />}>
          <Route path="/customer" element={<DashboardLayout title="Customer Portal" roleLabel="Customer" />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
