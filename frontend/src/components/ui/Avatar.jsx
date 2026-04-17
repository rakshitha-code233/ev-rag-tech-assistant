/**
 * Avatar component — displays user initials in a blue circle.
 * Derives initials from the first letter of each word (up to 2 words), uppercased.
 */
export default function Avatar({ username = '', size = 'md' }) {
  const initials = getInitials(username)

  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
  }

  return (
    <div
      className={`${sizeClasses[size] || sizeClasses.md} rounded-full bg-blue-600 flex items-center justify-center font-semibold text-white flex-shrink-0`}
      aria-label={`Avatar for ${username}`}
    >
      {initials}
    </div>
  )
}

/**
 * Derive initials from a username string.
 * Takes the first letter of each word (up to 2), uppercased.
 * For a single-word username, only the first letter is shown.
 */
export function getInitials(username) {
  if (!username || typeof username !== 'string') return 'EV'
  const words = username.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return 'EV'
  return words
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('')
}
