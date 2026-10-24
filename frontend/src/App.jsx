import { useState } from 'react'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './context/useAuth'
import { LoginForm } from './components/LoginForm'
import { RegisterForm } from './components/RegisterForm'
import { AuthenticatedView } from './components/AuthenticatedView'
import './App.css'

function AppContent() {
  const { isAuthenticated } = useAuth()
  const [authMode, setAuthMode] = useState('login')

  if (isAuthenticated) {
    return <AuthenticatedView />
  }

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="header-brand">
          <span className="brand-icon">🅿️</span>
          <h1>Vehicle Parking System</h1>
        </div>
        <span className="console-tag">Facility Console</span>
      </header>

      <main className="app-content">
        {authMode === 'login' ? (
          <LoginForm onSwitchToRegister={() => setAuthMode('register')} />
        ) : (
          <RegisterForm onSwitchToLogin={() => setAuthMode('login')} />
        )}
      </main>

      <footer className="app-footer">
        <p>
          Vehicle Parking System &copy; 2026 • Enterprise Parking Operations
        </p>
      </footer>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
