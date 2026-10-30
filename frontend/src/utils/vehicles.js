/**
 * Vehicle constants and validation utilities (US-05/06/08; FR-01/02/13).
 */

export const VEHICLE_TYPES = [
  { value: 'Two-Wheeler', label: 'Two-Wheeler (Motorcycle, Scooter)' },
  { value: 'Compact', label: 'Compact (Hatchback, Sedan)' },
  { value: 'SUV', label: 'SUV / Large Vehicle' },
  { value: 'EV Charging', label: 'EV Charging (Dedicated EV Bay)' },
]

const REGISTRATION_NUMBER_PATTERN =
  /^(?:[A-Z]{2}-?(?:[0-9]{1,2}-?)?[A-Z]{1,8}-?[0-9]{1,4}|[0-9]{2}-?BH-?[0-9]{4}-?[A-Z]{1,2})$/

export function normalizePlate(plate) {
  if (typeof plate !== 'string') return ''
  let normalized = plate.trim().toUpperCase()

  if (!normalized || !/^[A-Z0-9 -]+$/.test(normalized)) return normalized

  if (normalized.includes('-')) {
    return normalized.replace(/ *- */g, '-')
  }

  if (normalized.includes(' ')) {
    const parts = normalized.split(/ +/)
    if (parts.length === 3 || parts.length === 4) {
      normalized = parts.join('-')
    }
  }

  return normalized
}

export function validateRegistrationNumber(plate) {
  const raw = typeof plate === 'string' ? plate.trim() : ''
  const normalized = normalizePlate(plate)
  if (!normalized) {
    return { isValid: false, normalized, error: 'Registration number is required.' }
  }
  if (raw.length > 20) {
    return {
      isValid: false,
      normalized,
      error: 'Ensure this field has no more than 20 characters.',
    }
  }
  if (!REGISTRATION_NUMBER_PATTERN.test(normalized)) {
    return {
      isValid: false,
      normalized,
      error: 'Enter a valid registration number (e.g. KA-01-AB-1234 or 22-BH-1234-AA).',
    }
  }
  return { isValid: true, normalized, error: null }
}

export function validateVehicleUpdateInput({ registration_number, vehicle_type, owner_name, owner_phone }) {
  const errors = {}

  if (registration_number !== undefined) {
    const validation = validateRegistrationNumber(registration_number)
    if (!validation.isValid) errors.registration_number = [validation.error]
  }

  if (vehicle_type !== undefined) {
    const validTypes = VEHICLE_TYPES.map((t) => t.value)
    if (typeof vehicle_type !== 'string' || !validTypes.includes(vehicle_type)) {
      errors.vehicle_type = ['A valid vehicle type is required.']
    }
  }

  for (const [field, maxLength] of [['owner_name', 100], ['owner_phone', 20]]) {
    const value = { owner_name, owner_phone }[field]
    if (value !== undefined) {
      if (typeof value !== 'string') {
        errors[field] = ['Expected a string.']
      } else if (value.length > maxLength) {
        errors[field] = [`Ensure this field has no more than ${maxLength} characters.`]
      }
    }
  }

  return { isValid: Object.keys(errors).length === 0, errors }
}

// Search deliberately supports partial plate prefixes, so validate only
// presence and length here; the backend still validates and scopes the query.
export function validateSearchPlateInput(plate) {
  const normalized = normalizePlate(plate)
  if (!normalized) {
    return {
      isValid: false,
      error: 'Please enter a license plate number to search.',
      normalized: '',
    }
  }
  if (normalized.length > 20) {
    return {
      isValid: false,
      error: 'Registration number cannot exceed 20 characters.',
      normalized,
    }
  }
  return { isValid: true, error: null, normalized }
}
