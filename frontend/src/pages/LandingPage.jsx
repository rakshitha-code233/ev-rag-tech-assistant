import { useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Bot, FileText, Clock, Zap, ChevronRight } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import ThemeToggle from '../components/ui/ThemeToggle'
import { Share2, Settings } from 'lucide-react'

const FEATURE_CARDS = [
  {
    icon: Bot,
    title: 'EV Assistant',
    description:
      'Ask diagnostic questions and get AI-powered answers grounded in your uploaded repair manuals with exact page citations.',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
  },
  {
    icon: FileText,
    title: 'Upload Manuals',
    description:
      'Upload PDF repair manuals to build your knowledge base. The assistant retrieves relevant sections to answer your questions.',
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
  },
  {
    icon: Clock,
    title: 'Chat History',
    description:
      'Review all your previous diagnostic conversations. Search and revisit past answers whenever you need them.',
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/10',
  },
]

function EVCarIllustration() {
  return (
    <div className="relative flex items-center justify-center w-full h-full min-h-[280px]">
      {/* Glow rings */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-72 h-72 rounded-full border border-blue-500/10 animate-pulse" />
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-56 h-56 rounded-full border border-blue-500/15" />
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-40 h-40 rounded-full bg-blue-500/5 border border-blue-500/20" />
      </div>

      {/* EV Car SVG */}
      <svg
        viewBox="0 0 320 160"
        className="w-72 h-36 ev-car-glow relative z-10"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Electric vehicle illustration"
        role="img"
      >
        {/* Car body */}
        <path
          d="M40 110 L40 85 Q42 70 60 65 L90 55 Q110 40 160 38 Q210 36 240 50 L270 65 Q285 70 285 85 L285 110 Z"
          fill="#1e3a5f"
          stroke="#3b82f6"
          strokeWidth="1.5"
        />
        {/* Roof */}
        <path
          d="M90 65 Q110 42 160 40 Q210 38 240 52 L260 65 Z"
          fill="#0f2747"
          stroke="#3b82f6"
          strokeWidth="1"
        />
        {/* Windows */}
        <path
          d="M100 63 Q115 48 155 46 L200 46 Q215 48 225 58 L225 63 Z"
          fill="#1d4ed8"
          opacity="0.6"
        />
        {/* Windshield divider */}
        <line x1="162" y1="46" x2="162" y2="63" stroke="#3b82f6" strokeWidth="0.8" opacity="0.5" />
        {/* Front wheel */}
        <circle cx="95" cy="112" r="18" fill="#0a0e1a" stroke="#3b82f6" strokeWidth="2" />
        <circle cx="95" cy="112" r="10" fill="#0f172a" stroke="#60a5fa" strokeWidth="1.5" />
        <circle cx="95" cy="112" r="3" fill="#3b82f6" />
        {/* Rear wheel */}
        <circle cx="230" cy="112" r="18" fill="#0a0e1a" stroke="#3b82f6" strokeWidth="2" />
        <circle cx="230" cy="112" r="10" fill="#0f172a" stroke="#60a5fa" strokeWidth="1.5" />
        <circle cx="230" cy="112" r="3" fill="#3b82f6" />
        {/* Headlight */}
        <ellipse cx="278" cy="82" rx="6" ry="4" fill="#93c5fd" opacity="0.9" />
        <path d="M284 80 L300 75 L300 89 L284 84 Z" fill="#93c5fd" opacity="0.3" />
        {/* Tail light */}
        <rect x="38" y="80" width="5" height="8" rx="1" fill="#ef4444" opacity="0.8" />
        {/* Charge port */}
        <rect x="42" y="88" width="8" height="5" rx="1" fill="#1d4ed8" stroke="#3b82f6" strokeWidth="0.5" />
        {/* Lightning bolt on door */}
        <path
          d="M155 72 L148 85 L155 85 L148 98 L162 82 L155 82 Z"
          fill="#3b82f6"
          opacity="0.8"
        />
        {/* Ground reflection */}
        <ellipse cx="162" cy="130" rx="100" ry="6" fill="#3b82f6" opacity="0.08" />
        {/* Ground line */}
        <line x1="30" y1="130" x2="295" y2="130" stroke="#1d4ed8" strokeWidth="0.5" opacity="0.4" />
      </svg>

      {/* Floating stats */}
      <div className="absolute top-4 right-4 bg-blue-900/40 border border-blue-700/30 rounded-lg px-3 py-1.5 text-xs text-blue-300">
        <span className="text-green-400 font-semibold">●</span> Battery: 87%
      </div>
      <div className="absolute bottom-8 left-4 bg-blue-900/40 border border-blue-700/30 rounded-lg px-3 py-1.5 text-xs text-blue-300">
        Range: 312 mi
      </div>
    </div>
  )
}

export default function LandingPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true })
    }
  }, [isAuthenticated, navigate])

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#0a0e1a' }}>
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-blue-900/20">
        <div className="flex items-center gap-3">
          <img src="/ev-app-icon.png" alt="EV Logo" className="w-8 h-8 rounded-lg" />
          <span className="text-white font-semibold text-base">EV Diagnostic Assistant</span>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors" aria-label="Share">
            <Share2 size={18} />
          </button>
          <button className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors" aria-label="Settings">
            <Settings size={18} />
          </button>
          <button
            onClick={() => navigate('/login')}
            className="btn-primary text-sm px-4 py-2 ml-2"
          >
            Login
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col">
        <section className="flex flex-col lg:flex-row items-center gap-8 px-6 lg:px-16 py-12 lg:py-20">
          {/* Left: Text */}
          <div className="flex-1 max-w-xl">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-6">
              <Zap size={14} className="text-blue-400" />
              <span className="text-blue-400 text-sm font-medium">Smart EV Diagnostics</span>
            </div>

            {/* Heading */}
            <h1 className="text-4xl lg:text-5xl font-bold leading-tight mb-4">
              <span className="text-white">Welcome to </span>
              <span className="text-blue-400">EV Diagnostic Assistant</span>
            </h1>

            {/* Subtitle */}
            <p className="text-slate-400 text-lg leading-relaxed mb-8">
              AI-powered diagnostics grounded in your repair manuals. Get cited answers to EV
              fault codes, procedures, and technical questions — instantly.
            </p>

            {/* CTA */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <button
                onClick={() => navigate('/login')}
                className="btn-primary flex items-center gap-2 text-base px-6 py-3"
              >
                Login to Get Started
                <ChevronRight size={18} />
              </button>
              <p className="text-slate-400 text-sm">
                Don&apos;t have an account?{' '}
                <Link to="/register" className="text-blue-400 hover:text-blue-300 underline">
                  Sign up
                </Link>
              </p>
            </div>
          </div>

          {/* Right: EV Car Illustration */}
          <div className="flex-1 w-full max-w-lg">
            <EVCarIllustration />
          </div>
        </section>

        {/* Feature Cards */}
        <section className="px-6 lg:px-16 pb-16">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {FEATURE_CARDS.map(({ icon: Icon, title, description, color, bg }) => (
              <div
                key={title}
                className="glass-card p-6 hover:shadow-glow-md transition-all duration-300 hover:-translate-y-1"
              >
                <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center mb-4`}>
                  <Icon size={20} className={color} />
                </div>
                <h3 className="text-white font-semibold text-base mb-2">{title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
