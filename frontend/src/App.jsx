import React, { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Optimization from './pages/Optimization'
import MlDashboard from './pages/MlDashboard'
import LiveTracking from './pages/LiveTracking'
import IncidentManagement from './pages/IncidentManagement'
import ReturnCargo from './pages/ReturnCargo'
import WhatIfSimulator from './pages/WhatIfSimulator'
import AnalyticsDashboard from './pages/AnalyticsDashboard'
import DriverMode from './pages/DriverMode'
import RoleHome from './pages/RoleHome'
import TripPlanner from './pages/TripPlanner'
import FleetOperatorDashboard from './pages/FleetOperatorDashboard'
import ProtectedRoute from './components/auth/ProtectedRoute'
import useAuthStore from './store/authStore'
import { useI18nStore } from './services/i18n'
import LanguageSelector from './components/common/LanguageSelector'
import SimpleModeToggle from './components/common/SimpleModeToggle'
import VoiceAssistantModal from './components/voice/VoiceAssistantModal'
import { ROLES } from './services/constants'
import { getUnreadNotificationCount } from './services/analyticsApi'

// Layout for authenticated routes
function DashboardLayout({ title, roleLabel, children }) {
  const { user, logout } = useAuthStore()
  const { simpleMode, t } = useI18nStore()
  const [unreadCount, setUnreadCount] = useState(0)
  const [isVoiceOpen, setIsVoiceOpen] = useState(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768)
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark')

  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-theme')
    } else {
      document.body.classList.remove('light-theme')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

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

  const role = user?.role || 'driver'
  
  // Navigation Links based on role
  const NAV_ITEMS_BY_ROLE = {
    admin: [
      { path: '/home', label: '🏠 Home' },
      { path: '/fleet-operator', label: '🛰️ Fleet Operator' },
      { path: '/incidents', label: '🚨 Incidents' },
      { path: '/return-cargo', label: '🔄 Return Cargo' },
      { path: '/ml', label: '📊 AI/ML' },
      { path: '/what-if', label: '⚡ What-If' },
      { path: '/analytics', label: '📈 Analytics' },
    ],
    fleet_operator: [
      { path: '/home', label: '🏠 Home' },
      { path: '/fleet-operator', label: '🛰️ Fleet Operator Workspace' },
      { path: '/incidents', label: '🚨 Incidents' },
      { path: '/return-cargo', label: '🔄 Return Cargo' },
    ],
    driver: [
      { path: '/home', label: '🏠 Home' },
      { path: '/trip-planner', label: '🗺️ Trip Planner' },
      { path: '/driver-mode', label: '🚛 Driver Cockpit' },
    ],
    customer: [
      { path: '/home', label: '🏠 Home' },
      { path: '/tracking', label: '📍 Track Carrier' },
      { path: '/analytics', label: '📈 My Analytics' },
    ],
  }

  const items = NAV_ITEMS_BY_ROLE[role] || NAV_ITEMS_BY_ROLE.driver
  const bottomNavItems = items.slice(0, 4)

  return (
    <div
      style={{
        padding: '20px',
        maxWidth: '1440px',
        margin: '0 auto',
        fontFamily: "'Inter', sans-serif",
        paddingBottom: isMobile ? '80px' : '20px',
        position: 'relative',
      }}
    >
      {/* Low-opacity background watermark logo */}
      <img
        src="/logo.png"
        alt="Watermark"
        style={{
          position: 'fixed',
          bottom: '5%',
          left: '5%',
          width: '25%',
          maxWidth: '220px',
          opacity: 0.02,
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px',
          borderBottom: '1px solid var(--color-border)',
          paddingBottom: '16px',
          gap: '12px',
          zIndex: 10,
          position: 'relative',
        }}
      >
        {/* Left Side: Hamburger Menu + Logo & Info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Hamburger Menu Toggle Button (Left Top Corner) */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Toggle Menu"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-text-primary, #fff)',
              fontSize: '1.8rem',
              cursor: 'pointer',
              padding: '4px 8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'transform 0.2s',
              transform: isMenuOpen ? 'rotate(90deg)' : 'none',
            }}
          >
            {isMenuOpen ? '✕' : '☰'}
          </button>

          {/* Logo & Info */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <img src="/logo.png" alt="Logo" style={{ height: '24px', opacity: 0.9 }} />
              <Link to="/home" style={{ textDecoration: 'none' }}>
                <h1 style={{ fontSize: '1.5rem', fontWeight: '800', margin: 0, color: 'var(--color-text-primary, #fff)' }}>
                  {t('app_title', 'CARGO PILOT')}
                </h1>
              </Link>
              <span style={{ fontSize: '0.75rem', fontWeight: 800, padding: '2px 8px', borderRadius: 6, background: '#6366f122', color: '#a5b4fc', border: '1px solid #6366f144' }}>
                {roleLabel}
              </span>
            </div>
            <p className="text-muted" style={{ fontSize: '0.8rem', margin: '4px 0 0', color: 'var(--color-text-secondary, #9ca3af)' }}>
              {user?.email}
            </p>
          </div>

          {/* Hamburger Dropdown Menu (Left-aligned) */}
          {isMenuOpen && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: '0',
                background: 'var(--color-bg-secondary, #1e293b)',
                border: '1px solid var(--color-border, #334155)',
                borderRadius: 16,
                padding: '16px',
                boxShadow: 'var(--shadow-card)',
                zIndex: 999,
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                minWidth: '240px',
                backdropFilter: 'blur(15px)',
              }}
            >
              {/* Navigation Links */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--color-purple, #8b5cf6)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px', textAlign: 'left' }}>
                  Navigation
                </span>
                {items.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsMenuOpen(false)}
                    style={{
                      textDecoration: 'none',
                      color: 'var(--color-text-primary, #f1f5f9)',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      padding: '8px 12px',
                      borderRadius: 8,
                      background: 'var(--color-bg-hover, #2d3748)',
                      border: '1px solid var(--color-border, #334155)',
                      display: 'flex',
                      alignItems: 'center',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'var(--color-brand, #3b82f6)'
                      e.currentTarget.style.color = '#fff'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'var(--color-bg-hover, #2d3748)'
                      e.currentTarget.style.color = 'var(--color-text-primary, #f1f5f9)'
                    }}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>

              {/* Divider */}
              <div style={{ height: '1px', background: 'var(--color-border, #334155)', margin: '4px 0' }} />

              {/* Settings & Language */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--color-purple, #8b5cf6)', textTransform: 'uppercase', letterSpacing: '0.04em', textAlign: 'left' }}>
                  Settings
                </span>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <LanguageSelector />
                  <SimpleModeToggle />
                </div>
              </div>

              {/* Divider */}
              <div style={{ height: '1px', background: 'var(--color-border, #334155)', margin: '4px 0' }} />

              {/* Sign Out */}
              <button
                onClick={() => {
                  setIsMenuOpen(false)
                  logout()
                }}
                style={{
                  width: '100%',
                  padding: '10px',
                  fontWeight: 800,
                  fontSize: '0.85rem',
                  background: 'rgba(239, 68, 68, 0.1)',
                  color: 'var(--color-danger, #ef4444)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: 8,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'
                }}
              >
                {t('sign_out', 'Sign Out')}
              </button>
            </div>
          )}
        </div>

        {/* Right Side: Global Controls (Speak, Notifications, Theme Mode Toggle) */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {/* Theme Mode Toggle Button (Night Mode / Light Mode) */}
          <button
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            style={{
              background: 'var(--color-bg-hover, #2d3748)',
              border: '1px solid var(--color-border, #334155)',
              cursor: 'pointer',
              fontSize: '1.25rem',
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow-glow)',
              transition: 'background var(--transition-fast)',
            }}
            title={theme === 'light' ? 'Switch to Night Mode (Dark)' : 'Switch to Day Mode (Light)'}
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>

          {/* Universal Persistent Voice Button - Commented out to reduce cockpit clutter */}
          {/*
          <button
            onClick={() => setIsVoiceOpen(true)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '7px 14px',
              fontSize: '0.85rem',
              fontWeight: 800,
              cursor: 'pointer',
              boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)',
              transition: 'all 0.2s',
            }}
          >
            <span>🎤</span>
            <span>{t('speak', 'Speak')}</span>
          </button>
          */}

          {/* Unread Notifications Count */}
          {unreadCount > 0 && (
            <span style={{ background: '#ef4444', color: '#fff', fontSize: '0.75rem', fontWeight: 800, padding: '4px 8px', borderRadius: 12 }}>
              🔔 {unreadCount}
            </span>
          )}
        </div>
      </header>

      {/* Mobile Bottom Navigation Bar */}
      {isMobile && (
        <div
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            background: '#131326f2',
            borderTop: '1px solid #2d2d48',
            display: 'flex',
            justifyContent: 'space-around',
            alignItems: 'center',
            zIndex: 9999,
            padding: '8px 0 12px',
            backdropFilter: 'blur(10px)',
          }}
        >
          {bottomNavItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              style={{
                textDecoration: 'none',
                color: '#9ca3af',
                fontSize: '0.75rem',
                fontWeight: 700,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '2px',
              }}
            >
              <span style={{ fontSize: '1.25rem' }}>{item.label.split(' ')[0]}</span>
              <span>{item.label.split(' ').slice(1).join(' ')}</span>
            </Link>
          ))}
        </div>
      )}

      <div style={{ position: 'relative', zIndex: 1 }}>
        {children || (
          <div className="card">
            <h3>Operational Dashboard</h3>
            <p className="mt-4" style={{ color: 'var(--color-text-secondary)' }}>
              Cargo Pilot Fleet portal configured with Universal Voice Assistant, Real-time GPS Tracking, OR-Tools optimization, and AI models.
            </p>
          </div>
        )}
      </div>

      {/* Floating Universal Voice Assistant Trigger at Bottom-Right - Commented out to prevent overlay clutter */}
      {/*
      <button
        onClick={() => setIsVoiceOpen(true)}
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: 64,
          height: 64,
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #6366f1, #a855f7)',
          color: '#fff',
          border: 'none',
          boxShadow: '0 8px 30px rgba(99, 102, 241, 0.6)',
          fontSize: '1.8rem',
          cursor: 'pointer',
          zIndex: 9000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s',
        }}
        title="Universal Voice Assistant"
      >
        🎤
      </button>
      */}

      {/* Voice Assistant Modal */}
      <VoiceAssistantModal isOpen={isVoiceOpen} onClose={() => setIsVoiceOpen(false)} />
    </div>
  )
}

export default function App() {
  const { accessToken, fetchProfile, user } = useAuthStore()

  useEffect(() => {
    if (accessToken) {
      fetchProfile()
    }
  }, [accessToken, fetchProfile])

  const ALL_ROLES = [
    ROLES.ADMIN,
    ROLES.FLEET_OPERATOR,
    ROLES.DRIVER,
    ROLES.CUSTOMER,
  ]

  const userRole = user?.role || 'fleet_operator'
  const userRoleLabel = userRole === 'admin' ? 'Administrator'
    : userRole === 'fleet_operator' ? 'Fleet Operator'
    : userRole === 'driver' ? 'Driver'
    : userRole === 'customer' ? 'Enterprise Customer'
    : 'Fleet Operator'

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signin" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/register" element={<Signup />} />
        
        {/* Protected Navigation */}
        <Route element={<ProtectedRoute allowedRoles={ALL_ROLES} />}>
          {/* Phase 8 Role Home & Simple Driver Interfaces */}
          <Route path="/home" element={
            <DashboardLayout title="Cargo Pilot — Home" roleLabel={userRoleLabel}>
              <RoleHome />
            </DashboardLayout>
          } />

          <Route path="/driver-mode" element={
            <DashboardLayout title="Driver Cockpit — Simple Mode" roleLabel="Lead Driver">
              <DriverMode />
            </DashboardLayout>
          } />

          <Route path="/driver" element={
            <DashboardLayout title="Driver Cockpit — Simple Mode" roleLabel="Lead Driver">
              <DriverMode />
            </DashboardLayout>
          } />

          <Route path="/trip-planner" element={
            <DashboardLayout title="Interactive Multimodal Trip Planner" roleLabel={userRoleLabel}>
              <TripPlanner />
            </DashboardLayout>
          } />

          {/* Phase 1–7 Routes */}
          <Route path="/admin" element={
            <DashboardLayout title="Admin Console — Fleet Optimization" roleLabel="Administrator">
              <Optimization />
            </DashboardLayout>
          } />
          
          <Route path="/fleet-operator" element={
            <DashboardLayout title="Fleet Operator Workspace" roleLabel="Fleet Operator">
              <FleetOperatorDashboard />
            </DashboardLayout>
          } />

          <Route path="/operator" element={<Navigate to="/fleet-operator" replace />} />
          <Route path="/fleet" element={<Navigate to="/fleet-operator" replace />} />

          <Route path="/tracking" element={
            <DashboardLayout title="Live Fleet Tracking & Telematics" roleLabel={userRoleLabel}>
              <LiveTracking />
            </DashboardLayout>
          } />

          <Route path="/customer" element={
            <DashboardLayout title="Customer Portal — Consignment Analytics" roleLabel="Customer">
              <AnalyticsDashboard />
            </DashboardLayout>
          } />

          <Route path="/ml" element={
            <DashboardLayout title="AI/ML Intelligence & Predictions" roleLabel={userRoleLabel}>
              <MlDashboard />
            </DashboardLayout>
          } />

          <Route path="/incidents" element={
            <DashboardLayout title="Incident Management & Recovery" roleLabel={userRoleLabel}>
              <IncidentManagement />
            </DashboardLayout>
          } />

          <Route path="/return-cargo" element={
            <DashboardLayout title="Return Cargo & Empty-KM Reduction" roleLabel={userRoleLabel}>
              <ReturnCargo />
            </DashboardLayout>
          } />

          <Route path="/what-if" element={
            <DashboardLayout title="What-If Contingency Simulator" roleLabel={userRoleLabel}>
              <WhatIfSimulator />
            </DashboardLayout>
          } />

          <Route path="/analytics" element={
            <DashboardLayout title="Enterprise Analytics & Performance" roleLabel={userRoleLabel}>
              <AnalyticsDashboard />
            </DashboardLayout>
          } />
        </Route>

        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
