import assert from 'node:assert/strict'
import test from 'node:test'
import { parseApiError } from '../src/utils/apiErrors.js'

const envelope = (details = {}) => ({
  error: 'Please correct the highlighted fields.',
  code: 'VALIDATION_ERROR',
  details,
})

test('field messages retain all actionable validation errors', () => {
  assert.deepEqual(parseApiError(envelope({ label: ['Required.', 'Too long.'] })), {
    message: 'Please correct the highlighted fields.',
    code: 'VALIDATION_ERROR',
    fieldErrors: { label: ['Required.', 'Too long.'] },
    formErrors: [],
  })
})

test('non-field validation appears at form level', () => {
  const error = parseApiError(envelope({ non_field_errors: ['Invalid combination.'] }))
  assert.deepEqual(error.formErrors, ['Invalid combination.'])
  assert.deepEqual(error.fieldErrors, {})
})

test('root list validation appears at form level', () => {
  assert.deepEqual(parseApiError(envelope(['Invalid input.'])).formErrors, ['Invalid input.'])
})

test('nested fields use dotted paths', () => {
  const error = parseApiError(envelope({ vehicle: { label: ['Required.'] } }))
  assert.deepEqual(error.fieldErrors, { 'vehicle.label': ['Required.'] })
})

test('list serializer details retain row indices', () => {
  const error = parseApiError(envelope([{}, { label: ['Required.'] }]))
  assert.deepEqual(error.fieldErrors, { '1.label': ['Required.'] })
})

test('indexed serializer details retain row indices', () => {
  const error = parseApiError(envelope({ 1: { label: ['Required.'] } }))
  assert.deepEqual(error.fieldErrors, { '1.label': ['Required.'] })
})

test('general API errors preserve the code and safe message', () => {
  const error = parseApiError({ error: 'The slot is occupied.', code: 'CONFLICT', details: {} })
  assert.equal(error.code, 'CONFLICT')
  assert.equal(error.message, 'The slot is occupied.')
  assert.deepEqual(error.fieldErrors, {})
})

test('empty, network and non-JSON responses use a safe fallback', () => {
  for (const value of [null, undefined, new Error('private network detail'), '<html>private</html>', []]) {
    const error = parseApiError(value)
    assert.equal(error.code, 'REQUEST_FAILED')
    assert.equal(error.message, 'Unable to complete the request. Please try again.')
    assert.deepEqual(error.fieldErrors, {})
    assert.deepEqual(error.formErrors, [])
  }
})

test('malformed or obsolete envelopes use a safe fallback', () => {
  for (const value of [
    {}, { ...envelope(), error: '' }, { ...envelope(), code: 400 },
    { ...envelope(), code: 'bad code' }, { ...envelope(), details: null },
    { error: { code: 'VALIDATION_ERROR', message: 'Old shape.' } },
  ]) {
    assert.equal(parseApiError(value).code, 'REQUEST_FAILED')
  }
})

test('non-message values are ignored without converting objects into text', () => {
  const error = parseApiError(envelope({ label: [null, 42, '', 'Required.'] }))
  assert.deepEqual(error.fieldErrors, { label: ['Required.'] })
})

test('parsing does not mutate the server response', () => {
  const details = Object.freeze({ label: Object.freeze(['Required.']) })
  const payload = Object.freeze(envelope(details))
  assert.deepEqual(parseApiError(payload).fieldErrors, { label: ['Required.'] })
})

test('field names cannot modify object prototypes', () => {
  const details = JSON.parse('{"__proto__":["Required."]}')
  const error = parseApiError(envelope(details))
  assert.equal(Object.getPrototypeOf(error.fieldErrors), Object.prototype)
  assert.deepEqual(Object.getOwnPropertyDescriptor(error.fieldErrors, '__proto__').value, ['Required.'])
  assert.equal(Object.prototype.polluted, undefined)
})
