import { useState, useEffect } from 'react'
import { useAuth } from '../context/useAuth'
import { parseApiError } from '../utils/apiErrors'
import { VEHICLE_TYPES, normalizePlate, validateVehicleUpdateInput } from '../utils/vehicles'

export function VehicleProfileView({ initialVehicleId, onBackToRegistration, onVehicleUpdated }) {
  const { fetchWithAuth, user } = useAuth()
  const [vehicles, setVehicles] = useState([])
  const [selectedId, setSelectedId] = useState(initialVehicleId || null)
  const [vehicle, setVehicle] = useState(null)
  const [isLoadingList, setIsLoadingList] = useState(true)
  const [isLoadingDetails, setIsLoadingDetails] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editFormData, setEditFormData] = useState({
    registration_number: '',
    vehicle_type: 'Compact',
    owner_name: '',
    owner_phone: '',
  })
  const [fieldErrors, setFieldErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)
  const [isSaving, setIsSaving] = useState(false)

  // Fetch all vehicles belonging to the user
  useEffect(() => {
    let ignore = false
    async function loadList() {
      setIsLoadingList(true)
      try {
        const response = await fetchWithAuth('/api/v1/vehicles/')
        if (!ignore && response.ok) {
          const data = await response.json()
          const list = Array.isArray(data) ? data : []
          setVehicles(list)
          if (list.length > 0) {
            setSelectedId((prev) => prev || list[0].id)
          }
        }
      } catch {
        // Safe fallback
      } finally {
        if (!ignore) {
          setIsLoadingList(false)
        }
      }
    }

    loadList()
    return () => {
      ignore = true
    }
  }, [fetchWithAuth])

  // Fetch full details for the selected vehicle (US-06 / FR-02)
  useEffect(() => {
    if (!selectedId) return
    let ignore = false

    async function loadDetails() {
      setIsLoadingDetails(true)
      setFormError(null)
      try {
        const response = await fetchWithAuth(`/api/v1/vehicles/${selectedId}/`)
        if (!ignore && response.ok) {
          const data = await response.json()
          setVehicle(data)
          setEditFormData({
            registration_number: data.registration_number || '',
            vehicle_type: data.vehicle_type || 'Compact',
            owner_name: data.owner_name || '',
            owner_phone: data.owner_phone || '',
          })
          setIsEditing(false)
          setFieldErrors({})
          setSuccessMessage(null)
        } else if (!ignore) {
          const errData = await response.json().catch(() => null)
          const parsed = parseApiError(errData)
          setFormError(parsed.message || 'Failed to load vehicle profile details.')
          setVehicle(null)
        }
      } catch {
        if (!ignore) {
          setFormError('Network error occurred while fetching vehicle details.')
          setVehicle(null)
        }
      } finally {
        if (!ignore) {
          setIsLoadingDetails(false)
        }
      }
    }

    loadDetails()
    return () => {
      ignore = true
    }
  }, [selectedId, fetchWithAuth])

  const handleStartEdit = () => {
    if (!vehicle) return
    setEditFormData({
      registration_number: vehicle.registration_number || '',
      vehicle_type: vehicle.vehicle_type || 'Compact',
      owner_name: vehicle.owner_name || '',
      owner_phone: vehicle.owner_phone || '',
    })
    setFieldErrors({})
    setFormError(null)
    setSuccessMessage(null)
    setIsEditing(true)
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setFieldErrors({})
    setFormError(null)
    if (vehicle) {
      setEditFormData({
        registration_number: vehicle.registration_number || '',
        vehicle_type: vehicle.vehicle_type || 'Compact',
        owner_name: vehicle.owner_name || '',
        owner_phone: vehicle.owner_phone || '',
      })
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setEditFormData((prev) => ({ ...prev, [name]: value }))
    if (fieldErrors[name]) {
      setFieldErrors((prev) => ({ ...prev, [name]: null }))
    }
    if (formError) setFormError(null)
  }

  const handleSaveEdit = async (e) => {
    e.preventDefault()
    setFieldErrors({})
    setFormError(null)
    setSuccessMessage(null)

    const normalizedPlate = normalizePlate(editFormData.registration_number)
    const validation = validateVehicleUpdateInput({
      registration_number: normalizedPlate,
      vehicle_type: editFormData.vehicle_type,
    })

    if (!validation.isValid) {
      setFieldErrors(validation.errors)
      return
    }

    setIsSaving(true)
    try {
      const payload = {
        registration_number: normalizedPlate,
        vehicle_type: editFormData.vehicle_type,
        owner_name: (editFormData.owner_name || '').trim(),
        owner_phone: (editFormData.owner_phone || '').trim(),
      }

      const response = await fetchWithAuth(`/api/v1/vehicles/${selectedId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await response.json().catch(() => null)

      if (response.ok) {
        setVehicle(data)
        setSuccessMessage(`Vehicle profile for ${data.registration_number} updated successfully.`)
        setIsEditing(false)
        // Refresh local list state
        setVehicles((prev) =>
          prev.map((v) => (v.id === selectedId ? { ...v, ...data } : v))
        )
        if (onVehicleUpdated) {
          onVehicleUpdated(data)
        }
      } else {
        const parsed = parseApiError(data)
        setFormError(parsed.message || 'Failed to update vehicle profile.')
        setFieldErrors(parsed.fieldErrors || {})
      }
    } catch {
      setFormError('Network error occurred while updating vehicle profile.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="vehicle-profile-container" id="vehicle-profile-view">
      <div className="profile-view-header">
        <div className="profile-header-main">
          <div className="profile-eyebrow">
            <span className="profile-telemetry-tag">Fleet Telemetry</span>
            <span className="profile-id-tag">Vehicle Record</span>
          </div>
          <h2 className="profile-view-title">🚗 Vehicle Profile & Fleet Management</h2>
          <p className="profile-view-subtitle">
            Inspect verified registration details, update vehicle classification, and manage owner contacts.
          </p>
        </div>

        {onBackToRegistration && (
          <button
            type="button"
            className="btn btn-secondary btn-back"
            id="btn-back-to-registration"
            onClick={onBackToRegistration}
          >
            ← Back to Registration
          </button>
        )}
      </div>

      {successMessage && (
        <div className="alert alert-success" id="profile-success-alert" role="status">
          <span className="alert-icon">✓</span>
          <span className="alert-text">{successMessage}</span>
        </div>
      )}

      {formError && (
        <div className="alert alert-error" id="profile-error-alert" role="alert">
          <span className="alert-icon">✗</span>
          <span className="alert-text">{formError}</span>
        </div>
      )}

      {isLoadingList ? (
        <div className="profile-loading-panel">
          <div className="btn-spinner" aria-hidden="true"></div>
          <p>Loading registered fleet records...</p>
        </div>
      ) : vehicles.length === 0 ? (
        <div className="profile-empty-card" id="profile-empty-state">
          <div className="empty-icon">🚗</div>
          <h3>No Vehicles Registered</h3>
          <p>You have not registered any vehicles in your fleet yet.</p>
          {onBackToRegistration && (
            <button
              type="button"
              className="btn btn-primary"
              id="btn-register-first-vehicle"
              onClick={onBackToRegistration}
            >
              Register Your First Vehicle
            </button>
          )}
        </div>
      ) : (
        <div className="profile-layout-grid">
          {/* Vehicle Switcher Sidebar */}
          <div className="profile-selector-pane" id="profile-vehicle-selector">
            <h4 className="pane-heading">Your Fleet ({vehicles.length})</h4>
            <div className="selector-list" role="tablist" aria-label="Select vehicle to inspect">
              {vehicles.map((v) => {
                const isCurrent = v.id === selectedId
                return (
                  <button
                    key={v.id}
                    type="button"
                    role="tab"
                    aria-selected={isCurrent}
                    className={`selector-item ${isCurrent ? 'selected' : ''}`}
                    id={`selector-vehicle-${v.id}`}
                    onClick={() => setSelectedId(v.id)}
                  >
                    <div className="selector-plate font-mono">{v.registration_number}</div>
                    <div className="selector-meta">
                      <span className="selector-type">{v.vehicle_type}</span>
                      {v.owner_name && <span className="selector-owner">👤 {v.owner_name}</span>}
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Vehicle Profile Details / Edit Card */}
          <div className="profile-detail-pane">
            {isLoadingDetails ? (
              <div className="profile-loading-panel">
                <div className="btn-spinner" aria-hidden="true"></div>
                <p>Retrieving vehicle telemetry and registration details...</p>
              </div>
            ) : vehicle ? (
              <div className="profile-detail-card" id={`profile-card-${vehicle.id}`}>
                <div className="card-top-bar">
                  <div className="plate-badge-container">
                    <span className="plate-region">IND</span>
                    <span className="plate-number font-mono" id="profile-display-plate">
                      {vehicle.registration_number}
                    </span>
                  </div>

                  <div className="card-top-actions">
                    {!isEditing && (
                      <button
                        type="button"
                        className="btn btn-primary btn-edit-profile"
                        id="btn-edit-vehicle-profile"
                        onClick={handleStartEdit}
                      >
                        ✏️ Edit Profile
                      </button>
                    )}
                  </div>
                </div>

                {!isEditing ? (
                  /* Read-Only Inspection View */
                  <div className="profile-inspect-grid" id="profile-inspect-view">
                    <div className="inspect-row">
                      <span className="inspect-label">Vehicle Classification:</span>
                      <span className="inspect-value badge-type" id="profile-display-type">
                        {vehicle.vehicle_type}
                      </span>
                    </div>

                    <div className="inspect-row">
                      <span className="inspect-label">Registered Owner:</span>
                      <span className="inspect-value font-semibold" id="profile-display-owner">
                        {vehicle.owner_name || user?.username || '—'}
                      </span>
                    </div>

                    <div className="inspect-row">
                      <span className="inspect-label">Contact Phone:</span>
                      <span className="inspect-value" id="profile-display-phone">
                        {vehicle.owner_phone ? `📞 ${vehicle.owner_phone}` : '—'}
                      </span>
                    </div>

                    <div className="inspect-row">
                      <span className="inspect-label">Record Identifier:</span>
                      <span className="inspect-value font-mono">#{vehicle.id}</span>
                    </div>

                    {vehicle.created_at && (
                      <div className="inspect-row">
                        <span className="inspect-label">Registration Date:</span>
                        <span className="inspect-value text-muted">
                          {new Date(vehicle.created_at).toLocaleString()}
                        </span>
                      </div>
                    )}

                    {vehicle.updated_at && (
                      <div className="inspect-row">
                        <span className="inspect-label">Last Profile Update:</span>
                        <span className="inspect-value text-muted">
                          {new Date(vehicle.updated_at).toLocaleString()}
                        </span>
                      </div>
                    )}

                    <div className="ownership-guarantee-note">
                      <span className="guarantee-icon">🛡️</span>
                      <span>
                        Verified Fleet Asset: Linked securely to authenticated account{' '}
                        <strong>{user?.username}</strong>. Server-side ownership isolation active.
                      </span>
                    </div>
                  </div>
                ) : (
                  /* Edit Mode Form (US-06) */
                  <form
                    onSubmit={handleSaveEdit}
                    noValidate
                    className="profile-edit-form"
                    id="profile-edit-form"
                  >
                    <div className="edit-form-header">
                      <h4>Edit Profile for #{vehicle.id}</h4>
                      <p className="text-muted">Update plate identifier, classification, or contact info.</p>
                    </div>

                    <div className="form-group">
                      <label htmlFor="edit-profile-plate">
                        License Plate / Registration Number <span className="required">*</span>
                      </label>
                      <input
                        type="text"
                        id="edit-profile-plate"
                        name="registration_number"
                        className={`form-input font-mono ${fieldErrors.registration_number ? 'input-error' : ''}`}
                        value={editFormData.registration_number}
                        onChange={handleInputChange}
                        disabled={isSaving}
                        required
                        autoComplete="off"
                      />
                      {fieldErrors.registration_number && (
                        <span className="field-error-text" id="edit-plate-error">
                          {fieldErrors.registration_number.join(' ')}
                        </span>
                      )}
                    </div>

                    <div className="form-group">
                      <label htmlFor="edit-profile-type">
                        Vehicle Classification <span className="required">*</span>
                      </label>
                      <select
                        id="edit-profile-type"
                        name="vehicle_type"
                        className={`form-input ${fieldErrors.vehicle_type ? 'input-error' : ''}`}
                        value={editFormData.vehicle_type}
                        onChange={handleInputChange}
                        disabled={isSaving}
                        required
                      >
                        {VEHICLE_TYPES.map((t) => (
                          <option key={t.value} value={t.value}>
                            {t.label}
                          </option>
                        ))}
                      </select>
                      {fieldErrors.vehicle_type && (
                        <span className="field-error-text" id="edit-type-error">
                          {fieldErrors.vehicle_type.join(' ')}
                        </span>
                      )}
                    </div>

                    <div className="form-row">
                      <div className="form-group col-half">
                        <label htmlFor="edit-profile-owner">Owner Name</label>
                        <input
                          type="text"
                          id="edit-profile-owner"
                          name="owner_name"
                          className="form-input"
                          value={editFormData.owner_name}
                          onChange={handleInputChange}
                          disabled={isSaving}
                        />
                      </div>

                      <div className="form-group col-half">
                        <label htmlFor="edit-profile-phone">Contact Phone</label>
                        <input
                          type="tel"
                          id="edit-profile-phone"
                          name="owner_phone"
                          className="form-input"
                          value={editFormData.owner_phone}
                          onChange={handleInputChange}
                          disabled={isSaving}
                        />
                      </div>
                    </div>

                    <div className="edit-actions-bar">
                      <button
                        type="submit"
                        className="btn btn-primary"
                        id="btn-save-profile"
                        disabled={isSaving}
                      >
                        {isSaving ? (
                          <>
                            <span className="btn-spinner" aria-hidden="true"></span>
                            Saving Profile...
                          </>
                        ) : (
                          'Save Profile Changes'
                        )}
                      </button>

                      <button
                        type="button"
                        className="btn btn-secondary"
                        id="btn-cancel-profile"
                        onClick={handleCancelEdit}
                        disabled={isSaving}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                )}
              </div>
            ) : (
              <div className="profile-error-card">
                <p>Please select a vehicle from the list to view its profile.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
