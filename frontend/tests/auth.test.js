import assert from 'node:assert/strict'
import test from 'node:test'

// Helper to decode JWT payload without external library
function decodeJwtPayload(token) {
  if (!token || typeof token !== 'string') return null
  const parts = token.split('.')
  if (parts.length !== 3) return null
  try {
    const payloadJson = Buffer.from(parts[1], 'base64url').toString('utf8')
    return JSON.parse(payloadJson)
  } catch {
    return null
  }
}

// Error envelope extractor aligning with US-31 contract
function extractAuthErrorMessage(responseBody) {
  if (!responseBody || typeof responseBody !== 'object') {
    return 'Authentication failed. Please check your credentials.'
  }
  if (typeof responseBody.error === 'string' && responseBody.error.trim()) {
    return responseBody.error
  }
  return 'Authentication failed. Please check your credentials.'
}

test('JWT payload decoder correctly parses claims from valid token format', () => {
  const payload = {
    user_id: 42,
    username: 'operator1',
    role: 'Operator',
    token_version: 1,
    exp: 1800000000,
  }
  const fakeToken = `header.${Buffer.from(JSON.stringify(payload)).toString('base64url')}.signature`
  const decoded = decodeJwtPayload(fakeToken)

  assert.equal(decoded.user_id, 42)
  assert.equal(decoded.username, 'operator1')
  assert.equal(decoded.role, 'Operator')
  assert.equal(decoded.token_version, 1)
})

test('JWT decoder safely returns null for malformed tokens', () => {
  assert.equal(decodeJwtPayload(''), null)
  assert.equal(decodeJwtPayload('invalid.token'), null)
  assert.equal(decodeJwtPayload(null), null)
  assert.equal(decodeJwtPayload(123), null)
})

test('extractAuthErrorMessage extracts error from US-31 formatted body', () => {
  const body = {
    error: 'Invalid username or password.',
    code: 'AUTHENTICATION_FAILED',
    details: {},
  }
  assert.equal(extractAuthErrorMessage(body), 'Invalid username or password.')
})

test('extractAuthErrorMessage provides safe fallback when error field is missing or malformed', () => {
  assert.equal(
    extractAuthErrorMessage({}),
    'Authentication failed. Please check your credentials.'
  )
  assert.equal(
    extractAuthErrorMessage(null),
    'Authentication failed. Please check your credentials.'
  )
  assert.equal(
    extractAuthErrorMessage('string error'),
    'Authentication failed. Please check your credentials.'
  )
})
