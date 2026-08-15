import React from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import { ROLE_HOME_PATH } from '../../services/constants'

export default function ProtectedRoute({ allowedRoles }) {
  const { isAuthenticated, user } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    const redirectPath = ROLE_HOME_PATH[user.role] || '/login'
    return <Navigate to={redirectPath} replace />
  }

  return <Outlet />
}
