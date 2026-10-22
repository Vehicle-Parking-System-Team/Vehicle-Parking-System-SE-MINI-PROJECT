import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/useAuth'
import { parseApiError } from '../utils/apiErrors'
import { VEHICLE_TYPES, normalizePlate } from '../utils/vehicles'

export function VehicleRegistrationForm({ onVehicleRegistered }) {
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

    const trimmedPlate = normalizePlate(formData.registration_number)
    if (!trimmedPlate) {
      setFieldErrors({ registration_number: ['Registration number is required.'] })
      return
    }
    if (trimmedPlate.length > 20) {
      setFieldErrors({ registration_number: ['Ensure this field has no more than 20 characters.'] })
      return
    }
    if (!formData.vehicle_type) {
      setFieldErrors({ vehicle_type: ['Vehicle type is required.'] })
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

  return (
    <div className="vehicle-registration-container" id="vehicle-registration-section">
      <div className="section-header">
        <h3>🚗 Vehicle Registration (US-05 / FR-01)</h3>
        <p className="section-subtitle">
          Register a vehicle with license plate number, vehicle class, and owner information.
        </p>
      </div>

      {successMessage && (
        <div className="alert alert-success" id="vehicle-registration-success" role="status">
          <span className="alert-icon">✓</span>
          <span className="alert-text">{successMessage}</span>
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
            {vehicles.map((v) => (
              <div key={v.id || v.registration_number} className="vehicle-badge-card">
                <div className="vehicle-plate font-mono">{v.registration_number}</div>
                <div className="vehicle-meta">
                  <span className="badge-type">{v.vehicle_type}</span>
                  {v.owner_name && <span className="owner-tag">👤 {v.owner_name}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
