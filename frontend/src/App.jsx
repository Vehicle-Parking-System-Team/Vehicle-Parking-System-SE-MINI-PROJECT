import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/useAuth'
import { LoginForm } from './components/LoginForm'
import { AuthenticatedView } from './components/AuthenticatedView'
import './App.css'

function AuthMain() {
  const { isAuthenticated } = useAuth()

  return (
    <main className="app-content">
      {isAuthenticated ? <AuthenticatedView /> : <LoginForm />}
    </main>
  )
}

function App() {
  return (
    <AuthProvider>
      <div className="app-layout">
        <header className="app-header">
          <div className="header-brand">
            <span className="brand-icon">🅿️</span>
            <h1>Vehicle Parking System</h1>
          </div>
          <span className="sprint-tag">Sprint 1 • US-01 Auth Baseline</span>
        </header>

        <AuthMain />

        <footer className="app-footer">
          <p>
            Vehicle Parking System &copy; 2026 • Security & IAM Subsystem (FR-15, FR-16, FR-17)
          </p>
        </footer>
      </div>
    </AuthProvider>
  )
}

export default App
