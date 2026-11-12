import { useEffect, useState } from 'react'
import { useAuth } from '../context/useAuth'
import { requestReservations } from '../utils/reservations'
import { parseApiError } from '../utils/apiErrors'

export default function ReservationForm({ slot, reservation, onClose, onSaved }) {
  const { fetchWithAuth } = useAuth()
  const [vehicles, setVehicles] = useState([])
  const [vehicle, setVehicle] = useState('')
  const [start, setStart] = useState(reservation ? new Date(reservation.start_time).toISOString().slice(0, 16) : '')
  const [duration, setDuration] = useState(reservation ? Math.round((new Date(reservation.end_time) - new Date(reservation.start_time)) / 60000) : 60)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [vehiclesLoading, setVehiclesLoading] = useState(!reservation)

  useEffect(() => {
    if (reservation) return
    let cancelled = false
    fetchWithAuth('/api/vehicles/')
      .then(async (response) => {
        const body = await response.json().catch(() => null)
        if (!response.ok) throw parseApiError(body)
        if (!Array.isArray(body)) throw new Error('Unable to read your vehicles.')
        if (!cancelled) { setVehicles(body); setVehicle(String(body[0]?.id ?? '')) }
      })
      .catch((err) => { if (!cancelled) setError(err.message || 'Could not load vehicles.') })
      .finally(() => { if (!cancelled) setVehiclesLoading(false) })
    return () => { cancelled = true }
  }, [fetchWithAuth, reservation])

  async function submit(event) {
    event.preventDefault()
    if (loading) return
    setLoading(true)
    setError('')
    try {
      const startTime = new Date(start)
      if (Number.isNaN(startTime.getTime()) || startTime <= new Date()) throw new Error('Choose a future start time.')
      const payload = {
        start_time: startTime.toISOString(),
        duration_minutes: Number(duration),
        ...(!reservation ? { slot: slot.id, vehicle: Number(vehicle) } : {}),
      }
      await requestReservations(fetchWithAuth, reservation ? `${reservation.id}/` : '', {
        method: reservation ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      onSaved()
    } catch (err) { setError(err.message || 'Reservation failed. Please retry.') }
    finally { setLoading(false) }
  }

  return (
    <div className="bay-dialog-backdrop">
      <dialog open className="bay-dialog" aria-labelledby="reservation-form-title" onCancel={onClose}>
        <h2 id="reservation-form-title">{reservation ? 'Reschedule reservation' : `Book bay ${slot.slot_number}`}</h2>
        {error && <p className="bay-alert" role="alert">{error}</p>}
        <form onSubmit={submit}>
          {!reservation && <label className="bay-field">Your vehicle
            <select value={vehicle} required disabled={vehiclesLoading} onChange={e => setVehicle(e.target.value)}>
              {vehicles.map(v => <option key={v.id} value={v.id}>{v.registration_number} — {v.vehicle_type}</option>)}
            </select>
          </label>}
          {!reservation && !vehiclesLoading && vehicles.length === 0 && <p>Register a vehicle before booking.</p>}
          <label className="bay-field">Start date and time
            <input type="datetime-local" required value={start} onChange={e => setStart(e.target.value)} />
          </label>
          <label className="bay-field">Duration (minutes)
            <input type="number" min="1" max="1440" required value={duration} onChange={e => setDuration(e.target.value)} />
          </label>
          <div className="bay-dialog-footer">
            <button type="button" className="bay-button bay-button-quiet" disabled={loading} onClick={onClose}>Cancel</button>
            <button type="submit" className="bay-button bay-button-primary" disabled={loading || (!reservation && (vehiclesLoading || !vehicle))}>{loading ? 'Saving…' : reservation ? 'Save changes' : 'Confirm booking'}</button>
          </div>
        </form>
      </dialog>
    </div>
  )
}
