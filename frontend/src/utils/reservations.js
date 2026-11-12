import { parseApiError } from './apiErrors.js'

export async function requestReservations(fetchWithAuth, path = '', options = {}) {
  const response = await fetchWithAuth(`/api/parking/reservations/${path}`, {
    cache: 'no-store', ...options,
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) throw parseApiError(data) 
  if (!data) throw new Error('Reservation service returned no data.')
  return data
}

export function canModifyReservation(reservation, now = new Date()) {
  return reservation.status === 'Confirmed' && new Date(reservation.start_time) > now
}
