import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

let refreshPromise = null

function clearAuth() {
  localStorage.removeItem(
    'ssas_access_token'
  )

  localStorage.removeItem(
    'ssas_refresh_token'
  )

  localStorage.removeItem(
    'ssas_user'
  )
}

api.interceptors.request.use(
  (config) => {
    const token =
      localStorage.getItem(
        'ssas_access_token'
      )

    if (token) {
      config.headers.Authorization =
        `Bearer ${token}`
    }

    return config
  },

  (error) =>
    Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,

  async (error) => {
    const originalRequest =
      error.config

    const status =
      error.response?.status

    const url =
      originalRequest?.url || ''

    const isAuthRequest =
      url.includes('/auth/login') ||
      url.includes('/auth/google') ||
      url.includes('/auth/register') ||
      url.includes('/auth/refresh')

    if (
      status !== 401 ||
      originalRequest?._retry ||
      isAuthRequest
    ) {
      return Promise.reject(error)
    }

    const refreshToken =
      localStorage.getItem(
        'ssas_refresh_token'
      )

    if (!refreshToken) {
      clearAuth()
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      if (!refreshPromise) {
        refreshPromise = axios
          .post(
            '/api/auth/refresh',
            {
              refresh_token:
                refreshToken,
            }
          )
          .then((response) => {
            const data =
              response.data

            localStorage.setItem(
              'ssas_access_token',
              data.access_token
            )

            if (
              data.refresh_token
            ) {
              localStorage.setItem(
                'ssas_refresh_token',
                data.refresh_token
              )
            }

            return data.access_token
          })
          .finally(() => {
            refreshPromise = null
          })
      }

      const newToken =
        await refreshPromise

      originalRequest.headers.Authorization =
        `Bearer ${newToken}`

      return api(originalRequest)

    } catch (refreshError) {
      clearAuth()

      if (
        window.location.pathname !==
        '/login'
      ) {
        window.location.assign(
          '/login'
        )
      }

      return Promise.reject(
        refreshError
      )
    }
  }
)

export default api
