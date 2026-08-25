import {
  Activity,
  BarChart3,
  Bell,
  BrainCircuit,
  Database,
  FileText,
  LayoutDashboard,
  LogOut,
  PieChart,
  User,
} from 'lucide-react'

import {
  useLocation,
  useNavigate,
} from 'react-router-dom'

import { useAuth } from '../context/AuthContext'


const menuItems = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    label: 'Datasets',
    path: '/datasets',
    icon: Database,
  },
  {
    label: 'Statistical Analysis',
    path: '/analysis',
    icon: Activity,
  },
  {
    label: 'AI / ML Analysis',
    path: '/ml',
    icon: BrainCircuit,
  },
  {
    label: 'Visualizations',
    path: '/visualizations',
    icon: PieChart,
  },
  {
    label: 'Reports',
    path: '/reports',
    icon: FileText,
  },
  {
    label: 'Notifications',
    path: '/notifications',
    icon: Bell,
  },
]


export default function AppShell({
  children,
}) {
  const navigate = useNavigate()
  const location = useLocation()

  const {
    user,
    logout,
  } = useAuth()


  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }


  return (
    <div className="dashboard-shell">

      <aside className="sidebar">

        <div className="sidebar-brand">

          <div className="sidebar-logo">
            <BarChart3 size={24} />
          </div>

          <div>
            <strong>SSAS</strong>
            <span>
              Statistical Analysis
            </span>
          </div>

        </div>


        <nav className="sidebar-nav">

          {menuItems.map((item) => {
            const Icon = item.icon

            const active =
              location.pathname ===
              item.path

            return (
              <button
                key={item.path}
                className={
                  active
                    ? 'nav-item active'
                    : 'nav-item'
                }
                onClick={() =>
                  navigate(item.path)
                }
              >
                <Icon size={19} />

                {item.label}
              </button>
            )
          })}

        </nav>


        <div className="sidebar-user">

          <div className="sidebar-user-icon">
            <User size={17} />
          </div>

          <div>
            <strong>
              {user?.username}
            </strong>

            <span>
              {user?.role}
            </span>
          </div>

        </div>


        <button
          className="logout-button"
          onClick={handleLogout}
        >
          <LogOut size={19} />
          Sign out
        </button>

      </aside>


      <main className="dashboard-main">
        {children}
      </main>

    </div>
  )
}
