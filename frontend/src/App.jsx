import {
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import ProtectedRoute
  from './components/ProtectedRoute'

import AdminRoute
  from './components/AdminRoute'

import LoginPage
  from './pages/auth/LoginPage'

import RegisterPage
  from './pages/auth/RegisterPage'

import DashboardPage
  from './pages/dashboard/DashboardPage'

import DatasetsPage
  from './pages/datasets/DatasetsPage'

import AnalysisPage
  from './pages/analysis/AnalysisPage'

import MLPage
  from './pages/ml/MLPage'

import VisualizationsPage
  from './pages/visualizations/VisualizationsPage'

import ReportsPage
  from './pages/reports/ReportsPage'

import NotificationsPage
  from './pages/notifications/NotificationsPage'

import AdminPage
  from './pages/admin/AdminPage'

import UserManagementPage
  from './pages/admin/UserManagementPage'

function Protected({
  children,
}) {
  return (
    <ProtectedRoute>
      {children}
    </ProtectedRoute>
  )
}


function AdminProtected({
  children,
}) {
  return (
    <AdminRoute>
      {children}
    </AdminRoute>
  )
}


export default function App() {
  return (
    <Routes>

      {/* Default route */}
      <Route
        path="/"
        element={
          <Navigate
            to="/dashboard"
            replace
          />
        }
      />


      {/* Authentication */}
      <Route
        path="/login"
        element={
          <LoginPage />
        }
      />

      <Route
        path="/register"
        element={
          <RegisterPage />
        }
      />


      {/* Dashboard */}
      <Route
        path="/dashboard"
        element={
          <Protected>
            <DashboardPage />
          </Protected>
        }
      />


      {/* Dataset Management */}
      <Route
        path="/datasets"
        element={
          <Protected>
            <DatasetsPage />
          </Protected>
        }
      />


      {/* Statistical Analysis */}
      <Route
        path="/analysis"
        element={
          <Protected>
            <AnalysisPage />
          </Protected>
        }
      />


      {/* AI / Machine Learning */}
      <Route
        path="/ml"
        element={
          <Protected>
            <MLPage />
          </Protected>
        }
      />


      {/* Visualizations */}
      <Route
        path="/visualizations"
        element={
          <Protected>
            <VisualizationsPage />
          </Protected>
        }
      />


      {/* Reports */}
      <Route
        path="/reports"
        element={
          <Protected>
            <ReportsPage />
          </Protected>
        }
      />


      {/* Notifications */}
      <Route
        path="/notifications"
        element={
          <Protected>
            <NotificationsPage />
          </Protected>
        }
      />

<Route
  path="/admin"
  element={
    <AdminProtected>
      <AdminPage />
    </AdminProtected>
  }
/>

<Route
  path="/admin/users"
  element={
    <AdminProtected>
      <UserManagementPage />
    </AdminProtected>
  }
/>
    </Routes>
  )
}
