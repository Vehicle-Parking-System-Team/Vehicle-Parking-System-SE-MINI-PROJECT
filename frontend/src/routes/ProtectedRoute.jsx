import { useEffect } from 'react'
import { useAuth } from '../context/useAuth'
import { isRoleAuthorized } from '../utils/rbac'

/**
 * ProtectedRoute component (US-02 / FR-16, NFR-SEC-01).
 * Guards views against unauthenticated access and restricts role-specific views
 * to authorized roles (Administrator, Operator, Customer).
 */
export function ProtectedRoute({
  children,
  allowedRoles,
  redirectTo = '/login',
  fallback = null,
}) {
  const { user, isAuthenticated, isLoading } = useAuth()

  // Safe redirect hook for direct URL navigation in browser environments
  useEffect(() => {
    if (!isLoading && !isAuthenticated && typeof window !== 'undefined' && window.location) {
      if (redirectTo && window.location.pathname !== redirectTo && !window.location.hash.includes(redirectTo)) {
        // Safe navigation preservation: if routing library is not present, history replace or hash can be set
      }
    }
  }, [isLoading, isAuthenticated, redirectTo])

  // 1. Loading state: Prevents brief exposure of protected content during auth hydration
  if (isLoading) {
    return (
      <div
        className="auth-loading-state"
        id="protected-route-loading"
        role="status"
        aria-live="polite"
      >
        <div className="status-indicator">
          <span className="status-dot"></span>
          Verifying security context...
        </div>
        <p>Checking authentication and role permissions...</p>
      </div>
    )
  }

  // 2. Unauthenticated check: Block and prompt login
  if (!isAuthenticated || !user) {
    return (
      fallback || (
        <div
          className="auth-card rbac-guard-card unauthenticated-guard"
          id="protected-route-unauthenticated"
          role="alert"
        >
          <div className="status-indicator alert-error">
            <span className="status-dot"></span>
            Authentication Required (HTTP 401)
          </div>
          <h2>Access Restricted</h2>
          <p className="auth-subtitle">
            You must be logged in with an active account to view this page.
          </p>
        </div>
      )
    )
  }

  // 3. Role authorization check: Enforce documented RBAC matrix
  const authorized = isRoleAuthorized(user.role, allowedRoles)
  if (!authorized) {
    return (
      fallback || (
        <div
          className="auth-card rbac-guard-card forbidden-guard"
          id="protected-route-forbidden"
          role="alert"
        >
          <div className="status-indicator alert-error">
            <span className="status-dot"></span>
            Permission Denied (HTTP 403)
          </div>
          <h2>Unauthorized Role</h2>
          <p className="auth-subtitle">
            Your assigned role <strong>{user.role || 'Unspecified'}</strong> does not have permission to access this resource.
          </p>
          <div className="session-info-box">
            <h4>Access Requirements</h4>
            <p>
              This section is restricted to: <code>{allowedRoles ? allowedRoles.join(', ') : 'Authorized Personnel'}</code>.
            </p>
          </div>
        </div>
      )
    )
  }

  // 4. Authorized: Safely render protected children
  return children
}

export default ProtectedRoute
