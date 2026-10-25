import { parseApiError } from './apiErrors.js'

export const AVAILABILITY_REFRESH_MS = 30_000

export async function requestAvailability(signal) {
  const response = await fetch('/api/parking/availability/', {
    cache: 'no-store',
    credentials: 'omit',
    signal,
  })
  const body = await response.json().catch(() => null)
  if (!response.ok) throw parseApiError(body)
  if (!Array.isArray(body)) throw new Error('Availability could not be read.')
  return body
}

export function filterAvailability(slots, zone, vehicleType) {
  return slots.filter((slot) =>
    (!zone || String(slot.zone) === zone) &&
    (!vehicleType || slot.vehicle_type === vehicleType),
  )
}
