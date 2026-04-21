import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, MessageSquare, ChevronRight, Clock, MoreVertical, Trash2, Edit2 } from 'lucide-react'
import Sidebar from '../components/layout/Sidebar'
import Header from '../components/layout/Header'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { getHistory, deleteConversation, renameConversation } from '../services/historyService'

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

function ConversationContextMenu({ conversation, onDelete, onRename, onClose }) {
  const menuRef = useRef(null)
  const [isRenaming, setIsRenaming] = useState(false)
  const [newTitle, setNewTitle] = useState(conversation.title)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  const handleRename = async () => {
    if (!newTitle.trim()) {
      setError('Title cannot be empty')
      return
    }
    if (newTitle === conversation.title) {
      setIsRenaming(false)
      onClose()
      return
    }

    setIsLoading(true)
    setError('')
    try {
      await onRename(conversation.id, newTitle.trim())
      setIsRenaming(false)
      onClose()
    } catch (err) {
      console.error('Rename failed:', err)
      setError(err.message || 'Failed to rename')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async () => {
    if (confirm(`Delete "${conversation.title}"? This cannot be undone.`)) {
      setIsLoading(true)
      setError('')
      try {
        await onDelete(conversation.id)
        onClose()
      } catch (err) {
        console.error('Delete failed:', err)
        setError(err.message || 'Failed to delete')
        setIsLoading(false)
      }
    }
  }

  return (
    <div
      ref={menuRef}
      className="fixed bg-slate-800 border border-slate-700 rounded-lg shadow-lg z-50 min-w-48"
      style={{
        top: '50%',
        right: '20px',
        transform: 'translateY(-50%)',
      }}
    >
      {isRenaming ? (
        <div className="p-3 space-y-2">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="New title..."
            className="input-field text-sm w-full"
            autoFocus
            disabled={isLoading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !isLoading) handleRename()
              if (e.key === 'Escape') {
                setIsRenaming(false)
                setError('')
              }
            }}
          />
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <div className="flex gap-2">
            <button
              onClick={handleRename}
              disabled={isLoading}
              className="flex-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white text-sm rounded transition-colors"
            >
              {isLoading ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={() => {
                setIsRenaming(false)
                setError('')
              }}
              disabled={isLoading}
              className="flex-1 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-700/50 text-white text-sm rounded transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          <button
            onClick={() => {
              setIsRenaming(true)
              setError('')
            }}
            disabled={isLoading}
            className="w-full flex items-center gap-2 px-4 py-2.5 text-slate-300 hover:text-white hover:bg-slate-700/50 disabled:opacity-50 transition-colors text-sm"
          >
            <Edit2 size={16} />
            Rename
          </button>
          <button
            onClick={handleDelete}
            disabled={isLoading}
            className="w-full flex items-center gap-2 px-4 py-2.5 text-red-400 hover:text-red-300 hover:bg-red-500/10 disabled:opacity-50 transition-colors text-sm border-t border-slate-700"
          >
            <Trash2 size={16} />
            Delete
          </button>
        </>
      )}
    </div>
  )
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const [conversations, setConversations] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedQuery, setDebouncedQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [openMenuId, setOpenMenuId] = useState(null)

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

  const handleDelete = async (conversationId) => {
    try {
      await deleteConversation(conversationId)
      setConversations((prev) => prev.filter((c) => c.id !== conversationId))
      setOpenMenuId(null)
      setError('') // Clear any previous errors
    } catch (err) {
      console.error('Delete error:', err)
      setError(err.message || 'Failed to delete conversation')
    }
  }

  const handleRename = async (conversationId, newTitle) => {
    try {
      await renameConversation(conversationId, newTitle)
      setConversations((prev) =>
        prev.map((c) => (c.id === conversationId ? { ...c, title: newTitle } : c))
      )
      setOpenMenuId(null)
      setError('') // Clear any previous errors
    } catch (err) {
      console.error('Rename error:', err)
      setError(err.message || 'Failed to rename conversation')
    }
  }

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
                <div
                  key={conv.id}
                  className="flex items-center gap-2 group"
                >
                  <button
                    onClick={() => navigate(`/chat/${conv.id}`)}
                    className="flex-1 flex items-center gap-4 px-4 py-4 rounded-xl border border-blue-900/30 hover:border-blue-500/30 hover:bg-blue-500/5 transition-all duration-200 text-left"
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

                  {/* Action buttons */}
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setOpenMenuId(openMenuId === conv.id ? null : conv.id)
                      }}
                      className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
                      title="More options"
                    >
                      <MoreVertical size={16} className="text-slate-400 hover:text-white" />
                    </button>
                  </div>

                  {/* Context menu */}
                  {openMenuId === conv.id && (
                    <ConversationContextMenu
                      conversation={conv}
                      onDelete={handleDelete}
                      onRename={handleRename}
                      onClose={() => setOpenMenuId(null)}
                    />
                  )}
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
