import { useEffect, useState, useCallback, useMemo } from 'react'
import { AuthContext } from './authContextDef'

const API_BASE = '/api/auth'
const TOKEN_KEY = 'vps_access_token'
const REFRESH_KEY = 'vps_refresh_token'
const USER_KEY = 'vps_user'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem(USER_KEY)
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem(TOKEN_KEY) || null)
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem(REFRESH_KEY) || null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // Clear all credentials from state and storage
  const clearSession = useCallback(() => {
    setUser(null)
    setAccessToken(null)
    setRefreshToken(null)
    setError(null)
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USER_KEY)
  }, [])

  // Save credentials to state and storage
  const saveSession = useCallback((tokens, userData) => {
    setAccessToken(tokens.access)
    setRefreshToken(tokens.refresh)
    setUser(userData)
    setError(null)
    localStorage.setItem(TOKEN_KEY, tokens.access)
    localStorage.setItem(REFRESH_KEY, tokens.refresh)
    localStorage.setItem(USER_KEY, JSON.stringify(userData))
  }, [])

  // Authenticate user with credentials (US-01 / FR-15)
  const login = useCallback(async (username, password) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        const errorMsg = data.error || 'Authentication failed. Please check your credentials.'
        setError(errorMsg)
        return { success: false, error: errorMsg }
      }

      saveSession({ access: data.access, refresh: data.refresh }, data.user)
      return { success: true, user: data.user }
    } catch {
      const networkError = 'Network error: Unable to contact the authentication service.'
      setError(networkError)
      return { success: false, error: networkError }
    } finally {
      setIsLoading(false)
    }
  }, [saveSession])

  // Public customer self-registration (DEC-13 / SAD §3.4.2 & §5.1)
  const register = useCallback(async (username, email, password, passwordConfirm) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          email,
          password,
          password_confirm: passwordConfirm,
        }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        const errorMsg = data.error || 'Registration failed. Please check your details.'
        setError(errorMsg)
        return {
          success: false,
          error: errorMsg,
          code: data.code,
          details: data.details || {},
        }
      }

      saveSession({ access: data.access, refresh: data.refresh }, data.user)
      return { success: true, user: data.user }
    } catch {
      const networkError = 'Network error: Unable to contact the registration service.'
      setError(networkError)
      return { success: false, error: networkError }
    } finally {
      setIsLoading(false)
    }
  }, [saveSession])

  // Secure logout invalidating tokens on server (US-01 / FR-15 / FR-17)
  const logout = useCallback(async () => {
    setIsLoading(true)
    const currentRefresh = refreshToken
    const currentAccess = accessToken

    try {
      if (currentRefresh && currentAccess) {
        await fetch(`${API_BASE}/logout/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${currentAccess}`,
          },
          body: JSON.stringify({ refresh: currentRefresh }),
        })
      }
    } catch {
      // Server-side invalidation attempted; continue local purge
    } finally {
      clearSession()
      setIsLoading(false)
    }
  }, [accessToken, refreshToken, clearSession])

  // Refresh access token using current refresh token
  const refreshTokens = useCallback(async () => {
    if (!refreshToken) {
      clearSession()
      return null
    }

    try {
      const response = await fetch(`${API_BASE}/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        clearSession()
        return null
      }

      setAccessToken(data.access)
      localStorage.setItem(TOKEN_KEY, data.access)

      if (data.refresh) {
        setRefreshToken(data.refresh)
        localStorage.setItem(REFRESH_KEY, data.refresh)
      }

      return data.access
    } catch {
      clearSession()
      return null
    }
  }, [refreshToken, clearSession])

  // Authenticated fetch wrapper automatically injecting Bearer header and refreshing if 401
  const fetchWithAuth = useCallback(async (url, options = {}) => {
    let token = accessToken
    if (!token) throw new Error('No authentication token available.')

    const headers = {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    }

    let response = await fetch(url, { ...options, headers })

    if (response.status === 401 && refreshToken) {
      token = await refreshTokens()
      if (token) {
        headers.Authorization = `Bearer ${token}`
        response = await fetch(url, { ...options, headers })
      }
    }

    return response
  }, [accessToken, refreshToken, refreshTokens])

  const clearError = useCallback(() => setError(null), [])

  // Update local user state and storage (US-04)
  const updateUser = useCallback((userData) => {
    setUser((prev) => {
      const merged = { ...prev, ...userData }
      localStorage.setItem(USER_KEY, JSON.stringify(merged))
      return merged
    })
  }, [])

  // Verify session on initial load if tokens exist
  useEffect(() => {
    if (accessToken) {
      fetch(`${API_BASE}/me/`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      })
        .then((res) => {
          if (!res.ok) {
            return refreshTokens().then((newTok) => {
              if (!newTok) clearSession()
            })
          }
          return res.json().then((userData) => {
            setUser(userData)
            localStorage.setItem(USER_KEY, JSON.stringify(userData))
          })
        })
        .catch(() => {})
    }
  }, [accessToken, refreshTokens, clearSession])

  const value = useMemo(() => ({
    user,
    accessToken,
    isAuthenticated: Boolean(user && accessToken),
    isLoading,
    error,
    login,
    register,
    logout,
    updateUser,
    refreshTokens,
    fetchWithAuth,
    clearError,
  }), [user, accessToken, isLoading, error, login, register, logout, updateUser, refreshTokens, fetchWithAuth, clearError])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
