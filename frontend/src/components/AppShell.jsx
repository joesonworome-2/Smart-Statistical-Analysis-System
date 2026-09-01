import {
  BarChart3,
  Bell,
  Brain,
  ClipboardList,
  Database,
  FileText,
  LogOut,
  Search,
  User,
} from 'lucide-react'

import {
  useLocation,
  useNavigate,
} from 'react-router-dom'

import {
  useAuth,
} from '../context/AuthContext'

import './AppShell.css'


// ==========================================================
// NAVIGATION
// ==========================================================

const NAVIGATION_ITEMS = [

  {
    label:
      'Statistics Calculator',

    path:
      '/dashboard',

    icon:
      BarChart3,
  },

  {
    label:
      'Survey',

    path:
      '/survey',

    icon:
      ClipboardList,
  },

  {
    label:
      'Datasets',

    path:
      '/datasets',

    icon:
      Database,
  },

  {
    label:
      'Analysis',

    path:
      '/analysis',

    icon:
      BarChart3,
  },

  {
    label:
      'AI / ML',

    path:
      '/ml',

    icon:
      Brain,
  },

  {
    label:
      'Visualization',

    path:
      '/visualizations',

    icon:
      BarChart3,
  },

  {
    label:
      'Reports',

    path:
      '/reports',

    icon:
      FileText,
  },

  {
    label:
      'Notifications',

    path:
      '/notifications',

    icon:
      Bell,
  },

]


// ==========================================================
// APP SHELL
// ==========================================================

export default function AppShell({
  children,
}) {

  const navigate =
    useNavigate()


  const location =
    useLocation()


  const {
    user,
    logout,
  } = useAuth()


  // ========================================================
  // ACTIVE NAVIGATION
  // ========================================================

  const isActive =
    (
      path
    ) => {

      return (
        location.pathname ===
        path
      )
    }


  // ========================================================
  // LOGOUT
  // ========================================================

  const handleLogout =
    async () => {

      try {

        await logout()

      } catch (
        error
      ) {

        console.error(
          'Logout failed:',
          error
        )

      } finally {

        navigate(
          '/'
        )
      }
    }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <div className="ssas-shell">


      {/* ==================================================
          TOP NAVIGATION
          ================================================== */}

      <header className="ssas-topbar">


        {/* BRAND */}

        <button
          type="button"

          className="ssas-topbar-brand"

          onClick={() =>
            navigate(
              '/dashboard'
            )
          }
        >

          <BarChart3
            size={39}
          />


          <div>

            <strong>
              SSAS
            </strong>

            <span>
              Smart Statistical Analysis System
            </span>

          </div>

        </button>


        {/* NAVIGATION */}

        <nav className="ssas-topbar-navigation">


          {
            NAVIGATION_ITEMS.map(
              (
                item
              ) => {

                const Icon =
                  item.icon


                return (

                  <button
                    key={
                      item.path
                    }

                    type="button"

                    className={
                      isActive(
                        item.path
                      )
                        ?
                        'active'
                        :
                        ''
                    }

                    onClick={() =>
                      navigate(
                        item.path
                      )
                    }
                  >

                    <Icon
                      className="ssas-nav-mobile-icon"
                      size={17}
                    />

                    <span>
                      {
                        item.label
                      }
                    </span>

                  </button>

                )
              }
            )
          }


        </nav>


        {/* USER */}

        <div className="ssas-topbar-actions">


          <button
            type="button"

            className="ssas-user-button"
          >

            <User
              size={19}
            />

            <span>

              {
                user?.username
                ||
                user?.name
                ||
                'User'
              }

            </span>

          </button>


          <button
            type="button"

            className="ssas-signout-button"

            onClick={
              handleLogout
            }
          >

            <LogOut
              size={19}
            />

            <span>
              Sign out
            </span>

          </button>


          <button
            type="button"

            className="ssas-search-button"

            title="Statistics Calculator"

            onClick={() =>
              navigate(
                '/dashboard'
              )
            }
          >

            <Search
              size={23}
            />

          </button>


        </div>


      </header>


      {/* ==================================================
          PAGE CONTENT
          ================================================== */}

      <main className="ssas-shell-content">

        {children}

      </main>


    </div>

  )
}
