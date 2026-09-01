import {
  useEffect,
  useState,
} from 'react'

import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from 'react-router-dom'

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

import './AuthPages.css'


// ==========================================================
// GOOGLE IDENTITY SERVICES LOADER
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
// LOGIN PAGE
// ==========================================================

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


  const [
    email,
    setEmail,
  ] = useState('')


  const [
    password,
    setPassword,
  ] = useState('')


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
  // DESTINATION AFTER LOGIN
  // ========================================================

  const destination =
    location.state?.from
    ||
    '/dashboard'


  // ========================================================
  // GOOGLE SIGN-IN
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
                      'Google did not return a valid sign-in credential.'
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
                      destination,
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
                      'Unable to sign in with Google.'
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
                'google-login-button'
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
                    360,
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
      destination,
    ]
  )


  // ========================================================
  // USER ALREADY LOGGED IN
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
  // NORMAL LOGIN
  // ========================================================

  const handleSubmit =
    async (
      event
    ) => {

      event.preventDefault()


      setError(
        ''
      )


      setLoading(
        true
      )


      try {

        await login(
          email.trim(),
          password
        )


        navigate(
          destination,
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
          'Unable to sign in. Check your email and password.'
        )

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
          DATA ANALYSIS VIDEO BACKGROUND
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
          PAGE CONTENT
          ================================================== */}

      <main className="auth-modern-layout">


        {/* =================================================
            CAPTION
            ================================================= */}

        <section className="auth-story">


          <span className="auth-story-eyebrow">

            SMARTER DATA ANALYSIS

          </span>


          <h1>

            Make every dataset
            <strong>
              {' '}
              tell a clearer story.
            </strong>

          </h1>


          <p>

            Transform raw data into meaningful
            statistical evidence, discover patterns,
            compare relationships and make better
            informed decisions.

          </p>


          <div className="auth-story-features">


            <div>

              <span>
                01
              </span>

              <div>

                <strong>
                  Analyze
                </strong>

                <p>
                  Apply statistical methods
                  to your datasets.
                </p>

              </div>

            </div>


            <div>

              <span>
                02
              </span>

              <div>

                <strong>
                  Understand
                </strong>

                <p>
                  Turn statistical output into
                  clear interpretations.
                </p>

              </div>

            </div>


            <div>

              <span>
                03
              </span>

              <div>

                <strong>
                  Communicate
                </strong>

                <p>
                  Present findings through
                  visualizations and reports.
                </p>

              </div>

            </div>


          </div>


        </section>


        {/* =================================================
            LOGIN CARD
            ================================================= */}

        <section className="auth-modern-card login-card">


          <div className="auth-card-heading">


            <span>
              WELCOME BACK
            </span>


            <h2>
              Login
            </h2>


            <p>
              Continue to your statistical workspace.
            </p>


          </div>


          {/* SUCCESS */}

          {
            location
              .state
              ?.message
            &&
            (

              <div className="auth-alert success">

                {
                  location
                    .state
                    .message
                }

              </div>

            )
          }


          {/* ERROR */}

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
              GOOGLE SIGN-IN
              ================================================= */}

          {
            import.meta
              .env
              .VITE_GOOGLE_CLIENT_ID
              ?
              (

                <div className="google-auth-section">


                  <div
                    id="google-login-button"
                    className="google-login-container"
                  />


                  {
                    googleLoading
                    &&
                    (

                      <span className="google-loading-text">

                        Signing in with Google...

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


          {/* DIVIDER */}

          <div className="auth-divider">

            <span>
              OR
            </span>

          </div>


          {/* =================================================
              EMAIL LOGIN
              ================================================= */}

          <form
            className="auth-modern-form"

            onSubmit={
              handleSubmit
            }
          >


            <div className="auth-modern-field">


              <label
                htmlFor="login-email"
              >

                Email

              </label>


              <div className="auth-modern-input">


                <Mail
                  size={18}
                />


                <input
                  id="login-email"

                  type="email"

                  placeholder="Enter your email"

                  value={
                    email
                  }

                  onChange={
                    (
                      event
                    ) =>
                      setEmail(
                        event
                          .target
                          .value
                      )
                  }

                  autoComplete="email"

                  required
                />


              </div>


            </div>


            <div className="auth-modern-field">


              <div className="auth-password-heading">


                <label
                  htmlFor="login-password"
                >

                  Password

                </label>


                <button
                  type="button"

                  onClick={() =>
                    setError(
                      'Password recovery is not configured yet.'
                    )
                  }
                >

                  Forgot password?

                </button>


              </div>


              <div className="auth-modern-input">


                <LockKeyhole
                  size={18}
                />


                <input
                  id="login-password"

                  type={
                    showPassword
                      ?
                      'text'
                      :
                      'password'
                  }

                  placeholder="Enter your password"

                  value={
                    password
                  }

                  onChange={
                    (
                      event
                    ) =>
                      setPassword(
                        event
                          .target
                          .value
                      )
                  }

                  autoComplete="current-password"

                  required
                />


                <button
                  type="button"

                  className="auth-password-toggle"

                  aria-label={
                    showPassword
                      ?
                      'Hide password'
                      :
                      'Show password'
                  }

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
                      (
                        <EyeOff
                          size={18}
                        />
                      )
                      :
                      (
                        <Eye
                          size={18}
                        />
                      )
                  }


                </button>


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
                  'Logging in...'
                  :
                  'Log In'
              }

            </button>


          </form>


          <div className="auth-switch">


            <span>

              Don't have an account?

            </span>


            <Link
              to="/register"
            >

              Create account

            </Link>


          </div>


        </section>


      </main>


      <footer className="auth-modern-footer">

        Statistical Analysis
        {' • '}
        Machine Learning
        {' • '}
        Visualization
        {' • '}
        Reporting

      </footer>


    </div>

  )
}
