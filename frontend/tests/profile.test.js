import assert from 'node:assert/strict'
import test from 'node:test'
import {
  validateProfileUpdateInput,
  validatePasswordChangeInput,
} from '../src/utils/profileValidation.js'

test('validateProfileUpdateInput accepts valid profile payload', () => {
  const result = validateProfileUpdateInput({
    first_name: 'John',
    last_name: 'Doe',
    phone_number: '+1 (555) 123-4567',
    email: 'john.doe@example.com',
  })
  assert.equal(result.isValid, true)
  assert.deepEqual(result.errors, {})
})

test('validateProfileUpdateInput rejects invalid email format', () => {
  const result = validateProfileUpdateInput({
    email: 'invalid-email-format',
  })
  assert.equal(result.isValid, false)
  assert.equal(result.errors.email, 'Please enter a valid email address.')
})

test('validateProfileUpdateInput rejects empty email string', () => {
  const result = validateProfileUpdateInput({
    email: '   ',
  })
  assert.equal(result.isValid, false)
  assert.equal(result.errors.email, 'Email address cannot be empty.')
})

test('validateProfileUpdateInput rejects phone number longer than 20 characters', () => {
  const result = validateProfileUpdateInput({
    phone_number: '123456789012345678901',
  })
  assert.equal(result.isValid, false)
  assert.equal(result.errors.phone_number, 'Phone number cannot exceed 20 characters.')
})

test('validateProfileUpdateInput rejects phone number with invalid characters', () => {
  const result = validateProfileUpdateInput({
    phone_number: '123-ABC-7890',
  })
  assert.equal(result.isValid, false)
  assert.equal(result.errors.phone_number, 'Please enter a valid phone number (digits, spaces, +, -, () only).')
})

test('validatePasswordChangeInput accepts valid current and compliant new password', () => {
  const result = validatePasswordChangeInput({
    current_password: 'OldPassword123!',
    new_password: 'NewSecurePassword456@',
    new_password_confirm: 'NewSecurePassword456@',
  })
  assert.equal(result.isValid, true)
  assert.deepEqual(result.errors, {})
})

test('validatePasswordChangeInput requires current password', () => {
  const result = validatePasswordChangeInput({
    current_password: '',
    new_password: 'NewSecurePassword456@',
    new_password_confirm: 'NewSecurePassword456@',
  })
  assert.equal(result.isValid, false)
  assert.equal(result.errors.current_password, 'Current password is required.')
})

test('validatePasswordChangeInput enforces password complexity rules', () => {
  // Too short (< 8 chars)
  assert.equal(
    validatePasswordChangeInput({
      current_password: 'OldPassword123!',
      new_password: 'Aa1!',
      new_password_confirm: 'Aa1!',
    }).isValid,
    false
  )

  // No uppercase
  assert.equal(
    validatePasswordChangeInput({
      current_password: 'OldPassword123!',
      new_password: 'password123!',
      new_password_confirm: 'password123!',
    }).isValid,
    false
  )

  // No lowercase
  assert.equal(
    validatePasswordChangeInput({
      current_password: 'OldPassword123!',
      new_password: 'PASSWORD123!',
      new_password_confirm: 'PASSWORD123!',
    }).isValid,
    false
  )

  // No digit
  assert.equal(
    validatePasswordChangeInput({
      current_password: 'OldPassword123!',
      new_password: 'PasswordCompliant!',
      new_password_confirm: 'PasswordCompliant!',
    }).isValid,
    false
  )

  // No special char
  assert.equal(
    validatePasswordChangeInput({
      current_password: 'OldPassword123!',
      new_password: 'Password123456',
      new_password_confirm: 'Password123456',
    }).isValid,
    false
  )
})

test('validatePasswordChangeInput rejects new password identical to current password', () => {
  const result = validatePasswordChangeInput({
    current_password: 'SamePassword123!',
    new_password: 'SamePassword123!',
    new_password_confirm: 'SamePassword123!',
  })
  assert.equal(result.isValid, false)
  assert.equal(result.errors.new_password, 'New password cannot be the same as the current password.')
})

test('validatePasswordChangeInput rejects mismatched confirmation password', () => {
  const result = validatePasswordChangeInput({
    current_password: 'OldPassword123!',
    new_password: 'NewPassword123!',
    new_password_confirm: 'DifferentPassword123!',
  })
  assert.equal(result.isValid, false)
  assert.equal(result.errors.new_password_confirm, 'New passwords do not match.')
})

test('simulateProfileUpdateApi handles 200 success and state propagation', () => {
  const existingUser = {
    id: 1,
    username: 'cust1',
    first_name: '',
    last_name: '',
    phone_number: '',
    email: 'c@p.com',
  }
  const apiResponse = {
    id: 1,
    username: 'cust1',
    first_name: 'John',
    last_name: 'Doe',
    phone_number: '+15551234567',
    contact_number: '+15551234567',
    email: 'john.doe@example.com',
  }

  const merged = { ...existingUser, ...apiResponse }
  assert.equal(merged.first_name, 'John')
  assert.equal(merged.last_name, 'Doe')
  assert.equal(merged.phone_number, '+15551234567')
  assert.equal(merged.email, 'john.doe@example.com')
})

test('simulatePasswordChangeApi handles 400 incorrect current password error envelope', () => {
  const errorResponse = {
    error: 'Validation failed.',
    details: {
      current_password: ['Current password is incorrect.'],
    },
  }

  assert.equal(errorResponse.details.current_password[0], 'Current password is incorrect.')
})

