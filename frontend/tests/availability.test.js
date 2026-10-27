import assert from 'node:assert/strict'
import test from 'node:test'
import { filterAvailability, requestAvailability } from '../src/utils/availability.js'
import { summarizeSlots } from '../src/utils/parkingLayout.js'

const slots = [
  { id: 1, zone: 1, vehicle_type: 'Compact', status: 'available', is_active: true },
  { id: 2, zone: 1, vehicle_type: 'SUV', status: 'occupied', is_active: true },
  { id: 3, zone: 2, vehicle_type: 'any', status: 'reserved', is_active: true },
  { id: 4, zone: 2, vehicle_type: 'Compact', status: 'maintenance', is_active: true },
]

test('zone and exact type filters compose without including legacy any', () => {
  assert.deepEqual(filterAvailability(slots, '1', 'Compact').map((slot) => slot.id), [1])
  assert.deepEqual(filterAvailability(slots, '', 'Compact').map((slot) => slot.id), [1, 4])
  assert.deepEqual(filterAvailability(slots, '2', '').map((slot) => slot.id), [3, 4])
  assert.deepEqual(filterAvailability(slots, '2', 'SUV'), [])
  assert.equal(filterAvailability(slots, '', '').length, 4)
})

test('summary reconciles to filtered rows and handles empty results', () => {
  const summary = summarizeSlots(filterAvailability(slots, '1', ''))
  assert.equal(summary.total, 2)
  assert.equal(summary.AVAILABLE, 1)
  assert.equal(summary.OCCUPIED, 1)
  assert.equal(summarizeSlots([]).total, 0)
  const all = summarizeSlots(slots)
  assert.equal(all.total, all.AVAILABLE + all.OCCUPIED + all.RESERVED + all.MAINTENANCE)
})

test('public request omits credentials, bypasses cache and accepts cancellation', async (t) => {
  const controller = new AbortController()
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(url, '/api/parking/availability/')
    assert.equal(options.cache, 'no-store')
    assert.equal(options.credentials, 'omit')
    assert.equal(options.signal, controller.signal)
    assert.equal(options.headers, undefined)
    return new Response(JSON.stringify(slots))
  })
  assert.deepEqual(await requestAvailability(controller.signal), slots)
})

test('each refresh reads the next response instead of retaining a cached list', async (t) => {
  let calls = 0
  t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify(
    calls++ ? [{ ...slots[0], status: 'occupied' }] : [slots[0]],
  )))
  assert.equal((await requestAvailability())[0].status, 'available')
  assert.equal((await requestAvailability())[0].status, 'occupied')
})

test('failed requests and malformed responses cannot masquerade as an empty facility', async (t) => {
  const fetchMock = t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({
    error: 'Unavailable', code: 'INTERNAL_ERROR', details: {},
  }), { status: 500 }))
  await assert.rejects(requestAvailability(), (error) => error.message === 'Unavailable' && error.code === 'INTERNAL_ERROR')
  fetchMock.mock.mockImplementation(async () => new Response('{}'))
  await assert.rejects(requestAvailability(), /Availability could not be read/)
  fetchMock.mock.mockImplementation(async () => new Response('<html>offline</html>'))
  await assert.rejects(requestAvailability(), /Availability could not be read/)
})
