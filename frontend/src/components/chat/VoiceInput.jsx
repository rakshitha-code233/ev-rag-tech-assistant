import { useEffect, useRef, useState } from 'react'
import { Mic, Square, Loader2 } from 'lucide-react'
import { transcribeAudio } from '../../services/voiceService'

/**
 * Voice input component using MediaRecorder API.
 * Returns null if MediaRecorder is not supported.
 *
 * States: idle → requesting-permission → recording → transcribing → error
 */
export default function VoiceInput({ onTranscript, disabled, transcriptionAvailable = true }) {
  const [state, setState] = useState('idle') // idle | requesting-permission | recording | transcribing | error
  const [errorMessage, setErrorMessage] = useState('')
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const streamRef = useRef(null)

  // Feature detection — return null if MediaRecorder is unsupported
  const [isSupported] = useState(() => typeof window !== 'undefined' && !!window.MediaRecorder)

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
      }
    }
  }, [])

  if (!isSupported) return null

  const isDisabled = disabled || !transcriptionAvailable || state === 'transcribing'

  const handleMicClick = async () => {
    if (state !== 'idle') return
    if (!transcriptionAvailable) return

    setState('requesting-permission')
    setErrorMessage('')

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      chunksRef.current = []

      const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        stream.getTracks().forEach((t) => t.stop())
        streamRef.current = null

        setState('transcribing')
        try {
          const text = await transcribeAudio(blob)
          onTranscript(text)
          setState('idle')
        } catch {
          setErrorMessage('Transcription failed. Please try again or type your question.')
          setState('error')
          setTimeout(() => setState('idle'), 4000)
        }
      }

      recorder.start()
      setState('recording')
    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMessage('Microphone access was denied. Please allow microphone access in your browser settings.')
      } else {
        setErrorMessage('Could not access microphone. Please try again.')
      }
      setState('error')
      setTimeout(() => setState('idle'), 5000)
    }
  }

  const handleStopClick = () => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.stop()
    }
  }

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-center gap-1">
        {state === 'recording' ? (
          <>
            {/* Pulsing red dot */}
            <span className="recording-dot w-2.5 h-2.5 rounded-full bg-red-500 mr-1" aria-hidden="true" />
            <button
              onClick={handleStopClick}
              className="p-2 rounded-lg bg-red-600/20 text-red-400 hover:bg-red-600/30 transition-colors"
              aria-label="Stop voice recording"
              type="button"
            >
              <Square size={16} />
            </button>
          </>
        ) : state === 'transcribing' || state === 'requesting-permission' ? (
          <button
            disabled
            className="p-2 rounded-lg text-slate-500 cursor-not-allowed"
            aria-label="Processing voice input"
            type="button"
          >
            <Loader2 size={16} className="animate-spin" />
          </button>
        ) : (
          <button
            onClick={handleMicClick}
            disabled={isDisabled}
            className={`p-2 rounded-lg transition-colors ${
              !transcriptionAvailable
                ? 'text-slate-600 cursor-not-allowed'
                : 'text-slate-400 hover:text-blue-400 hover:bg-blue-500/10'
            }`}
            aria-label="Start voice recording"
            title={
              !transcriptionAvailable
                ? 'Voice input unavailable: transcription service not configured'
                : 'Start voice recording'
            }
            type="button"
          >
            <Mic size={16} />
          </button>
        )}
      </div>

      {(state === 'error') && errorMessage && (
        <p className="text-red-400 text-xs mt-1 max-w-xs text-center" role="alert">
          {errorMessage}
        </p>
      )}
    </div>
  )
}
