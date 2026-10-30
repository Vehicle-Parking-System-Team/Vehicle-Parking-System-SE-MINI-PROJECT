export const AUTH_STORAGE_KEYS = ['vps_access_token', 'vps_refresh_token', 'vps_user']

export function clearStoredAuthSession(storage) {
  AUTH_STORAGE_KEYS.forEach((key) => storage.removeItem(key))
}
