/** Build a minimal PATCH so stale form values cannot overwrite other admins' edits. */
export function changedZoneFields(original, current) {
  if (!original) return {}
  const changes = {}
  for (const key of ['name', 'description', 'is_active']) {
    if (current[key] !== original[key]) changes[key] = current[key]
  }
  return changes
}
