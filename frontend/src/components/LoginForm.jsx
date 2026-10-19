import { useState } from 'react'
import { useAuth } from '../context/useAuth'

export function LoginForm() {
  const { login, isLoading, error, clearError } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [localValidation, setLocalValidation] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    setLocalValidation('')

    if (!username.trim() || !password) {
      setLocalValidation('Please enter both your username and password.')
      return
    }

    await login(username.trim(), password)
  }

  const displayedError = localValidation || error

  return (
    <div className="auth-card" id="login-container">
      <div className="auth-header">
        <div className="auth-badge">Security & Access Management</div>
        <h2>Sign In to Vehicle Parking System</h2>
        <p className="auth-subtitle">
          Enter your authorized credentials to access facility operations and management.
        </p>
      </div>

      {displayedError && (
        <div className="alert-banner alert-error" role="alert" id="auth-error-banner">
          <span className="alert-icon" aria-hidden="true">⚠️</span>
          <span className="alert-text">{displayedError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="auth-form" aria-busy={isLoading}>
        <div className="form-group">
          <label htmlFor="auth-username">
            Username <span className="required-indicator" aria-hidden="true">*</span>
          </label>
          <input
            id="auth-username"
            name="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => {
              setUsername(e.target.value)
              if (displayedError) {
                clearError()
                setLocalValidation('')
              }
            }}
            placeholder="e.g. operator1 or admin"
            required
            disabled={isLoading}
            autoFocus
          />
        </div>

        <div className="form-group">
          <label htmlFor="auth-password">
            Password <span className="required-indicator" aria-hidden="true">*</span>
          </label>
          <input
            id="auth-password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value)
              if (displayedError) {
                clearError()
                setLocalValidation('')
              }
            }}
            placeholder="••••••••••••"
            required
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          className="btn-primary"
          id="btn-login-submit"
          disabled={isLoading}
        >
          {isLoading ? (
            <span className="btn-loading">
              <span className="spinner" aria-hidden="true"></span>
              Authenticating...
            </span>
          ) : (
            'Sign In'
          )}
        </button>
      </form>

      <div className="auth-footer">
        <p className="security-note">
          🔒 Protected by stateless JSON Web Tokens with server-side revocation on logout (NFR-SEC-01).
        </p>
      </div>
    </div>
  )
}
