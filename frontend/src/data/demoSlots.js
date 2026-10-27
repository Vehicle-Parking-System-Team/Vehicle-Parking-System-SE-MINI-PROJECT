// Explicitly selected, read-only design preview. Never sent to the API.
export const DEMO_SLOTS = [-1, 0, 1].flatMap((floor, floorIndex) =>
  Array.from({ length: 24 }, (_, index) => ({
    id: -(floorIndex * 24 + index + 1),
    slot_number: `${floor < 0 ? 'B1' : floor === 0 ? 'G' : 'L1'}-${index < 12 ? 'A' : 'B'}${String((index % 12) + 1).padStart(2, '0')}`,
    zone: index < 12 ? -1 : -2,
    zone_name: index < 12 ? 'A' : 'B',
    floor,
    vehicle_type:
      index > 19 ? 'EV Charging' : index % 7 === 0 ? 'SUV' : 'Compact',
    status:
      index === 7
        ? 'maintenance'
        : index % 8 === 0
          ? 'reserved'
          : index % 3 === 0
            ? 'available'
            : 'occupied',
    is_active: index !== 23,
  })),
)
