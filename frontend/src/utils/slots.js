import { parseApiError } from './apiErrors.js'

async function requestParking(fetchWithAuth, resource, path, options) {
  const response = await fetchWithAuth(`/api/parking/${resource}/${path}`, {
    cache: 'no-store',
    ...options,
  })
  if (response.status === 204) return null
  const body = await response.json().catch(() => null)
  if (!response.ok) throw parseApiError(body)
  if (!body) throw new Error('The slot service returned an empty response.')
  return body
}

export function requestSlots(fetchWithAuth, path = '', options) {
  return requestParking(fetchWithAuth, 'slots', path, options)
}

export function requestZones(fetchWithAuth, path = '', options) {
  return requestParking(fetchWithAuth, 'zones', path, options)
}
