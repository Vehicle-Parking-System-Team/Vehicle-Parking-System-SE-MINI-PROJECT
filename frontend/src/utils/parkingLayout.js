export const STATUS = {
  AVAILABLE: { label: 'Available', color: '#70787d' },
  OCCUPIED: { label: 'Occupied', color: '#a6afb6' },
  RESERVED: { label: 'Reserved', color: '#b6aa91' },
  MAINTENANCE: { label: 'Maintenance', color: '#c9a57c' },
  INACTIVE: { label: 'Deactivated', color: '#808587' },
}

export function slotState(slot) {
  return slot.is_active && slot.zone_is_active !== false
    ? slot.status.toUpperCase()
    : 'INACTIVE'
}

export function floorLabel(floor) {
  if (floor == null) return 'Unmapped floor'
  return floor < 0
    ? `Basement ${Math.abs(floor)}`
    : floor === 0
      ? 'Ground floor'
      : `Level ${floor}`
}

export function floorCode(floor) {
  if (floor == null) return '?'
  return floor < 0 ? `B${Math.abs(floor)}` : floor === 0 ? 'G' : `L${floor}`
}

export function summarizeSlots(slots) {
  const counts = {
    total: slots.length,
    AVAILABLE: 0,
    OCCUPIED: 0,
    RESERVED: 0,
    MAINTENANCE: 0,
    INACTIVE: 0,
  }
  for (const slot of slots) counts[slotState(slot)] += 1
  return counts
}

// Deterministic schematic coordinates. The current API has no physical layout data.
export function buildFloorLayout(slots) {
  const zones = [...new Set(slots.map((slot) => slot.zone))].sort((a, b) => {
    const name = (id) =>
      slots.find((slot) => slot.zone === id)?.zone_name || String(id)
    return name(a).localeCompare(name(b)) || a - b
  })
  const bands = []
  for (const zone of zones) {
    const items = slots
      .filter((slot) => slot.zone === zone)
      .sort(
        (a, b) =>
          a.slot_number.localeCompare(b.slot_number, undefined, {
            numeric: true,
          }) || a.id - b.id,
      )
    for (let start = 0; start < items.length; start += 12)
      bands.push({ zone, slots: items.slice(start, start + 12) })
  }
  const depth = Math.max(1, bands.length) * 15 + 5
  const placements = bands.flatMap((band, bandIndex) =>
    band.slots.map((slot, index) => ({
      slot,
      x: ((index % 6) - 2.5) * 3.2,
      z: bandIndex * 15 - (bands.length - 1) * 7.5 + (index < 6 ? -4.2 : 4.2),
      rotation: index < 6 ? 0 : Math.PI,
    })),
  )
  return {
    width: 24,
    depth,
    placements,
    bands: bands.map((band, index) => ({
      zone:
        slots.find((slot) => slot.zone === band.zone)?.zone_name ||
        String(band.zone),
      z: index * 15 - (bands.length - 1) * 7.5,
    })),
  }
}
