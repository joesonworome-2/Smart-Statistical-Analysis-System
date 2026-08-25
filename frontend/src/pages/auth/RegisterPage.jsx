import {
  useState,
} from 'react'

import {
  Link,
  Navigate,
  useNavigate,
} from 'react-router-dom'

import {
  BarChart3,
} from 'lucide-react'

import { useAuth } from '../../context/AuthContext'

const initialForm = {
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  password: '',
}

export default function RegisterPage() {
  const {
    user,
    register,
  } = useAuth()

  const navigate =
    useNavigate()

  const [form, setForm] =
    useState(initialForm)

  const [error, setError] =
    useState('')

  const [loading, setLoading] =
    useState(false)

  if (user) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    )
  }

  const handleChange = (
    event
  ) => {
    const {
      name,
      value,
    } = event.target

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }))
  }

  const handleSubmit = async (
    event
  ) => {
    event.preventDefault()

    setError('')

    if (
      form.password.length < 8
    ) {
      setError(
        'Password must contain at least 8 characters.'
      )

      return
    }

    setLoading(true)

    try {
      await register({
        first_name:
          form.first_name.trim(),

        last_name:
          form.last_name.trim(),

        username:
          form.username.trim(),

        email:
          form.email.trim(),

        password:
          form.password,
      })

      navigate(
        '/login',
        {
          replace: true,
          state: {
            message:
              'Account created successfully. You can now sign in.',
          },
        }
      )

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to create account.'
      )

    } finally {
      setLoading(false)
    }
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
            CREATE YOUR ACCOUNT
          </span>

          <h1>
            Turn your data
            into meaningful
            information.
          </h1>

          <p>
            Create an account to
            upload datasets,
            analyze data, visualize
            results and generate
            statistical reports.
          </p>

        </div>

        <div className="brand-footer">
          Smart Statistical
          Analysis System
        </div>

      </section>

      <section className="auth-form-panel">

        <form
          className="auth-card register-card"
          onSubmit={handleSubmit}
        >

          <div className="auth-card-header">
            <h2>Create account</h2>

            <p>
              Enter your details
              below.
            </p>
          </div>

          {error && (
            <div className="alert error">
              {error}
            </div>
          )}

          <div className="two-column">

            <div>
              <label className="form-label">
                First name
              </label>

              <input
                className="plain-input"
                name="first_name"
                value={form.first_name}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label className="form-label">
                Last name
              </label>

              <input
                className="plain-input"
                name="last_name"
                value={form.last_name}
                onChange={handleChange}
                required
              />
            </div>

          </div>

          <label className="form-label">
            Username
          </label>

          <input
            className="plain-input"
            name="username"
            minLength={3}
            maxLength={50}
            value={form.username}
            onChange={handleChange}
            required
          />

          <label className="form-label">
            Email
          </label>

          <input
            className="plain-input"
            name="email"
            type="email"
            value={form.email}
            onChange={handleChange}
            required
          />

          <label className="form-label">
            Password
          </label>

          <input
            className="plain-input"
            name="password"
            type="password"
            minLength={8}
            maxLength={128}
            value={form.password}
            onChange={handleChange}
            required
          />

          <small className="field-help">
            Minimum 8 characters.
          </small>

          <button
            type="submit"
            className="primary-button"
            disabled={loading}
          >
            {loading
              ? 'Creating account...'
              : 'Create account'}
          </button>

          <p className="auth-switch">
            Already registered?
            {' '}
            <Link to="/login">
              Sign in
            </Link>
          </p>

        </form>

      </section>

    </div>
  )
}
