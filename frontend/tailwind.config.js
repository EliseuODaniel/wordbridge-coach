/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gray: {
          50: '#f7f9fc',
          100: '#eef2f7',
          200: '#d8e0ec',
          300: '#b7c3d4',
          400: '#8d9bb0',
          500: '#66758c',
          600: '#435269',
          700: '#29384d',
          800: '#142337',
          900: '#081422',
          950: '#040a12',
        },
        primary: {
          50: '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#8294ff',
          500: '#6677f5',
          600: '#5362dc',
          700: '#434eb5',
          800: '#373f91',
          900: '#303873',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
        },
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#ef4444',
          600: '#dc2626',
        },
        info: {
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Avenir Next', 'Segoe UI', 'ui-sans-serif', 'system-ui'],
        display: ['Inter', 'Avenir Next', 'Segoe UI', 'ui-sans-serif', 'system-ui'],
      },
      boxShadow: {
        'panel': '0 24px 70px -30px rgba(0, 0, 0, 0.72)',
        'glow': '0 16px 50px -22px rgba(102, 119, 245, 0.65)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
