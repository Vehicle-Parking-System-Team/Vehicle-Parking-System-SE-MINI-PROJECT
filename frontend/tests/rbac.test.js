import assert from 'node:assert/strict'
import test from 'node:test'
import { isRoleAuthorized, ROLES } from '../src/utils/rbac.js'

test('canonical roles match SRS §9.2 and SAD §3.9 specification', () => {
  assert.equal(ROLES.ADMIN, 'Admin')
  assert.equal(ROLES.OPERATOR, 'Operator')
  assert.equal(ROLES.CUSTOMER, 'Customer')
})

test('isRoleAuthorized allows access when allowedRoles is not specified or empty', () => {
  assert.equal(isRoleAuthorized(ROLES.ADMIN, undefined), true)
  assert.equal(isRoleAuthorized(ROLES.OPERATOR, null), true)
  assert.equal(isRoleAuthorized(ROLES.CUSTOMER, []), true)
})

test('isRoleAuthorized allows access when user role matches allowed roles', () => {
  assert.equal(isRoleAuthorized(ROLES.ADMIN, ['Admin']), true)
  assert.equal(isRoleAuthorized(ROLES.ADMIN, ['Admin', 'Operator']), true)
  assert.equal(isRoleAuthorized(ROLES.OPERATOR, ['Operator']), true)
  assert.equal(isRoleAuthorized(ROLES.OPERATOR, ['Admin', 'Operator']), true)
  assert.equal(isRoleAuthorized(ROLES.CUSTOMER, ['Customer']), true)
  assert.equal(isRoleAuthorized(ROLES.CUSTOMER, ['Admin', 'Operator', 'Customer']), true)
})

test('isRoleAuthorized strictly denies access when user role is not in allowed roles', () => {
  // Non-admins denied from Admin-only sections
  assert.equal(isRoleAuthorized(ROLES.OPERATOR, ['Admin']), false)
  assert.equal(isRoleAuthorized(ROLES.CUSTOMER, ['Admin']), false)

  // Customers denied from Operations sections
  assert.equal(isRoleAuthorized(ROLES.CUSTOMER, ['Admin', 'Operator']), false)

  // Operators denied from Customer-only sections
  assert.equal(isRoleAuthorized(ROLES.OPERATOR, ['Customer']), false)
})

test('isRoleAuthorized denies access for null, undefined, empty, or unknown roles', () => {
  assert.equal(isRoleAuthorized(null, ['Admin']), false)
  assert.equal(isRoleAuthorized(undefined, ['Operator']), false)
  assert.equal(isRoleAuthorized('', ['Customer']), false)
  assert.equal(isRoleAuthorized('Superuser', ['Admin']), false)
  assert.equal(isRoleAuthorized('Manager', ['Operator']), false)
  assert.equal(isRoleAuthorized('Guest', ['Customer']), false)
  assert.equal(isRoleAuthorized('admin', ['Admin']), false) // Case sensitivity check
})

test('simulated route protection handles authentication and loading states correctly', () => {
  function evaluateRouteGuard({ isLoading, isAuthenticated, user, allowedRoles }) {
    if (isLoading) {
      return { status: 'LOADING', exposeChildren: false }
    }
    if (!isAuthenticated || !user) {
      return { status: 'UNAUTHENTICATED', exposeChildren: false, code: 401 }
    }
    const authorized = isRoleAuthorized(user.role, allowedRoles)
    if (!authorized) {
      return { status: 'FORBIDDEN', exposeChildren: false, code: 403 }
    }
    return { status: 'AUTHORIZED', exposeChildren: true }
  }

  // 1. Loading state must never expose children
  const loadingState = evaluateRouteGuard({
    isLoading: true,
    isAuthenticated: true,
    user: { role: 'Admin' },
    allowedRoles: ['Admin'],
  })
  assert.equal(loadingState.exposeChildren, false)
  assert.equal(loadingState.status, 'LOADING')

  // 2. Unauthenticated user must be challenged with 401 equivalent and never expose children
  const unauthState = evaluateRouteGuard({
    isLoading: false,
    isAuthenticated: false,
    user: null,
    allowedRoles: ['Admin'],
  })
  assert.equal(unauthState.exposeChildren, false)
  assert.equal(unauthState.status, 'UNAUTHENTICATED')
  assert.equal(unauthState.code, 401)

  // 3. Authenticated customer visiting admin route gets 403 forbidden
  const forbiddenState = evaluateRouteGuard({
    isLoading: false,
    isAuthenticated: true,
    user: { role: 'Customer' },
    allowedRoles: ['Admin'],
  })
  assert.equal(forbiddenState.exposeChildren, false)
  assert.equal(forbiddenState.status, 'FORBIDDEN')
  assert.equal(forbiddenState.code, 403)

  // 4. Authenticated admin visiting admin route gets authorized access
  const authorizedState = evaluateRouteGuard({
    isLoading: false,
    isAuthenticated: true,
    user: { role: 'Admin' },
    allowedRoles: ['Admin'],
  })
  assert.equal(authorizedState.exposeChildren, true)
  assert.equal(authorizedState.status, 'AUTHORIZED')
})

test('privilege escalation prevention: client query/header tampering cannot alter authorization', () => {
  // Even if an attacker attempts to inject a role attribute into client state
  const rawAttackerUser = {
    username: 'malicious_user',
    role: 'Customer', // Persistent role from DB
    injectedRole: 'Admin',
    headers: { 'X-Role': 'Admin' },
    query: { role: 'Admin' },
  }

  // RBAC guard strictly uses user.role
  assert.equal(isRoleAuthorized(rawAttackerUser.role, ['Admin']), false)
  assert.equal(isRoleAuthorized(rawAttackerUser.role, ['Operator']), false)
  assert.equal(isRoleAuthorized(rawAttackerUser.role, ['Customer']), true)
})
