import api from './api'

/**
 * Log in with email and password.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{token: string, user: {id: number, username: string, email: string}}>}
 */
export async function login(email, password) {
  const response = await api.post('/api/auth/login', { email, password })
  return response.data
}

/**
 * Register a new account.
 * @param {string} username
 * @param {string} email
 * @param {string} password
 * @returns {Promise<{message: string}>}
 */
export async function register(username, email, password) {
  const response = await api.post('/api/auth/register', { username, email, password })
  return response.data
}
