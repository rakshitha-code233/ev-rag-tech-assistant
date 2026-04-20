import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

/**
 * Decode a JWT payload without verifying the signature.
 * Used only to check expiry client-side (no network call needed).
 */
function decodeJwtPayload(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const json = atob(base64)
    return JSON.parse(json)
  } catch {
    return null
  }
}

function isTokenValid(token) {
  if (!token) return false
  const payload = decodeJwtPayload(token)
  if (!payload) return false
  const now = Math.floor(Date.now() / 1000)
  return payload.exp > now
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('ev_diag_token'))
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('ev_diag_token')
    if (stored && isTokenValid(stored)) {
      const payload = decodeJwtPayload(stored)
      return payload
        ? { id: payload.sub, username: payload.username, email: payload.email }
        : null
    }
    return null
  })
  const [loading, setLoading] = useState(true)

  // Validate token on mount + listen for forced logout from API interceptor
  useEffect(() => {
    const stored = localStorage.getItem('ev_diag_token')
    if (stored && isTokenValid(stored)) {
      const payload = decodeJwtPayload(stored)
      if (payload) {
        setToken(stored)
        setUser({ id: payload.sub, username: payload.username, email: payload.email })
      }
    } else {
      localStorage.removeItem('ev_diag_token')
      setToken(null)
      setUser(null)
    }
    setLoading(false)

    // Listen for 401 events from the Axios interceptor
    const handleForceLogout = () => {
      setToken(null)
      setUser(null)
    }
    window.addEventListener('auth:logout', handleForceLogout)
    return () => window.removeEventListener('auth:logout', handleForceLogout)
  }, [])

  const login = useCallback(async (email, password) => {
    const response = await api.post('/api/auth/login', { email, password })
    const { token: newToken, user: newUser } = response.data
    localStorage.setItem('ev_diag_token', newToken)
    setToken(newToken)
    setUser(newUser)
  }, [])

  const register = useCallback(async (username, email, password) => {
    await api.post('/api/auth/register', { username, email, password })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('ev_diag_token')
    setToken(null)
    setUser(null)
  }, [])

  const value = {
    user,
    token,
    login,
    register,
    logout,
    isAuthenticated: !!token && isTokenValid(token),
    loading,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export default AuthContext
