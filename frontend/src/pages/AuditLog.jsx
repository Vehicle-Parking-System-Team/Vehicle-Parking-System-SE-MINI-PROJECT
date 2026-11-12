import { Fragment, useEffect, useState } from 'react'
import { useAuth } from '../context/useAuth'
import { AUDIT_ACTIONS, AUDIT_PAGE_SIZE, EMPTY_AUDIT_FILTERS, auditQuery, auditStateChanges, requestAudit } from '../utils/audit'
import './AuditLog.css'

const timestamp = new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'medium' })
const formatValue = (value) => value === undefined ? 'Not recorded' : JSON.stringify(value)

function EventDetails({ event }) {
  const changes = auditStateChanges(event.details)
  return (
    <div className="audit-event-details">
      <dl>
        <div><dt>Event ID</dt><dd>{event.id}</dd></div>
        <div><dt>Actor ID</dt><dd>{event.actor_id ?? 'No verified actor'}</dd></div>
        <div><dt>Peer IP</dt><dd>{event.ip_address || 'Not recorded'}</dd></div>
        <div><dt>Timestamp (UTC)</dt><dd>{event.occurred_at}</dd></div>
      </dl>
      {changes.length > 0 && (
        <table className="audit-changes">
          <caption>State changes</caption>
          <thead><tr><th scope="col">Field</th><th scope="col">Previous</th><th scope="col">New</th></tr></thead>
          <tbody>{changes.map((change) => (
            <tr key={change.field}><th scope="row">{change.field}</th><td>{formatValue(change.before)}</td><td>{formatValue(change.after)}</td></tr>
          ))}</tbody>
        </table>
      )}
      <details><summary>Recorded event payload</summary><pre>{JSON.stringify(event.details, null, 2)}</pre></details>
    </div>
  )
}

export default function AuditLog() {
  const { fetchWithAuth } = useAuth()
  const [draft, setDraft] = useState(EMPTY_AUDIT_FILTERS)
  const [filters, setFilters] = useState(EMPTY_AUDIT_FILTERS)
  const [page, setPage] = useState(1)
  const [revision, setRevision] = useState(0)
  const [result, setResult] = useState(null)
  const [expanded, setExpanded] = useState(null)
  const [filterError, setFilterError] = useState('')
  const query = auditQuery(filters, page)
  const requestKey = `${query}:${revision}`
  const current = result?.key === requestKey ? result : null
  const loading = !current

  useEffect(() => {
    const controller = new AbortController()
    let ignore = false
    let timedOut = false
    const timer = setTimeout(() => { timedOut = true; controller.abort() }, 15_000)
    requestAudit(fetchWithAuth, query, controller.signal).then((data) => {
      if (!ignore) setResult({ key: requestKey, data })
    }).catch((error) => {
      if (!ignore) setResult({ key: requestKey, error: timedOut ? new Error('The audit request timed out. Please retry.') : error })
    }).finally(() => clearTimeout(timer))
    return () => { ignore = true; clearTimeout(timer); controller.abort() }
  }, [fetchWithAuth, query, requestKey])

  function applyFilters(event) {
    event.preventDefault()
    try {
      auditQuery(draft)
      setFilters({ ...draft })
      setPage(1)
      setExpanded(null)
      setFilterError('')
      setRevision((value) => value + 1)
    } catch (error) { setFilterError(error.message) }
  }

  function clearFilters() {
    setDraft(EMPTY_AUDIT_FILTERS)
    setFilters(EMPTY_AUDIT_FILTERS)
    setFilterError('')
    setPage(1)
    setExpanded(null)
    setRevision((value) => value + 1)
  }

  const data = current?.data
  const lastPage = Math.max(1, Math.ceil((data?.count || 0) / AUDIT_PAGE_SIZE))
  const fields = [
    ['event_type', 'Action', 'text', 'e.g. account.updated'],
    ['actor', 'Actor username or ID', 'text', 'Search recorded actors'],
    ['resource_type', 'Resource type', 'text', 'e.g. user or parking_zone'],
    ['start', 'From (inclusive)', 'datetime-local'],
    ['end', 'Until (exclusive)', 'datetime-local'],
  ]

  return (
    <section className="audit-page" aria-labelledby="audit-heading">
      <div className="bay-page-heading">
        <div><span className="bay-eyebrow">SECURITY & ACCOUNTABILITY</span><h1 id="audit-heading">Audit log<span>.</span></h1><p>Inspect security and operational events, newest first.</p></div>
        <button type="button" className="bay-button bay-button-light" disabled={loading} onClick={() => setRevision((value) => value + 1)}>Refresh events</button>
      </div>
      <p className="audit-notice">Read-only history. Actor names and roles reflect the time of the event. Times and date filters use your browser’s local timezone ({Intl.DateTimeFormat().resolvedOptions().timeZone}).</p>
      <form className="audit-filters" onSubmit={applyFilters} aria-label="Filter audit events">
        {fields.map(([key, label, type, placeholder]) => (
          <div key={key}><label htmlFor={`audit-${key}`}>{label}</label><input id={`audit-${key}`} type={type} placeholder={placeholder} list={key === 'event_type' ? 'audit-actions' : undefined}
            maxLength={key === 'actor' ? 150 : 100} value={draft[key]} onChange={(event) => setDraft((current) => ({ ...current, [key]: event.target.value }))} /></div>
        ))}
        <datalist id="audit-actions">{AUDIT_ACTIONS.map((action) => <option key={action} value={action} />)}</datalist>
        <div className="audit-filter-actions"><button className="bay-button bay-button-primary" type="submit">Apply filters</button><button className="bay-button bay-button-light" type="button" onClick={clearFilters}>Clear filters</button></div>
      </form>
      {filterError && <p className="bay-alert" role="alert">{filterError}</p>}
      <div aria-busy={loading} className="audit-results">
        {loading ? <p role="status">Loading audit events…</p> : current.error ? (
          <div className="bay-alert" role="alert">{current.error.message}<button type="button" onClick={() => setRevision((value) => value + 1)}>Retry audit events</button></div>
        ) : data.results.length === 0 ? <p role="status">No audit events match these filters.</p> : (
          <>
            <p role="status">{data.count} events · Page {page} of {lastPage}</p>
            <div className="audit-table-scroll" tabIndex={0} role="region" aria-label="Audit events, scroll horizontally for all columns">
              <table className="audit-table">
                <caption>Security and operational audit events</caption>
                <thead><tr>{['Time', 'Actor / role', 'Action', 'Resource', 'Details'].map((label) => <th scope="col" key={label}>{label}</th>)}</tr></thead>
                <tbody>{data.results.map((event) => (
                  <Fragment key={event.id}>
                    <tr><td><time dateTime={event.occurred_at}>{timestamp.format(new Date(event.occurred_at))}</time></td>
                      <td><strong>{event.actor_username || 'No verified actor'}</strong><small>{event.actor_role || '—'}</small></td>
                      <td><code>{event.event_type}</code></td><td>{event.resource_type || '—'}<small>{event.resource_id || '—'}</small></td>
                      <td><button type="button" className="bay-button bay-button-light" aria-expanded={expanded === event.id} aria-controls={`audit-details-${event.id}`} onClick={() => setExpanded(expanded === event.id ? null : event.id)}>{expanded === event.id ? 'Hide' : 'Inspect'}<span className="audit-sr-only"> event {event.id}</span></button></td></tr>
                    {expanded === event.id && <tr id={`audit-details-${event.id}`}><td colSpan={5}><EventDetails event={event} /></td></tr>}
                  </Fragment>
                ))}</tbody>
              </table>
            </div>
          </>
        )}
        <nav className="audit-pagination" aria-label="Audit pagination">
          <button type="button" className="bay-button bay-button-light" disabled={loading || page <= 1} onClick={() => { setPage((value) => value - 1); setExpanded(null) }}>Previous page</button>
          <span>{data ? `Page ${page} of ${lastPage}` : '—'}</span>
          <button type="button" className="bay-button bay-button-light" disabled={loading || !data || !data.next} onClick={() => { setPage((value) => value + 1); setExpanded(null) }}>Next page</button>
        </nav>
      </div>
    </section>
  )
}
