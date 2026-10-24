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

test('validateLoginInput rejects empty username or password', () => {
  function validateLoginInput(username, password) {
    if (!username || !username.trim() || !password) {
      return { isValid: false, error: 'Please enter both your username and password.' }
    }
    return { isValid: true, error: null }
  }

  assert.equal(validateLoginInput('', '').isValid, false)
  assert.equal(validateLoginInput('   ', 'pass').isValid, false)
  assert.equal(validateLoginInput('operator1', '').isValid, false)
  assert.equal(validateLoginInput('operator1', 'pass123').isValid, true)
})

test('validateRegisterInput validates username, email, and password policies', () => {
  function validateRegisterInput({ username, email, password, passwordConfirm }) {
    const errors = {}
    const trimmedUser = (username || '').trim()
    const trimmedEmail = (email || '').trim()

    if (!trimmedUser) errors.username = 'Username is required.'
    else if (!/^[\w.@+-]+$/.test(trimmedUser)) errors.username = 'Invalid username.'

    if (!trimmedEmail) errors.email = 'Email address is required.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) errors.email = 'Invalid email.'

    if (!password) errors.password = 'Password is required.'
    else if (password.length < 8) errors.password = 'Too short.'
    else if (!/[A-Z]/.test(password)) errors.password = 'No uppercase.'
    else if (!/[a-z]/.test(password)) errors.password = 'No lowercase.'
    else if (!/[0-9]/.test(password)) errors.password = 'No digit.'
    else if (!/[^A-Za-z0-9]/.test(password)) errors.password = 'No special.'

    if (password !== passwordConfirm) errors.password_confirm = 'Passwords do not match.'

    return { isValid: Object.keys(errors).length === 0, errors }
  }

  // Empty fields
  assert.equal(validateRegisterInput({}).isValid, false)

  // Mismatched passwords
  const mismatch = validateRegisterInput({
    username: 'cust1',
    email: 'c@p.com',
    password: 'SecurePass123!',
    passwordConfirm: 'DifferentPass123!',
  })
  assert.equal(mismatch.isValid, false)
  assert.equal(mismatch.errors.password_confirm, 'Passwords do not match.')

  // Weak password
  const weak = validateRegisterInput({
    username: 'cust1',
    email: 'c@p.com',
    password: 'weak',
    passwordConfirm: 'weak',
  })
  assert.equal(weak.isValid, false)
  assert.equal(weak.errors.password, 'Too short.')

  // Valid registration
  const valid = validateRegisterInput({
    username: 'cust1',
    email: 'c@p.com',
    password: 'SecurePass123!',
    passwordConfirm: 'SecurePass123!',
  })
  assert.equal(valid.isValid, true)
})
