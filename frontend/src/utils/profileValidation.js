/**
 * Profile and password management validation utilities (US-04).
 */

export function validateProfileUpdateInput({ first_name, last_name, phone_number, email } = {}) {
  const errors = {}

  if (email !== undefined && email !== null) {
    const trimmedEmail = email.trim()
    if (!trimmedEmail) {
      errors.email = 'Email address cannot be empty.'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      errors.email = 'Please enter a valid email address.'
    }
  }

  if (phone_number !== undefined && phone_number !== null) {
    const trimmedPhone = phone_number.trim()
    let parenthesisDepth = 0
    let hasUnbalancedParentheses = false

    for (const character of trimmedPhone) {
      if (character === '(') parenthesisDepth += 1
      if (character === ')') {
        parenthesisDepth -= 1
        if (parenthesisDepth < 0) hasUnbalancedParentheses = true
      }
    }

    const hasInvalidPlus = trimmedPhone.includes('+') &&
      (trimmedPhone.indexOf('+') !== 0 || trimmedPhone.lastIndexOf('+') !== 0)
    const hasInvalidPhoneFormat = trimmedPhone !== '' && (
      !/^[0-9+()\- ]+$/.test(trimmedPhone) ||
      !/\d/.test(trimmedPhone) ||
      hasInvalidPlus ||
      hasUnbalancedParentheses ||
      parenthesisDepth !== 0
    )

    if (trimmedPhone.length > 20) {
      errors.phone_number = 'Phone number cannot exceed 20 characters.'
    } else if (hasInvalidPhoneFormat) {
      errors.phone_number = 'Please enter a valid phone number with digits, an optional leading +, and balanced parentheses.'
    }
  }

  if (first_name !== undefined && first_name !== null) {
    if (first_name.length > 150) {
      errors.first_name = 'First name cannot exceed 150 characters.'
    }
  }

  if (last_name !== undefined && last_name !== null) {
    if (last_name.length > 150) {
      errors.last_name = 'Last name cannot exceed 150 characters.'
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  }
}

export function validatePasswordChangeInput({
  current_password,
  new_password,
  new_password_confirm,
} = {}) {
  const errors = {}

  if (!current_password) {
    errors.current_password = 'Current password is required.'
  }

  if (!new_password) {
    errors.new_password = 'New password is required.'
  } else if (new_password.length < 8) {
    errors.new_password = 'Password must be at least 8 characters long.'
  } else if (!/[A-Z]/.test(new_password)) {
    errors.new_password = 'Password must contain at least one uppercase letter.'
  } else if (!/[a-z]/.test(new_password)) {
    errors.new_password = 'Password must contain at least one lowercase letter.'
  } else if (!/[0-9]/.test(new_password)) {
    errors.new_password = 'Password must contain at least one digit.'
  } else if (!/[^A-Za-z0-9]/.test(new_password)) {
    errors.new_password = 'Password must contain at least one special character.'
  } else if (current_password && new_password === current_password) {
    errors.new_password = 'New password cannot be the same as the current password.'
  }

  if (!new_password_confirm) {
    errors.new_password_confirm = 'Please confirm your new password.'
  } else if (new_password && new_password !== new_password_confirm) {
    errors.new_password_confirm = 'New passwords do not match.'
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  }
}

