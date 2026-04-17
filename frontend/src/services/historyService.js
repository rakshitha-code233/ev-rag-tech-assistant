import api from './api'

/**
 * Get all conversation history for the current user.
 * @returns {Promise<Array<{id: number, title: string, messages: Array, created_at: string}>>}
 */
export async function getHistory() {
  const response = await api.get('/api/history')
  return response.data
}

/**
 * Get a single conversation by ID for the current user.
 * @param {number|string} id - Conversation ID
 * @returns {Promise<{id: number, title: string, messages: Array, created_at: string}>}
 */
export async function getConversation(id) {
  const response = await api.get(`/api/history/${id}`)
  return response.data
}

/**
 * Save a conversation to history.
 * @param {string} title - First user message (truncated to 80 chars)
 * @param {Array<{role: string, content: string, timestamp: string}>} messages
 * @returns {Promise<{id: number}>}
 */
export async function saveConversation(title, messages) {
  const response = await api.post('/api/history', {
    title: title.slice(0, 80),
    messages,
  })
  return response.data
}
