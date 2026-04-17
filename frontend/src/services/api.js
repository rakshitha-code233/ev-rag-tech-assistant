import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor — inject Authorization header
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('ev_diag_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — handle common error codes
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Network error
      return Promise.reject(
        new Error('Unable to connect to the server. Please try again later.')
      )
    }

    const { status, data } = error.response

    if (status === 401) {
      // Don't auto-redirect or wipe token here — let the component/page handle it.
      // Only clear token for non-auth endpoints so expired sessions are cleaned up
      // without interfering with fresh logins.
      const isAuthEndpoint =
        error.config?.url?.includes('/api/auth/login') ||
        error.config?.url?.includes('/api/auth/register')
      if (!isAuthEndpoint) {
        // Token was rejected by server — clear it so ProtectedRoute redirects cleanly
        localStorage.removeItem('ev_diag_token')
        // Use React Router navigation instead of hard redirect to avoid full page reload
        // The ProtectedRoute will handle the redirect on next render
        window.dispatchEvent(new CustomEvent('auth:logout'))
      }
      const message = data?.error || 'Session expired. Please log in again.'
      return Promise.reject(new Error(message))
    }

    if (status === 403) {
      return Promise.reject(
        new Error('You do not have permission to perform this action.')
      )
    }

    if (status === 404) {
      return Promise.reject(new Error('The requested resource was not found.'))
    }

    if (status === 500) {
      return Promise.reject(
        new Error('A server error occurred. Please try again later.')
      )
    }

    // Other 4xx — use server message if available
    const message =
      data?.error || data?.message || `Request failed with status ${status}`
    return Promise.reject(new Error(message))
  }
)

export default api
