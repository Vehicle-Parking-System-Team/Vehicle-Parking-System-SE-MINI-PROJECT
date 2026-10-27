import { useState } from 'react'
import { useAuth } from '../context/useAuth'

export function RegisterForm({ onSwitchToLogin }) {
  const { register, isLoading, error, clearError } = useAuth()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [localErrors, setLocalErrors] = useState({})
  const [generalError, setGeneralError] = useState('')

  const validate = () => {
    const errs = {}
    const trimmedUser = username.trim()
    const trimmedEmail = email.trim()

    if (!trimmedUser) {
      errs.username = 'Username is required.'
    } else if (!/^[\w.@+-]+$/.test(trimmedUser)) {
      errs.username = 'Enter a valid username (letters, numbers, and @/./+/-/_ only).'
    }

    if (!trimmedEmail) {
      errs.email = 'Email address is required.'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      errs.email = 'Please enter a valid email address.'
    }

    if (!password) {
      errs.password = 'Password is required.'
    } else if (password.length < 8) {
      errs.password = 'Password must be at least 8 characters long.'
    } else if (!/[A-Z]/.test(password)) {
      errs.password = 'Password must contain at least one uppercase letter.'
    } else if (!/[a-z]/.test(password)) {
      errs.password = 'Password must contain at least one lowercase letter.'
    } else if (!/[0-9]/.test(password)) {
      errs.password = 'Password must contain at least one digit.'
    } else if (!/[^A-Za-z0-9]/.test(password)) {
      errs.password = 'Password must contain at least one special character.'
    }

    if (!passwordConfirm) {
      errs.password_confirm = 'Please confirm your password.'
    } else if (password !== passwordConfirm) {
      errs.password_confirm = 'Passwords do not match.'
    }

    return errs
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    setGeneralError('')

    const clientErrors = validate()
    if (Object.keys(clientErrors).length > 0) {
      setLocalErrors(clientErrors)
      return
    }

    setLocalErrors({})

    const res = await register(
      username.trim(),
      email.trim(),
      password,
      passwordConfirm,
    )

    if (!res.success) {
      if (res.details && typeof res.details === 'object') {
        const fieldErrs = {}
        Object.entries(res.details).forEach(([key, val]) => {
          if (Array.isArray(val) && val.length > 0) {
            fieldErrs[key] = val[0]
          } else if (typeof val === 'string') {
            fieldErrs[key] = val
          }
        })
        if (Object.keys(fieldErrs).length > 0) {
          setLocalErrors(fieldErrs)
        }
      }
      setGeneralError(res.error || 'Registration failed. Please check the form.')
    }
  }

  const displayedGeneralError = generalError || error

  return (
    <div className="auth-card" id="register-container">
      <div className="auth-header">
        <div className="auth-badge">New Customer</div>
        <h2>Create an Account</h2>
        <p className="auth-subtitle">
          Register for facility access and vehicle management.
        </p>
      </div>

      {displayedGeneralError && (
        <div className="alert-banner alert-error" role="alert" id="register-error-banner">
          <span className="alert-icon" aria-hidden="true">⚠️</span>
          <span className="alert-text">{displayedGeneralError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="auth-form" aria-busy={isLoading}>
        <div className="form-group">
          <label htmlFor="reg-username">
            Username <span className="required-indicator" aria-hidden="true">*</span>
          </label>
          <input
            id="reg-username"
            name="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => {
              setUsername(e.target.value)
              if (localErrors.username) setLocalErrors((prev) => ({ ...prev, username: null }))
              if (displayedGeneralError) {
                clearError()
                setGeneralError('')
              }
            }}
            placeholder="Choose a username"
            required
            disabled={isLoading}
            autoFocus
          />
          {localErrors.username && (
            <span className="field-error-text" role="alert">{localErrors.username}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="reg-email">
            Email Address <span className="required-indicator" aria-hidden="true">*</span>
          </label>
          <input
            id="reg-email"
            name="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value)
              if (localErrors.email) setLocalErrors((prev) => ({ ...prev, email: null }))
              if (displayedGeneralError) {
                clearError()
                setGeneralError('')
              }
            }}
            placeholder="name@example.com"
            required
            disabled={isLoading}
          />
          {localErrors.email && (
            <span className="field-error-text" role="alert">{localErrors.email}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="reg-password">
            Password <span className="required-indicator" aria-hidden="true">*</span>
          </label>
          <div className="password-input-wrapper">
            <input
              id="reg-password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                if (localErrors.password) setLocalErrors((prev) => ({ ...prev, password: null }))
                if (displayedGeneralError) {
                  clearError()
                  setGeneralError('')
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
          <small className="form-hint">
            Minimum 8 characters with uppercase, lowercase, number, and special character.
          </small>
          {localErrors.password && (
            <span className="field-error-text" role="alert">{localErrors.password}</span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="reg-password-confirm">
            Confirm Password <span className="required-indicator" aria-hidden="true">*</span>
          </label>
          <div className="password-input-wrapper">
            <input
              id="reg-password-confirm"
              name="password_confirm"
              type={showConfirmPassword ? 'text' : 'password'}
              autoComplete="new-password"
              value={passwordConfirm}
              onChange={(e) => {
                setPasswordConfirm(e.target.value)
                if (localErrors.password_confirm) {
                  setLocalErrors((prev) => ({ ...prev, password_confirm: null }))
                }
                if (displayedGeneralError) {
                  clearError()
                  setGeneralError('')
                }
              }}
              placeholder="••••••••••••"
              required
              disabled={isLoading}
            />
            <button
              type="button"
              className="btn-password-toggle"
              onClick={() => setShowConfirmPassword((prev) => !prev)}
              aria-label={showConfirmPassword ? 'Hide confirmation password' : 'Show confirmation password'}
              aria-pressed={showConfirmPassword}
            >
              {showConfirmPassword ? '👁️' : '👁️‍🗨️'}
            </button>
          </div>
          {localErrors.password_confirm && (
            <span className="field-error-text" role="alert">{localErrors.password_confirm}</span>
          )}
        </div>

        <button
          type="submit"
          className="btn-primary"
          id="btn-register-submit"
          disabled={isLoading}
        >
          {isLoading ? (
            <span className="btn-loading">
              <span className="spinner" aria-hidden="true"></span>
              Creating Account...
            </span>
          ) : (
            'Sign Up'
          )}
        </button>
      </form>

      <div className="auth-footer">
        <p className="auth-switch-text">
          Already have an account?{' '}
          <button
            type="button"
            className="btn-link"
            id="btn-switch-to-login"
            onClick={onSwitchToLogin}
            disabled={isLoading}
          >
            Sign In
          </button>
        </p>
      </div>
    </div>
  )
}
