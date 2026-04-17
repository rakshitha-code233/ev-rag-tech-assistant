import { AlertCircle } from 'lucide-react'

/**
 * Inline error message component.
 */
export default function ErrorMessage({ message, id, className = '' }) {
  if (!message) return null

  return (
    <div
      id={id}
      role="alert"
      className={`flex items-center gap-2 text-red-400 text-sm mt-1 ${className}`}
    >
      <AlertCircle size={14} className="flex-shrink-0" />
      <span>{message}</span>
    </div>
  )
}
