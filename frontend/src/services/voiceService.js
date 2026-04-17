import api from './api'

/**
 * Sends an audio Blob to the transcription endpoint and returns the transcript string.
 *
 * @param {Blob} audioBlob - The recorded audio blob from MediaRecorder.
 * @returns {Promise<string>} The transcribed text.
 * @throws {Error} If the request fails or the server returns a non-2xx status.
 */
export async function transcribeAudio(audioBlob) {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')
  const response = await api.post('/api/chat/transcribe', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data.transcript
}
