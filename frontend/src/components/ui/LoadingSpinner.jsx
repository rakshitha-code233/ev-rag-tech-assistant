/**
 * Animated loading spinner.
 */
export default function LoadingSpinner({ size = 'md', className = '' }) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3',
  }

  return (
    <div
      className={`${sizeClasses[size] || sizeClasses.md} rounded-full border-blue-500 border-t-transparent animate-spin ${className}`}
      role="status"
      aria-label="Loading"
    />
  )
}
