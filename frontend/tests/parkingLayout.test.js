import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildFloorLayout,
  floorCode,
  floorLabel,
  slotState,
  summarizeSlots,
} from '../src/utils/parkingLayout.js'
import { DEMO_SLOTS } from '../src/data/demoSlots.js'
import { requestSlots, requestZones } from '../src/utils/slots.js'

test('unknown historical floors are explicitly unmapped rather than ground floor', () => {
  assert.equal(floorLabel(null), 'Unmapped floor')
  assert.equal(floorCode(null), '?')
  assert.equal(floorLabel(0), 'Ground floor')
})

test('historical active bays in an inactive zone are not shown as available', () => {
  assert.equal(
    slotState({ is_active: true, zone_is_active: false, status: 'available' }),
    'INACTIVE',
  )
})

test('same bay number in different zones retains both IDs and separate placements', () => {
  const layout = buildFloorLayout([
    { id: 7, zone: 2, zone_name: 'South', slot_number: 'A-1' },
    { id: 8, zone: 1, zone_name: 'North', slot_number: 'A-1' },
  ])
  assert.deepEqual(
    layout.placements.map(({ slot }) => slot.id),
    [8, 7],
  )
  assert.deepEqual(
    layout.bands.map(({ zone }) => zone),
    ['North', 'South'],
  )
  assert.notEqual(layout.placements[0].z, layout.placements[1].z)
})

test('zone creation uses existing PR64 route and authenticated request helper', async () => {
  const values = { name: 'New zone' }
  const result = await requestZones(
    async (url, options) => {
      assert.equal(url, '/api/parking/zones/')
      assert.equal(options.method, 'POST')
      assert.equal(options.cache, 'no-store')
      assert.deepEqual(JSON.parse(options.body), values)
      return { status: 201, ok: true, json: async () => ({ id: 4, ...values }) }
    },
    '',
    { method: 'POST', body: JSON.stringify(values) },
  )
  assert.equal(result.id, 4)
})

test('inactive bays are never counted as available even when retained status is AVAILABLE', () => {
  const slots = [
    { id: 1, status: 'available', is_active: false },
    { id: 2, status: 'available', is_active: true },
    { id: 3, status: 'occupied', is_active: true },
  ]
  assert.equal(slotState(slots[0]), 'INACTIVE')
  assert.deepEqual(summarizeSlots(slots), {
    total: 3,
    AVAILABLE: 1,
    OCCUPIED: 1,
    RESERVED: 0,
    MAINTENANCE: 0,
    INACTIVE: 1,
  })
})

test('schematic positions are stable across API ordering and do not overlap within zones', () => {
  const floor = DEMO_SLOTS.filter((slot) => slot.floor === 0)
  const a = buildFloorLayout(floor)
  const b = buildFloorLayout([...floor].reverse())
  assert.deepEqual(a, b)
  assert.equal(
    new Set(a.placements.map(({ x, z }) => `${x},${z}`)).size,
    floor.length,
  )
  assert.deepEqual(
    new Set(a.placements.map(({ slot }) => slot.id)),
    new Set(floor.map((slot) => slot.id)),
  )
})

test('empty and overflowing zone bands produce finite bounded placements', () => {
  const empty = buildFloorLayout([])
  assert.deepEqual(empty.placements, [])
  assert.ok(empty.width > 0 && empty.depth > 0)
  const many = Array.from({ length: 61 }, (_, index) => ({
    id: index + 1,
    slot_number: `S-${index}`,
    zone: 'A',
  }))
  const layout = buildFloorLayout(many)
  assert.equal(layout.bands.length, 6)
  assert.equal(
    new Set(layout.placements.map(({ x, z }) => `${x},${z}`)).size,
    many.length,
  )
  for (const { x, z } of layout.placements)
    assert.ok(Math.abs(x) < layout.width / 2 && Math.abs(z) < layout.depth / 2)
})

test('sample data is distinct across floors and basement labels remain meaningful', () => {
  assert.equal(new Set(DEMO_SLOTS.map((slot) => slot.id)).size, 72)
  assert.ok(DEMO_SLOTS.every((slot) => slot.id < 0))
  assert.equal(floorCode(-2), 'B2')
  assert.equal(floorCode(0), 'G')
  assert.equal(floorCode(3), 'L3')
  assert.equal(floorLabel(-1), 'Basement 1')
})

test('slot API handles DELETE 204 without attempting JSON parsing', async () => {
  let jsonRead = false
  const fetchWithAuth = async (url, options) => {
    assert.equal(url, '/api/parking/slots/5/')
    assert.equal(options.method, 'DELETE')
    return {
      status: 204,
      json: () => {
        jsonRead = true
      },
    }
  }
  assert.equal(
    await requestSlots(fetchWithAuth, '5/', { method: 'DELETE' }),
    null,
  )
  assert.equal(jsonRead, false)
})

test('slot API preserves occupied conflict and duplicate field details through the shared parser', async () => {
  await assert.rejects(
    requestSlots(
      async () => ({
        status: 409,
        ok: false,
        json: async () => ({
          error: 'An occupied slot cannot be deactivated.',
          code: 'CONFLICT',
          details: {},
        }),
      }),
      '5/',
      { method: 'DELETE' },
    ),
    (error) => error.code === 'CONFLICT',
  )
  await assert.rejects(
    requestSlots(async () => ({
      status: 400,
      ok: false,
      json: async () => ({
        error: 'Correct the fields.',
        code: 'VALIDATION_ERROR',
        details: { slot_number: ['Already exists.'] },
      }),
    })),
    (error) => error.fieldErrors.slot_number[0] === 'Already exists.',
  )
})
