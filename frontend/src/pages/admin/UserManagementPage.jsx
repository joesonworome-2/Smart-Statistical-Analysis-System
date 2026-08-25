import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
  ArrowLeft,
  CheckCircle2,
  RefreshCw,
  Search,
  ShieldCheck,
  ShieldOff,
  UserCheck,
  UserCog,
  UserRound,
  Users,
  UserX,
} from 'lucide-react'

import {
  useNavigate,
} from 'react-router-dom'

import api from '../../api/api'

import {
  useAuth,
} from '../../context/AuthContext'


export default function UserManagementPage() {
  const navigate = useNavigate()

  const {
    user: currentUser,
  } = useAuth()

  const [usersList, setUsersList] =
    useState([])

  const [stats, setStats] =
    useState({
      total_users: 0,
      active_users: 0,
      inactive_users: 0,
      admins: 0,
      normal_users: 0,
      google_users: 0,
    })

  const [search, setSearch] =
    useState('')

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState('')

  const [success, setSuccess] =
    useState('')

  const [updatingId, setUpdatingId] =
    useState(null)


  const loadUsers = useCallback(
    async () => {
      setLoading(true)
      setError('')

      try {
        const [
          usersResponse,
          statsResponse,
        ] = await Promise.all([
          api.get(
            '/users/admin/list',
            {
              params: {
                search:
                  search.trim()
                  || undefined,
              },
            }
          ),

          api.get(
            '/users/admin/stats'
          ),
        ])

        setUsersList(
          usersResponse.data.users ||
          []
        )

        setStats(
          statsResponse.data
        )

      } catch (err) {
        console.error(
          'User management error:',
          err
        )

        setError(
          err.response?.data?.detail ||
          'Unable to load users.'
        )

      } finally {
        setLoading(false)
      }
    },
    [search]
  )


  useEffect(() => {
    loadUsers()
  }, [loadUsers])


  const changeRole = async (
    targetUser
  ) => {
    const newRole =
      targetUser.role === 'admin'
        ? 'user'
        : 'admin'

    const action =
      newRole === 'admin'
        ? 'promote'
        : 'demote'

    const confirmed =
      window.confirm(
        `Are you sure you want to ${action} ` +
        `${targetUser.email}?`
      )

    if (!confirmed) {
      return
    }

    setUpdatingId(
      targetUser.id
    )

    setError('')
    setSuccess('')

    try {
      await api.patch(
        `/users/admin/${targetUser.id}/role`,
        {
          role: newRole,
        }
      )

      setSuccess(
        `${targetUser.email} is now ${newRole}.`
      )

      await loadUsers()

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to update user role.'
      )

    } finally {
      setUpdatingId(null)
    }
  }


  const changeStatus = async (
    targetUser
  ) => {
    const newStatus =
      !targetUser.is_active

    const action =
      newStatus
        ? 'activate'
        : 'deactivate'

    const confirmed =
      window.confirm(
        `Are you sure you want to ${action} ` +
        `${targetUser.email}?`
      )

    if (!confirmed) {
      return
    }

    setUpdatingId(
      targetUser.id
    )

    setError('')
    setSuccess('')

    try {
      await api.patch(
        `/users/admin/${targetUser.id}/status`,
        {
          is_active: newStatus,
        }
      )

      setSuccess(
        `${targetUser.email} has been ${action}d.`
      )

      await loadUsers()

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to update account status.'
      )

    } finally {
      setUpdatingId(null)
    }
  }


  const statCards = [
    {
      title: 'Total Users',
      value: stats.total_users,
      icon: Users,
    },
    {
      title: 'Active Users',
      value: stats.active_users,
      icon: UserCheck,
    },
    {
      title: 'Inactive Users',
      value: stats.inactive_users,
      icon: UserX,
    },
    {
      title: 'Administrators',
      value: stats.admins,
      icon: ShieldCheck,
    },
  ]


  return (
    <div className="user-management-page">

      <header className="user-management-header">

        <div>

          <button
            type="button"
            className="admin-back-button"
            onClick={() =>
              navigate('/admin')
            }
          >
            <ArrowLeft size={17} />
            Admin Console
          </button>

          <h1>
            User Management
          </h1>

          <p>
            Manage SSAS user accounts,
            roles and account status.
          </p>

        </div>

        <button
          type="button"
          className="admin-refresh-button"
          onClick={loadUsers}
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

          Refresh
        </button>

      </header>


      {error && (
        <div className="alert error">
          {error}
        </div>
      )}


      {success && (
        <div className="alert success">
          <CheckCircle2 size={17} />
          {success}
        </div>
      )}


      <section className="admin-stat-grid">

        {statCards.map(
          (card) => {
            const Icon = card.icon

            return (
              <div
                className="admin-stat-card"
                key={card.title}
              >
                <div
                  className="admin-stat-icon"
                >
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
              </div>
            )
          }
        )}

      </section>


      <section className="user-management-panel">

        <div className="user-toolbar">

          <div className="admin-search-box">
            <Search size={18} />

            <input
              type="search"
              placeholder={
                'Search by name, email or username'
              }
              value={search}
              onChange={(event) =>
                setSearch(
                  event.target.value
                )
              }
            />
          </div>

          <div className="user-count-label">
            {usersList.length}
            {' '}
            user
            {usersList.length !== 1
              ? 's'
              : ''}
          </div>

        </div>


        <div className="admin-table-wrapper">

          <table className="admin-users-table">

            <thead>
              <tr>
                <th>User</th>
                <th>Username</th>
                <th>Provider</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>


            <tbody>

              {loading ? (
                <tr>
                  <td
                    colSpan="7"
                    className="admin-empty-row"
                  >
                    Loading users...
                  </td>
                </tr>
              ) : usersList.length === 0 ? (
                <tr>
                  <td
                    colSpan="7"
                    className="admin-empty-row"
                  >
                    No users found.
                  </td>
                </tr>
              ) : (
                usersList.map(
                  (targetUser) => {
                    const isSelf =
                      currentUser?.id ===
                      targetUser.id

                    const isUpdating =
                      updatingId ===
                      targetUser.id

                    return (
                      <tr
                        key={targetUser.id}
                      >

                        <td>
                          <div
                            className="admin-user-info"
                          >
                            <div
                              className="admin-user-avatar"
                            >
                              <UserRound
                                size={19}
                              />
                            </div>

                            <div>
                              <strong>
                                {
                                  targetUser
                                    .first_name
                                }{' '}
                                {
                                  targetUser
                                    .last_name
                                }
                              </strong>

                              <span>
                                {
                                  targetUser
                                    .email
                                }
                              </span>

                              {isSelf && (
                                <small>
                                  You
                                </small>
                              )}
                            </div>
                          </div>
                        </td>


                        <td>
                          {
                            targetUser
                              .username
                          }
                        </td>


                        <td>
                          <span
                            className="admin-provider-badge"
                          >
                            {
                              targetUser
                                .auth_provider ||
                              'password'
                            }
                          </span>
                        </td>


                        <td>
                          <span
                            className={
                              targetUser.role ===
                              'admin'
                                ? 'admin-role-badge admin'
                                : 'admin-role-badge user'
                            }
                          >
                            {
                              targetUser.role
                            }
                          </span>
                        </td>


                        <td>
                          <span
                            className={
                              targetUser
                                .is_active
                                ? 'admin-status-badge active'
                                : 'admin-status-badge inactive'
                            }
                          >
                            {
                              targetUser
                                .is_active
                                ? 'Active'
                                : 'Inactive'
                            }
                          </span>
                        </td>


                        <td>
                          {
                            targetUser
                              .created_at
                              ? new Date(
                                  targetUser
                                    .created_at
                                )
                                  .toLocaleDateString()
                              : '—'
                          }
                        </td>


                        <td>
                          <div
                            className="admin-user-actions"
                          >

                            <button
                              type="button"
                              className="admin-action-button"
                              disabled={
                                isUpdating ||
                                (
                                  isSelf &&
                                  targetUser.role ===
                                  'admin'
                                )
                              }
                              onClick={() =>
                                changeRole(
                                  targetUser
                                )
                              }
                              title={
                                targetUser.role ===
                                'admin'
                                  ? 'Demote to user'
                                  : 'Promote to admin'
                              }
                            >
                              {
                                targetUser.role ===
                                'admin'
                                  ? (
                                    <ShieldOff
                                      size={16}
                                    />
                                  )
                                  : (
                                    <UserCog
                                      size={16}
                                    />
                                  )
                              }

                              {
                                targetUser.role ===
                                'admin'
                                  ? 'Demote'
                                  : 'Promote'
                              }
                            </button>


                            <button
                              type="button"
                              className={
                                targetUser
                                  .is_active
                                  ? 'admin-action-button danger'
                                  : 'admin-action-button success'
                              }
                              disabled={
                                isUpdating ||
                                isSelf
                              }
                              onClick={() =>
                                changeStatus(
                                  targetUser
                                )
                              }
                            >
                              {
                                targetUser
                                  .is_active
                                  ? (
                                    <>
                                      <UserX
                                        size={16}
                                      />
                                      Deactivate
                                    </>
                                  )
                                  : (
                                    <>
                                      <UserCheck
                                        size={16}
                                      />
                                      Activate
                                    </>
                                  )
                              }
                            </button>

                          </div>
                        </td>

                      </tr>
                    )
                  }
                )
              )}

            </tbody>

          </table>

        </div>

      </section>

    </div>
  )
}
