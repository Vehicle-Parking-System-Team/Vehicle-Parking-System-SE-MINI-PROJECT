/**
 * Coordinates refreshes for requests that received an unauthorized response.
 *
 * Requests can fail with 401 after another request has already completed a
 * refresh. Comparing the failed request's access token with the current one
 * avoids reusing a rotated refresh token in that staggered-response case.
 */
export function createTokenRefreshCoordinator({
  getAccessToken,
  getRefreshToken,
  refresh,
  clearSession,
}) {
  let refreshPromise = null

  return async function refreshAfterUnauthorized(failedAccessToken) {
    const currentAccessToken = getAccessToken()

    // A different request already refreshed this session. Reuse its token.
    if (currentAccessToken && currentAccessToken !== failedAccessToken) {
      return currentAccessToken
    }

    const refreshCredential = getRefreshToken()
    if (!refreshCredential) {
      clearSession()
      return null
    }

    // Requests that fail together share one rotation operation.
    if (!refreshPromise) {
      const pendingRefresh = Promise.resolve().then(() => refresh(refreshCredential))
      const sharedRefresh = pendingRefresh.finally(() => {
        if (refreshPromise === sharedRefresh) refreshPromise = null
      })
      refreshPromise = sharedRefresh
    }

    return refreshPromise
  }
}
