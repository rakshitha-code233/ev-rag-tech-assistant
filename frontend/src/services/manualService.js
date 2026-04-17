import api from './api'

/**
 * List all uploaded manuals.
 * @returns {Promise<Array<{filename: string, size: number, uploaded_at: string}>>}
 */
export async function listManuals() {
  const response = await api.get('/api/manuals')
  return response.data
}

/**
 * Upload a PDF manual.
 * @param {File} file
 * @param {(progress: number) => void} [onProgress]
 * @returns {Promise<{filename: string, size: number, uploaded_at: string}>}
 */
export async function uploadManual(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/api/manuals/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percent)
      }
    },
  })
  return response.data
}

/**
 * Delete a manual by filename.
 * @param {string} filename
 * @returns {Promise<{message: string}>}
 */
export async function deleteManual(filename) {
  const response = await api.delete(`/api/manuals/${encodeURIComponent(filename)}`)
  return response.data
}
