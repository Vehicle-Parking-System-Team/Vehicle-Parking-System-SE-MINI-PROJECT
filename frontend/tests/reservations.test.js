import test from 'node:test'
import assert from 'node:assert/strict'
import { requestReservations, canModifyReservation } from '../src/utils/reservations.js'

test('reservation client uses authenticated API and preserves paginated results', async () => {
  let url, options
  const fetchWithAuth = async (u, o) => {
    url = u; options = o
    return { ok: true, json: async () => ({ count: 1, results: [{ id: 1 }] }) }
  }
  const result = await requestReservations(fetchWithAuth, '?page=2')
  assert.equal(url, '/api/parking/reservations/?page=2')
  assert.equal(options.cache, 'no-store')
  assert.equal(result.results[0].id, 1)
})

test('reservation client sends authenticated mutation', async () => {
  let options
  await requestReservations(async (_, o) => {
    options = o
    return { ok: true, json: async () => ({ id: 5 }) }
  }, '5/', { method: 'DELETE' })
  assert.equal(options.method, 'DELETE')
})

test('only future confirmed bookings are eligible for modification', () => {
  const now = new Date('2026-11-12T10:00:00Z')
  assert.equal(canModifyReservation({ status: 'Confirmed', start_time: '2026-11-13T10:00:00Z' }, now), true)
  assert.equal(canModifyReservation({ status: 'Cancelled', start_time: '2026-11-13T10:00:00Z' }, now), false)
  assert.equal(canModifyReservation({ status: 'Confirmed', start_time: '2026-11-11T10:00:00Z' }, now), false)
})
