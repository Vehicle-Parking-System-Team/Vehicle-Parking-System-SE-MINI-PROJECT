import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../context/useAuth'
import { requestReservations, canModifyReservation } from '../utils/reservations'
import ReservationForm from '../components/ReservationForm'

export default function ReservationsPage() {
  const { fetchWithAuth } = useAuth()
  const [records, setRecords] = useState([])
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)
  const [status, setStatus] = useState('')
  const [editing, setEditing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [revision, setRevision] = useState(0)
  const [busyId, setBusyId] = useState(null)

  const refresh = useCallback(() => setRevision(value => value + 1), [])
  useEffect(() => {
    const controller = new AbortController()
    let active = true
    setLoading(true)
    setError('')
    const params = new URLSearchParams({ page: String(page) })
    if (status) params.set('status', status)
    requestReservations(fetchWithAuth, `?${params}`, { signal: controller.signal })
      .then(data => {
        if (!active) return
        setRecords(data.results)
        setCount(data.count)
      })
      .catch(err => { if (active) setError(err.message || 'Unable to load reservations.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false; controller.abort() }
  }, [fetchWithAuth, page, status, revision])

  async function cancel(reservation) {
    if (!window.confirm(`Cancel reservation ${reservation.reservation_code}?`)) return
    setBusyId(reservation.id)
    setError('')
    try {
      await requestReservations(fetchWithAuth, `${reservation.id}/`, { method: 'DELETE' })
      setNotice('Reservation cancelled.')
      refresh()
    } catch (err) { setError(err.message || 'Unable to cancel reservation.') }
    finally { setBusyId(null) }
  }

  return <section className="bay-legacy-page">
    <div className="bay-page-heading"><div><span className="bay-eyebrow">YOUR BOOKINGS</span><h1>My reservations<span>.</span></h1><p>Review, reschedule or cancel upcoming bookings.</p></div></div>
    <label className="bay-field">Filter by status
      <select value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}>
        <option value="">All reservations</option>
        {['Confirmed', 'Cancelled', 'Fulfilled'].map(value => <option key={value} value={value}>{value}</option>)}
      </select>
    </label>
    {error && <p className="bay-alert" role="alert">{error} <button onClick={refresh}>Retry</button></p>}
    {notice && <p className="bay-success" role="status">{notice}</p>}
    {loading ? <p role="status">Loading reservations…</p> : records.length === 0 ? <p>No reservations found.</p> : (
      <div className="bay-quick-grid">
        {records.map(reservation => <article className="bay-quick-card" key={reservation.id}>
          <strong>{reservation.reservation_code}</strong>
          <p>Status: {reservation.status}</p>
          <p>Vehicle #{reservation.vehicle} · Bay #{reservation.slot}</p>
          <p>Start: {new Date(reservation.start_time).toLocaleString()}</p>
          <p>End: {new Date(reservation.end_time).toLocaleString()}</p>
          {canModifyReservation(reservation) && <div className="bay-dialog-footer">
            <button className="bay-button bay-button-quiet" disabled={busyId === reservation.id} onClick={() => setEditing(reservation)}>Reschedule</button>
            <button className="bay-button bay-button-quiet" disabled={busyId === reservation.id} onClick={() => cancel(reservation)}>Cancel booking</button>
          </div>}
        </article>)}
      </div>
    )}
    <nav aria-label="Reservation pages" className="bay-dialog-footer">
      <button className="bay-button bay-button-quiet" disabled={page === 1 || loading} onClick={() => setPage(n => n - 1)}>Previous</button>
      <span>Page {page} of {Math.max(1, Math.ceil(count / 10))}</span>
      <button className="bay-button bay-button-quiet" disabled={page * 10 >= count || loading} onClick={() => setPage(n => n + 1)}>Next</button>
    </nav>
    {editing && <ReservationForm reservation={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); setNotice('Reservation rescheduled.'); refresh() }} />}
  </section>
}
