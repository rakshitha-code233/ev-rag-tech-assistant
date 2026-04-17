import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Share2, Settings, Zap, ChevronDown, LogOut, User } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import ThemeToggle from '../ui/ThemeToggle'
import Avatar from '../ui/Avatar'

export default function Header({ showLoginButton = false }) {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const [dropdownOpen, setDropdownOpen] = useState(false)
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

  return (
    <header
      className="flex items-center justify-between px-6 py-3 border-b border-blue-900/30 flex-shrink-0"
      style={{ backgroundColor: '#0a0e1a' }}
    >
      {/* Logo + Name */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
          <Zap size={16} className="text-white" />
        </div>
        <span className="text-white font-semibold text-base hidden sm:block">
          EV Diagnostic Assistant
        </span>
      </div>

      {/* Right side controls */}
      <div className="flex items-center gap-2">
        <ThemeToggle />

        <button
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
          aria-label="Share"
        >
          <Share2 size={18} />
        </button>

        <button
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
          aria-label="Settings"
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
                className="absolute right-0 top-full mt-2 w-48 rounded-xl border border-blue-900/30 shadow-lg z-50 overflow-hidden animate-fade-in"
                style={{ backgroundColor: '#0d1117' }}
                role="menu"
              >
                <div className="px-4 py-3 border-b border-blue-900/30">
                  <p className="text-white text-sm font-medium">{user.username}</p>
                  <p className="text-slate-400 text-xs truncate">{user.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-red-400 hover:bg-red-600/10 transition-colors"
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
  )
}
