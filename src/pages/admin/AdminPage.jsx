import {
  useEffect,
  useState,
} from 'react'

import {
  Activity,
  BarChart3,
  Bell,
  BrainCircuit,
  Database,
  FileText,
  RefreshCw,
  ShieldCheck,
  Users,
} from 'lucide-react'

import {
  useNavigate,
} from 'react-router-dom'

import api from '../../api/api'

import {
  useAuth,
} from '../../context/AuthContext'


export default function AdminPage() {
  const {
    user,
  } = useAuth()

  const navigate =
    useNavigate()

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState('')

  const [stats, setStats] =
    useState({
      datasets: 0,
      reports: 0,
      notifications: 0,
      unread: 0,
      systemStatus: 'Checking',
    })


  const loadAdminData =
    async () => {
      setLoading(true)
      setError('')

      try {
        const results =
          await Promise.allSettled([
            api.get('/datasets'),
            api.get('/reports'),
            api.get('/notifications'),
            api.get(
              '/notifications/unread-count'
            ),
            api.get('/health'),
          ])

        const [
          datasetsResult,
          reportsResult,
          notificationsResult,
          unreadResult,
          healthResult,
        ] = results

        setStats({
          datasets:
            datasetsResult.status ===
            'fulfilled'
              ? (
                  datasetsResult
                    .value.data.total ??
                  datasetsResult
                    .value.data.count ??
                  0
                )
              : 0,

          reports:
            reportsResult.status ===
            'fulfilled'
              ? (
                  reportsResult
                    .value.data.count ??
                  reportsResult
                    .value.data.total ??
                  0
                )
              : 0,

          notifications:
            notificationsResult.status ===
            'fulfilled'
              ? (
                  notificationsResult
                    .value.data.count ??
                  notificationsResult
                    .value.data.total ??
                  0
                )
              : 0,

          unread:
            unreadResult.status ===
            'fulfilled'
              ? (
                  unreadResult
                    .value.data
                    .unread_count ??
                  0
                )
              : 0,

          systemStatus:
            healthResult.status ===
            'fulfilled'
              ? (
                  healthResult
                    .value.data.status ??
                  'Online'
                )
              : 'Unavailable',
        })

      } catch (err) {
        console.error(
          'Admin dashboard error:',
          err
        )

        setError(
          'Unable to load administrator dashboard.'
        )

      } finally {
        setLoading(false)
      }
    }


  useEffect(() => {
    loadAdminData()
  }, [])


  const cards = [
    {
      title: 'Datasets',
      value: stats.datasets,
      icon: Database,
      route: '/datasets',
    },
    {
      title: 'Reports',
      value: stats.reports,
      icon: FileText,
      route: '/reports',
    },
    {
      title: 'Notifications',
      value: stats.notifications,
      icon: Bell,
      route: '/notifications',
    },
    {
      title: 'Unread Alerts',
      value: stats.unread,
      icon: Activity,
      route: '/notifications',
    },
  ]


  return (
    <div className="admin-page">

      <header className="admin-header">

        <div>
          <div className="admin-title-row">
            <ShieldCheck size={30} />

            <h1>
              SSAS Admin Console
            </h1>
          </div>

          <p>
            System administration,
            monitoring and management.
          </p>
        </div>

        <div className="admin-user-card">
          <span>
            Administrator
          </span>

          <strong>
            {user?.first_name}{' '}
            {user?.last_name}
          </strong>

          <small>
            {user?.email}
          </small>
        </div>

      </header>


      {error && (
        <div className="alert error">
          {error}
        </div>
      )}


      <section className="admin-status-bar">

        <div>
          <Activity size={20} />

          <span>
            System Status:
          </span>

          <strong>
            {stats.systemStatus}
          </strong>
        </div>

        <button
          type="button"
          className="admin-refresh-button"
          onClick={loadAdminData}
          disabled={loading}
        >
          <RefreshCw
            size={17}
            className={
              loading
                ? 'admin-spin'
                : ''
            }
          />

          {loading
            ? 'Refreshing...'
            : 'Refresh'}
        </button>

      </section>


      <section className="admin-stat-grid">

        {cards.map((card) => {
          const Icon = card.icon

          return (
            <button
              key={card.title}
              type="button"
              className="admin-stat-card"
              onClick={() =>
                navigate(card.route)
              }
            >
              <div className="admin-stat-icon">
                <Icon size={24} />
              </div>

              <div>
                <span>
                  {card.title}
                </span>

                <strong>
                  {loading
                    ? '...'
                    : card.value}
                </strong>
              </div>
            </button>
          )
        })}

      </section>


      <section className="admin-section">

        <div className="admin-section-heading">
          <h2>
            Administration Modules
          </h2>

          <p>
            Manage SSAS system
            resources and services.
          </p>
        </div>


        <div className="admin-module-grid">

          <button
            className="admin-module-card"
            onClick={() =>
              navigate('/datasets')
            }
          >
            <Database size={28} />

            <div>
              <h3>
                Dataset Management
              </h3>

              <p>
                View and manage
                uploaded datasets.
              </p>
            </div>
          </button>


          <button
            className="admin-module-card"
            onClick={() =>
              navigate('/analysis')
            }
          >
            <BarChart3 size={28} />

            <div>
              <h3>
                Statistical Analysis
              </h3>

              <p>
                Access statistical
                analysis tools.
              </p>
            </div>
          </button>


          <button
            className="admin-module-card"
            onClick={() =>
              navigate('/ml')
            }
          >
            <BrainCircuit size={28} />

            <div>
              <h3>
                AI / ML Management
              </h3>

              <p>
                View machine learning
                operations and models.
              </p>
            </div>
          </button>


          <button
            className="admin-module-card"
            onClick={() =>
              navigate('/reports')
            }
          >
            <FileText size={28} />

            <div>
              <h3>
                Report Management
              </h3>

              <p>
                Generate and manage
                system reports.
              </p>
            </div>
          </button>


          <button
            className="admin-module-card"
            onClick={() =>
              navigate(
                '/notifications'
              )
            }
          >
            <Bell size={28} />

            <div>
              <h3>
                Notifications
              </h3>

              <p>
                Monitor alerts and
                notification delivery.
              </p>
            </div>
          </button>


          <button
            className="
              admin-module-card
              admin-module-disabled
            "
            disabled
          >
            <Users size={28} />

            <div>
              <h3>
                User Management
              </h3>

              <p>
                User administration
                API will be connected
                in the next stage.
              </p>
            </div>
          </button>

        </div>

      </section>

    </div>
  )
}
