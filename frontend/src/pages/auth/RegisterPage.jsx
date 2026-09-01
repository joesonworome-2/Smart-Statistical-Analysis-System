import {
  useEffect,
  useState,
} from 'react'

import {
  Link,
  Navigate,
  useNavigate,
} from 'react-router-dom'

import {
  BarChart3,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  User,
} from 'lucide-react'

import {
  useAuth,
} from '../../context/AuthContext'

import './AuthPages.css'


// ==========================================================
// INITIAL FORM
// ==========================================================

const initialForm = {
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  password: '',
  confirm_password: '',
}


// ==========================================================
// GOOGLE SCRIPT
// ==========================================================

function loadGoogleScript() {

  return new Promise(
    (
      resolve,
      reject
    ) => {

      if (
        window.google
          ?.accounts
          ?.id
      ) {

        resolve(
          window.google
        )

        return
      }


      const existingScript =
        document.getElementById(
          'google-identity-services'
        )


      if (
        existingScript
      ) {

        existingScript.addEventListener(
          'load',
          () =>
            resolve(
              window.google
            ),
          {
            once: true,
          }
        )


        existingScript.addEventListener(
          'error',
          reject,
          {
            once: true,
          }
        )


        return
      }


      const script =
        document.createElement(
          'script'
        )


      script.id =
        'google-identity-services'


      script.src =
        'https://accounts.google.com/gsi/client'


      script.async =
        true


      script.defer =
        true


      script.onload =
        () =>
          resolve(
            window.google
          )


      script.onerror =
        () =>
          reject(
            new Error(
              'Unable to load Google Sign-In.'
            )
          )


      document.head.appendChild(
        script
      )
    }
  )
}


// ==========================================================
// REGISTER PAGE
// ==========================================================

export default function RegisterPage() {

  const {
    user,
    register,
    googleLogin,
  } = useAuth()


  const navigate =
    useNavigate()


  const [
    form,
    setForm,
  ] = useState(
    initialForm
  )


  const [
    showPassword,
    setShowPassword,
  ] = useState(false)


  const [
    error,
    setError,
  ] = useState('')


  const [
    loading,
    setLoading,
  ] = useState(false)


  const [
    googleLoading,
    setGoogleLoading,
  ] = useState(false)


  // ========================================================
  // GOOGLE REGISTRATION / LOGIN
  // ========================================================

  useEffect(
    () => {

      if (
        user
      ) {
        return
      }


      const clientId =
        import.meta
          .env
          .VITE_GOOGLE_CLIENT_ID


      if (
        !clientId
      ) {
        return
      }


      let cancelled =
        false


      const setupGoogle =
        async () => {

          try {

            const google =
              await loadGoogleScript()


            if (
              cancelled
            ) {
              return
            }


            google.accounts.id.initialize({
              client_id:
                clientId,


              callback:
                async (
                  response
                ) => {

                  if (
                    !response
                      ?.credential
                  ) {

                    setError(
                      'Google did not return a valid credential.'
                    )

                    return
                  }


                  setError(
                    ''
                  )


                  setGoogleLoading(
                    true
                  )


                  try {

                    await googleLogin(
                      response.credential
                    )


                    navigate(
                      '/dashboard',
                      {
                        replace:
                          true,
                      }
                    )

                  } catch (
                    err
                  ) {

                    setError(
                      err
                        ?.response
                        ?.data
                        ?.detail
                      ||
                      'Unable to continue with Google.'
                    )

                  } finally {

                    setGoogleLoading(
                      false
                    )
                  }
                },
            })


            const container =
              document.getElementById(
                'google-register-button'
              )


            if (
              container
            ) {

              container.innerHTML =
                ''


              google.accounts.id.renderButton(
                container,
                {
                  type:
                    'standard',

                  theme:
                    'outline',

                  size:
                    'large',

                  text:
                    'continue_with',

                  shape:
                    'rectangular',

                  logo_alignment:
                    'left',

                  width:
                    400,
                }
              )
            }

          } catch (
            err
          ) {

            console.error(
              err
            )


            if (
              !cancelled
            ) {

              setError(
                'Google Sign-In could not be loaded.'
              )
            }
          }
        }


      setupGoogle()


      return () => {

        cancelled =
          true
      }

    },

    [
      user,
      googleLogin,
      navigate,
    ]
  )


  // ========================================================
  // ALREADY LOGGED IN
  // ========================================================

  if (
    user
  ) {

    return (

      <Navigate
        to="/dashboard"
        replace
      />

    )
  }


  // ========================================================
  // CHANGE INPUT
  // ========================================================

  const handleChange =
    (
      event
    ) => {

      const {
        name,
        value,
      } =
        event.target


      setForm(
        (
          previous
        ) => ({
          ...previous,

          [name]:
            value,
        })
      )
    }


  // ========================================================
  // REGISTER
  // ========================================================

  const handleSubmit =
    async (
      event
    ) => {

      event.preventDefault()


      setError(
        ''
      )


      if (
        form.password.length
        <
        8
      ) {

        setError(
          'Password must contain at least 8 characters.'
        )

        return
      }


      if (
        form.password
        !==
        form.confirm_password
      ) {

        setError(
          'Passwords do not match.'
        )

        return
      }


      setLoading(
        true
      )


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
            replace:
              true,

            state: {
              message:
                'Account created successfully. You can now sign in.',
            },
          }
        )

      } catch (
        err
      ) {

        const detail =
          err
            ?.response
            ?.data
            ?.detail


        if (
          typeof detail ===
          'string'
        ) {

          setError(
            detail
          )

        } else {

          setError(
            'Unable to create account.'
          )
        }

      } finally {

        setLoading(
          false
        )
      }
    }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <div className="auth-modern-page">


      {/* ==================================================
          BACKGROUND
          ================================================== */}

      <div
        className="auth-background"
        aria-hidden="true"
      >

        <video
          className="auth-background-video"

          autoPlay
          muted
          loop
          playsInline

          preload="auto"
        >

          <source
            src="/videos/dashboard-bg.mp4"
            type="video/mp4"
          />

        </video>


        <div className="auth-background-overlay" />

        <div className="auth-grid-overlay" />

      </div>


      {/* ==================================================
          BRAND
          ================================================== */}

      <header className="auth-modern-header">


        <button
          type="button"

          className="auth-modern-brand"

          onClick={() =>
            navigate(
              '/'
            )
          }
        >


          <BarChart3
            size={38}
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


      </header>


      {/* ==================================================
          CONTENT
          ================================================== */}

      <main className="auth-modern-layout register-layout">


        {/* =================================================
            CAPTION
            ================================================= */}

        <section className="auth-story">


          <span className="auth-story-eyebrow">

            START YOUR ANALYSIS

          </span>


          <h1>

            From raw numbers to
            <strong>
              {' '}
              meaningful evidence.
            </strong>

          </h1>


          <p>

            Create your SSAS account and build a
            statistical workspace where datasets
            become analysis, insights,
            visualizations and reports.

          </p>


          <div className="auth-story-features">


            <div>

              <span>
                01
              </span>

              <div>

                <strong>
                  Upload
                </strong>

                <p>
                  Bring CSV and Excel datasets
                  into your workspace.
                </p>

              </div>

            </div>


            <div>

              <span>
                02
              </span>

              <div>

                <strong>
                  Analyze
                </strong>

                <p>
                  Explore descriptive,
                  inferential and advanced methods.
                </p>

              </div>

            </div>


            <div>

              <span>
                03
              </span>

              <div>

                <strong>
                  Report
                </strong>

                <p>
                  Turn your findings into
                  understandable evidence.
                </p>

              </div>

            </div>


          </div>


        </section>


        {/* =================================================
            REGISTER CARD
            ================================================= */}

        <section className="auth-modern-card register-card-modern">


          <div className="auth-card-heading">


            <span>
              GET STARTED
            </span>


            <h2>
              Create account
            </h2>


            <p>
              Create your SSAS workspace.
            </p>


          </div>


          {
            error
            &&
            (

              <div className="auth-alert error">

                {error}

              </div>

            )
          }


          {/* =================================================
              GOOGLE
              ================================================= */}

          {
            import.meta
              .env
              .VITE_GOOGLE_CLIENT_ID
              ?
              (

                <div className="google-auth-section">

                  <div
                    id="google-register-button"
                    className="google-login-container"
                  />


                  {
                    googleLoading
                    &&
                    (

                      <span className="google-loading-text">

                        Continuing with Google...

                      </span>

                    )
                  }

                </div>

              )
              :
              (

                <div className="google-auth-placeholder">

                  Continue with Google

                  <small>

                    Add VITE_GOOGLE_CLIENT_ID
                    to enable Google Sign-In.

                  </small>

                </div>

              )
          }


          <div className="auth-divider">

            <span>
              OR
            </span>

          </div>


          {/* =================================================
              FORM
              ================================================= */}

          <form
            className="auth-modern-form"

            onSubmit={
              handleSubmit
            }
          >


            <div className="auth-two-columns">


              <div className="auth-modern-field">


                <label
                  htmlFor="register-first-name"
                >

                  First name

                </label>


                <input
                  id="register-first-name"

                  className="auth-plain-input"

                  name="first_name"

                  value={
                    form.first_name
                  }

                  onChange={
                    handleChange
                  }

                  required
                />


              </div>


              <div className="auth-modern-field">


                <label
                  htmlFor="register-last-name"
                >

                  Last name

                </label>


                <input
                  id="register-last-name"

                  className="auth-plain-input"

                  name="last_name"

                  value={
                    form.last_name
                  }

                  onChange={
                    handleChange
                  }

                  required
                />


              </div>


            </div>


            <div className="auth-modern-field">


              <label
                htmlFor="register-username"
              >

                Username

              </label>


              <div className="auth-modern-input">


                <User
                  size={18}
                />


                <input
                  id="register-username"

                  name="username"

                  type="text"

                  minLength={3}

                  maxLength={50}

                  placeholder="Choose a username"

                  value={
                    form.username
                  }

                  onChange={
                    handleChange
                  }

                  autoComplete="username"

                  required
                />


              </div>


            </div>


            <div className="auth-modern-field">


              <label
                htmlFor="register-email"
              >

                Email

              </label>


              <div className="auth-modern-input">


                <Mail
                  size={18}
                />


                <input
                  id="register-email"

                  name="email"

                  type="email"

                  placeholder="Enter your email"

                  value={
                    form.email
                  }

                  onChange={
                    handleChange
                  }

                  autoComplete="email"

                  required
                />


              </div>


            </div>


            <div className="auth-modern-field">


              <label
                htmlFor="register-password"
              >

                Password

              </label>


              <div className="auth-modern-input">


                <LockKeyhole
                  size={18}
                />


                <input
                  id="register-password"

                  name="password"

                  type={
                    showPassword
                      ?
                      'text'
                      :
                      'password'
                  }

                  minLength={8}

                  maxLength={128}

                  placeholder="Minimum 8 characters"

                  value={
                    form.password
                  }

                  onChange={
                    handleChange
                  }

                  autoComplete="new-password"

                  required
                />


                <button
                  type="button"

                  className="auth-password-toggle"

                  onClick={() =>
                    setShowPassword(
                      (
                        current
                      ) =>
                        !current
                    )
                  }
                >

                  {
                    showPassword
                      ?
                      <EyeOff size={18} />
                      :
                      <Eye size={18} />
                  }

                </button>


              </div>


            </div>


            <div className="auth-modern-field">


              <label
                htmlFor="register-confirm-password"
              >

                Confirm password

              </label>


              <div className="auth-modern-input">


                <LockKeyhole
                  size={18}
                />


                <input
                  id="register-confirm-password"

                  name="confirm_password"

                  type={
                    showPassword
                      ?
                      'text'
                      :
                      'password'
                  }

                  minLength={8}

                  maxLength={128}

                  placeholder="Re-enter your password"

                  value={
                    form.confirm_password
                  }

                  onChange={
                    handleChange
                  }

                  autoComplete="new-password"

                  required
                />


              </div>


            </div>


            <button
              type="submit"

              className="auth-primary-button"

              disabled={
                loading
                ||
                googleLoading
              }
            >

              {
                loading
                  ?
                  'Creating account...'
                  :
                  'Create account'
              }

            </button>


          </form>


          <div className="auth-switch">


            <span>
              Already registered?
            </span>


            <Link
              to="/login"
            >

              Sign in

            </Link>


          </div>


        </section>


      </main>


    </div>

  )
}
