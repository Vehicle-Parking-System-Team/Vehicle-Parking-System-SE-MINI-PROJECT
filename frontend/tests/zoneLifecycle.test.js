import test from 'node:test'
import assert from 'node:assert/strict'
import { requestZones } from '../src/utils/slots.js'

test('zone lifecycle PATCH uses the existing authenticated zone endpoint', async () => {
  const payload = { name: 'Updated', description: 'North entrance', is_active: false }
  const saved = await requestZones(async (url, options) => {
    assert.equal(url, '/api/parking/zones/7/')
    assert.equal(options.method, 'PATCH')
    assert.deepEqual(JSON.parse(options.body), payload)
    return { ok: true, status: 200, json: async () => ({ id: 7, ...payload }) }
  }, '7/', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  assert.equal(saved.is_active, false)
})
