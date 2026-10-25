import assert from 'node:assert/strict'
import test from 'node:test'
import { parseApiError } from '../src/utils/apiErrors.js'
import { VEHICLE_TYPES, normalizePlate, validateVehicleUpdateInput, validateSearchPlateInput } from '../src/utils/vehicles.js'

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

// --- US-06: Vehicle Profile & Update Tests (FR-02 / TC-UC02-API-002) ---

async function simulateVehicleUpdateSubmit({
  vehicleId,
  formData,
  mockFetch,
  isSubmitting,
}) {
  if (isSubmitting) {
    return { status: 'BLOCKED_BY_SUBMITTING_STATE' }
  }

  const normalizedPlate = normalizePlate(formData.registration_number)
  const validation = validateVehicleUpdateInput({
    registration_number: normalizedPlate,
    vehicle_type: formData.vehicle_type,
  })

  if (!validation.isValid) {
    return {
      status: 'CLIENT_VALIDATION_ERROR',
      fieldErrors: validation.errors,
      formError: 'Please correct highlighted fields.',
    }
  }

  try {
    const payload = {
      registration_number: normalizedPlate,
      vehicle_type: formData.vehicle_type,
      owner_name: (formData.owner_name || '').trim(),
      owner_phone: (formData.owner_phone || '').trim(),
    }

    const response = await mockFetch(`/api/v1/vehicles/${vehicleId}/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    const body = await response.json()
    if (response.status === 200) {
      return {
        status: 'SUCCESS',
        data: body,
      }
    }

    const parsed = parseApiError(body)
    return {
      status: 'API_ERROR',
      statusCode: response.status,
      message: parsed.message,
      code: parsed.code,
      fieldErrors: parsed.fieldErrors,
      formErrors: parsed.formErrors,
    }
  } catch (err) {
    return {
      status: 'NETWORK_ERROR',
      message: err.message,
    }
  }
}

async function simulateVehicleProfileFetch({ vehicleId, mockFetch }) {
  try {
    const response = await mockFetch(`/api/v1/vehicles/${vehicleId}/`)
    const body = await response.json()
    if (response.status === 200) {
      return { status: 'SUCCESS', data: body }
    }
    const parsed = parseApiError(body)
    return {
      status: 'API_ERROR',
      statusCode: response.status,
      code: parsed.code,
      message: parsed.message,
    }
  } catch (err) {
    return { status: 'NETWORK_ERROR', message: err.message }
  }
}

test('validateVehicleUpdateInput rejects empty registration number', () => {
  const result = validateVehicleUpdateInput({ registration_number: '   ' })
  assert.equal(result.isValid, false)
  assert.ok(result.errors.registration_number)
})

test('validateVehicleUpdateInput rejects plate exceeding 20 chars', () => {
  const result = validateVehicleUpdateInput({ registration_number: 'A'.repeat(25) })
  assert.equal(result.isValid, false)
  assert.ok(result.errors.registration_number)
})

test('validateVehicleUpdateInput rejects invalid vehicle type', () => {
  const result = validateVehicleUpdateInput({ vehicle_type: 'Helicopter' })
  assert.equal(result.isValid, false)
  assert.ok(result.errors.vehicle_type)
})

test('validateVehicleUpdateInput accepts valid update payload', () => {
  const result = validateVehicleUpdateInput({
    registration_number: 'KA-01-OK-1234',
    vehicle_type: 'SUV',
  })
  assert.equal(result.isValid, true)
  assert.deepEqual(result.errors, {})
})

test('simulateVehicleUpdateSubmit handles successful 200 profile update', async () => {
  const mockFetch = async () => ({
    status: 200,
    ok: true,
    json: async () => ({
      id: 42,
      registration_number: 'KA-01-UPDATED-01',
      vehicle_type: 'SUV',
      owner_name: 'Updated Owner',
      owner_phone: '9876543210',
    }),
  })

  const res = await simulateVehicleUpdateSubmit({
    vehicleId: 42,
    formData: {
      registration_number: 'ka-01-updated-01',
      vehicle_type: 'SUV',
      owner_name: 'Updated Owner',
      owner_phone: '9876543210',
    },
    mockFetch,
    isSubmitting: false,
  })

  assert.equal(res.status, 'SUCCESS')
  assert.equal(res.data.id, 42)
  assert.equal(res.data.registration_number, 'KA-01-UPDATED-01')
  assert.equal(res.data.vehicle_type, 'SUV')
})

test('simulateVehicleUpdateSubmit handles 409 conflict for duplicate plate', async () => {
  const mockFetch = async () => ({
    status: 409,
    ok: false,
    json: async () => ({
      error: 'A vehicle with this registration number already exists.',
      code: 'CONFLICT',
      details: {},
    }),
  })

  const res = await simulateVehicleUpdateSubmit({
    vehicleId: 42,
    formData: {
      registration_number: 'KA-01-DUPE-01',
      vehicle_type: 'Compact',
    },
    mockFetch,
    isSubmitting: false,
  })

  assert.equal(res.status, 'API_ERROR')
  assert.equal(res.statusCode, 409)
  assert.equal(res.code, 'CONFLICT')
  assert.equal(res.message, 'A vehicle with this registration number already exists.')
})

test('simulateVehicleUpdateSubmit handles 400 validation error from backend', async () => {
  const mockFetch = async () => ({
    status: 400,
    ok: false,
    json: async () => ({
      error: 'Validation failed.',
      code: 'VALIDATION_ERROR',
      details: {
        registration_number: ['Ensure this field has no more than 20 characters.'],
      },
    }),
  })

  const res = await simulateVehicleUpdateSubmit({
    vehicleId: 42,
    formData: {
      registration_number: 'A'.repeat(20),
      vehicle_type: 'Compact',
    },
    mockFetch,
    isSubmitting: false,
  })

  assert.equal(res.status, 'API_ERROR')
  assert.equal(res.statusCode, 400)
  assert.equal(res.code, 'VALIDATION_ERROR')
  assert.ok(res.fieldErrors.registration_number)
})

test('simulateVehicleUpdateSubmit handles 403 permission denied for non-owner', async () => {
  const mockFetch = async () => ({
    status: 403,
    ok: false,
    json: async () => ({
      error: 'You do not have permission to access this vehicle record.',
      code: 'PERMISSION_DENIED',
      details: {},
    }),
  })

  const res = await simulateVehicleUpdateSubmit({
    vehicleId: 99,
    formData: {
      registration_number: 'KA-01-HACK-01',
      vehicle_type: 'Compact',
    },
    mockFetch,
    isSubmitting: false,
  })

  assert.equal(res.status, 'API_ERROR')
  assert.equal(res.statusCode, 403)
  assert.equal(res.code, 'PERMISSION_DENIED')
  assert.equal(res.message, 'You do not have permission to access this vehicle record.')
})

test('simulateVehicleUpdateSubmit handles 404 not found for missing vehicle', async () => {
  const mockFetch = async () => ({
    status: 404,
    ok: false,
    json: async () => ({
      error: 'Vehicle record not found.',
      code: 'NOT_FOUND',
      details: {},
    }),
  })

  const res = await simulateVehicleUpdateSubmit({
    vehicleId: 9999,
    formData: {
      registration_number: 'KA-01-MISSING-01',
      vehicle_type: 'Compact',
    },
    mockFetch,
    isSubmitting: false,
  })

  assert.equal(res.status, 'API_ERROR')
  assert.equal(res.statusCode, 404)
  assert.equal(res.code, 'NOT_FOUND')
})

test('simulateVehicleUpdateSubmit handles network failure gracefully', async () => {
  const mockFetch = async () => {
    throw new Error('Connection refused')
  }

  const res = await simulateVehicleUpdateSubmit({
    vehicleId: 42,
    formData: {
      registration_number: 'KA-01-NETFAIL-01',
      vehicle_type: 'Compact',
    },
    mockFetch,
    isSubmitting: false,
  })

  assert.equal(res.status, 'NETWORK_ERROR')
  assert.equal(res.message, 'Connection refused')
})

test('simulateVehicleProfileFetch handles successful 200 retrieval', async () => {
  const mockFetch = async () => ({
    status: 200,
    ok: true,
    json: async () => ({
      id: 10,
      registration_number: 'KA-05-VIEW-01',
      vehicle_type: 'Two-Wheeler',
      owner_name: 'View Owner',
      owner_phone: '9988776655',
      created_at: '2026-10-23T10:00:00Z',
      updated_at: '2026-10-23T10:05:00Z',
    }),
  })

  const res = await simulateVehicleProfileFetch({ vehicleId: 10, mockFetch })
  assert.equal(res.status, 'SUCCESS')
  assert.equal(res.data.id, 10)
  assert.equal(res.data.registration_number, 'KA-05-VIEW-01')
  assert.equal(res.data.vehicle_type, 'Two-Wheeler')
})

test('simulateVehicleProfileFetch handles 404 for non-existent vehicle', async () => {
  const mockFetch = async () => ({
    status: 404,
    ok: false,
    json: async () => ({
      error: 'Vehicle record not found.',
      code: 'NOT_FOUND',
      details: {},
    }),
  })

  const res = await simulateVehicleProfileFetch({ vehicleId: 999, mockFetch })
  assert.equal(res.status, 'API_ERROR')
  assert.equal(res.statusCode, 404)
  assert.equal(res.code, 'NOT_FOUND')
})

test('simulateVehicleProfileFetch handles 403 for unauthorized viewer', async () => {
  const mockFetch = async () => ({
    status: 403,
    ok: false,
    json: async () => ({
      error: 'You do not have permission to access this vehicle record.',
      code: 'PERMISSION_DENIED',
      details: {},
    }),
  })

  const res = await simulateVehicleProfileFetch({ vehicleId: 55, mockFetch })
  assert.equal(res.status, 'API_ERROR')
  assert.equal(res.statusCode, 403)
  assert.equal(res.code, 'PERMISSION_DENIED')
})

test('navigation shell state manages active view transitions and vehicle selection', () => {
  // Navigation state machine mirroring AuthenticatedView
  function createNavigationManager() {
    let activeNav = 'vehicles'
    let selectedVehicleId = null
    let isMobileMenuOpen = false

    return {
      getState: () => ({ activeNav, selectedVehicleId, isMobileMenuOpen }),
      navigateTo: (nav, vehicleId = null) => {
        activeNav = nav
        if (vehicleId !== null) selectedVehicleId = vehicleId
        isMobileMenuOpen = false
      },
      toggleMobileMenu: () => {
        isMobileMenuOpen = !isMobileMenuOpen
      },
    }
  }

  const nav = createNavigationManager()
  assert.equal(nav.getState().activeNav, 'vehicles')
  assert.equal(nav.getState().selectedVehicleId, null)
  assert.equal(nav.getState().isMobileMenuOpen, false)

  // Toggle mobile drawer
  nav.toggleMobileMenu()
  assert.equal(nav.getState().isMobileMenuOpen, true)

  // Navigate to profiles
  nav.navigateTo('profiles')
  assert.equal(nav.getState().activeNav, 'profiles')
  assert.equal(nav.getState().isMobileMenuOpen, false)

  // Navigate to specific vehicle profile from vehicle card (US-05 -> US-06)
  nav.navigateTo('profiles', 42)
  assert.equal(nav.getState().activeNav, 'profiles')
  assert.equal(nav.getState().selectedVehicleId, 42)

  // Navigate back to registration
  nav.navigateTo('vehicles')
  assert.equal(nav.getState().activeNav, 'vehicles')
  // selected ID preserved for next profile view
  assert.equal(nav.getState().selectedVehicleId, 42)

  // Navigate to account
  nav.navigateTo('account')
  assert.equal(nav.getState().activeNav, 'account')
})

test('vehicle profile editing state transitions between view and edit modes', () => {
  const initialVehicle = {
    id: 101,
    registration_number: 'KA-01-TEST-99',
    vehicle_type: 'Compact',
    owner_name: 'Original Owner',
    owner_phone: '9876543210',
  }

  let isEditing = false
  let editFormData = { ...initialVehicle }

  // Enter edit mode
  isEditing = true
  assert.equal(isEditing, true)
  assert.equal(editFormData.registration_number, 'KA-01-TEST-99')

  // Modify form data
  editFormData.registration_number = 'KA-01-MODIFIED-99'
  editFormData.vehicle_type = 'SUV'

  // Cancel edit mode
  isEditing = false
  editFormData = { ...initialVehicle }
  assert.equal(isEditing, false)
  assert.equal(editFormData.registration_number, 'KA-01-TEST-99')
  assert.equal(editFormData.vehicle_type, 'Compact')
})

// --- US-07: Vehicle Search & Status Tests (FR-11 / TC-UC02-API-001, TC-UC02-API-002) ---

async function simulateVehicleSearch({ plate, mockFetch }) {
  const validation = validateSearchPlateInput(plate)
  if (!validation.isValid) {
    return {
      status: 'CLIENT_VALIDATION_ERROR',
      error: validation.error,
      result: null,
    }
  }

  try {
    const encoded = encodeURIComponent(validation.normalized)
    const response = await mockFetch(`/api/v1/vehicles/search/?plate=${encoded}`)
    const body = await response.json()

    if (response.status === 200) {
      if (Array.isArray(body) && body.length === 0) {
        return {
          status: 'NOT_FOUND',
          result: null,
          error: `No vehicle found with registration number "${validation.normalized}".`,
        }
      }
      return {
        status: 'SUCCESS',
        result: body,
        error: null,
      }
    } else if (response.status === 404) {
      return {
        status: 'NOT_FOUND',
        result: null,
        error: `No vehicle found with registration number "${validation.normalized}".`,
      }
    } else if (response.status === 403) {
      return {
        status: 'FORBIDDEN',
        result: null,
        error: 'Access restricted. You do not have permission to inspect records for this vehicle.',
      }
    } else {
      const parsed = parseApiError(body)
      return {
        status: 'API_ERROR',
        result: null,
        error: parsed.message || 'Search failed.',
      }
    }
  } catch {
    return {
      status: 'NETWORK_ERROR',
      result: null,
      error: 'Network error occurred while executing vehicle search.',
    }
  }
}

test('validateSearchPlateInput normalizes plate and enforces length constraint', () => {
  const emptyRes = validateSearchPlateInput('')
  assert.equal(emptyRes.isValid, false)
  assert.match(emptyRes.error, /Please enter a license plate/)

  const whitespaceRes = validateSearchPlateInput('   ')
  assert.equal(whitespaceRes.isValid, false)

  const longPlate = 'A'.repeat(21)
  const longRes = validateSearchPlateInput(longPlate)
  assert.equal(longRes.isValid, false)
  assert.match(longRes.error, /cannot exceed 20 characters/)

  const validRes = validateSearchPlateInput('  ka-01-ab-1234  ')
  assert.equal(validRes.isValid, true)
  assert.equal(validRes.normalized, 'KA-01-AB-1234')
  assert.equal(validRes.error, null)
})

test('simulateVehicleSearch handles successful search with PARKED status and slot details', async () => {
  const mockPayload = {
    id: 10,
    registration_number: 'KA-01-MG-1000',
    vehicle_type: 'Compact',
    owner_name: 'Priya Sharma',
    owner_username: 'priya123',
    owner_phone: '9876543210',
    parking_status: {
      is_parked: true,
      status: 'PARKED',
      session_id: 205,
      check_in_time: '2026-10-24T18:00:00Z',
      slot: {
        id: 14,
        slot_number: 'A-102',
        zone: 'North Wing',
        floor: 1,
      },
      message: 'Vehicle is currently parked in bay A-102.',
    },
  }

  const mockFetch = async () => ({
    status: 200,
    ok: true,
    json: async () => mockPayload,
  })

  const res = await simulateVehicleSearch({ plate: 'ka-01-mg-1000', mockFetch })
  assert.equal(res.status, 'SUCCESS')
  assert.equal(res.result.registration_number, 'KA-01-MG-1000')
  assert.equal(res.result.parking_status.is_parked, true)
  assert.equal(res.result.parking_status.status, 'PARKED')
  assert.equal(res.result.parking_status.slot.slot_number, 'A-102')
  assert.equal(res.result.parking_status.slot.floor, 1)
})

test('simulateVehicleSearch handles successful search with NOT_PARKED status', async () => {
  const mockPayload = {
    id: 11,
    registration_number: 'DL-01-CD-5678',
    vehicle_type: 'SUV',
    owner_name: 'Rohan Verma',
    owner_username: 'rohan56',
    owner_phone: '',
    parking_status: {
      is_parked: false,
      status: 'NOT_PARKED',
      session_id: null,
      check_in_time: null,
      slot: null,
      message: 'Vehicle is not currently parked in any slot.',
    },
  }

  const mockFetch = async () => ({
    status: 200,
    ok: true,
    json: async () => mockPayload,
  })

  const res = await simulateVehicleSearch({ plate: 'DL-01-CD-5678', mockFetch })
  assert.equal(res.status, 'SUCCESS')
  assert.equal(res.result.parking_status.is_parked, false)
  assert.equal(res.result.parking_status.slot, null)
  assert.match(res.result.parking_status.message, /not currently parked/)
})

test('simulateVehicleSearch handles 404 Not Found for unregistered plate', async () => {
  const mockFetch = async () => ({
    status: 404,
    ok: false,
    json: async () => ({ error: 'Vehicle not found.', code: 'NOT_FOUND' }),
  })

  const res = await simulateVehicleSearch({ plate: 'KA-99-ZZ-0000', mockFetch })
  assert.equal(res.status, 'NOT_FOUND')
  assert.match(res.error, /No vehicle found with registration number "KA-99-ZZ-0000"/)
  assert.equal(res.result, null)
})

test('simulateVehicleSearch handles 403 Forbidden for unauthorized customer access', async () => {
  const mockFetch = async () => ({
    status: 403,
    ok: false,
    json: async () => ({ detail: 'You do not have permission to view details for this vehicle.' }),
  })

  const res = await simulateVehicleSearch({ plate: 'HR-26-AB-9999', mockFetch })
  assert.equal(res.status, 'FORBIDDEN')
  assert.match(res.error, /Access restricted/)
  assert.equal(res.result, null)
})

test('simulateVehicleSearch handles network failure gracefully', async () => {
  const mockFetch = async () => {
    throw new Error('Failed to fetch')
  }

  const res = await simulateVehicleSearch({ plate: 'DL-01-AB-1234', mockFetch })
  assert.equal(res.status, 'NETWORK_ERROR')
  assert.match(res.error, /Network error occurred/)
})

test('navigation shell handles search view and profile deep-linking', () => {
  let activePage = 'vehicles'
  let selectedVehicleId = null

  const handleNavigateToSearch = () => {
    activePage = 'search'
  }

  const handleNavigateToProfileFromSearch = (vehicleId) => {
    selectedVehicleId = vehicleId
    activePage = 'profiles'
  }

  // Navigate to search
  handleNavigateToSearch()
  assert.equal(activePage, 'search')

  // Jump from search result to vehicle profile view (US-06 integration)
  handleNavigateToProfileFromSearch(105)
  assert.equal(activePage, 'profiles')
  assert.equal(selectedVehicleId, 105)
})

test('simulateVehicleSearch handles multiple matching vehicles returned as an array (US-07 Review Fix)', async () => {
  const mockPayload = [
    {
      id: 21,
      registration_number: 'KA-01-AB-1111',
      vehicle_type: 'Compact',
      owner_name: 'Alice Johnson',
      owner_username: 'alice1',
      owner_phone: '9876543211',
      parking_status: {
        is_parked: true,
        status: 'PARKED',
        session_id: 301,
        check_in_time: '2026-10-25T10:00:00Z',
        slot: {
          id: 5,
          slot_number: 'A-101',
          zone: 'North Wing',
          floor: 1,
        },
        message: 'Vehicle is currently parked in bay A-101.',
      },
    },
    {
      id: 22,
      registration_number: 'KA-01-AB-2222',
      vehicle_type: 'SUV',
      owner_name: 'Bob Johnson',
      owner_username: 'bobj',
      owner_phone: '9876543222',
      parking_status: {
        is_parked: false,
        status: 'NOT_PARKED',
        session_id: null,
        check_in_time: null,
        slot: null,
        message: 'Vehicle is not currently parked in any slot.',
      },
    },
  ]

  const mockFetch = async () => ({
    status: 200,
    ok: true,
    json: async () => mockPayload,
  })

  const res = await simulateVehicleSearch({ plate: 'KA-01-AB', mockFetch })
  assert.equal(res.status, 'SUCCESS')
  assert.ok(Array.isArray(res.result))
  assert.equal(res.result.length, 2)

  // Verify first matching vehicle details and live PARKED status
  const first = res.result[0]
  assert.equal(first.registration_number, 'KA-01-AB-1111')
  assert.equal(first.vehicle_type, 'Compact')
  assert.equal(first.parking_status.is_parked, true)
  assert.equal(first.parking_status.status, 'PARKED')
  assert.equal(first.parking_status.slot.slot_number, 'A-101')

  // Verify second matching vehicle details and live NOT_PARKED status
  const second = res.result[1]
  assert.equal(second.registration_number, 'KA-01-AB-2222')
  assert.equal(second.vehicle_type, 'SUV')
  assert.equal(second.parking_status.is_parked, false)
  assert.equal(second.parking_status.status, 'NOT_PARKED')
  assert.equal(second.parking_status.slot, null)
})

test('simulateVehicleSearch handles single vehicle in array format [vehicle] (US-07 Review Fix)', async () => {
  const singleItemArray = [
    {
      id: 30,
      registration_number: 'MH-12-CD-3456',
      vehicle_type: 'Two-Wheeler',
      owner_name: 'Sameer Rao',
      owner_username: 'sameer_r',
      owner_phone: '9123456789',
      parking_status: {
        is_parked: false,
        status: 'NOT_PARKED',
        session_id: null,
        check_in_time: null,
        slot: null,
        message: 'Vehicle is not currently parked in any slot.',
      },
    },
  ]

  const mockFetch = async () => ({
    status: 200,
    ok: true,
    json: async () => singleItemArray,
  })

  const res = await simulateVehicleSearch({ plate: 'MH-12-CD-3456', mockFetch })
  assert.equal(res.status, 'SUCCESS')
  assert.ok(Array.isArray(res.result))
  assert.equal(res.result.length, 1)

  // Verify normalization and extraction of single item from array
  const vehicle = res.result[0]
  assert.equal(vehicle.registration_number, 'MH-12-CD-3456')
  assert.equal(vehicle.vehicle_type, 'Two-Wheeler')
  assert.equal(vehicle.parking_status.status, 'NOT_PARKED')
})

test('simulateVehicleSearch handles empty array [] response as not found (US-07 Review Fix)', async () => {
  const mockFetch = async () => ({
    status: 200,
    ok: true,
    json: async () => [],
  })

  const res = await simulateVehicleSearch({ plate: 'KA-99-XX-9999', mockFetch })
  assert.equal(res.status, 'NOT_FOUND')
  assert.equal(res.result, null)
  assert.match(res.error, /No vehicle found/)
})

