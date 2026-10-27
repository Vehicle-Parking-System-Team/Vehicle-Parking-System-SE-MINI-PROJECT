import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/useAuth'
import { VEHICLE_TYPES } from '../utils/vehicles'
import { requestSlots, requestZones } from '../utils/slots'
import BayIcon from './BayIcon'

export default function SlotEditor({ slot, onClose, onSaved }) {
  const { fetchWithAuth } = useAuth()
  const dialogRef = useRef(null)
  const [form, setForm] = useState({
    slot_number: slot?.slot_number || '',
    zone: String(slot?.zone ?? ''),
    floor: slot ? String(slot.floor ?? '') : '0',
    vehicle_type: slot?.vehicle_type || 'Compact',
    is_active: slot?.is_active ?? true,
  })
  const [zones, setZones] = useState([])
  const [zoneName, setZoneName] = useState('')
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  useEffect(() => {
    const dialog = dialogRef.current
    dialog.showModal()
    return () => dialog.close()
  }, [])
  useEffect(() => {
    let ignore = false
    requestZones(fetchWithAuth)
      .then((data) => {
        if (!Array.isArray(data))
          throw new Error('The zone list could not be read.')
        if (!ignore) setZones(data)
      })
      .catch((failure) => {
        if (!ignore) setError(failure)
      })
    return () => {
      ignore = true
    }
  }, [fetchWithAuth])

  async function createZone() {
    if (!zoneName.trim() || saving) return
    setSaving(true)
    setError(null)
    try {
      const zone = await requestZones(fetchWithAuth, '', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: zoneName.trim() }),
      })
      setZones((current) => [...current, zone])
      setForm((current) => ({ ...current, zone: String(zone.id) }))
      setZoneName('')
    } catch (failure) {
      setError(failure)
    } finally {
      setSaving(false)
    }
  }

  async function submit(event) {
    event.preventDefault()
    if (saving) return
    setSaving(true)
    setError(null)
    try {
      const values = { ...form, zone: Number(form.zone) }
      if (form.floor === '') delete values.floor
      else values.floor = Number(form.floor)
      const saved = await requestSlots(
        fetchWithAuth,
        slot ? `${slot.id}/` : '',
        {
          method: slot ? 'PATCH' : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(values),
        },
      )
      onSaved(saved)
    } catch (failure) {
      setError(failure)
    } finally {
      setSaving(false)
    }
  }

  function fieldError(name) {
    return (
      error?.fieldErrors?.[name] && (
        <span className="bay-field-error" id={`${name}-error`}>
          {error.fieldErrors[name].join(' ')}
        </span>
      )
    )
  }
  const legacyType = !VEHICLE_TYPES.some(
    (type) => type.value === form.vehicle_type,
  )

  return (
    <dialog
      className="bay-dialog"
      ref={dialogRef}
      aria-labelledby="slot-editor-title"
      onCancel={(event) => {
        if (saving) event.preventDefault()
        else onClose()
      }}
    >
      <div className="bay-dialog-heading">
        <div>
          <span className="bay-eyebrow">SPACE CONFIGURATION</span>
          <h2 id="slot-editor-title">
            {slot ? 'Refine this space.' : 'Make room for more.'}
          </h2>
        </div>
        <button
          className="bay-icon-button"
          type="button"
          aria-label="Close slot editor"
          onClick={onClose}
          disabled={saving}
        >
          <BayIcon name="close" />
        </button>
      </div>
      <p className="bay-muted">
        {slot
          ? 'Update the specifications of this parking bay.'
          : 'New parking bays are created as Available.'}
      </p>
      {error && (
        <div className="bay-alert" role="alert">
          {[
            error.message || 'Unable to reach the parking service.',
            ...(error.formErrors || []),
          ].join(' ')}
        </div>
      )}
      <form onSubmit={submit}>
        <fieldset disabled={saving}>
          <div className="bay-field-pair">
            <label className="bay-field" htmlFor="edit-slot_number">
              Slot number
              <input
                id="edit-slot_number"
                maxLength={30}
                value={form.slot_number}
                required
                onChange={(event) =>
                  setForm({ ...form, slot_number: event.target.value })
                }
                aria-invalid={Boolean(error?.fieldErrors?.slot_number)}
                aria-describedby={
                  error?.fieldErrors?.slot_number
                    ? 'slot_number-error'
                    : undefined
                }
              />
              {fieldError('slot_number')}
            </label>
            <label className="bay-field" htmlFor="edit-zone">
              Zone
              <select
                id="edit-zone"
                aria-label="Zone"
                value={form.zone}
                required
                onChange={(event) =>
                  setForm({ ...form, zone: event.target.value })
                }
                aria-invalid={Boolean(error?.fieldErrors?.zone)}
              >
                <option value="">Choose a zone</option>
                {zones
                  .filter((zone) => zone.is_active || zone.id === slot?.zone)
                  .map((zone) => (
                    <option value={zone.id} key={zone.id}>
                      {zone.name}
                      {zone.is_active ? '' : ' (inactive)'}
                    </option>
                  ))}
              </select>
              {fieldError('zone')}
            </label>
            <label className="bay-field" htmlFor="edit-floor">
              Floor
              <input
                id="edit-floor"
                type="number"
                step={1}
                value={form.floor}
                placeholder="Unmapped"
                required={!slot || slot.floor !== null}
                onChange={(event) =>
                  setForm({ ...form, floor: event.target.value })
                }
                aria-invalid={Boolean(error?.fieldErrors?.floor)}
              />
              {fieldError('floor')}
            </label>
            <label className="bay-field" htmlFor="edit-vehicle_type">
              Vehicle type
              <select
                id="edit-vehicle_type"
                aria-label="Vehicle type"
                value={form.vehicle_type}
                onChange={(event) =>
                  setForm({ ...form, vehicle_type: event.target.value })
                }
                aria-invalid={Boolean(error?.fieldErrors?.vehicle_type)}
              >
                {legacyType && (
                  <option value={form.vehicle_type}>
                    {form.vehicle_type} (existing)
                  </option>
                )}
                {VEHICLE_TYPES.map((type) => (
                  <option value={type.value} key={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              {fieldError('vehicle_type')}
            </label>
          </div>
          <label className="bay-field" htmlFor="new-zone">
            New zone name (optional)
            <input
              id="new-zone"
              maxLength={100}
              value={zoneName}
              onChange={(event) => setZoneName(event.target.value)}
            />
            {fieldError('name')}
          </label>
          <button
            type="button"
            className="bay-button bay-button-quiet"
            disabled={!zoneName.trim()}
            onClick={createZone}
          >
            Create zone
          </button>
          {slot && !slot.is_active && (
            <label className="bay-reactivate">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) =>
                  setForm({ ...form, is_active: event.target.checked })
                }
              />
              Reactivate this bay
            </label>
          )}
          <div className="bay-dialog-footer">
            <button
              type="button"
              className="bay-button bay-button-quiet"
              onClick={onClose}
            >
              Cancel
            </button>
            <button type="submit" className="bay-button bay-button-primary">
              {saving
                ? 'Saving space...'
                : slot
                  ? 'Save changes'
                  : 'Create parking bay'}
              <BayIcon name="arrow" size={17} />
            </button>
          </div>
        </fieldset>
      </form>
    </dialog>
  )
}
