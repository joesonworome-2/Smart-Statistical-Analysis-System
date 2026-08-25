import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import {
  GoogleOAuthProvider,
} from '@react-oauth/google'

import './styles/app.css'

import App from './App'
import {
  AuthProvider,
} from './context/AuthContext'

const googleClientId =
  import.meta.env
    .VITE_GOOGLE_CLIENT_ID

createRoot(
  document.getElementById('root')
).render(
  <StrictMode>
    <GoogleOAuthProvider
      clientId={googleClientId}
    >
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </GoogleOAuthProvider>
  </StrictMode>
)
