import { useState } from 'react'
import { useAuth } from '../context/useAuth'
import { VehicleRegistrationForm } from './VehicleRegistrationForm'
import { VehicleProfileView } from './VehicleProfileView'
import BayIcon from './BayIcon'
import SlotsPage from '../pages/Slots'
import SearchPage from '../pages/Search'

export function AuthenticatedView() {
  const { user, logout, isLoading } = useAuth()
  const canManage = ['Admin', 'Operator'].includes(user?.role)
  const [page, setPage] = useState(canManage ? 'facility' : 'vehicles')
  const [selectedVehicleId, setSelectedVehicleId] = useState(null)

  const activePage = page === 'facility' && !canManage ? 'vehicles' : page
  const navigation = [
    ...(canManage ? [['facility', 'Facility overview', 'map']] : []),
    ['vehicles', 'My vehicles', 'car'],
    ['profiles', 'Vehicle profiles', 'edit'],
    ['search', 'Vehicle search', 'search'],
    ['account', 'Account', 'user'],
  ]

  const handleNavigateToProfile = (vehicleId) => {
    setSelectedVehicleId(vehicleId)
    setPage('profiles')
  }

  return (
    <div className="bay-app">
      <a className="bay-skip" href="#bay-main">
        Skip to content
      </a>
      <aside className="bay-sidebar">
        <a className="bay-brand" href="#bay-main" aria-label="BAY workspace">
          <span className="bay-brand-mark">
            <i />
            <i />
            <i />
            <i />
          </span>
          <span>
            BAY<span className="bay-brand-dot">.</span>
          </span>
        </a>
        <p className="bay-sidebar-label">A BETTER WAY TO PARK</p>
        <div className="bay-location">
          <span className="bay-location-icon">
            <BayIcon name="layers" size={19} />
          </span>
          <div>
            <strong>Parking facility</strong>
            <span>Your spatial workspace</span>
          </div>
        </div>
        <span className="bay-nav-label">WORKSPACE</span>
        <nav aria-label="Workspace">
          {navigation.map(([key, title, icon]) => (
            <button
              key={key}
              type="button"
              id={`nav-${key}`}
              className={activePage === key ? 'is-active' : ''}
              aria-current={activePage === key ? 'page' : undefined}
              onClick={() => setPage(key)}
            >
              <BayIcon name={icon} size={19} />
              <span>{title}</span>
              {activePage === key && <i />}
            </button>
          ))}
        </nav>
        <div className="bay-sidebar-note">
          <div className="bay-mini-deck">
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
          </div>
          <span className="bay-eyebrow">SPATIAL WORKSPACE</span>
          <p>
            Every space.
            <br />A new perspective.
          </p>
          <span className="bay-small">
            Thoughtfully designed for
            <br />
            the way your facility moves.
          </span>
        </div>
        <div className="bay-sidebar-bottom">
          <span className="bay-avatar">
            {user?.username?.slice(0, 2).toUpperCase()}
          </span>
          <div>
            <strong id="user-display-username">{user?.username}</strong>
            <small id="user-display-role">{user?.role} workspace</small>
          </div>
          <button
            type="button"
            className="bay-icon-button"
            id="btn-logout"
            aria-label="Log out"
            onClick={logout}
            disabled={isLoading}
          >
            <BayIcon name="exit" size={18} />
          </button>
        </div>
      </aside>
      <div className="bay-main-shell">
        <header className="bay-topbar">
          <div>
            <span>Workspace</span>
            <span>/</span>
            <strong>
              {navigation.find(([key]) => key === activePage)?.[1]}
            </strong>
          </div>
          <span className="bay-workspace-status">
            <i />
            {user?.role}
            <span>workspace</span>
          </span>
        </header>
        <main id="bay-main" className="bay-main" tabIndex={-1}>
          {activePage === 'facility' ? (
            <SlotsPage />
          ) : activePage === 'vehicles' ? (
            <section className="bay-legacy-page" id="authenticated-container">
              <div className="bay-page-heading">
                <div>
                  <span className="bay-eyebrow">
                    READY FOR THE NEXT ARRIVAL
                  </span>
                  <h1>
                    Room to move<span>.</span>
                  </h1>
                  <p>Your vehicles. One place.</p>
                </div>
              </div>
              <VehicleRegistrationForm
                onNavigateToProfile={handleNavigateToProfile}
              />
            </section>
          ) : activePage === 'profiles' ? (
            <section className="bay-legacy-page" id="vehicle-profile-section">
              <VehicleProfileView
                initialVehicleId={selectedVehicleId}
                onBackToRegistration={() => setPage('vehicles')}
              />
            </section>
          ) : activePage === 'search' ? (
            <section className="bay-legacy-page" id="vehicle-search-section">
              <SearchPage
                onNavigateToProfile={handleNavigateToProfile}
                onNavigateToRegister={() => setPage('vehicles')}
              />
            </section>
          ) : (
            <section className="bay-account">
              <span className="bay-eyebrow">YOUR WORKSPACE</span>
              <h1>
                A little about you<span>.</span>
              </h1>
              <div className="bay-account-card">
                <span className="bay-avatar bay-avatar-large">
                  {user?.username?.slice(0, 2).toUpperCase()}
                </span>
                <h2>{user?.username}</h2>
                <p>{user?.email || 'No email provided'}</p>
                <dl className="bay-slot-details">
                  <div>
                    <dt>Role</dt>
                    <dd>{user?.role}</dd>
                  </div>
                  <div>
                    <dt>Account status</dt>
                    <dd id="user-display-status">{user?.status || 'active'}</dd>
                  </div>
                </dl>
                <button
                  className="bay-button bay-button-primary"
                  onClick={logout}
                  disabled={isLoading}
                >
                  {isLoading ? 'Signing out...' : 'Sign out securely'}
                  <BayIcon name="exit" size={17} />
                </button>
              </div>
            </section>
          )}
        </main>
        <footer className="bay-footer">
          <span>
            BAY<span>.</span> Built around your space.
          </span>
          <span>
            VEHICLE PARKING SYSTEM <i /> 2026
          </span>
        </footer>
      </div>
    </div>
  )
}
