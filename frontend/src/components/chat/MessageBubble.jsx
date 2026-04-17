import ReactMarkdown from 'react-markdown'
import { Bot } from 'lucide-react'
import Avatar from '../ui/Avatar'

/**
 * Chat message bubble.
 * User messages: right-aligned, blue background.
 * Assistant messages: left-aligned, darker blue background, rendered as Markdown.
 */
export default function MessageBubble({ role, content, userInitials }) {
  const isUser = role === 'user'

  if (isUser) {
    return (
      <div className="flex items-end justify-end gap-2 animate-fade-in">
        <div
          className="rounded-2xl rounded-tr-sm px-4 py-3 max-w-[75%] text-white text-sm leading-relaxed"
          style={{ backgroundColor: '#1e3a5f' }}
          data-role="user"
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
        className="rounded-2xl rounded-tl-sm px-4 py-3 max-w-[75%] text-white text-sm leading-relaxed"
        style={{ backgroundColor: '#0f2747' }}
        data-role="assistant"
      >
        <ReactMarkdown
          components={{
            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
            ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>,
            ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
            li: ({ children }) => <li className="text-slate-200">{children}</li>,
            strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
            code: ({ children }) => (
              <code className="bg-blue-900/50 px-1.5 py-0.5 rounded text-blue-200 text-xs font-mono">
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
  return (
    <div className="flex items-end gap-2 animate-fade-in">
      <div className="w-8 h-8 rounded-full bg-blue-900 border border-blue-700 flex items-center justify-center flex-shrink-0">
        <Bot size={16} className="text-blue-400" />
      </div>
      <div
        className="rounded-2xl rounded-tl-sm px-4 py-3"
        style={{ backgroundColor: '#0f2747' }}
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
