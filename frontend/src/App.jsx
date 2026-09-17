import {
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import ProtectedRoute from './components/ProtectedRoute'
import AdminRoute from './components/AdminRoute'

import StatisticsCalculatorLanding from './pages/StatisticsCalculatorLanding'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'

import SurveyPage from './pages/survey/SurveyPage'
import DatasetsPage from './pages/datasets/DatasetsPage'
import DataWorkspacePage from './pages/datasets/DataWorkspacePage'
import DataPreparationPage from './pages/datasets/DataPreparationPage'
import AnalysisPage from './pages/analysis/AnalysisPage'
import VisualizationsPage from './pages/visualizations/VisualizationsPage'
import ReportsPage from './pages/reports/ReportsPage'
import NotificationsPage from './pages/notifications/NotificationsPage'

import AdminPage from './pages/admin/AdminPage'
import UserManagementPage from './pages/admin/UserManagementPage'

function Protected({ children }) {
  return (
    <ProtectedRoute>
      {children}
    </ProtectedRoute>
  )
}

function AdminProtected({ children }) {
  return (
    <AdminRoute>
      {children}
    </AdminRoute>
  )
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<StatisticsCalculatorLanding />}
      />

      <Route
        path="/statistics-calculator"
        element={<StatisticsCalculatorLanding />}
      />

      <Route
        path="/login"
        element={<LoginPage />}
      />

      <Route
        path="/register"
        element={<RegisterPage />}
      />

      <Route
        path="/dashboard"
        element={
          <Protected>
            <StatisticsCalculatorLanding />
          </Protected>
        }
      />

      <Route
        path="/survey"
        element={
          <Protected>
            <SurveyPage />
          </Protected>
        }
      />

      <Route
        path="/datasets"
        element={
          <Protected>
            <DatasetsPage />
          </Protected>
        }
      />

      <Route
        path="/datasets/new"
        element={
          <Protected>
            <DataWorkspacePage />
          </Protected>
        }
      />

      <Route
        path="/datasets/:datasetId/workspace"
        element={
          <Protected>
            <DataWorkspacePage />
          </Protected>
        }
      />

      <Route
        path="/datasets/:datasetId/prepare"
        element={
          <Protected>
            <DataPreparationPage />
          </Protected>
        }
      />

      <Route
        path="/analysis"
        element={
          <Protected>
            <AnalysisPage />
          </Protected>
        }
      />

      <Route
        path="/visualizations"
        element={
          <Protected>
            <VisualizationsPage />
          </Protected>
        }
      />

      <Route
        path="/reports"
        element={
          <Protected>
            <ReportsPage />
          </Protected>
        }
      />

      {/* Old user-facing AI/ML route now uses Predictive Analytics. */}
      <Route
        path="/ml"
        element={
          <Protected>
            <Navigate
              to="/datasets?method=predictive"
              replace
            />
          </Protected>
        }
      />

      {/* Notifications are available only from the Admin Console. */}
      <Route
        path="/notifications"
        element={
          <AdminProtected>
            <NotificationsPage />
          </AdminProtected>
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

      <Route
        path="*"
        element={
          <Navigate
            to="/"
            replace
          />
        }
      />
    </Routes>
  )
}
