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
 * Save a new conversation to history.
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

/**
 * Update an existing conversation's messages.
 * @param {number} id - Conversation ID
 * @param {Array} messages
 * @returns {Promise<{id: number}>}
 */
export async function updateConversation(id, messages) {
  const response = await api.put(`/api/history/${id}`, { messages })
  return response.data
}

/**
 * Rename a conversation.
 * @param {number} id - Conversation ID
 * @param {string} title - New title
 * @returns {Promise<{id: number, title: string}>}
 */
export async function renameConversation(id, title) {
  const response = await api.patch(`/api/history/${id}`, { title })
  return response.data
}

/**
 * Delete a conversation.
 * @param {number} id - Conversation ID
 * @returns {Promise<{message: string}>}
 */
export async function deleteConversation(id) {
  const response = await api.delete(`/api/history/${id}`)
  return response.data
}
