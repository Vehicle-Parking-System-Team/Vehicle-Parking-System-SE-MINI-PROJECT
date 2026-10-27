/**
 * Role-Based Access Control utility functions and canonical roles.
 * Traceability: US-02 / FR-16, NFR-SEC-01.
 */

export const ROLES = {
  ADMIN: 'Admin',
  OPERATOR: 'Operator',
  CUSTOMER: 'Customer',
}

/**
 * Validates whether a user role satisfies allowed roles constraint.
 * @param {string|null|undefined} userRole
 * @param {string[]} [allowedRoles]
 * @returns {boolean}
 */
export function isRoleAuthorized(userRole, allowedRoles) {
  if (!allowedRoles || allowedRoles.length === 0) return true
  if (!userRole) return false
  return allowedRoles.includes(userRole)
}
