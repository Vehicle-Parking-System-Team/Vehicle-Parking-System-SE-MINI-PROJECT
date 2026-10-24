import { useState } from 'react'
import { useAuth } from '../context/useAuth'
import { VehicleRegistrationForm } from './VehicleRegistrationForm'
import { VehicleProfileView } from './VehicleProfileView'

export function AuthenticatedView() {
  const { user, logout, isLoading } = useAuth()
  const [activeNav, setActiveNav] = useState('vehicles')
  const [selectedVehicleId, setSelectedVehicleId] = useState(null)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const roleBadgeClass = {
    Admin: 'badge-admin',
    Operator: 'badge-operator',
    Customer: 'badge-customer',
  }[user?.role] || 'badge-default'

  const navigateTo = (navDestination, vehicleId = null) => {
    setActiveNav(navDestination)
    if (vehicleId) {
      setSelectedVehicleId(vehicleId)
    }
    setIsMobileMenuOpen(false)
  }

  return (
    <div className="authenticated-shell" id="authenticated-shell">
      {/* Top Application Bar */}
      <header className="auth-topbar">
        <div className="topbar-left">
          <button
            type="button"
            className="mobile-nav-toggle"
            id="btn-sidebar-toggle"
            aria-label="Toggle navigation menu"
            aria-expanded={isMobileMenuOpen}
            onClick={() => setIsMobileMenuOpen((prev) => !prev)}
          >
            {isMobileMenuOpen ? '✕' : '☰'}
          </button>

          <div className="header-brand">
            <span className="brand-icon">🅿️</span>
            <h1>Vehicle Parking System</h1>
          </div>
          <span className="console-tag">Facility Console</span>
        </div>

        <div className="topbar-right">
          <div className="user-capsule" id="user-header-capsule">
            <span className="user-capsule-name font-mono">{user?.username}</span>
            <span className={`profile-badge ${roleBadgeClass}`}>
              {user?.role}
            </span>
          </div>

          <button
            type="button"
            className="btn btn-sm btn-logout-topbar"
            id="btn-topbar-logout"
            onClick={logout}
            disabled={isLoading}
            title="Sign out of facility session"
          >
            {isLoading ? '...' : 'Sign Out'}
          </button>
        </div>
      </header>

      {/* Main Authenticated Layout with Sidebar */}
      <div className="authenticated-layout">
        {/* Mobile Backdrop */}
        {isMobileMenuOpen && (
          <div
            className="sidebar-backdrop"
            onClick={() => setIsMobileMenuOpen(false)}
            aria-hidden="true"
          />
        )}

        {/* Responsive Navigation Sidebar */}
        <aside
          className={`app-sidebar ${isMobileMenuOpen ? 'sidebar-mobile-open' : ''}`}
          id="app-sidebar"
          aria-label="Console Navigation"
        >
          {/* User Status Card */}
          <div className="sidebar-user-card">
            <div className="user-avatar-circle">
              {user?.username ? user.username.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="sidebar-user-info">
              <span className="sidebar-username font-mono">{user?.username}</span>
              <span className={`sidebar-role-badge ${roleBadgeClass}`}>{user?.role}</span>
              <div className="sidebar-session-dot">
                <span className="status-dot"></span>
                <span>Active Session</span>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="sidebar-nav" aria-label="Main Navigation">
            <div className="nav-group-title">Facility Modules</div>

            <button
              type="button"
              className={`sidebar-nav-item ${activeNav === 'vehicles' ? 'active' : ''}`}
              id="nav-vehicles"
              aria-current={activeNav === 'vehicles' ? 'page' : undefined}
              onClick={() => navigateTo('vehicles')}
            >
              <span className="nav-item-icon">🚗</span>
              <div className="nav-item-content">
                <span className="nav-item-label">Vehicle Registration</span>
                <span className="nav-item-hint">Register & view fleet</span>
              </div>
            </button>

            <button
              type="button"
              className={`sidebar-nav-item ${activeNav === 'profiles' ? 'active' : ''}`}
              id="nav-profiles"
              aria-current={activeNav === 'profiles' ? 'page' : undefined}
              onClick={() => navigateTo('profiles')}
            >
              <span className="nav-item-icon">📋</span>
              <div className="nav-item-content">
                <span className="nav-item-label">Vehicle Profiles</span>
                <span className="nav-item-hint">Inspect & update details</span>
              </div>
            </button>

            <div className="nav-group-title">Session & Security</div>

            <button
              type="button"
              className={`sidebar-nav-item ${activeNav === 'account' ? 'active' : ''}`}
              id="nav-account"
              aria-current={activeNav === 'account' ? 'page' : undefined}
              onClick={() => navigateTo('account')}
            >
              <span className="nav-item-icon">👤</span>
              <div className="nav-item-content">
                <span className="nav-item-label">Account & Role</span>
                <span className="nav-item-hint">Credentials & status</span>
              </div>
            </button>
          </nav>

          {/* Sidebar Footer */}
          <div className="sidebar-footer">
            <button
              type="button"
              className="btn-sidebar-logout"
              id="btn-logout"
              onClick={logout}
              disabled={isLoading}
            >
              <span className="logout-icon">⏻</span>
              {isLoading ? 'Signing Out...' : 'Sign Out'}
            </button>
          </div>
        </aside>

        {/* Viewport Content Area */}
        <main className="authenticated-viewport" id="authenticated-viewport">
          {activeNav === 'vehicles' && (
            <div className="auth-card authenticated-card" id="authenticated-container">
              <VehicleRegistrationForm
                onNavigateToProfile={(vehicleId) => navigateTo('profiles', vehicleId)}
              />
            </div>
          )}

          {activeNav === 'profiles' && (
            <VehicleProfileView
              initialVehicleId={selectedVehicleId}
              onBackToRegistration={() => navigateTo('vehicles')}
            />
          )}

          {activeNav === 'account' && (
            <div className="auth-card authenticated-card" id="authenticated-account-view">
              <div className="auth-header">
                <div className="status-indicator">
                  <span className="status-dot"></span>
                  Active Authenticated Session
                </div>
                <h2>Account & Credentials</h2>
                <p className="auth-subtitle">
                  Verified security credentials and role-based permissions for account{' '}
                  <strong className="font-mono">{user?.username}</strong>.
                </p>
              </div>

              <div className="user-profile-grid">
                <div className="profile-row">
                  <span className="profile-label">Username:</span>
                  <span className="profile-value font-mono" id="user-display-username">
                    {user?.username}
                  </span>
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
                    {user?.status || 'active'}
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

              <div className="auth-actions" style={{ marginTop: '2rem' }}>
                <button
                  type="button"
                  className="btn-danger"
                  onClick={logout}
                  disabled={isLoading}
                  id="btn-account-logout"
                >
                  {isLoading ? 'Signing Out...' : 'Sign Out of Facility Console'}
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
