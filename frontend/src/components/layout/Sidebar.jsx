import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Bot,
  Clock,
  FileText,
  LogOut,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/chat', label: 'EV Assistant', icon: Bot },
  { to: '/history', label: 'Chat History', icon: Clock },
  { to: '/upload', label: 'Upload Manuals', icon: FileText },
]

export default function Sidebar() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const sidebarContent = (
    <div className="flex flex-col h-full" style={{ backgroundColor: '#0d1117' }}>
      {/* Logo */}
      <div className={`flex items-center border-b border-blue-900/30 ${collapsed ? 'justify-center px-2 py-4' : 'gap-3 px-4 py-4'}`}>
        <img
          src="/ev-app-icon.png"
          alt="EV Logo"
          className="w-9 h-9 flex-shrink-0 rounded-lg"
        />
        {!collapsed && (
          <span className="text-white font-semibold text-sm leading-tight">
            EV Diagnostic<br />
            <span className="text-blue-400">Assistant</span>
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1" aria-label="Main navigation">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setMobileOpen(false)}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 w-full ${
                collapsed ? 'justify-center' : ''
              } ${
                isActive
                  ? 'bg-blue-700 text-white shadow-glow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`
            }
          >
            <Icon size={18} className="flex-shrink-0" />
            {!collapsed && label}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="px-2 py-4 border-t border-blue-900/30">
        <button
          onClick={handleLogout}
          title={collapsed ? 'Logout' : undefined}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                     text-red-400 hover:text-white hover:bg-red-600/20 transition-all duration-200 w-full ${
                       collapsed ? 'justify-center' : ''
                     }`}
          aria-label="Logout"
        >
          <LogOut size={18} className="flex-shrink-0" />
          {!collapsed && 'Logout'}
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        className="lg:hidden fixed top-3 left-3 z-50 w-10 h-10 flex items-center justify-center rounded-xl overflow-hidden shadow-lg"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
      >
        {mobileOpen ? (
          <div className="w-10 h-10 bg-slate-800 flex items-center justify-center rounded-xl">
            <X size={20} className="text-white" />
          </div>
        ) : (
          <img src="/ev-app-icon.png" alt="Menu" className="w-10 h-10 rounded-xl object-cover" />
        )}
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/60"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={`lg:hidden fixed top-0 left-0 z-40 h-full w-64 transform transition-transform duration-300 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Sidebar navigation"
      >
        {sidebarContent}
      </aside>

      {/* Desktop sidebar with collapse toggle */}
      <aside
        className={`hidden lg:flex flex-col flex-shrink-0 h-screen relative transition-all duration-300 ${
          collapsed ? 'w-16' : 'w-64'
        }`}
        style={{ backgroundColor: '#0d1117' }}
        aria-label="Sidebar navigation"
      >
        {sidebarContent}

        {/* Collapse toggle button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center shadow-lg hover:bg-blue-700 transition-colors z-10"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
        </button>
      </aside>
    </>
  )
}
