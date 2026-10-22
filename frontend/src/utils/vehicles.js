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
