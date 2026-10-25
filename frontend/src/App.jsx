import { useState } from 'react'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/useAuth'
import { LoginForm } from './components/LoginForm'
import { RegisterForm } from './components/RegisterForm'
import { AuthenticatedView } from './components/AuthenticatedView'
import BayIcon from './components/BayIcon'
import SlotsPage from './pages/Slots'
import './App.css'

function AuthMain() {
  const { isAuthenticated } = useAuth()
  const [authMode, setAuthMode] = useState('login')
  const [showAvailability, setShowAvailability] = useState(false)

  if (isAuthenticated) {
    return <AuthenticatedView />
  }

  if (showAvailability) {
    return (
      <div className="bay-main-shell">
        <header className="bay-topbar">
          <strong>BAY · Parking availability</strong>
          <button type="button" className="bay-button bay-button-light" onClick={() => setShowAvailability(false)}>Back to sign in</button>
        </header>
        <main className="bay-main"><SlotsPage availability /></main>
      </div>
    )
  }

  return (
    <main className="bay-login">
      <div className="bay-login-intro">
        <span className="bay-brand">
          BAY<span className="bay-brand-dot">.</span>
        </span>
        <span className="bay-eyebrow">PARKING. IN PERSPECTIVE.</span>
        <h1>
          Good spaces.
          <br />
          Great possibilities.
        </h1>
        <p>
          A thoughtfully connected workspace
          <br />
          for the way your facility moves.
        </p>
        <div className="bay-login-art" aria-hidden="true">
          <BayIcon name="layers" size={170} />
        </div>
        <small>EVERY ARRIVAL DESERVES A BETTER EXPERIENCE.</small>
      </div>
      <div className="bay-login-form">
        {authMode === 'login' ? (
          <LoginForm onSwitchToRegister={() => setAuthMode('register')} />
        ) : (
          <RegisterForm onSwitchToLogin={() => setAuthMode('login')} />
        )}
        <span className="bay-login-caption">Your space starts here.</span>
        <button type="button" className="bay-button bay-button-light" onClick={() => setShowAvailability(true)}>View parking availability</button>
      </div>
    </main>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AuthMain />
    </AuthProvider>
  )
}
