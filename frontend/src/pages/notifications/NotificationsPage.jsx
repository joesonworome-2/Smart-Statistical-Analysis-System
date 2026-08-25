import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Bell,
  Check,
  CheckCheck,
  FileText,
  Inbox,
  LoaderCircle,
  Mail,
  MailCheck,
  MailX,
  RefreshCw,
} from 'lucide-react'

import api from '../../api/api'
import AppShell from '../../components/AppShell'


const FILTERS = [
  {
    value: 'all',
    label: 'All',
  },
  {
    value: 'unread',
    label: 'Unread',
  },
  {
    value: 'report_ready',
    label: 'Reports',
  },
  {
    value: 'test',
    label: 'Tests',
  },
]


export default function NotificationsPage() {
  const [notifications, setNotifications] =
    useState([])

  const [unreadCount, setUnreadCount] =
    useState(0)

  const [filter, setFilter] =
    useState('all')

  const [loading, setLoading] =
    useState(true)

  const [refreshing, setRefreshing] =
    useState(false)

  const [markingId, setMarkingId] =
    useState(null)

  const [markingAll, setMarkingAll] =
    useState(false)

  const [error, setError] =
    useState('')


  const filteredNotifications =
    useMemo(
      () => {
        if (
          filter === 'unread'
        ) {
          return notifications.filter(
            (notification) =>
              !notification.is_read
          )
        }

        if (
          filter === 'report_ready'
        ) {
          return notifications.filter(
            (notification) =>
              notification.type ===
              'report_ready'
          )
        }

        if (
          filter === 'test'
        ) {
          return notifications.filter(
            (notification) =>
              notification.type ===
                'test' ||
              notification.type ===
                'system_test'
          )
        }

        return notifications
      },
      [
        notifications,
        filter,
      ]
    )


  const sentCount =
    useMemo(
      () =>
        notifications.filter(
          (notification) =>
            notification.email_status ===
            'sent'
        ).length,
      [notifications]
    )


  const failedCount =
    useMemo(
      () =>
        notifications.filter(
          (notification) =>
            notification.email_status ===
            'failed'
        ).length,
      [notifications]
    )


  const reportCount =
    useMemo(
      () =>
        notifications.filter(
          (notification) =>
            notification.type ===
            'report_ready'
        ).length,
      [notifications]
    )


  const loadNotifications =
    async (
      background = false
    ) => {

      if (background) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      setError('')

      try {
        const [
          notificationResponse,
          unreadResponse,
        ] = await Promise.all([
          api.get('/notifications'),

          api.get(
            '/notifications/unread-count'
          ),
        ])

        setNotifications(
          notificationResponse
            .data
            .notifications || []
        )

        setUnreadCount(
          unreadResponse
            .data
            .unread_count ?? 0
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Unable to load notifications.'
          )
        )

      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    }


  useEffect(() => {
    loadNotifications()
  }, [])


  const markAsRead =
    async (
      notificationId
    ) => {

      setMarkingId(
        notificationId
      )

      setError('')

      try {
        await api.patch(
          `/notifications/${notificationId}/read`
        )

        setNotifications(
          (previous) =>
            previous.map(
              (notification) =>
                notification
                  .notification_id ===
                  notificationId
                  ? {
                      ...notification,
                      is_read: true,
                    }
                  : notification
            )
        )

        setUnreadCount(
          (previous) =>
            Math.max(
              0,
              previous - 1
            )
        )

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Unable to mark notification as read.'
          )
        )

      } finally {
        setMarkingId(null)
      }
    }


  const markAllAsRead =
    async () => {

      const unread =
        notifications.filter(
          (notification) =>
            !notification.is_read
        )

      if (
        unread.length === 0
      ) {
        return
      }

      setMarkingAll(true)
      setError('')

      try {
        await Promise.all(
          unread.map(
            (notification) =>
              api.patch(
                `/notifications/${notification.notification_id}/read`
              )
          )
        )

        setNotifications(
          (previous) =>
            previous.map(
              (notification) => ({
                ...notification,
                is_read: true,
              })
            )
        )

        setUnreadCount(0)

      } catch (err) {
        setError(
          getErrorMessage(
            err,
            'Unable to mark all notifications as read.'
          )
        )

        await loadNotifications(
          true
        )

      } finally {
        setMarkingAll(false)
      }
    }


  if (loading) {
    return (
      <AppShell>

        <div className="notification-loading">

          <LoaderCircle
            size={30}
            className="spin-icon"
          />

          Loading notifications...

        </div>

      </AppShell>
    )
  }


  return (
    <AppShell>

      <header className="notification-header">

        <div>

          <span className="eyebrow dark">
            NOTIFICATION CENTER
          </span>

          <h1>
            Notifications
          </h1>

          <p>
            View report-ready alerts,
            in-app messages and email
            delivery activity.
          </p>

        </div>


        <div className="notification-header-icon">

          <Bell size={29} />

          {unreadCount > 0 && (
            <span>
              {unreadCount}
            </span>
          )}

        </div>

      </header>


      {error && (
        <div className="alert error">
          {error}
        </div>
      )}


      <section className="notification-stats">

        <StatCard
          icon={<Inbox />}
          label="Total"
          value={
            notifications.length
          }
        />

        <StatCard
          icon={<Bell />}
          label="Unread"
          value={unreadCount}
        />

        <StatCard
          icon={<FileText />}
          label="Report Alerts"
          value={reportCount}
        />

        <StatCard
          icon={<MailCheck />}
          label="Emails Sent"
          value={sentCount}
        />

        <StatCard
          icon={<MailX />}
          label="Email Failures"
          value={failedCount}
        />

      </section>


      <section className="notification-panel">

        <div className="notification-toolbar">

          <div className="notification-filters">

            {FILTERS.map(
              (item) => (

                <button
                  key={item.value}
                  className={
                    filter ===
                    item.value
                      ? 'notification-filter active'
                      : 'notification-filter'
                  }
                  onClick={() =>
                    setFilter(
                      item.value
                    )
                  }
                >
                  {item.label}
                </button>

              )
            )}

          </div>


          <div className="notification-actions">

            <button
              className="notification-secondary-button"
              onClick={() =>
                loadNotifications(true)
              }
              disabled={refreshing}
            >

              <RefreshCw
                size={16}
                className={
                  refreshing
                    ? 'spin-icon'
                    : ''
                }
              />

              Refresh

            </button>


            <button
              className="notification-read-all"
              onClick={
                markAllAsRead
              }
              disabled={
                unreadCount === 0 ||
                markingAll
              }
            >

              {markingAll ? (
                <LoaderCircle
                  size={16}
                  className="spin-icon"
                />
              ) : (
                <CheckCheck
                  size={16}
                />
              )}

              Mark all read

            </button>

          </div>

        </div>


        {filteredNotifications.length ===
        0 ? (

          <div className="notification-empty">

            <Bell size={44} />

            <h3>
              No notifications
            </h3>

            <p>
              There are no notifications
              matching this filter.
            </p>

          </div>

        ) : (

          <div className="notification-list">

            {
              filteredNotifications.map(
                (notification) => (

                  <NotificationItem
                    key={
                      notification
                        .notification_id
                    }
                    notification={
                      notification
                    }
                    marking={
                      markingId ===
                      notification
                        .notification_id
                    }
                    onMarkRead={
                      markAsRead
                    }
                  />

                )
              )
            }

          </div>

        )}

      </section>

    </AppShell>
  )
}


function NotificationItem({
  notification,
  marking,
  onMarkRead,
}) {

  const reportReady =
    notification.type ===
    'report_ready'

  return (
    <article
      className={
        notification.is_read
          ? 'notification-item'
          : 'notification-item unread'
      }
    >

      <div
        className={
          reportReady
            ? 'notification-type-icon report'
            : 'notification-type-icon mail'
        }
      >

        {reportReady ? (
          <FileText size={20} />
        ) : (
          <Mail size={20} />
        )}

      </div>


      <div className="notification-body">

        <div className="notification-title-row">

          <div>

            <div className="notification-title">

              {!notification.is_read && (
                <span className="notification-unread-dot" />
              )}

              <strong>
                {notification.title}
              </strong>

            </div>


            <div className="notification-meta">

              <span>
                {
                  humanize(
                    notification.type
                  )
                }
              </span>

              <span>
                {
                  formatDate(
                    notification.created_at
                  )
                }
              </span>

            </div>

          </div>


          <EmailStatus
            status={
              notification.email_status
            }
          />

        </div>


        <p className="notification-message">
          {notification.message}
        </p>


        {notification
          .metadata
          ?.file_name && (

          <div className="notification-report-file">

            <FileText size={15} />

            <span>
              {
                notification
                  .metadata
                  .file_name
              }
            </span>

          </div>

        )}


        {notification.email_error && (

          <div className="notification-email-error">

            <MailX size={15} />

            <span>
              {
                notification
                  .email_error
              }
            </span>

          </div>

        )}


        <div className="notification-footer">

          <span>
            Channel:{' '}
            <strong>
              {
                humanize(
                  notification.channel
                )
              }
            </strong>
          </span>


          {!notification.is_read && (

            <button
              onClick={() =>
                onMarkRead(
                  notification
                    .notification_id
                )
              }
              disabled={marking}
            >

              {marking ? (
                <LoaderCircle
                  size={14}
                  className="spin-icon"
                />
              ) : (
                <Check size={14} />
              )}

              Mark as read

            </button>

          )}

        </div>

      </div>

    </article>
  )
}


function EmailStatus({
  status,
}) {

  if (
    status === 'sent'
  ) {
    return (
      <span className="email-status sent">
        <MailCheck size={13} />
        Sent
      </span>
    )
  }


  if (
    status === 'failed'
  ) {
    return (
      <span className="email-status failed">
        <MailX size={13} />
        Failed
      </span>
    )
  }


  return (
    <span className="email-status neutral">
      In App
    </span>
  )
}


function StatCard({
  icon,
  label,
  value,
}) {
  return (
    <div className="notification-stat">

      <div>
        {icon}
      </div>

      <section>

        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>

      </section>

    </div>
  )
}


function humanize(
  value
) {
  return String(
    value || ''
  )
    .replaceAll('_', ' ')
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    )
}


function formatDate(
  value
) {
  if (!value) {
    return '-'
  }

  return new Date(
    value
  ).toLocaleString()
}


function getErrorMessage(
  error,
  fallback
) {

  const detail =
    error.response
      ?.data
      ?.detail

  if (
    typeof detail ===
    'string'
  ) {
    return detail
  }

  if (
    Array.isArray(detail)
  ) {
    return detail
      .map(
        (item) =>
          item.msg ||
          JSON.stringify(item)
      )
      .join(' ')
  }

  return (
    error.message ||
    fallback
  )
}
