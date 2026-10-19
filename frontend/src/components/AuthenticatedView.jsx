import { useState } from 'react'
import { useAuth } from '../context/useAuth'

export function AuthenticatedView() {
  const { user, logout, fetchWithAuth, isLoading } = useAuth()
  const [testResult, setTestResult] = useState(null)
  const [isTesting, setIsTesting] = useState(false)

  const handleTestProtectedEndpoint = async () => {
    setIsTesting(true)
    setTestResult(null)

    try {
      const response = await fetchWithAuth('/api/auth/me/')
      const data = await response.json().catch(() => ({}))

      if (response.ok) {
        setTestResult({
          status: 'success',
          message: `HTTP ${response.status} OK — Access token verified. Authenticated as ${data.username} (${data.role}).`,
        })
      } else {
        setTestResult({
          status: 'error',
          message: `HTTP ${response.status} — ${data.error || 'Protected endpoint rejected the request.'}`,
        })
      }
    } catch (err) {
      setTestResult({
        status: 'error',
        message: err.message || 'Failed to communicate with protected route.',
      })
    } finally {
      setIsTesting(false)
    }
  }

  const roleBadgeClass = {
    Admin: 'badge-admin',
    Operator: 'badge-operator',
    Customer: 'badge-customer',
  }[user?.role] || 'badge-default'

  return (
    <div className="auth-card authenticated-card" id="authenticated-container">
      <div className="auth-header">
        <div className="status-indicator">
          <span className="status-dot"></span>
          Active Authenticated Session
        </div>
        <h2>Welcome, {user?.username}</h2>
        <p className="auth-subtitle">
          Identity verified with JWT bearer authorization.
        </p>
      </div>

      <div className="user-profile-grid">
        <div className="profile-row">
          <span className="profile-label">Username:</span>
          <span className="profile-value font-mono" id="user-display-username">{user?.username}</span>
        </div>
        <div className="profile-row">
          <span className="profile-label">Assigned Role:</span>
          <span className={`profile-badge ${roleBadgeClass}`} id="user-display-role">
            {user?.role}
          </span>
        </div>
        <div className="profile-row">
          <span className="profile-label">Account Status:</span>
          <span className="profile-badge badge-active" id="user-display-status">
            {user?.status}
          </span>
        </div>
        <div className="profile-row">
          <span className="profile-label">User ID:</span>
          <span className="profile-value font-mono">#{user?.id}</span>
        </div>
        {user?.email && (
          <div className="profile-row">
            <span className="profile-label">Email:</span>
            <span className="profile-value">{user?.email}</span>
          </div>
        )}
      </div>

      <div className="session-info-box">
        <h4>Session & Security Policies</h4>
        <ul>
          <li><strong>Access Token:</strong> 15-minute stateless JWT lifetime (NFR-SEC-05).</li>
          <li><strong>Refresh Token:</strong> 7-day persistent rotation.</li>
          <li><strong>Instant Revocation:</strong> Logout terminates active tokens server-side.</li>
        </ul>
      </div>

      {testResult && (
        <div
          className={`alert-banner ${testResult.status === 'success' ? 'alert-success' : 'alert-error'}`}
          role="status"
          id="api-test-result"
        >
          <span className="alert-icon" aria-hidden="true">
            {testResult.status === 'success' ? '✅' : '❌'}
          </span>
          <span className="alert-text">{testResult.message}</span>
        </div>
      )}

      <div className="auth-actions">
        <button
          type="button"
          className="btn-secondary"
          onClick={handleTestProtectedEndpoint}
          disabled={isTesting || isLoading}
          id="btn-test-auth"
        >
          {isTesting ? 'Verifying...' : 'Test Protected API Route (/api/auth/me/)'}
        </button>

        <button
          type="button"
          className="btn-danger"
          onClick={logout}
          disabled={isLoading}
          id="btn-logout"
        >
          {isLoading ? 'Revoking Session...' : 'Log Out (Secure Invalidation)'}
        </button>
      </div>
    </div>
  )
}
