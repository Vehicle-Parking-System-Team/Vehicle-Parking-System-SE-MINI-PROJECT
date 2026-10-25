import { useState } from 'react'
import { useAuth } from '../context/useAuth'

export function LoginForm({ onSwitchToRegister }) {
  const { login, isLoading, error, clearError } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [localValidation, setLocalValidation] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    setLocalValidation('')

    if (!username.trim() || !password) {
      setLocalValidation('Please enter both your username/email and password.')
      return
    }

    await login(username.trim(), password)
  }

  const displayedError = localValidation || error

  return (
    <div className="auth-card" id="login-container">
      <div className="auth-header">
        <div className="auth-badge">Authorized Access</div>
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
            Username or Email <span className="required-indicator" aria-hidden="true">*</span>
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
            placeholder="Enter username or email"
            required
            disabled={isLoading}
            autoFocus
          />
        </div>

        <div className="form-group">
          <label htmlFor="auth-password">
            Password <span className="required-indicator" aria-hidden="true">*</span>
          </label>
          <div className="password-input-wrapper">
            <input
              id="auth-password"
              name="password"
              type={showPassword ? 'text' : 'password'}
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
            <button
              type="button"
              className="btn-password-toggle"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              aria-pressed={showPassword}
            >
              {showPassword ? '👁️' : '👁️‍🗨️'}
            </button>
          </div>
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
        {onSwitchToRegister && (
          <p className="auth-switch-text">
            Don't have an account?{' '}
            <button
              type="button"
              className="btn-link"
              id="btn-switch-to-register"
              onClick={onSwitchToRegister}
              disabled={isLoading}
            >
              Sign Up
            </button>
          </p>
        )}
        <p className="security-note">
          🔒 Secure session with tokenized authentication
        </p>
      </div>
    </div>
  )
}
