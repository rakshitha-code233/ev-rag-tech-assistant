import { useNavigate } from 'react-router-dom'
import { Bot, FileText, Clock, ChevronRight, Zap } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import Sidebar from '../components/layout/Sidebar'
import Header from '../components/layout/Header'

const NAV_CARDS = [
  {
    to: '/chat',
    icon: Bot,
    title: 'EV Assistant',
    description: 'Ask diagnostic questions and get AI-powered answers grounded in your repair manuals.',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
  },
  {
    to: '/upload',
    icon: FileText,
    title: 'Upload Manuals',
    description: 'Add PDF repair manuals to build your knowledge base for better diagnostic answers.',
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/20',
  },
  {
    to: '/history',
    icon: Clock,
    title: 'Chat History',
    description: 'Review and search all your previous diagnostic conversations.',
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/10',
    border: 'border-cyan-500/20',
  },
]

function EVCarSmall() {
  return (
    <div className="relative flex items-center justify-center">
      <div className="absolute inset-0 bg-glow-blue rounded-full" />
      <svg
        viewBox="0 0 280 140"
        className="w-64 h-32 ev-car-glow relative z-10"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Electric vehicle"
        role="img"
      >
        <path
          d="M35 100 L35 78 Q37 64 53 59 L80 50 Q98 36 145 34 Q192 32 218 46 L245 59 Q258 64 258 78 L258 100 Z"
          fill="#1e3a5f"
          stroke="#3b82f6"
          strokeWidth="1.5"
        />
        <path
          d="M80 59 Q98 44 145 42 Q192 40 218 54 L235 59 Z"
          fill="#0f2747"
          stroke="#3b82f6"
          strokeWidth="1"
        />
        <path
          d="M90 57 Q103 44 140 42 L178 42 Q192 44 200 54 L200 57 Z"
          fill="#1d4ed8"
          opacity="0.6"
        />
        <circle cx="85" cy="102" r="16" fill="#0a0e1a" stroke="#3b82f6" strokeWidth="2" />
        <circle cx="85" cy="102" r="9" fill="#0f172a" stroke="#60a5fa" strokeWidth="1.5" />
        <circle cx="85" cy="102" r="3" fill="#3b82f6" />
        <circle cx="208" cy="102" r="16" fill="#0a0e1a" stroke="#3b82f6" strokeWidth="2" />
        <circle cx="208" cy="102" r="9" fill="#0f172a" stroke="#60a5fa" strokeWidth="1.5" />
        <circle cx="208" cy="102" r="3" fill="#3b82f6" />
        <ellipse cx="252" cy="74" rx="5" ry="3.5" fill="#93c5fd" opacity="0.9" />
        <rect x="33" y="72" width="4" height="7" rx="1" fill="#ef4444" opacity="0.8" />
        <path d="M138 64 L132 75 L138 75 L132 86 L145 73 L138 73 Z" fill="#3b82f6" opacity="0.8" />
        <ellipse cx="145" cy="118" rx="88" ry="5" fill="#3b82f6" opacity="0.08" />
      </svg>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  return (
    <div className="page-layout">
      <Sidebar />
      <div className="main-content">
        <Header />
        <main className="flex-1 overflow-y-auto px-6 lg:px-10 py-8">
          {/* Welcome section */}
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 mb-10">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-6 h-6 rounded bg-blue-600/20 flex items-center justify-center">
                  <Zap size={12} className="text-blue-400" />
                </div>
                <span className="text-blue-400 text-sm font-medium">Dashboard</span>
              </div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Welcome back,{' '}
                <span className="text-blue-400">{user?.username || 'Technician'}</span>
              </h1>
              <p className="text-slate-400">
                Your AI-powered EV diagnostic assistant is ready. What would you like to do today?
              </p>
            </div>
            <EVCarSmall />
          </div>

          {/* Navigation cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {NAV_CARDS.map(({ to, icon: Icon, title, description, color, bg, border }) => (
              <button
                key={to}
                onClick={() => navigate(to)}
                className={`glass-card p-6 text-left hover:shadow-glow-md transition-all duration-300 hover:-translate-y-1 border ${border} group`}
              >
                <div className={`w-12 h-12 rounded-xl ${bg} flex items-center justify-center mb-4`}>
                  <Icon size={22} className={color} />
                </div>
                <h3 className="text-white font-semibold text-base mb-2">{title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-4">{description}</p>
                <div className={`flex items-center gap-1 text-sm font-medium ${color}`}>
                  Open
                  <ChevronRight size={14} className="group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            ))}
          </div>
        </main>
      </div>
    </div>
  )
}
