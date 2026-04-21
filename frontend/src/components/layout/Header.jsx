import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Share2, Settings, ChevronDown, LogOut, X } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { useTheme } from '../../contexts/ThemeContext'
import Avatar from '../ui/Avatar'

function SettingsModal({ onClose }) {
  const { theme, toggleTheme } = useTheme()
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="w-96 rounded-2xl border border-blue-900/30 shadow-xl p-6"
        style={{ backgroundColor: '#0d1117' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-white font-semibold text-base">Settings</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors flex-shrink-0">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-blue-900/20 gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium">Dark Mode</p>
              <p className="text-slate-500 text-xs mt-0.5">Toggle light / dark theme</p>
            </div>
            <button
              onClick={toggleTheme}
              className={`relative w-12 h-6 rounded-full transition-colors flex-shrink-0 ${
                theme === 'dark' ? 'bg-blue-600' : 'bg-slate-600'
              }`}
              aria-label="Toggle theme"
            >
              <span
                className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${
                  theme === 'dark' ? 'translate-x-6' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
          <div className="flex items-center justify-between py-3">
            <div>
              <p className="text-white text-sm font-medium">App Version</p>
              <p className="text-slate-500 text-xs mt-0.5">EV Diagnostic Assistant v1.0</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Header({ showLoginButton = false }) {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const dropdownRef = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/')
    setDropdownOpen(false)
  }

  const handleShare = async () => {
    // Always share the root URL so unauthenticated users land on the landing page
    const shareUrl = `${window.location.protocol}//${window.location.host}`
    const shareData = {
      title: 'EV Diagnostic Assistant',
      text: 'AI-powered EV diagnostics grounded in repair manuals — Smart • Reliable • Electric',
      url: shareUrl,
    }
    if (navigator.share) {
      try {
        await navigator.share(shareData)
      } catch {
        // User cancelled share
      }
    } else {
      // Fallback: copy URL to clipboard
      await navigator.clipboard.writeText(shareUrl)
      alert('Link copied to clipboard!')
    }
  }

  return (
    <>
      {settingsOpen && <SettingsModal onClose={() => setSettingsOpen(false)} />}
      <header
        className="flex items-center justify-between pl-16 pr-4 lg:px-6 py-3 border-b border-blue-900/30 flex-shrink-0"
        style={{ backgroundColor: '#0a0e1a' }}
      >
        {/* App name only - logo is in sidebar */}
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-white font-semibold text-base whitespace-nowrap">
            EV Diagnostic Assistant
          </span>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleShare}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            aria-label="Share"
            title="Share this page"
          >
            <Share2 size={18} />
          </button>

          <button
            onClick={() => setSettingsOpen(true)}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            aria-label="Settings"
            title="Settings"
          >
            <Settings size={18} />
          </button>

          {showLoginButton && !isAuthenticated ? (
            <button
              onClick={() => navigate('/login')}
              className="btn-primary text-sm px-4 py-2 ml-2"
            >
              Login
            </button>
          ) : isAuthenticated && user ? (
            <div className="relative ml-2" ref={dropdownRef}>
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 p-1 rounded-lg hover:bg-white/5 transition-colors"
                aria-label="User menu"
                aria-expanded={dropdownOpen}
                aria-haspopup="true"
              >
                <Avatar username={user.username} size="sm" />
                <ChevronDown size={14} className="text-slate-400" />
              </button>

              {dropdownOpen && (
                <div
                  className="absolute right-0 top-full mt-2 w-52 rounded-xl border border-slate-700 shadow-xl z-50 overflow-hidden animate-fade-in"
                  style={{ backgroundColor: '#1e293b' }}
                  role="menu"
                >
                  <div className="px-4 py-3 border-b border-slate-700">
                    <p style={{ color: '#ffffff', fontSize: '0.875rem', fontWeight: 600 }}>{user.username}</p>
                    <p style={{ color: '#94a3b8', fontSize: '0.75rem', marginTop: '2px' }} className="truncate">{user.email}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-2 w-full px-4 py-2.5 text-sm hover:bg-red-600/10 transition-colors"
                    style={{ color: '#f87171' }}
                    role="menuitem"
                  >
                    <LogOut size={14} />
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </header>
    </>
  )
}
