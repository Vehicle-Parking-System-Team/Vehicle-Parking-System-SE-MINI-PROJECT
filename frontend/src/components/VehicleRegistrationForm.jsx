import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/useAuth'
import { parseApiError } from '../utils/apiErrors'
import { VEHICLE_TYPES, normalizePlate, validateRegistrationNumber, validateVehicleUpdateInput } from '../utils/vehicles'

export function VehicleRegistrationForm({ onVehicleRegistered, onNavigateToProfile }) {
  const { fetchWithAuth, user } = useAuth()
  const [formData, setFormData] = useState({
    registration_number: '',
    vehicle_type: 'Compact',
    owner_name: '',
    owner_phone: '',
  })
  const [fieldErrors, setFieldErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [vehicles, setVehicles] = useState([])
  const [isLoadingVehicles, setIsLoadingVehicles] = useState(false)

  // Edit vehicle profile state (US-06 / FR-02)
  const [editingVehicleId, setEditingVehicleId] = useState(null)
  const [editFormData, setEditFormData] = useState({})
  const [editFieldErrors, setEditFieldErrors] = useState({})
  const [editFormError, setEditFormError] = useState(null)
  const [isSavingEdit, setIsSavingEdit] = useState(false)
  const [editSuccessMessage, setEditSuccessMessage] = useState(null)

  // Fetch existing vehicles registered to the user
  const loadUserVehicles = useCallback(async () => {
    setIsLoadingVehicles(true)
    try {
      const response = await fetchWithAuth('/api/v1/vehicles/')
      if (response.ok) {
        const data = await response.json()
        setVehicles(Array.isArray(data) ? data : [])
      }
    } catch {
      // Non-blocking background fetch failure
    } finally {
      setIsLoadingVehicles(false)
    }
  }, [fetchWithAuth])

  useEffect(() => {
    let ignore = false
    async function fetchVehicles() {
      setIsLoadingVehicles(true)
      try {
        const response = await fetchWithAuth('/api/v1/vehicles/')
        if (!ignore && response.ok) {
          const data = await response.json()
          setVehicles(Array.isArray(data) ? data : [])
        }
      } catch {
        // Safe network fallback
      } finally {
        if (!ignore) {
          setIsLoadingVehicles(false)
        }
      }
    }
    fetchVehicles()
    return () => {
      ignore = true
    }
  }, [fetchWithAuth])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (fieldErrors[name]) {
      setFieldErrors((prev) => ({ ...prev, [name]: null }))
    }
    if (formError) setFormError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFieldErrors({})
    setFormError(null)
    setSuccessMessage(null)

    const plateValidation = validateRegistrationNumber(formData.registration_number)
    if (!plateValidation.isValid) {
      setFieldErrors({ registration_number: [plateValidation.error] })
      return
    }
    const trimmedPlate = plateValidation.normalized
    if (!formData.vehicle_type || !VEHICLE_TYPES.some((type) => type.value === formData.vehicle_type)) {
      setFieldErrors({ vehicle_type: ['A valid vehicle type is required.'] })
      return
    }

    setIsSubmitting(true)
    try {
      const payload = {
        registration_number: trimmedPlate,
        vehicle_type: formData.vehicle_type,
        owner_name: formData.owner_name.trim() || user?.username,
        owner_phone: formData.owner_phone.trim(),
      }

      const response = await fetchWithAuth('/api/v1/vehicles/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await response.json().catch(() => null)

      if (response.status === 201) {
        setSuccessMessage(`Vehicle ${data.registration_number} (${data.vehicle_type}) registered successfully.`)
        setFormData({
          registration_number: '',
          vehicle_type: 'Compact',
          owner_name: '',
          owner_phone: '',
        })
        setVehicles((prev) => [data, ...prev])
        if (onVehicleRegistered) onVehicleRegistered(data)
        loadUserVehicles()
      } else {
        const parsed = parseApiError(data)
        setFormError(parsed.message || 'Registration failed.')
        setFieldErrors(parsed.fieldErrors || {})
      }
    } catch (err) {
      setFormError(err.message || 'Network error occurred while connecting to vehicle service.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleStartEdit = (vehicle) => {
    setEditingVehicleId(vehicle.id)
    setEditFormData({
      registration_number: vehicle.registration_number || '',
      vehicle_type: vehicle.vehicle_type || 'Compact',
      owner_name: vehicle.owner_name || '',
      owner_phone: vehicle.owner_phone || '',
    })
    setEditFieldErrors({})
    setEditFormError(null)
    setEditSuccessMessage(null)
  }

  const handleCancelEdit = () => {
    setEditingVehicleId(null)
    setEditFormData({})
    setEditFieldErrors({})
    setEditFormError(null)
  }

  const handleEditChange = (e) => {
    const { name, value } = e.target
    setEditFormData((prev) => ({ ...prev, [name]: value }))
    if (editFieldErrors[name]) {
      setEditFieldErrors((prev) => ({ ...prev, [name]: null }))
    }
    if (editFormError) setEditFormError(null)
  }

  const handleSaveEdit = async (e, vehicleId) => {
    e.preventDefault()
    setEditFieldErrors({})
    setEditFormError(null)
    setEditSuccessMessage(null)

    const normalizedPlate = normalizePlate(editFormData.registration_number)
    const validation = validateVehicleUpdateInput({
      registration_number: normalizedPlate,
      vehicle_type: editFormData.vehicle_type,
    })

    if (!validation.isValid) {
      setEditFieldErrors(validation.errors)
      return
    }

    setIsSavingEdit(true)
    try {
      const payload = {
        registration_number: normalizedPlate,
        vehicle_type: editFormData.vehicle_type,
        owner_name: (editFormData.owner_name || '').trim(),
        owner_phone: (editFormData.owner_phone || '').trim(),
      }

      const response = await fetchWithAuth(`/api/v1/vehicles/${vehicleId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await response.json().catch(() => null)

      if (response.ok) {
        setEditSuccessMessage(`Vehicle ${data.registration_number} profile updated successfully.`)
        setVehicles((prev) =>
          prev.map((v) => (v.id === vehicleId ? { ...v, ...data } : v))
        )
        setEditingVehicleId(null)
      } else {
        const parsed = parseApiError(data)
        setEditFormError(parsed.message || 'Update failed.')
        setEditFieldErrors(parsed.fieldErrors || {})
      }
    } catch (err) {
      setEditFormError(err.message || 'Network error occurred while updating vehicle profile.')
    } finally {
      setIsSavingEdit(false)
    }
  }

  return (
    <div className="vehicle-registration-container" id="vehicle-registration-section">
      <div className="section-header">
        <h3>🚗 Vehicle Registration & Fleet Management</h3>
        <p className="section-subtitle">
          Register new vehicles and view or update existing vehicle profiles and contact details.
        </p>
      </div>

      {successMessage && (
        <div className="alert alert-success" id="vehicle-registration-success" role="status">
          <span className="alert-icon">✓</span>
          <span className="alert-text">{successMessage}</span>
        </div>
      )}

      {editSuccessMessage && (
        <div className="alert alert-success" id="vehicle-edit-success" role="status">
          <span className="alert-icon">✓</span>
          <span className="alert-text">{editSuccessMessage}</span>
        </div>
      )}

      {formError && (
        <div className="alert alert-error" id="vehicle-registration-error" role="alert">
          <span className="alert-icon">✗</span>
          <span className="alert-text">{formError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="vehicle-form" noValidate>
        <div className="form-group">
          <label htmlFor="registration_number">
            Registration Number / License Plate <span className="required">*</span>
          </label>
          <input
            type="text"
            id="registration_number"
            name="registration_number"
            className={`form-input ${fieldErrors.registration_number ? 'input-error' : ''}`}
            placeholder="e.g. KA-01-AB-1234"
            value={formData.registration_number}
            onChange={handleChange}
            disabled={isSubmitting}
            autoComplete="off"
            required
          />
          {fieldErrors.registration_number && (
            <span className="field-error-text" id="reg-number-error">
              {fieldErrors.registration_number.join(' ')}
            </span>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="vehicle_type">
            Vehicle Type <span className="required">*</span>
          </label>
          <select
            id="vehicle_type"
            name="vehicle_type"
            className={`form-input ${fieldErrors.vehicle_type ? 'input-error' : ''}`}
            value={formData.vehicle_type}
            onChange={handleChange}
            disabled={isSubmitting}
            required
          >
            {VEHICLE_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          {fieldErrors.vehicle_type && (
            <span className="field-error-text" id="vehicle-type-error">
              {fieldErrors.vehicle_type.join(' ')}
            </span>
          )}
        </div>

        <div className="form-row">
          <div className="form-group col-half">
            <label htmlFor="owner_name">Owner Name (Optional)</label>
            <input
              type="text"
              id="owner_name"
              name="owner_name"
              className="form-input"
              placeholder={user?.username || 'Full Name'}
              value={formData.owner_name}
              maxLength={100}
              onChange={handleChange}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group col-half">
            <label htmlFor="owner_phone">Owner Phone (Optional)</label>
            <input
              type="tel"
              id="owner_phone"
              name="owner_phone"
              className="form-input"
              placeholder="e.g. 9876543210"
              value={formData.owner_phone}
              maxLength={20}
              onChange={handleChange}
              disabled={isSubmitting}
            />
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          id="btn-register-vehicle"
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <>
              <span className="btn-spinner" aria-hidden="true"></span>
              Registering Vehicle...
            </>
          ) : (
            'Register Vehicle'
          )}
        </button>
      </form>

      <div className="registered-vehicles-list" id="registered-vehicles-block">
        <h4>Your Registered Vehicles ({vehicles.length})</h4>
        {isLoadingVehicles ? (
          <p className="loading-hint">Loading registered vehicles...</p>
        ) : vehicles.length === 0 ? (
          <p className="empty-hint">No vehicles registered yet. Use the form above to add one.</p>
        ) : (
          <div className="vehicles-grid">
            {vehicles.map((v) => {
              const isEditing = editingVehicleId === v.id

              if (isEditing) {
                return (
                  <div key={v.id} className="vehicle-badge-card vehicle-edit-card" id={`vehicle-edit-card-${v.id}`}>
                    <div className="card-edit-header">
                      <strong>Edit Vehicle #{v.id}</strong>
                    </div>

                    {editFormError && (
                      <div className="alert alert-error edit-alert" role="alert">
                        <span>{editFormError}</span>
                      </div>
                    )}

                    <form onSubmit={(e) => handleSaveEdit(e, v.id)} noValidate className="inline-edit-form">
                      <div className="form-group-sm">
                        <label htmlFor={`edit-plate-${v.id}`}>Plate Number</label>
                        <input
                          type="text"
                          id={`edit-plate-${v.id}`}
                          name="registration_number"
                          className={`form-input-sm ${editFieldErrors.registration_number ? 'input-error' : ''}`}
                          value={editFormData.registration_number}
                          onChange={handleEditChange}
                          disabled={isSavingEdit}
                          required
                        />
                        {editFieldErrors.registration_number && (
                          <span className="field-error-text-sm">
                            {editFieldErrors.registration_number.join(' ')}
                          </span>
                        )}
                      </div>

                      <div className="form-group-sm">
                        <label htmlFor={`edit-type-${v.id}`}>Vehicle Type</label>
                        <select
                          id={`edit-type-${v.id}`}
                          name="vehicle_type"
                          className={`form-input-sm ${editFieldErrors.vehicle_type ? 'input-error' : ''}`}
                          value={editFormData.vehicle_type}
                          onChange={handleEditChange}
                          disabled={isSavingEdit}
                          required
                        >
                          {VEHICLE_TYPES.map((t) => (
                            <option key={t.value} value={t.value}>
                              {t.label}
                            </option>
                          ))}
                        </select>
                        {editFieldErrors.vehicle_type && (
                          <span className="field-error-text-sm">
                            {editFieldErrors.vehicle_type.join(' ')}
                          </span>
                        )}
                      </div>

                      <div className="form-group-sm">
                        <label htmlFor={`edit-owner-${v.id}`}>Owner Name</label>
                        <input
                          type="text"
                          id={`edit-owner-${v.id}`}
                          name="owner_name"
                          className="form-input-sm"
                          value={editFormData.owner_name}
                          maxLength={100}
                          onChange={handleEditChange}
                          disabled={isSavingEdit}
                        />
                      </div>

                      <div className="form-group-sm">
                        <label htmlFor={`edit-phone-${v.id}`}>Owner Phone</label>
                        <input
                          type="tel"
                          id={`edit-phone-${v.id}`}
                          name="owner_phone"
                          className="form-input-sm"
                          value={editFormData.owner_phone}
                          maxLength={20}
                          onChange={handleEditChange}
                          disabled={isSavingEdit}
                        />
                      </div>

                      <div className="edit-btn-group">
                        <button
                          type="submit"
                          className="btn btn-sm btn-primary"
                          id={`btn-save-vehicle-${v.id}`}
                          disabled={isSavingEdit}
                        >
                          {isSavingEdit ? 'Saving...' : 'Save'}
                        </button>
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          id={`btn-cancel-vehicle-${v.id}`}
                          onClick={handleCancelEdit}
                          disabled={isSavingEdit}
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  </div>
                )
              }

              return (
                <div key={v.id || v.registration_number} className="vehicle-badge-card" id={`vehicle-card-${v.id}`}>
                  <div className="vehicle-card-top">
                    <div className="vehicle-plate font-mono">{v.registration_number}</div>
                    <div className="card-action-group">
                      {onNavigateToProfile && v.id && (
                        <button
                          type="button"
                          className="btn-profile-badge"
                          id={`btn-profile-vehicle-${v.id}`}
                          onClick={() => onNavigateToProfile(v.id)}
                          title="Open Vehicle Profile"
                        >
                          📋 Profile
                        </button>
                      )}
                      {v.id && (
                        <button
                          type="button"
                          className="btn-edit-badge"
                          id={`btn-edit-vehicle-${v.id}`}
                          onClick={() => handleStartEdit(v)}
                          title="Edit Vehicle Inline"
                        >
                          ✏️ Edit
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="vehicle-meta">
                    <span className="badge-type">{v.vehicle_type}</span>
                    {v.owner_name && <span className="owner-tag">👤 {v.owner_name}</span>}
                  </div>
                  {v.owner_phone && (
                    <div className="vehicle-sub-meta">
                      <span className="phone-tag">📞 {v.owner_phone}</span>
                    </div>
                  )}
                  {v.updated_at && (
                    <div className="vehicle-sub-meta text-muted">
                      <small>Updated: {new Date(v.updated_at).toLocaleDateString()}</small>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
