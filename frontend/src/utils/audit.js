import { parseApiError } from './apiErrors.js'

export const AUDIT_PAGE_SIZE = 50
export const EMPTY_AUDIT_FILTERS = { event_type: '', actor: '', resource_type: '', start: '', end: '' }
export const AUDIT_ACTIONS = [
  'auth.login_succeeded', 'auth.login_failed', 'auth.logout', 'auth.password_changed',
  'account.created', 'account.updated', 'parking_slot.maintenance_changed',
  'parking_zone.deactivated', 'billing.payment_recorded', 'billing.fee_waived',
  'reservation.cancelled', 'tariff.created', 'tariff.updated',
]

export function auditQuery(filters, page = 1) {
  const query = new URLSearchParams({ page: String(page), page_size: String(AUDIT_PAGE_SIZE) })
  for (const [key, value] of Object.entries(filters)) {
    if (!value.trim()) continue
    if (key === 'start' || key === 'end') {
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) throw new Error('Choose valid dates.')
      query.set(key, date.toISOString())
    } else if (['event_type', 'actor', 'resource_type'].includes(key)) query.set(key, value.trim())
  }
  if (query.has('start') && query.has('end') && query.get('start') >= query.get('end')) {
    throw new Error('End must be later than start.')
  }
  return query.toString()
}

export async function requestAudit(fetchWithAuth, query, signal) {
  // Construct our own same-origin URL; never send credentials to pagination links.
  const response = await fetchWithAuth(`/api/audit/?${query}`, { cache: 'no-store', signal })
  const body = await response.json().catch(() => null)
  if (!response.ok) throw parseApiError(body)
  if (!body || !Array.isArray(body.results) || !Number.isSafeInteger(body.count) || body.count < 0) {
    throw new Error('The audit trail could not be read.')
  }
  return body
}

export function auditStateChanges(details) {
  if (!details || typeof details !== 'object' || Array.isArray(details)) return []
  const before = details.previous_state || {}
  const after = details.new_state || {}
  const changes = [...new Set([...Object.keys(before), ...Object.keys(after)])]
    .filter((key) => before[key] !== after[key])
    .map((field) => ({ field, before: before[field], after: after[field] }))
  for (const key of Object.keys(details)) {
    if (key.startsWith('previous_') && key !== 'previous_state') {
      const field = key.slice('previous_'.length)
      if (Object.hasOwn(details, field) && details[key] !== details[field]) {
        changes.push({ field, before: details[key], after: details[field] })
      }
    }
  }
  return changes
}
