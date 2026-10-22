import assert from 'node:assert/strict'
import test from 'node:test'
import { parseApiError } from '../src/utils/apiErrors.js'
import { VEHICLE_TYPES, normalizePlate } from '../src/utils/vehicles.js'

const CANONICAL_VEHICLE_TYPES = VEHICLE_TYPES.map((t) => t.value)

// Client-side payload validator matching form requirements
function validateVehicleRegistrationInput({ registration_number, vehicle_type }) {
  const errors = {}
  const trimmedPlate = (registration_number || '').trim()

  if (!trimmedPlate) {
    errors.registration_number = ['Registration number is required.']
  } else if (trimmedPlate.length > 20) {
    errors.registration_number = ['Ensure this field has no more than 20 characters.']
  }

  if (!vehicle_type || !CANONICAL_VEHICLE_TYPES.includes(vehicle_type)) {
    errors.vehicle_type = ['A valid vehicle type is required.']
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
    normalizedPayload: Object.keys(errors).length === 0
      ? { registration_number: trimmedPlate.toUpperCase(), vehicle_type }
      : null,
  }
}

// Simulated submission handler mirroring VehicleRegistrationForm workflow
async function simulateVehicleRegistrationSubmit({
  formData,
  mockFetch,
  isSubmitting,
}) {
  if (isSubmitting) {
    return { status: 'BLOCKED_BY_SUBMITTING_STATE' }
  }

  const validation = validateVehicleRegistrationInput(formData)
  if (!validation.isValid) {
    return {
      status: 'CLIENT_VALIDATION_ERROR',
      fieldErrors: validation.errors,
      formError: 'Please correct highlighted fields.',
    }
  }

  try {
    const response = await mockFetch('/api/v1/vehicles/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(validation.normalizedPayload),
    })

    const body = await response.json()
    if (response.status === 201) {
      return {
        status: 'SUCCESS',
        data: body,
        message: `Vehicle ${body.registration_number} (${body.vehicle_type}) registered successfully.`,
      }
    }

    const parsed = parseApiError(body)
    return {
      status: 'API_ERROR',
      statusCode: response.status,
      code: parsed.code,
      message: parsed.message,
      fieldErrors: parsed.fieldErrors,
    }
  } catch (err) {
    return {
      status: 'NETWORK_ERROR',
      message: err.message || 'Network error occurred while connecting to vehicle service.',
    }
  }
}

test('canonical vehicle types match SAD §3.4.3 and DEC-14 specification', () => {
  assert.equal(CANONICAL_VEHICLE_TYPES.length, 4)
  assert.ok(CANONICAL_VEHICLE_TYPES.includes('Two-Wheeler'))
  assert.ok(CANONICAL_VEHICLE_TYPES.includes('Compact'))
  assert.ok(CANONICAL_VEHICLE_TYPES.includes('SUV'))
  assert.ok(CANONICAL_VEHICLE_TYPES.includes('EV Charging'))
})

test('normalizePlate trims whitespace and converts to uppercase', () => {
  assert.equal(normalizePlate('  ka-01-ab-1234  '), 'KA-01-AB-1234')
  assert.equal(normalizePlate('dl3cbb1122'), 'DL3CBB1122')
  assert.equal(normalizePlate(''), '')
  assert.equal(normalizePlate(null), '')
  assert.equal(normalizePlate(undefined), '')
})

test('validateVehicleRegistrationInput rejects empty or blank registration number', () => {
  const emptyRes = validateVehicleRegistrationInput({ registration_number: '', vehicle_type: 'Compact' })
  assert.equal(emptyRes.isValid, false)
  assert.ok(emptyRes.errors.registration_number)

  const spacesRes = validateVehicleRegistrationInput({ registration_number: '   ', vehicle_type: 'Compact' })
  assert.equal(spacesRes.isValid, false)
  assert.ok(spacesRes.errors.registration_number)

  const longRes = validateVehicleRegistrationInput({ registration_number: 'A'.repeat(21), vehicle_type: 'Compact' })
  assert.equal(longRes.isValid, false)
  assert.ok(longRes.errors.registration_number)
})

test('validateVehicleRegistrationInput rejects invalid or missing vehicle type', () => {
  const missingType = validateVehicleRegistrationInput({ registration_number: 'KA-01-AB-1234', vehicle_type: '' })
  assert.equal(missingType.isValid, false)
  assert.ok(missingType.errors.vehicle_type)

  const invalidType = validateVehicleRegistrationInput({ registration_number: 'KA-01-AB-1234', vehicle_type: 'Truck' })
  assert.equal(invalidType.isValid, false)
  assert.ok(invalidType.errors.vehicle_type)
})

test('validateVehicleRegistrationInput normalizes valid payload', () => {
  const result = validateVehicleRegistrationInput({
    registration_number: '  ka-05-xy-9876  ',
    vehicle_type: 'SUV',
  })
  assert.equal(result.isValid, true)
  assert.equal(result.normalizedPayload.registration_number, 'KA-05-XY-9876')
  assert.equal(result.normalizedPayload.vehicle_type, 'SUV')
})

test('simulateVehicleRegistrationSubmit blocks submissions while already submitting', async () => {
  const res = await simulateVehicleRegistrationSubmit({
    formData: { registration_number: 'KA-01-AB-1234', vehicle_type: 'Compact' },
    mockFetch: async () => {},
    isSubmitting: true,
  })
  assert.equal(res.status, 'BLOCKED_BY_SUBMITTING_STATE')
})

test('simulateVehicleRegistrationSubmit handles successful 201 response', async () => {
  const mockFetch = async (url, options) => {
    assert.equal(url, '/api/v1/vehicles/')
    assert.equal(options.method, 'POST')
    const sent = JSON.parse(options.body)
    assert.equal(sent.registration_number, 'KA-01-AB-1234')
    return {
      status: 201,
      ok: true,
      json: async () => ({
        id: 10,
        registration_number: sent.registration_number,
        vehicle_type: sent.vehicle_type,
        owner: 1,
        created_at: '2026-10-22T08:00:00Z',
      }),
    }
  }

  const res = await simulateVehicleRegistrationSubmit({
    formData: { registration_number: 'ka-01-ab-1234', vehicle_type: 'Compact' },
    mockFetch,
    isSubmitting: false,
  })

  assert.equal(res.status, 'SUCCESS')
  assert.equal(res.data.id, 10)
  assert.equal(res.data.registration_number, 'KA-01-AB-1234')
  assert.ok(res.message.includes('registered successfully'))
})

test('simulateVehicleRegistrationSubmit handles 409 conflict for duplicate plate', async () => {
  const mockFetch = async () => ({
    status: 409,
    ok: false,
    json: async () => ({
      error: 'A vehicle with this registration number already exists.',
      code: 'CONFLICT',
      details: {},
    }),
  })

  const res = await simulateVehicleRegistrationSubmit({
    formData: { registration_number: 'KA-01-DUP-9999', vehicle_type: 'SUV' },
    mockFetch,
    isSubmitting: false,
  })

  assert.equal(res.status, 'API_ERROR')
  assert.equal(res.statusCode, 409)
  assert.equal(res.code, 'CONFLICT')
  assert.equal(res.message, 'A vehicle with this registration number already exists.')
})

test('simulateVehicleRegistrationSubmit handles 400 validation error from server', async () => {
  const mockFetch = async () => ({
    status: 400,
    ok: false,
    json: async () => ({
      error: 'Validation failed.',
      code: 'VALIDATION_ERROR',
      details: {
        registration_number: ['This field is required.'],
      },
    }),
  })

  const res = await simulateVehicleRegistrationSubmit({
    formData: { registration_number: 'KA-01-VALID-01', vehicle_type: 'Compact' },
    mockFetch,
    isSubmitting: false,
  })

  assert.equal(res.status, 'API_ERROR')
  assert.equal(res.statusCode, 400)
  assert.equal(res.code, 'VALIDATION_ERROR')
  assert.ok(res.fieldErrors.registration_number)
})

test('simulateVehicleRegistrationSubmit handles network failure gracefully', async () => {
  const mockFetch = async () => {
    throw new Error('Failed to fetch')
  }

  const res = await simulateVehicleRegistrationSubmit({
    formData: { registration_number: 'KA-01-NET-01', vehicle_type: 'Compact' },
    mockFetch,
    isSubmitting: false,
  })

  assert.equal(res.status, 'NETWORK_ERROR')
  assert.equal(res.message, 'Failed to fetch')
})
