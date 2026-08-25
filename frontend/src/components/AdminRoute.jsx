import {
  Navigate,
  useLocation,
} from 'react-router-dom'

import {
  useAuth,
} from '../context/AuthContext'

export default function AdminRoute({
  children,
}) {
  const {
    user,
    loading,
  } = useAuth()

  const location =
    useLocation()

  if (loading) {
    return (
      <div className="admin-loading-screen">
        Checking administrator access...
      </div>
    )
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
        }}
      />
    )
  }

  if (user.role !== 'admin') {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    )
  }

  return children
}
