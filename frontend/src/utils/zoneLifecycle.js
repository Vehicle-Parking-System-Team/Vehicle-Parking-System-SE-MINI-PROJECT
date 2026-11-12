/** Build a minimal PATCH so stale form values cannot overwrite other admins' edits. */
export function changedZoneFields(original, current) {
  if (!original) return {}
  const changes = {}
  for (const key of ['name', 'description', 'is_active']) {
    if (current[key] !== original[key]) changes[key] = current[key]
  }
  return changes
}

/** Clear only an invalidated bay zone; keep every other draft field intact. */
export function reconcileBayZone(selectedZoneId, savedZone) {
  const invalidated = !savedZone.is_active && String(selectedZoneId) === String(savedZone.id)
  return { invalidated, zone: invalidated ? '' : selectedZoneId }
}
