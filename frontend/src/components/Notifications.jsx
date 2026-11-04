import { useEffect, useState } from 'react'
import { useAuth } from '../context/useAuth'
import { parseApiError } from '../utils/apiErrors'
import './Notifications.css'

export default function Notifications() {
  const { fetchWithAuth, user } = useAuth()
  const [inbox, setInbox] = useState({ results: [], unread_count: null })
  const [error, setError] = useState('')
  const [pending, setPending] = useState(null)
  const [revision, setRevision] = useState(0)
  const [showRead, setShowRead] = useState(false)
  const [page, setPage] = useState(1)

  useEffect(() => {
    let ignore = false
    let loading = false
    const controller = new AbortController()
    async function load() {
      if (loading || document.hidden) return
      loading = true
      try {
        const response = await fetchWithAuth(`/api/notifications/?unread_only=${!showRead}&page=${page}`, {
          signal: controller.signal, cache: 'no-store',
        })
        const body = await response.json()
        if (!response.ok) throw parseApiError(body)
        if (!ignore) { setInbox(body); setError('') }
      } catch (failure) {
        if (!ignore) setError(failure.message || 'Notifications could not be refreshed.')
      } finally {
        loading = false
      }
    }
    load()
    const timer = setInterval(load, 30000)
    document.addEventListener('visibilitychange', load)
    return () => {
      ignore = true
      controller.abort()
      clearInterval(timer)
      document.removeEventListener('visibilitychange', load)
    }
  }, [fetchWithAuth, revision, showRead, page])

  async function dismiss(id) {
    setPending(id)
    try {
      const response = await fetchWithAuth(`/api/notifications/${id}/read/`, { method: 'POST' })
      const body = await response.json()
      if (!response.ok) throw parseApiError(body)
      // Restart polling to discard any earlier in-flight inbox response.
      setPage(1)
      setRevision((value) => value + 1)
    } catch (failure) {
      setError(failure.message || 'Notification could not be dismissed.')
    } finally {
      setPending(null)
    }
  }

  const unread = inbox.results.filter((item) => !item.read_at)
  return (
    <section className="notifications" aria-label="Notifications">
      <div className="notifications-heading">
        <strong role="status">{inbox.unread_count === null ? 'Loading notifications…' : `Notifications · ${inbox.unread_count} unread`}</strong>
        <button className="bay-button bay-button-light" onClick={() => { setPage(1); setRevision((value) => value + 1) }}>Refresh alerts</button>
      </div>
      {error ? <p className="bay-alert" role="status">{error}</p> : null}
      {unread.slice(0, 3).map((item) => (
        <div className="notification-banner" role={item.kind === 'facility_full' ? 'alert' : 'status'} key={item.id}>
          <span>{item.message}</span>
          <button className="bay-button bay-button-light" disabled={pending !== null} onClick={() => dismiss(item.id)} aria-label={`Dismiss: ${item.message}`}>Dismiss</button>
        </div>
      ))}
      <details>
        <summary>View notifications</summary>
        <label className="notifications-history"><input type="checkbox" checked={showRead} onChange={(event) => { setShowRead(event.target.checked); setPage(1) }} /> Include dismissed alerts</label>
        <p className="bay-small">Page {page} · {inbox.count || 0} alerts. Refreshes every 30 seconds while this tab is visible.</p>
        {inbox.results.length ? <ul>{inbox.results.map((item) => (
          <li key={item.id}>
            <div><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString()} · {item.read_at ? 'Read' : 'Unread'}</small></div>
            {!item.read_at ? <button className="bay-button bay-button-light" disabled={pending !== null} onClick={() => dismiss(item.id)}>Dismiss</button> : null}
          </li>
        ))}</ul> : <p>No notifications to show, {user?.username}.</p>}
        <div className="notifications-heading">
          <button className="bay-button bay-button-light" disabled={!inbox.previous} onClick={() => setPage((value) => value - 1)}>Newer alerts</button>
          <button className="bay-button bay-button-light" disabled={!inbox.next} onClick={() => setPage((value) => value + 1)}>Older alerts</button>
        </div>
      </details>
    </section>
  )
}
