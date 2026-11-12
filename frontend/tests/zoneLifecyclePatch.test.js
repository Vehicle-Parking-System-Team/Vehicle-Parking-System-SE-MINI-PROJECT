import test from 'node:test'
import assert from 'node:assert/strict'
import { changedZoneFields } from '../src/utils/zoneLifecycle.js'

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
