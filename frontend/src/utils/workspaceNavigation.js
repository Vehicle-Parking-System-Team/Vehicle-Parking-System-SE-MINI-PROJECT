export function readWorkspaceLocation(href, allowedPages, fallback) {
  const url = new URL(href)
  const requested = url.searchParams.get('page')
  const page = allowedPages.includes(requested) ? requested : fallback
  const id = url.searchParams.get('vehicle')
  const vehicleId = page === 'profiles' && /^[1-9]\d*$/.test(id || '') && Number.isSafeInteger(Number(id))
    ? Number(id) : null
  return { page, vehicleId }
}

export function workspaceUrl(href, { page, vehicleId }) {
  const url = new URL(href)
  url.searchParams.set('page', page)
  url.searchParams.delete('vehicle')
  if (page === 'profiles' && vehicleId) url.searchParams.set('vehicle', String(vehicleId))
  return `${url.pathname}${url.search}${url.hash}`
}
