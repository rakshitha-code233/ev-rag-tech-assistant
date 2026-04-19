import ReactMarkdown from 'react-markdown'
import { Bot } from 'lucide-react'
import Avatar from '../ui/Avatar'
import { useTheme } from '../../contexts/ThemeContext'

/**
 * Chat message bubble.
 * User messages: right-aligned, blue background.
 * Assistant messages: left-aligned, darker blue background, rendered as Markdown.
 */
export default function MessageBubble({ role, content, userInitials }) {
  const isUser = role === 'user'
  const { theme } = useTheme()
  const isLight = theme === 'light'

  if (isUser) {
    return (
      <div className="flex items-end justify-end gap-2 animate-fade-in">
        <div
          className="rounded-2xl rounded-tr-sm px-4 py-3 max-w-[75%] text-sm leading-relaxed"
          style={{
            backgroundColor: isLight ? '#dbeafe' : '#1e3a5f',
            color: isLight ? '#0f172a' : '#ffffff',
          }}
        >
          {content}
        </div>
        <Avatar username={userInitials || 'U'} size="sm" />
      </div>
    )
  }

  return (
    <div className="flex items-end gap-2 animate-fade-in">
      <div className="w-8 h-8 rounded-full bg-blue-900 border border-blue-700 flex items-center justify-center flex-shrink-0">
        <Bot size={16} className="text-blue-400" />
      </div>
      <div
        className="rounded-2xl rounded-tl-sm px-4 py-3 max-w-[75%] text-sm leading-relaxed"
        style={{
          backgroundColor: isLight ? '#f1f5f9' : '#0f2747',
          color: isLight ? '#0f172a' : '#ffffff',
        }}
      >
        <ReactMarkdown
          components={{
            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
            ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>,
            ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
            li: ({ children }) => <li style={{ color: isLight ? '#334155' : '#e2e8f0' }}>{children}</li>,
            strong: ({ children }) => <strong style={{ color: isLight ? '#0f172a' : '#ffffff', fontWeight: 600 }}>{children}</strong>,
            code: ({ children }) => (
              <code
                className="px-1.5 py-0.5 rounded text-xs font-mono"
                style={{
                  backgroundColor: isLight ? '#e2e8f0' : 'rgba(30,58,138,0.5)',
                  color: isLight ? '#1e40af' : '#93c5fd',
                }}
              >
                {children}
              </code>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  )
}

/**
 * Typing indicator shown while assistant is generating a response.
 */
export function TypingIndicator() {
  const { theme } = useTheme()
  const isLight = theme === 'light'
  return (
    <div className="flex items-end gap-2 animate-fade-in">
      <div className="w-8 h-8 rounded-full bg-blue-900 border border-blue-700 flex items-center justify-center flex-shrink-0">
        <Bot size={16} className="text-blue-400" />
      </div>
      <div
        className="rounded-2xl rounded-tl-sm px-4 py-3"
        style={{ backgroundColor: isLight ? '#f1f5f9' : '#0f2747' }}
      >
        <div className="flex items-center gap-1.5 h-5">
          <span className="typing-dot w-2 h-2 rounded-full bg-blue-400" />
          <span className="typing-dot w-2 h-2 rounded-full bg-blue-400" />
          <span className="typing-dot w-2 h-2 rounded-full bg-blue-400" />
        </div>
      </div>
    </div>
  )
}
