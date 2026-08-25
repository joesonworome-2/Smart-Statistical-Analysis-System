import {
  createContext,
  useContext,
  useEffect,
  useState,
} from 'react'

import api from '../api/api'

const AuthContext = createContext(null)

function clearStoredAuth() {
  localStorage.removeItem('ssas_access_token')
  localStorage.removeItem('ssas_refresh_token')
  localStorage.removeItem('ssas_user')
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored =
        localStorage.getItem('ssas_user')

      return stored
        ? JSON.parse(stored)
        : null
    } catch {
      return null
    }
  })

  const [loading, setLoading] =
    useState(true)

  const saveUser = (userData) => {
    setUser(userData)

    localStorage.setItem(
      'ssas_user',
      JSON.stringify(userData)
    )
  }

  const saveTokens = (
    accessToken,
    refreshToken
  ) => {
    localStorage.setItem(
      'ssas_access_token',
      accessToken
    )

    localStorage.setItem(
      'ssas_refresh_token',
      refreshToken
    )
  }

  const loadCurrentUser = async () => {
    const response =
      await api.get('/auth/me')

    saveUser(response.data)

    return response.data
  }

  const login = async (
    email,
    password
  ) => {
    const response =
      await api.post(
        '/auth/login',
        {
          email,
          password,
        }
      )

    const {
      access_token,
      refresh_token,
    } = response.data

    saveTokens(
      access_token,
      refresh_token
    )

    return await loadCurrentUser()
  }

  const googleLogin = async (
    credential
  ) => {
    const response =
      await api.post(
        '/auth/google',
        {
          credential,
        }
      )

    const {
      access_token,
      refresh_token,
    } = response.data

    saveTokens(
      access_token,
      refresh_token
    )

    return await loadCurrentUser()
  }

  const register = async (
    formData
  ) => {
    const response =
      await api.post(
        '/auth/register',
        formData
      )

    return response.data
  }

  const logout = async () => {
    const refreshToken =
      localStorage.getItem(
        'ssas_refresh_token'
      )

    try {
      if (refreshToken) {
        await api.post(
          '/auth/logout',
          {
            refresh_token:
              refreshToken,
          }
        )
      }
    } catch (error) {
      console.warn(
        'Server logout failed:',
        error
      )
    } finally {
      clearStoredAuth()
      setUser(null)
    }
  }

  useEffect(() => {
    const initializeAuth =
      async () => {
        const accessToken =
          localStorage.getItem(
            'ssas_access_token'
          )

        const refreshToken =
          localStorage.getItem(
            'ssas_refresh_token'
          )

        if (
          !accessToken &&
          !refreshToken
        ) {
          setLoading(false)
          return
        }

        try {
          await loadCurrentUser()
        } catch {
          clearStoredAuth()
          setUser(null)
        } finally {
          setLoading(false)
        }
      }

    initializeAuth()
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        googleLogin,
        register,
        logout,
        loadCurrentUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context =
    useContext(AuthContext)

  if (!context) {
    throw new Error(
      'useAuth must be used inside AuthProvider'
    )
  }

  return context
}
