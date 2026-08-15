/**
 * Auth store using Zustand.
 * Manages: current user, tokens, login/logout actions.
 * Tokens stored in localStorage (simple for SIH prototype;
 * for production use HttpOnly cookies).
 */
import { create } from 'zustand'
import api from '../services/api.js'

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
      set({
        user: data.user,
        accessToken: data.access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      })
      return { success: true, role: data.user.role }
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed. Check credentials.'
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
    set({ user: null, accessToken: null, isAuthenticated: false, error: null })
  },

  fetchProfile: async () => {
    try {
      const { data } = await api.get('/auth/me')
      set({ user: data, isAuthenticated: true })
    } catch {
      get().logout()
    }
  },

  clearError: () => set({ error: null }),
}))

export default useAuthStore
