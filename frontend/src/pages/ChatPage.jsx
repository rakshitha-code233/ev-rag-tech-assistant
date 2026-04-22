import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import Sidebar from '../components/layout/Sidebar'
import Header from '../components/layout/Header'
import MessageBubble, { TypingIndicator } from '../components/chat/MessageBubble'
import ChatInput from '../components/chat/ChatInput'
import { sendMessage } from '../services/chatService'
import { saveConversation, getConversation, updateConversation } from '../services/historyService'
import api from '../services/api'
import { Bot } from 'lucide-react'

// Global abort controller for managing pending requests
let globalAbortController = null

function EmptyState({ onSuggestion }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center mb-4">
        <Bot size={28} className="text-blue-400" />
      </div>
      <h3 className="text-white font-semibold text-lg mb-2">EV Diagnostic Assistant</h3>
      <p className="text-slate-400 text-sm max-w-sm leading-relaxed">
        Ask me anything about EV diagnostics, fault codes, procedures, or repair guidance.
        I&apos;ll answer from your uploaded manuals with exact citations.
      </p>
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-md w-full">
        {[
          'How do I open the charge port?',
          'What does a battery warning mean?',
          'Where is the service disconnect?',
          'How to check charging alerts?',
        ].map((suggestion) => (
          <button
            key={suggestion}
            className="text-left px-4 py-2.5 rounded-lg border border-blue-900/40 text-slate-400 text-xs hover:text-white hover:border-blue-500/40 hover:bg-blue-500/5 transition-all"
            onClick={() => onSuggestion(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { user } = useAuth()
  const { id } = useParams()
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [chatError, setChatError] = useState('')
  const [transcriptionAvailable, setTranscriptionAvailable] = useState(true)
  const [conversationId, setConversationId] = useState(id ? parseInt(id) : null)
  const messagesEndRef = useRef(null)

  // Check health endpoint for transcription availability
  useEffect(() => {
    api.get('/api/health').then((res) => {
      setTranscriptionAvailable(res.data?.transcription_available ?? false)
    }).catch(() => {
      setTranscriptionAvailable(false)
    })
  }, [])

  // Cleanup: abort pending requests on unmount
  useEffect(() => {
    return () => {
      if (globalAbortController) {
        globalAbortController.abort()
      }
    }
  }, [])

  // Load existing conversation when id param is present
  useEffect(() => {
    if (!id) {
      setMessages([])
      setConversationId(null)
      return
    }
    setHistoryLoading(true)
    setChatError('')
    getConversation(id)
      .then((conv) => {
        setMessages(conv.messages || [])
        setConversationId(conv.id)
      })
      .catch(() => {
        setChatError('Could not load conversation. It may have been deleted.')
      })
      .finally(() => setHistoryLoading(false))
  }, [id])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSubmit = async (text) => {
    if (!text.trim() || isLoading) return

    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }

    // Update messages state with user message
    const messagesWithUser = [...messages, userMessage]
    setMessages(messagesWithUser)
    setIsLoading(true)
    setChatError('')

    // Create abort controller for this request
    globalAbortController = new AbortController()

    try {
      const title = text.slice(0, 80)
      let convId = conversationId

      // OPTIMISTIC PERSISTENCE: Save user message immediately (don't wait for response)
      if (!convId) {
        // New conversation: save with just the user message
        const res = await saveConversation(title, messagesWithUser)
        convId = res.id
        setConversationId(res.id)
      } else {
        // Existing conversation: update with new message
        await updateConversation(convId, messagesWithUser)
      }

      // Now send message to assistant
      const data = await sendMessage(text, globalAbortController.signal)
      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
      }

      // Append response to persisted conversation
      const messagesWithResponse = [...messagesWithUser, assistantMessage]
      setMessages(messagesWithResponse)
      await updateConversation(convId, messagesWithResponse).catch(() => {})
    } catch (err) {
      // Don't show error if request was aborted (component unmounted)
      if (err.name !== 'AbortError') {
        setChatError('Unable to get a response. Please try again.')
      }
    } finally {
      setIsLoading(false)
      globalAbortController = null
    }
  }

  return (
    <div className="page-layout">
      <Sidebar />
      <div className="main-content">
        <Header />
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 lg:px-8 py-6">
            {historyLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-slate-400 text-sm">Loading conversation…</div>
              </div>
            ) : messages.length === 0 ? (
              <EmptyState onSuggestion={handleSubmit} />
            ) : (
              <div className="max-w-3xl mx-auto space-y-4">
                {messages.map((msg, idx) => (
                  <MessageBubble
                    key={idx}
                    role={msg.role}
                    content={msg.content}
                    userInitials={user?.username || 'U'}
                  />
                ))}
                {isLoading && <TypingIndicator />}
                {chatError && (
                  <div
                    role="alert"
                    className="flex items-center gap-2 text-red-400 text-sm px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20"
                  >
                    {chatError}
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input bar */}
          <div className="max-w-3xl mx-auto w-full px-4 lg:px-8">
            <ChatInput
              onSubmit={handleSubmit}
              disabled={isLoading}
              transcriptionAvailable={transcriptionAvailable}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
