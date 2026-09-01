import {
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import ProtectedRoute
  from './components/ProtectedRoute'

import AdminRoute
  from './components/AdminRoute'


// ==========================================================
// PUBLIC PAGES
// ==========================================================

import StatisticsCalculatorLanding
  from './pages/StatisticsCalculatorLanding'

import LoginPage
  from './pages/auth/LoginPage'

import RegisterPage
  from './pages/auth/RegisterPage'


// ==========================================================
// PROTECTED PAGES
// ==========================================================

import SurveyPage
  from './pages/survey/SurveyPage'

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


// ==========================================================
// ADMIN PAGES
// ==========================================================

import AdminPage
  from './pages/admin/AdminPage'

import UserManagementPage
  from './pages/admin/UserManagementPage'


// ==========================================================
// PROTECTED WRAPPER
// ==========================================================

function Protected({
  children,
}) {

  return (

    <ProtectedRoute>

      {children}

    </ProtectedRoute>

  )
}


// ==========================================================
// ADMIN WRAPPER
// ==========================================================

function AdminProtected({
  children,
}) {

  return (

    <AdminRoute>

      {children}

    </AdminRoute>

  )
}


// ==========================================================
// APP
// ==========================================================

export default function App() {

  return (

    <Routes>


      {/* ==================================================
          PUBLIC LANDING PAGE
          ================================================== */}

      <Route
        path="/"
        element={
          <StatisticsCalculatorLanding />
        }
      />


      <Route
        path="/statistics-calculator"
        element={
          <StatisticsCalculatorLanding />
        }
      />


      {/* ==================================================
          AUTHENTICATION
          ================================================== */}

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


      {/* ==================================================
          DASHBOARD
          ================================================== */}

      <Route
        path="/dashboard"
        element={

          <Protected>

            <StatisticsCalculatorLanding />

          </Protected>

        }
      />


      {/* ==================================================
          SURVEY
          ================================================== */}

      <Route
        path="/survey"
        element={

          <Protected>

            <SurveyPage />

          </Protected>

        }
      />


      {/* ==================================================
          DATASETS
          ================================================== */}

      <Route
        path="/datasets"
        element={

          <Protected>

            <DatasetsPage />

          </Protected>

        }
      />


      {/* ==================================================
          STATISTICAL ANALYSIS
          ================================================== */}

      <Route
        path="/analysis"
        element={

          <Protected>

            <AnalysisPage />

          </Protected>

        }
      />


      {/* ==================================================
          AI / ML
          ================================================== */}

      <Route
        path="/ml"
        element={

          <Protected>

            <MLPage />

          </Protected>

        }
      />


      {/* ==================================================
          VISUALIZATION
          ================================================== */}

      <Route
        path="/visualizations"
        element={

          <Protected>

            <VisualizationsPage />

          </Protected>

        }
      />


      {/* ==================================================
          REPORTS
          ================================================== */}

      <Route
        path="/reports"
        element={

          <Protected>

            <ReportsPage />

          </Protected>

        }
      />


      {/* ==================================================
          NOTIFICATIONS
          ================================================== */}

      <Route
        path="/notifications"
        element={

          <Protected>

            <NotificationsPage />

          </Protected>

        }
      />


      {/* ==================================================
          ADMIN
          ================================================== */}

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


      {/* ==================================================
          UNKNOWN ROUTES
          ================================================== */}

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
