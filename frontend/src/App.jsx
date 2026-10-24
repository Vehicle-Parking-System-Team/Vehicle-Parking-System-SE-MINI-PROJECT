import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/useAuth'
import { LoginForm } from './components/LoginForm'
import { AuthenticatedView } from './components/AuthenticatedView'
import BayIcon from './components/BayIcon'
import './App.css'

function AuthMain() {
  const { isAuthenticated } = useAuth()
  if (isAuthenticated) return <AuthenticatedView />
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
        <LoginForm />
        <span className="bay-login-caption">Your space starts here.</span>
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
