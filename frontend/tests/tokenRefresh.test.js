import assert from 'node:assert/strict'
import test from 'node:test'

import { createTokenRefreshCoordinator } from '../src/utils/tokenRefresh.js'

test('staggered 401 responses reuse the access token from the completed refresh', async () => {
  let accessToken = 'access-v1'
  let refreshToken = 'refresh-v1'
  let refreshCalls = 0
  let clearCalls = 0

  const refreshAfterUnauthorized = createTokenRefreshCoordinator({
    getAccessToken: () => accessToken,
    getRefreshToken: () => refreshToken,
    clearSession: () => { clearCalls += 1 },
    refresh: async (credential) => {
      assert.equal(credential, 'refresh-v1')
      refreshCalls += 1
      accessToken = 'access-v2'
      refreshToken = 'refresh-v2'
      return accessToken
    },
  })

  const firstResult = await refreshAfterUnauthorized('access-v1')
  const delayedResult = await refreshAfterUnauthorized('access-v1')

  assert.equal(firstResult, 'access-v2')
  assert.equal(delayedResult, 'access-v2')
  assert.equal(refreshCalls, 1)
  assert.equal(clearCalls, 0)
})

test('simultaneous 401 responses share one in-flight refresh operation', async () => {
  let accessToken = 'access-v1'
  let refreshToken = 'refresh-v1'
  let refreshCalls = 0
  let resolveRefresh

  const pendingRefresh = new Promise((resolve) => {
    resolveRefresh = resolve
  })

  const refreshAfterUnauthorized = createTokenRefreshCoordinator({
    getAccessToken: () => accessToken,
    getRefreshToken: () => refreshToken,
    clearSession: () => assert.fail('A successful refresh must not clear the session'),
    refresh: async (credential) => {
      assert.equal(credential, 'refresh-v1')
      refreshCalls += 1
      return pendingRefresh
    },
  })

  const firstRequest = refreshAfterUnauthorized('access-v1')
  const secondRequest = refreshAfterUnauthorized('access-v1')
  await Promise.resolve()

  assert.equal(refreshCalls, 1)
  accessToken = 'access-v2'
  refreshToken = 'refresh-v2'
  resolveRefresh('access-v2')

  assert.deepEqual(await Promise.all([firstRequest, secondRequest]), [
    'access-v2',
    'access-v2',
  ])
  assert.equal(refreshCalls, 1)
})

test('missing refresh credentials clear the unusable session', async () => {
  let clearCalls = 0
  const refreshAfterUnauthorized = createTokenRefreshCoordinator({
    getAccessToken: () => 'access-v1',
    getRefreshToken: () => null,
    refresh: async () => assert.fail('Refresh must not run without credentials'),
    clearSession: () => { clearCalls += 1 },
  })

  assert.equal(await refreshAfterUnauthorized('access-v1'), null)
  assert.equal(clearCalls, 1)
})
