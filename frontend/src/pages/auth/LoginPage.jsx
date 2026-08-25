import {
  useState,
} from 'react'

import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from 'react-router-dom'

import {
  GoogleLogin,
} from '@react-oauth/google'

import {
  BarChart3,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
} from 'lucide-react'

import {
  useAuth,
} from '../../context/AuthContext'

export default function LoginPage() {
  const {
    user,
    login,
    googleLogin,
  } = useAuth()

  const navigate =
    useNavigate()

  const location =
    useLocation()

  const [email, setEmail] =
    useState('')

  const [password, setPassword] =
    useState('')

  const [
    showPassword,
    setShowPassword,
  ] = useState(false)

  const [error, setError] =
    useState('')

  const [loading, setLoading] =
    useState(false)

  const [googleLoading, setGoogleLoading] =
    useState(false)

  if (user) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    )
  }

  const getDestination = () =>
    location.state?.from ||
    '/dashboard'

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault()

    setError('')
    setLoading(true)

    try {
      await login(
        email.trim(),
        password
      )

      navigate(
        getDestination(),
        {
          replace: true,
        }
      )
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to sign in. Check your email and password.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSuccess =
    async (credentialResponse) => {
      setError('')

      if (
        !credentialResponse
          ?.credential
      ) {
        setError(
          'Google did not return a valid sign-in credential.'
        )
        return
      }

      setGoogleLoading(true)

      try {
        await googleLogin(
          credentialResponse
            .credential
        )

        navigate(
          getDestination(),
          {
            replace: true,
          }
        )
      } catch (err) {
        console.error(
          'Google login failed:',
          err
        )

        setError(
          err.response?.data?.detail ||
          'Unable to sign in with Google.'
        )
      } finally {
        setGoogleLoading(false)
      }
    }

  const handleGoogleError = () => {
    setError(
      'Google Sign-In was unsuccessful. Please try again.'
    )
  }

  return (
    <div className="auth-page">

      <section className="auth-brand-panel">

        <div className="brand-badge">
          <BarChart3 size={30} />
          <span>SSAS</span>
        </div>

        <div className="brand-copy">
          <span className="eyebrow">
            SMART DATA ANALYTICS
          </span>

          <h1>
            Smart Statistical
            Analysis System
          </h1>

          <p>
            Analyze datasets,
            perform statistical
            tests, train machine
            learning models,
            create visualizations,
            and generate intelligent
            reports from one
            platform.
          </p>
        </div>

        <div className="brand-footer">
          Secure • Intelligent •
          Data Driven
        </div>

      </section>

      <section className="auth-form-panel">

        <form
          className="auth-card"
          onSubmit={handleSubmit}
        >

          <div className="auth-card-header">
            <h2>Welcome back</h2>

            <p>
              Sign in to your SSAS
              account.
            </p>
          </div>

          {location.state?.message && (
            <div className="alert success">
              {
                location.state
                  .message
              }
            </div>
          )}

          {error && (
            <div className="alert error">
              {error}
            </div>
          )}

          <label className="form-label">
            Email address
          </label>

          <div className="input-wrapper">
            <Mail size={19} />

            <input
              type="email"
              placeholder="name@example.com"
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value
                )
              }
              required
              autoComplete="email"
            />
          </div>

          <label className="form-label">
            Password
          </label>

          <div className="input-wrapper">
            <LockKeyhole size={19} />

            <input
              type={
                showPassword
                  ? 'text'
                  : 'password'
              }
              placeholder="Enter your password"
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value
                )
              }
              required
              autoComplete="current-password"
            />

            <button
              type="button"
              className="password-toggle"
              onClick={() =>
                setShowPassword(
                  (value) =>
                    !value
                )
              }
              aria-label="Toggle password visibility"
            >
              {showPassword
                ? <EyeOff size={18} />
                : <Eye size={18} />}
            </button>
          </div>

          <button
            type="submit"
            className="primary-button"
            disabled={
              loading ||
              googleLoading
            }
          >
            {loading
              ? 'Signing in...'
              : 'Sign in'}
          </button>

          <div className="auth-divider">
            <span>or continue with</span>
          </div>

          <div
            className="google-login-wrapper"
          >
            {googleLoading ? (
              <div
                className="google-loading"
              >
                Signing in with
                Google...
              </div>
            ) : (
              <GoogleLogin
                onSuccess={
                  handleGoogleSuccess
                }
                onError={
                  handleGoogleError
                }
                useOneTap={false}
                theme="outline"
                size="large"
                text="continue_with"
                shape="rectangular"
              />
            )}
          </div>

          <p className="auth-switch">
            Don't have an account?
            {' '}
            <Link to="/register">
              Create account
            </Link>
          </p>

        </form>

      </section>

    </div>
  )
}
