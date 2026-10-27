/**
 * Vehicle constants and utilities (US-05 / FR-01, DEC-14, SAD §3.4.3).
 */

export const VEHICLE_TYPES = [
  { value: 'Two-Wheeler', label: 'Two-Wheeler (Motorcycle, Scooter)' },
  { value: 'Compact', label: 'Compact (Hatchback, Sedan)' },
  { value: 'SUV', label: 'SUV / Large Vehicle' },
  { value: 'EV Charging', label: 'EV Charging (Dedicated EV Bay)' },
]

export function normalizePlate(plate) {
  if (!plate || typeof plate !== 'string') return ''
  return plate.trim().toUpperCase()
}

export function validateVehicleUpdateInput({ registration_number, vehicle_type }) {
  const errors = {}

  if (registration_number !== undefined) {
    const trimmed = (registration_number || '').trim()
    if (!trimmed) {
      errors.registration_number = ['Registration number cannot be empty.']
    } else if (trimmed.length > 20) {
      errors.registration_number = ['Ensure this field has no more than 20 characters.']
    }
  }

  if (vehicle_type !== undefined) {
    const validTypes = VEHICLE_TYPES.map((t) => t.value)
    if (!vehicle_type || !validTypes.includes(vehicle_type)) {
      errors.vehicle_type = ['A valid vehicle type is required.']
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  }
}

export function validateSearchPlateInput(plate) {
  const trimmed = normalizePlate(plate)
  if (!trimmed) {
    return {
      isValid: false,
      error: 'Please enter a license plate number to search.',
      normalized: '',
    }
  }
  if (trimmed.length > 20) {
    return {
      isValid: false,
      error: 'Registration number cannot exceed 20 characters.',
      normalized: trimmed,
    }
  }
  return {
    isValid: true,
    error: null,
    normalized: trimmed,
  }
}
