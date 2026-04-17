/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#0a0e1a',
          50: '#e8eaf0',
          100: '#c5cad8',
          200: '#9fa8be',
          300: '#7886a4',
          400: '#5a6a90',
          500: '#3d4e7c',
          600: '#2e3d6a',
          700: '#1e2d58',
          800: '#0d1117',
          900: '#0a0e1a',
        },
        sidebar: '#0d1117',
        card: 'rgba(13, 25, 48, 0.8)',
        primary: {
          DEFAULT: '#3b82f6',
          dark: '#2563eb',
          hover: '#1d4ed8',
        },
        'active-nav': '#1d4ed8',
        'border-glow': 'rgba(59, 130, 246, 0.2)',
        'text-secondary': '#94a3b8',
        'input-bg': '#0f172a',
        'bubble-user': '#1e3a5f',
        'bubble-assistant': '#0f2747',
        danger: '#dc2626',
      },
      backgroundImage: {
        'glow-blue': 'radial-gradient(ellipse at center, rgba(59,130,246,0.15) 0%, transparent 70%)',
      },
      boxShadow: {
        'glow-sm': '0 0 10px rgba(59, 130, 246, 0.2)',
        'glow-md': '0 0 20px rgba(59, 130, 246, 0.3)',
        'glow-lg': '0 0 40px rgba(59, 130, 246, 0.4)',
        'card': '0 4px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(59, 130, 246, 0.15)',
      },
      animation: {
        'pulse-red': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}
