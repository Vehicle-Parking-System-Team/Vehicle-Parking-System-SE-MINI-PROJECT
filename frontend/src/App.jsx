import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/useAuth'
import { LoginForm } from './components/LoginForm'
import { AuthenticatedView } from './components/AuthenticatedView'
import { ProtectedRoute } from './routes/ProtectedRoute'
import './App.css'

function AuthMain() {
  const { isAuthenticated } = useAuth()

  return (
    <main className="app-content">
      {isAuthenticated ? (
        <ProtectedRoute>
          <AuthenticatedView />
        </ProtectedRoute>
      ) : (
        <LoginForm />
      )}
    </main>
  )
}

function App() {
  return (
    <AuthProvider>
      <div className="app-layout">
        <header className="app-header">
          <div className="header-brand">
            <span className="brand-icon">🚗</span>
            <h1>Vehicle Parking System</h1>
          </div>
          <span className="sprint-tag">Sprint 2 • US-02 Role-Based Access Control</span>
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
