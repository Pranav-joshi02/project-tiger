/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        page: {
          50: '#faf9f6',
          100: '#f0ede6',
          200: '#e6e2d9',
          300: '#d5d0c4',
        },
        forest: {
          50: '#f2f8f4',
          100: '#e1f0e5',
          200: '#c3e1cb',
          300: '#95cbab',
          400: '#5fae84',
          500: '#2d6a4f',
          600: '#23553f',
          700: '#1e4433',
          800: '#1b4332',
          900: '#081c15',
          950: '#040f0b',
        },
        gold: {
          50: '#fdf8ef',
          100: '#f9edda',
          200: '#f1d7b0',
          300: '#e5b96e',
          400: '#d4994b',
          500: '#c08530',
          600: '#a56c24',
          700: '#8a5520',
          800: '#6f4420',
          900: '#5a381c',
        },
        ink: {
          900: '#1e3529',
          800: '#2a453a',
          700: '#3a5c4c',
          600: '#5a6b60',
          500: '#728078',
          400: '#8a968e',
          300: '#a8b3ab',
          200: '#c8d0ca',
          100: '#e1e5df',
          50: '#f3f5f3',
        },
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['Manrope', 'sans-serif'],
        mono: ['"DM Mono"', 'monospace'],
      },
      boxShadow: {
        'card': '0 1px 3px rgba(30,53,41,0.06), 0 4px 12px rgba(30,53,41,0.04)',
        'card-hover': '0 4px 16px rgba(30,53,41,0.10), 0 1px 4px rgba(30,53,41,0.06)',
        'card-lg': '0 6px 24px rgba(30,53,41,0.08), 0 2px 8px rgba(30,53,41,0.04)',
        'sidebar': '4px 0 24px rgba(8,28,21,0.15)',
        'modal': '0 20px 60px rgba(30,53,41,0.20), 0 4px 16px rgba(30,53,41,0.10)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'slide-in-left': 'slideInLeft 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'scale-in': 'scaleIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(12px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInLeft: {
          '0%': { transform: 'translateX(-12px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
