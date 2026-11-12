import test from 'node:test'
import assert from 'node:assert/strict'
import { changedZoneFields, reconcileBayZone } from '../src/utils/zoneLifecycle.js'

test('editing description does not send stale activation state', () => {
  const original = { name: 'North', description: 'Old', is_active: true }
  const current = { name: 'North', description: 'Updated', is_active: true }
  assert.deepEqual(changedZoneFields(original, current), { description: 'Updated' })
})

test('explicit deactivation is sent but unchanged fields are not', () => {
  const original = { name: 'North', description: '', is_active: true }
  assert.deepEqual(changedZoneFields(original, { ...original, is_active: false }), { is_active: false })
  assert.deepEqual(changedZoneFields(original, { ...original }), {})
})

test('deactivating selected zone requires a new bay zone without resetting other fields', () => {
  const draft = { slot_number: 'NEW-1', floor: '3', zone: '7', vehicle_type: 'Compact' }
  const result = reconcileBayZone(draft.zone, { id: 7, is_active: false })
  assert.equal(result.invalidated, true)
  assert.deepEqual({ ...draft, zone: result.zone }, { ...draft, zone: '' })
})

test('editing an unrelated or still-active zone leaves bay selection intact', () => {
  assert.deepEqual(reconcileBayZone('7', { id: 8, is_active: false }), { invalidated: false, zone: '7' })
  assert.deepEqual(reconcileBayZone('7', { id: 7, is_active: true }), { invalidated: false, zone: '7' })
})
