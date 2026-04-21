import api from './api'

/**
 * Send a diagnostic message to the backend.
 * @param {string} message
 * @param {AbortSignal} signal - Optional abort signal to cancel the request
 * @returns {Promise<{answer: string}>}
 */
export async function sendMessage(message, signal) {
  const response = await api.post('/api/chat', { message }, { signal })
  return response.data
}
