/**
 * Auth store using Zustand.
 * Manages: current user, tokens, login/logout actions.
 * Tokens stored in localStorage (simple for SIH prototype;
 * for production use HttpOnly cookies).
 */
import { create } from 'zustand'
import api from '../services/api.js'

const DEMO_ACCOUNTS = {
  'admin@logistics.in': { password: 'Admin@123!', role: 'admin', full_name: 'Administrator', email: 'admin@logistics.in', id: 'demo-admin-id' },
  'operator@logistics.in': { password: 'Operator@123!', role: 'operator', full_name: 'Operations Manager', email: 'operator@logistics.in', id: 'demo-operator-id' },
  'fleet@logistics.in': { password: 'Fleet@123!', role: 'fleet_manager', full_name: 'Fleet Manager', email: 'fleet@logistics.in', id: 'demo-fleet-id' },
  'driver@logistics.in': { password: 'Driver@123!', role: 'driver', full_name: 'Lead Driver', email: 'driver@logistics.in', id: 'demo-driver-id' },
  'customer@logistics.in': { password: 'Customer@123!', role: 'customer', full_name: 'Enterprise Customer', email: 'customer@logistics.in', id: 'demo-customer-id' },
}

const useAuthStore = create((set, get) => ({
  // ── State ───────────────────────────────────────────────
  user: null,
  accessToken: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  // ── Actions ─────────────────────────────────────────────
  login: async (email, password) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.post('/auth/login', { email, password })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      localStorage.setItem('demo_user', JSON.stringify(data.user))
      set({
        user: data.user,
        accessToken: data.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      })
      return { success: true, role: data.user.role }
    } catch (err) {
      // Fallback for Vercel preview or offline backend mode
      const normalizedEmail = (email || '').trim().toLowerCase()
      const demoAccount = DEMO_ACCOUNTS[normalizedEmail]
      if (demoAccount && demoAccount.password === password) {
        const fallbackToken = 'demo_session_token_' + demoAccount.role
        localStorage.setItem('access_token', fallbackToken)
        localStorage.setItem('demo_user', JSON.stringify(demoAccount))
        set({
          user: demoAccount,
          accessToken: fallbackToken,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        })
        return { success: true, role: demoAccount.role }
      }

      let message = err.response?.data?.detail
      if (!message) {
        if (err.code === 'ERR_NETWORK' || !err.response || err.response?.status === 404) {
          message = 'Backend API is not reachable. In Vercel, set VITE_API_BASE_URL to your live backend service.'
        } else {
          message = 'Login failed. Check credentials.'
        }
      }
      set({ isLoading: false, error: message, isAuthenticated: false })
      return { success: false, error: message }
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout')
    } catch { /* ignore logout errors */ }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('demo_user')
    set({ user: null, accessToken: null, isAuthenticated: false, error: null })
  },

  fetchProfile: async () => {
    try {
      const { data } = await api.get('/auth/me')
      set({ user: data, isAuthenticated: true })
    } catch {
      const localUser = localStorage.getItem('demo_user')
      if (localUser) {
        try {
          set({ user: JSON.parse(localUser), isAuthenticated: true })
          return
        } catch {}
      }
      get().logout()
    }
  },

  clearError: () => set({ error: null }),
}))

export default useAuthStore
