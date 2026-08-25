import {
  useEffect,
  useState,
} from 'react'

import {
  Activity,
  Bell,
  BrainCircuit,
  Database,
  FileText,
  PieChart,
  ShieldCheck,
  User,
} from 'lucide-react'

import {
  useNavigate,
} from 'react-router-dom'

import api from '../../api/api'
import AppShell from '../../components/AppShell'
import { useAuth } from '../../context/AuthContext'


export default function DashboardPage() {
  const navigate = useNavigate()

  const {
    user,
  } = useAuth()

  const [stats, setStats] =
    useState({
      datasets: 0,
      reports: 0,
      notifications: 0,
    })

  const [
    systemHealthy,
    setSystemHealthy,
  ] = useState(null)


  useEffect(() => {

    const loadDashboard =
      async () => {

        const [
          datasetResult,
          reportResult,
          notificationResult,
          healthResult,
        ] = await Promise.allSettled([
          api.get('/datasets'),
          api.get('/reports'),
          api.get(
            '/notifications/unread-count'
          ),
          api.get('/health'),
        ])


        setStats({
          datasets:
            datasetResult.status ===
            'fulfilled'
              ? (
                  datasetResult
                    .value
                    .data
                    .total ?? 0
                )
              : 0,

          reports:
            reportResult.status ===
            'fulfilled'
              ? (
                  reportResult
                    .value
                    .data
                    .count ?? 0
                )
              : 0,

          notifications:
            notificationResult.status ===
            'fulfilled'
              ? (
                  notificationResult
                    .value
                    .data
                    .unread_count ??
                  notificationResult
                    .value
                    .data
                    .count ??
                  0
                )
              : 0,
        })


        if (
          healthResult.status ===
          'fulfilled'
        ) {
          setSystemHealthy(
            healthResult
              .value
              .data
              .status ===
              'healthy'
          )
        }

      }

    loadDashboard()

  }, [])


  return (
    <AppShell>

      <header className="dashboard-header">

        <div>
          <span className="eyebrow dark">
            OVERVIEW
          </span>

          <h1>
            Welcome, {user?.first_name}
          </h1>

          <p>
            Here is an overview of
            your statistical analysis
            workspace.
          </p>
        </div>


        <div className="user-profile">

          <div className="avatar">
            <User size={20} />
          </div>

          <div>
            <strong>
              {user?.first_name}{' '}
              {user?.last_name}
            </strong>

            <span>
              {user?.email}
            </span>
          </div>

        </div>

      </header>


      <section className="system-banner">

        <ShieldCheck size={22} />

        <div>
          <strong>
            SSAS Backend
          </strong>

          <span>
            {systemHealthy === true
              ? 'All services operational'
              : systemHealthy === false
                ? 'Some services unavailable'
                : 'Checking system status...'}
          </span>
        </div>

        <div
          className={
            systemHealthy
              ? 'status-dot online'
              : 'status-dot'
          }
        />

      </section>


      <section className="stats-grid">

        <StatCard
          icon={<Database />}
          title="Datasets"
          value={stats.datasets}
          text="Available datasets"
        />

        <StatCard
          icon={<FileText />}
          title="Reports"
          value={stats.reports}
          text="Generated reports"
        />

        <StatCard
          icon={<Bell />}
          title="Notifications"
          value={stats.notifications}
          text="Unread notifications"
        />

        <StatCard
          icon={<BrainCircuit />}
          title="AI / ML"
          value="Ready"
          text="Machine learning service"
        />

      </section>


      <section className="dashboard-content-grid">

        <div className="dashboard-panel">

          <div className="panel-header">
            <h2>Quick actions</h2>

            <p>
              Start working with
              your data.
            </p>
          </div>


          <div className="quick-actions">

            <QuickAction
              icon={<Database />}
              title="Upload Dataset"
              text="Import CSV or Excel data"
              onClick={() =>
                navigate('/datasets')
              }
            />

            <QuickAction
              icon={<Activity />}
              title="Run Analysis"
              text="Perform statistical tests"
              onClick={() =>
                navigate('/analysis')
              }
            />

            <QuickAction
              icon={<PieChart />}
              title="Create Visualization"
              text="Explore results visually"
              onClick={() =>
                navigate(
                  '/visualizations'
                )
              }
            />

            <QuickAction
              icon={<FileText />}
              title="Generate Report"
              text="Export analysis results"
              onClick={() =>
                navigate('/reports')
              }
            />

          </div>

        </div>


        <div className="dashboard-panel">

          <div className="panel-header">
            <h2>Account</h2>

            <p>
              Current authenticated
              user.
            </p>
          </div>


          <div className="account-details">

            <div>
              <span>Username</span>
              <strong>
                {user?.username}
              </strong>
            </div>

            <div>
              <span>Role</span>
              <strong>
                {user?.role}
              </strong>
            </div>

            <div>
              <span>Status</span>

              <strong className="active-text">
                {user?.is_active
                  ? 'Active'
                  : 'Inactive'}
              </strong>
            </div>

          </div>

        </div>

      </section>

    </AppShell>
  )
}


function StatCard({
  icon,
  title,
  value,
  text,
}) {
  return (
    <div className="stat-card">

      <div className="stat-icon">
        {icon}
      </div>

      <div>
        <span>{title}</span>
        <strong>{value}</strong>
        <small>{text}</small>
      </div>

    </div>
  )
}


function QuickAction({
  icon,
  title,
  text,
  onClick,
}) {
  return (
    <button
      className="quick-action"
      onClick={onClick}
    >

      <div className="quick-icon">
        {icon}
      </div>

      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>

    </button>
  )
}
