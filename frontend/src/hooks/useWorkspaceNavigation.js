import { useEffect, useState } from 'react'
import { readWorkspaceLocation, workspaceUrl } from '../utils/workspaceNavigation'

export function useWorkspaceNavigation(navigation, fallback) {
  const [href, setHref] = useState(() => window.location.href)
  const route = readWorkspaceLocation(href, navigation.map(([key]) => key), fallback)
  const canonical = workspaceUrl(href, route)

  useEffect(() => {
    const onPopState = () => setHref(window.location.href)
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  useEffect(() => {
    // Canonicalize missing, unknown or forbidden routes without adding history.
    window.history.replaceState(window.history.state, '', canonical)
  }, [canonical])

  function navigate(page, vehicleId = null) {
    const next = readWorkspaceLocation(
      new URL(workspaceUrl(window.location.href, { page, vehicleId }), window.location.origin).href,
      navigation.map(([key]) => key), fallback,
    )
    const url = workspaceUrl(window.location.href, next)
    if (url !== `${window.location.pathname}${window.location.search}${window.location.hash}`) {
      window.history.pushState(null, '', url)
    }
    setHref(window.location.href)
  }

  return { ...route, navigate }
}
