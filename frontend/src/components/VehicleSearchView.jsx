import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/useAuth'
import { validateSearchPlateInput } from '../utils/vehicles'
import { parseApiError } from '../utils/apiErrors'
import BayIcon from './BayIcon'

export function VehicleSearchView({
  initialPlate = '',
  onNavigateToProfile,
  onNavigateToRegister,
}) {
  const { fetchWithAuth, user } = useAuth()
  const [searchInput, setSearchInput] = useState(initialPlate || '')
  const [searchedPlate, setSearchedPlate] = useState('')
  const [searchResult, setSearchResult] = useState(null)
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState(null)
  const [errorCode, setErrorCode] = useState(null)
  const [userVehicles, setUserVehicles] = useState([])

  // Fetch user's registered vehicles for quick search shortcuts
  useEffect(() => {
    let ignore = false
    async function loadUserVehicles() {
      try {
        const response = await fetchWithAuth('/api/v1/vehicles/')
        if (!ignore && response.ok) {
          const data = await response.json()
          if (Array.isArray(data)) {
            setUserVehicles(data)
          }
        }
      } catch {
        // Fallback silently if offline or restricted
      }
    }
    loadUserVehicles()
    return () => {
      ignore = true
    }
  }, [fetchWithAuth])

  const executeSearch = useCallback(
    async (rawPlate) => {
      const validation = validateSearchPlateInput(rawPlate)
      if (!validation.isValid) {
        setSearchError(validation.error)
        setSearchResult(null)
        setErrorCode('INVALID_INPUT')
        return
      }

      const plateToQuery = validation.normalized
      setSearchedPlate(plateToQuery)
      setIsSearching(true)
      setSearchError(null)
      setErrorCode(null)
      setSearchResult(null)

      try {
        const encoded = encodeURIComponent(plateToQuery)
        const response = await fetchWithAuth(`/api/v1/vehicles/search/?plate=${encoded}`)

        if (response.ok) {
          const data = await response.json()
          if (Array.isArray(data) && data.length === 0) {
            setErrorCode('NOT_FOUND')
            setSearchError(`No vehicle found with registration number "${plateToQuery}".`)
            setSearchResult(null)
          } else {
            setSearchResult(data)
            setSearchError(null)
            setErrorCode(null)
          }
        } else if (response.status === 404) {
          setErrorCode('NOT_FOUND')
          setSearchError(`No vehicle found with registration number "${plateToQuery}".`)
          setSearchResult(null)
        } else if (response.status === 403) {
          setErrorCode('FORBIDDEN')
          setSearchError('Access restricted. You do not have permission to inspect records for this vehicle.')
          setSearchResult(null)
        } else {
          const errData = await response.json().catch(() => null)
          const parsed = parseApiError(errData)
          setErrorCode(response.status)
          setSearchError(parsed.message || 'An error occurred while searching for the vehicle.')
          setSearchResult(null)
        }
      } catch {
        setErrorCode('NETWORK_ERROR')
        setSearchError('Network error occurred while executing vehicle search. Please verify connection.')
        setSearchResult(null)
      } finally {
        setIsSearching(false)
      }
    },
    [fetchWithAuth]
  )

  // Auto-search if initial plate was provided
  useEffect(() => {
    if (!initialPlate || !initialPlate.trim()) return
    let ignore = false
    const timer = setTimeout(() => {
      if (!ignore) {
        executeSearch(initialPlate)
      }
    }, 0)
    return () => {
      ignore = true
      clearTimeout(timer)
    }
  }, [initialPlate, executeSearch])

  const handleFormSubmit = (e) => {
    e.preventDefault()
    executeSearch(searchInput)
  }

  const handleQuickPlateClick = (plate) => {
    setSearchInput(plate)
    executeSearch(plate)
  }

  const handleClear = () => {
    setSearchInput('')
    setSearchResult(null)
    setSearchError(null)
    setErrorCode(null)
    setSearchedPlate('')
  }

  const isCustomer = user?.role === 'Customer'
  const isMultiple = Array.isArray(searchResult) && searchResult.length > 1
  const isSingle =
    (Array.isArray(searchResult) && searchResult.length === 1) ||
    (searchResult && !Array.isArray(searchResult))
  const singleResult = Array.isArray(searchResult) ? searchResult[0] : searchResult

  return (
    <div className="vehicle-search-container" id="vehicle-search-container">
      {/* Header Banner */}
      <div className="bay-page-heading search-page-heading">
        <div>
          <span className="bay-eyebrow">LIVE FLEET & OCCUPANCY SEARCH</span>
          <h1>
            Vehicle Search & Status<span>.</span>
          </h1>
          <p>
            {isCustomer
              ? 'Locate your registered vehicle and check active bay allocation.'
              : 'Search any vehicle by license plate to inspect real-time bay allocation, classification, and owner credentials.'}
          </p>
        </div>
      </div>

      {/* Search Input Bar Card */}
      <div className="search-bar-card">
        <form onSubmit={handleFormSubmit} noValidate className="search-form" id="vehicle-search-form">
          <div className="search-input-wrapper">
            <span className="search-icon-adornment" aria-hidden="true">
              <BayIcon name="search" size={20} />
            </span>
            <input
              type="text"
              id="vehicle-search-input"
              className="search-input font-mono"
              placeholder="Enter license plate e.g. KA-01-AB-1234 or DL-05-CD-5678"
              value={searchInput}
              onChange={(e) => {
                setSearchInput(e.target.value)
                if (searchError) setSearchError(null)
              }}
              autoComplete="off"
              autoCapitalize="characters"
              spellCheck="false"
              disabled={isSearching}
              aria-label="Search by license plate"
            />
            {searchInput && (
              <button
                type="button"
                className="btn-clear-search"
                onClick={handleClear}
                aria-label="Clear search input"
                title="Clear input"
              >
                ✕
              </button>
            )}
          </div>

          <button
            type="submit"
            className="bay-button bay-button-primary btn-search-submit"
            id="btn-search-vehicle"
            disabled={isSearching || !searchInput.trim()}
          >
            {isSearching ? (
              <>
                <span className="spinner" aria-hidden="true" />
                <span>Searching...</span>
              </>
            ) : (
              <>
                <BayIcon name="search" size={17} />
                <span>Search Vehicle</span>
              </>
            )}
          </button>
        </form>

        {/* Quick Search Shortcuts for User's Registered Vehicles */}
        {userVehicles.length > 0 && (
          <div className="quick-search-section">
            <span className="quick-search-label">Quick search your vehicles:</span>
            <div className="quick-search-pills">
              {userVehicles.map((v) => (
                <button
                  key={v.id}
                  type="button"
                  className={`quick-plate-pill ${searchedPlate === v.registration_number ? 'active' : ''}`}
                  onClick={() => handleQuickPlateClick(v.registration_number)}
                  disabled={isSearching}
                  title={`Search ${v.registration_number}`}
                >
                  <span className="pill-dot">●</span>
                  <span className="font-mono">{v.registration_number}</span>
                  <small className="pill-type">({v.vehicle_type})</small>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Search States: Loading, Error, Not Found, Results */}
      <div className="search-results-area" id="search-results-area">
        {isSearching && (
          <div className="search-state-card state-loading" id="search-loading-state">
            <span className="spinner spinner-large" aria-hidden="true" />
            <p>Scanning registry and resolving real-time parking status for "{searchedPlate}"...</p>
          </div>
        )}

        {/* Error / Not Found / Forbidden States */}
        {!isSearching && searchError && (
          <div
            className={`search-state-card ${
              errorCode === 'NOT_FOUND'
                ? 'state-not-found'
                : errorCode === 'FORBIDDEN'
                ? 'state-forbidden'
                : 'state-error'
            }`}
            id="search-error-state"
            role="alert"
          >
            <div className="state-icon">
              {errorCode === 'NOT_FOUND' ? '🔍' : errorCode === 'FORBIDDEN' ? '🔒' : '⚠️'}
            </div>
            <div className="state-content">
              <h3>
                {errorCode === 'NOT_FOUND'
                  ? 'Vehicle Not Found'
                  : errorCode === 'FORBIDDEN'
                  ? 'Access Restricted'
                  : 'Search Failed'}
              </h3>
              <p>{searchError}</p>
              {errorCode === 'NOT_FOUND' && onNavigateToRegister && (
                <div className="state-actions">
                  <button
                    type="button"
                    className="bay-button bay-button-primary"
                    id="btn-go-to-register"
                    onClick={onNavigateToRegister}
                  >
                    <span>Register New Vehicle</span>
                    <BayIcon name="arrow" size={16} />
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Multiple Search Results Display */}
        {!isSearching && isMultiple && (
          <div className="search-multiple-results" id="search-multiple-results">
            <div className="multiple-results-header">
              <h3 id="multiple-results-count">Matching Vehicles ({searchResult.length})</h3>
              <p>Found {searchResult.length} matching vehicles for query "{searchedPlate}".</p>
            </div>
            <div className="multiple-results-list" id="multiple-results-list">
              {searchResult.map((v) => (
                <div
                  key={v.id}
                  className="search-result-display multiple-result-card"
                  id={`vehicle-search-result-${v.id}`}
                >
                  <div
                    className={`live-status-hero ${
                      v.parking_status?.is_parked ? 'status-parked' : 'status-not-parked'
                    }`}
                  >
                    <div className="status-hero-main">
                      <span className="status-indicator-badge">
                        {v.parking_status?.is_parked ? (
                          <>
                            <span className="pulse-dot green" />
                            <strong>PARKED IN FACILITY</strong>
                          </>
                        ) : (
                          <>
                            <span className="pulse-dot neutral" />
                            <strong>NOT CURRENTLY PARKED</strong>
                          </>
                        )}
                      </span>
                      <p className="status-hero-message">{v.parking_status?.message}</p>
                    </div>

                    {v.parking_status?.is_parked && v.parking_status?.slot && (
                      <div className="allocated-slot-pill">
                        <div className="slot-pill-left">
                          <span className="pill-sub">ALLOCATED BAY</span>
                          <strong className="slot-name font-mono">
                            {v.parking_status.slot.slot_number}
                          </strong>
                        </div>
                        <div className="slot-pill-right">
                          <span>{v.parking_status.slot.zone || 'Main Zone'}</span>
                          <small>
                            {v.parking_status.slot.floor !== null && v.parking_status.slot.floor !== undefined
                              ? `Floor ${v.parking_status.slot.floor}`
                              : 'Level 1'}
                          </small>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="search-spec-card">
                    <div className="spec-card-header">
                      <span className="bay-eyebrow">VEHICLE SPECIFICATION</span>
                      <div className="header-plate-row">
                        <h2 className="spec-plate font-mono">{v.registration_number}</h2>
                        <span className="badge-type">{v.vehicle_type}</span>
                      </div>
                    </div>

                    <dl className="search-spec-list">
                      <div className="spec-row">
                        <dt>Vehicle Classification</dt>
                        <dd>{v.vehicle_type}</dd>
                      </div>
                      <div className="spec-row">
                        <dt>Owner Full Name</dt>
                        <dd>{v.owner_name || v.owner_username || '—'}</dd>
                      </div>
                      <div className="spec-row">
                        <dt>Contact Telephone</dt>
                        <dd>{v.owner_phone ? `📞 ${v.owner_phone}` : 'Not provided'}</dd>
                      </div>
                      <div className="spec-row">
                        <dt>System User Account</dt>
                        <dd className="font-mono">@{v.owner_username}</dd>
                      </div>
                      {v.created_at && (
                        <div className="spec-row">
                          <dt>Initial Registration</dt>
                          <dd>{new Date(v.created_at).toLocaleDateString()}</dd>
                        </div>
                      )}
                      {v.parking_status?.check_in_time && (
                        <div className="spec-row">
                          <dt>Session Check-In</dt>
                          <dd>{new Date(v.parking_status.check_in_time).toLocaleString()}</dd>
                        </div>
                      )}
                    </dl>

                    <div className="spec-card-actions">
                      {onNavigateToProfile && (
                        <button
                          type="button"
                          className="bay-button bay-button-primary"
                          onClick={() => onNavigateToProfile(v.id)}
                        >
                          <BayIcon name="edit" size={16} />
                          <span>View & Edit Full Profile</span>
                        </button>
                      )}
                      <button
                        type="button"
                        className="bay-button bay-button-quiet"
                        onClick={() => setSearchResult(v)}
                        title="Focus on this vehicle"
                      >
                        <span>Focus View</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="spec-card-actions">
              <button
                type="button"
                className="bay-button bay-button-quiet"
                onClick={handleClear}
              >
                <span>New Search</span>
              </button>
            </div>
          </div>
        )}

        {/* Single Search Result Display */}
        {!isSearching && isSingle && singleResult && (
          <div className="search-result-display" id="vehicle-search-result-card">
            {/* Live Parking Status Hero Banner */}
            <div
              className={`live-status-hero ${
                singleResult.parking_status?.is_parked ? 'status-parked' : 'status-not-parked'
              }`}
              id="live-parking-status-banner"
            >
              <div className="status-hero-main">
                <span className="status-indicator-badge">
                  {singleResult.parking_status?.is_parked ? (
                    <>
                      <span className="pulse-dot green" />
                      <strong>PARKED IN FACILITY</strong>
                    </>
                  ) : (
                    <>
                      <span className="pulse-dot neutral" />
                      <strong>NOT CURRENTLY PARKED</strong>
                    </>
                  )}
                </span>
                <p className="status-hero-message">{singleResult.parking_status?.message}</p>
              </div>

              {singleResult.parking_status?.is_parked && singleResult.parking_status?.slot && (
                <div className="allocated-slot-pill" id="search-allocated-slot">
                  <div className="slot-pill-left">
                    <span className="pill-sub">ALLOCATED BAY</span>
                    <strong className="slot-name font-mono">
                      {singleResult.parking_status.slot.slot_number}
                    </strong>
                  </div>
                  <div className="slot-pill-right">
                    <span>{singleResult.parking_status.slot.zone || 'Main Zone'}</span>
                    <small>
                      {singleResult.parking_status.slot.floor !== null &&
                      singleResult.parking_status.slot.floor !== undefined
                        ? `Floor ${singleResult.parking_status.slot.floor}`
                        : 'Level 1'}
                    </small>
                  </div>
                </div>
              )}
            </div>

            {/* Vehicle Profile Details Card */}
            <div className="search-details-grid">
              {/* Core Vehicle Specifications */}
              <div className="search-spec-card">
                <div className="spec-card-header">
                  <span className="bay-eyebrow">VEHICLE SPECIFICATION</span>
                  <div className="header-plate-row">
                    <h2 className="spec-plate font-mono" id="search-display-plate">
                      {singleResult.registration_number}
                    </h2>
                    <span className="badge-type" id="search-display-type">
                      {singleResult.vehicle_type}
                    </span>
                  </div>
                </div>

                <dl className="search-spec-list">
                  <div className="spec-row">
                    <dt>Vehicle Classification</dt>
                    <dd>{singleResult.vehicle_type}</dd>
                  </div>
                  <div className="spec-row">
                    <dt>Owner Full Name</dt>
                    <dd id="search-display-owner">
                      {singleResult.owner_name || singleResult.owner_username || '—'}
                    </dd>
                  </div>
                  <div className="spec-row">
                    <dt>Contact Telephone</dt>
                    <dd id="search-display-phone">
                      {singleResult.owner_phone ? `📞 ${singleResult.owner_phone}` : 'Not provided'}
                    </dd>
                  </div>
                  <div className="spec-row">
                    <dt>System User Account</dt>
                    <dd className="font-mono">@{singleResult.owner_username}</dd>
                  </div>
                  {singleResult.created_at && (
                    <div className="spec-row">
                      <dt>Initial Registration</dt>
                      <dd>{new Date(singleResult.created_at).toLocaleDateString()}</dd>
                    </div>
                  )}
                  {singleResult.parking_status?.check_in_time && (
                    <div className="spec-row">
                      <dt>Session Check-In</dt>
                      <dd>{new Date(singleResult.parking_status.check_in_time).toLocaleString()}</dd>
                    </div>
                  )}
                </dl>

                {/* Navigation to Full Profile (US-06) */}
                <div className="spec-card-actions">
                  {onNavigateToProfile && (
                    <button
                      type="button"
                      className="bay-button bay-button-primary"
                      id="btn-view-profile-from-search"
                      onClick={() => onNavigateToProfile(singleResult.id)}
                    >
                      <BayIcon name="edit" size={16} />
                      <span>View & Edit Full Profile</span>
                    </button>
                  )}
                  <button
                    type="button"
                    className="bay-button bay-button-quiet"
                    id="btn-search-another"
                    onClick={handleClear}
                  >
                    <span>New Search</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Initial Empty State */}
        {!isSearching && !searchResult && !searchError && (
          <div className="search-state-card state-empty" id="search-empty-state">
            <span className="empty-search-icon" aria-hidden="true">
              <BayIcon name="search" size={40} />
            </span>
            <h3>Ready to inspect vehicle status</h3>
            <p>
              Enter a normalized license plate number in the search bar above to look up vehicle
              registration details and active parking allocation.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default VehicleSearchView
