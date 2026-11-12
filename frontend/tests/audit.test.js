import assert from 'node:assert/strict'
import test from 'node:test'
import { auditQuery, auditStateChanges, requestAudit, EMPTY_AUDIT_FILTERS } from '../src/utils/audit.js'

test('audit filters encode actions, actors and resources and use bounded pages', () => {
  const query = new URLSearchParams(auditQuery({ ...EMPTY_AUDIT_FILTERS, event_type: 'account.updated', actor: 'A & B', resource_type: 'user' }, 2))
  assert.equal(query.get('actor'), 'A & B')
  assert.equal(query.get('event_type'), 'account.updated')
  assert.equal(query.get('resource_type'), 'user')
  assert.equal(query.get('page_size'), '50')
  assert.equal(query.get('page'), '2')
  assert.equal(query.has('start'), false)
})

test('date filters encode instants and reject invalid or reversed intervals', () => {
  const query = new URLSearchParams(auditQuery({ start: '2026-11-12T14:30:00+05:30', end: '2026-11-12T15:30:00+05:30' }))
  assert.equal(query.get('start'), '2026-11-12T09:00:00.000Z')
  assert.equal(query.get('end'), '2026-11-12T10:00:00.000Z')
  assert.throws(() => auditQuery({ start: 'invalid' }), /valid dates/)
  assert.throws(() => auditQuery({ start: '2026-11-12T15:00Z', end: '2026-11-12T14:00Z' }), /later/)
})

test('state changes preserve false, zero, null and missing values without changing the payload', () => {
  const details = { previous_state: { role: 'Admin', unchanged: true, limit: 1 }, new_state: { role: 'Customer', unchanged: true, limit: 0, disabled: false, comment: null } }
  const before = structuredClone(details)
  assert.deepEqual(auditStateChanges(details), [
    { field: 'role', before: 'Admin', after: 'Customer' },
    { field: 'limit', before: 1, after: 0 },
    { field: 'disabled', before: undefined, after: false },
    { field: 'comment', before: undefined, after: null },
  ])
  assert.deepEqual(auditStateChanges({ previous_status: 'available', status: 'maintenance' }), [{ field: 'status', before: 'available', after: 'maintenance' }])
  assert.deepEqual(auditStateChanges({ outcome: 'failure' }), [])
  assert.deepEqual(auditStateChanges(null), [])
  assert.deepEqual(details, before)
})

test('audit reads use authenticated same-origin GET and support abort without following pagination URLs', async () => {
  const controller = new AbortController()
  const data = { count: 51, results: [{ id: 1 }], next: 'https://untrusted.test/audit/?page=2' }
  const result = await requestAudit(async (url, options) => {
    assert.equal(url, '/api/audit/?page=1')
    assert.equal(options.cache, 'no-store')
    assert.equal(options.signal, controller.signal)
    assert.equal(options.method, undefined)
    return new Response(JSON.stringify(data))
  }, 'page=1', controller.signal)
  assert.deepEqual(result, data)
})

test('permission failures and malformed responses cannot become empty audit histories', async () => {
  await assert.rejects(requestAudit(async () => new Response(JSON.stringify({ error: 'Permission denied', code: 'PERMISSION_DENIED', details: {} }), { status: 403 }), ''), (error) => error.message === 'Permission denied' && error.code === 'PERMISSION_DENIED')
  for (const body of ['{}', '<html>offline</html>', '{"count":-1,"results":[]}']) {
    await assert.rejects(requestAudit(async () => new Response(body), ''), /could not be read/)
  }
})
