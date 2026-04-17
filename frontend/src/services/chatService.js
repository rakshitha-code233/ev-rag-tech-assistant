import api from './api'

/**
 * Send a diagnostic message to the backend.
 * @param {string} message
 * @returns {Promise<{answer: string}>}
 */
export async function sendMessage(message) {
  const response = await api.post('/api/chat', { message })
  return response.data
}
