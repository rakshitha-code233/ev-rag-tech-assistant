import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import VoiceInput from './VoiceInput'

/**
 * Chat input bar.
 * Layout: [text input] [VoiceInput] [send button]
 * Submits on Enter (without Shift) or send button click.
 */
export default function ChatInput({ onSubmit, disabled = false, transcriptionAvailable = true }) {
  const [value, setValue] = useState('')
  const inputRef = useRef(null)

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleTranscript = (text) => {
    setValue(text)
    inputRef.current?.focus()
  }

  return (
    <div
      className="border-t border-blue-900/30 px-4 py-3"
      style={{ backgroundColor: '#0a0e1a' }}
    >
      <div
        className="flex items-center gap-2 rounded-xl border border-blue-900/40 px-3 py-2"
        style={{ backgroundColor: '#0f172a' }}
      >
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question..."
          disabled={disabled}
          className="flex-1 bg-transparent text-white placeholder-slate-500 text-sm focus:outline-none disabled:opacity-50"
          aria-label="Chat message input"
          id="chat-input"
        />

        <VoiceInput
          onTranscript={handleTranscript}
          disabled={disabled}
          transcriptionAvailable={transcriptionAvailable}
        />

        <button
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="p-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors
                     disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
          aria-label="Send message"
          type="button"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
