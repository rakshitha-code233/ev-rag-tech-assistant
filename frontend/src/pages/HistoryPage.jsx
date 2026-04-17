import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, MessageSquare, ChevronRight, Clock } from 'lucide-react'
import Sidebar from '../components/layout/Sidebar'
import Header from '../components/layout/Header'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { getHistory } from '../services/historyService'

function formatDate(isoString) {
  if (!isoString) return ''
  try {
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return isoString
  }
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const [conversations, setConversations] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  // Load history on mount
  useEffect(() => {
    setIsLoading(true)
    getHistory()
      .then((data) => {
        // Sort reverse-chronological (API already returns DESC, but ensure it)
        const sorted = [...data].sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        )
        setConversations(sorted)
      })
      .catch((err) => setError(err.message || 'Failed to load history'))
      .finally(() => setIsLoading(false))
  }, [])

  // Debounce search query (300ms)
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  const filtered = debouncedQuery
    ? conversations.filter((c) =>
        c.title.toLowerCase().includes(debouncedQuery.toLowerCase())
      )
    : conversations

  return (
    <div className="page-layout">
      <Sidebar />
      <div className="main-content">
        <Header />
        <main className="flex-1 overflow-y-auto px-6 lg:px-10 py-8">
          {/* Page header */}
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center">
              <Clock size={16} className="text-cyan-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Chat History</h1>
              <p className="text-slate-400 text-sm">Review your previous diagnostic conversations</p>
            </div>
          </div>

          {/* Search bar */}
          <div className="relative mb-6 max-w-xl">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search conversations..."
              className="input-field pl-9"
              aria-label="Search conversations"
            />
          </div>

          {/* Content */}
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <LoadingSpinner size="lg" />
            </div>
          ) : error ? (
            <div role="alert" className="text-red-400 text-sm py-4">
              {error}
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-16">
              <MessageSquare size={40} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No conversations yet.</p>
              <p className="text-slate-500 text-sm mt-1">
                Start a chat with the EV Assistant to see your history here.
              </p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16">
              <Search size={40} className="text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No conversations match your search.</p>
            </div>
          ) : (
            <div className="space-y-2 max-w-2xl">
              {filtered.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => navigate('/chat')}
                  className="w-full flex items-center gap-4 px-4 py-4 rounded-xl border border-blue-900/30 hover:border-blue-500/30 hover:bg-blue-500/5 transition-all duration-200 text-left group"
                  style={{ backgroundColor: 'rgba(13, 25, 48, 0.5)' }}
                >
                  <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                    <MessageSquare size={18} className="text-blue-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">
                      {conv.title || 'Untitled conversation'}
                    </p>
                    <p className="text-slate-500 text-xs mt-0.5">{formatDate(conv.created_at)}</p>
                  </div>
                  <ChevronRight
                    size={16}
                    className="text-slate-600 group-hover:text-blue-400 group-hover:translate-x-1 transition-all flex-shrink-0"
                  />
                </button>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
