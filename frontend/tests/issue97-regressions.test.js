import assert from 'node:assert/strict'
import test from 'node:test'
import { readFileSync } from 'node:fs'

const registrationSource = readFileSync(
  new URL('../src/components/VehicleRegistrationForm.jsx', import.meta.url),
  'utf8',
)
const searchSource = readFileSync(
  new URL('../src/components/VehicleSearchView.jsx', import.meta.url),
  'utf8',
)

test('staff-assisted registration leaves a blank owner name for the selected customer fallback', () => {
  assert.match(registrationSource, /owner_name:\s*formData\.owner_name\.trim\(\),/)
  assert.doesNotMatch(registrationSource, /owner_name:\s*formData\.owner_name\.trim\(\)\s*\|\|\s*user\?\.username/)
})

test('clearing during successful response JSON parsing prevents stale search state updates', () => {
  const parseIndex = searchSource.indexOf('const data = await response.json()')
  const guardIndex = searchSource.indexOf('if (!isCurrentRequest()) return', parseIndex)
  const resultIndex = searchSource.indexOf('if (Array.isArray(data) && data.length === 0)', parseIndex)
  assert.notEqual(parseIndex, -1)
  assert.ok(guardIndex > parseIndex, 'a generation guard must run after response.json() resolves')
  assert.ok(resultIndex > guardIndex, 'the guard must run before any parsed result is committed')
})

test('clearing during error response JSON parsing prevents stale error state updates', () => {
  const parseIndex = searchSource.indexOf('const errData = await response.json().catch(() => null)')
  const guardIndex = searchSource.indexOf('if (!isCurrentRequest()) return', parseIndex)
  const updateIndex = searchSource.indexOf('const parsed = parseApiError(errData)', parseIndex)
  assert.notEqual(parseIndex, -1)
  assert.ok(guardIndex > parseIndex, 'a generation guard must run after error JSON parsing')
  assert.ok(updateIndex > guardIndex, 'the guard must run before parsed error data is used')
})

const profileSource = readFileSync(
  new URL('../src/components/VehicleProfileView.jsx', import.meta.url),
  'utf8',
)
const usersSource = readFileSync(
  new URL('../src/pages/Users.jsx', import.meta.url),
  'utf8',
)

test('an explicitly requested vehicle profile is not hidden by an empty personal fleet', () => {
  assert.match(profileSource, /vehicles\.length === 0 && !initialVehicleId/)
  assert.match(profileSource, /fetchWithAuth\(\`\/api\/v1\/vehicles\/\$\{selectedId\}\/\`\)/)
})

test('vehicle-list failures in registration and profile views expose retry actions', () => {
  assert.match(registrationSource, /vehiclesLoadError && \(/)
  assert.match(registrationSource, /onClick=\{loadUserVehicles\}>Retry<\/button>/)
  assert.match(profileSource, /listError && \(/)
  assert.match(profileSource, />Retry<\/button>/)
})

test('user filter requests ignore stale responses before updating the list', () => {
  assert.match(usersSource, /const requestId = \+\+usersRequestId\.current/)
  assert.match(usersSource, /if \(requestId !== usersRequestId\.current\) return/)
  assert.match(usersSource, /if \(requestId === usersRequestId\.current\) setUsers/)
})

test('create-user modal exposes dialog semantics, keyboard containment, and labelled fields', () => {
  assert.match(usersSource, /role="dialog"/)
  assert.match(usersSource, /aria-modal="true"/)
  assert.match(usersSource, /event\.key === 'Escape'/)
  assert.match(usersSource, /event\.key === 'Tab'/)
  assert.match(usersSource, /querySelectorAll\(/)
  assert.match(usersSource, /htmlFor="create-user-username"/)
  assert.match(usersSource, /id="create-user-username"/)
})
