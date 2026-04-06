/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        surface: '#080d14',
        card: '#0d1520',
        safe: { DEFAULT: '#22c55e', dim: 'rgba(34,197,94,0.15)' },
        warn: { DEFAULT: '#f59e0b', dim: 'rgba(245,158,11,0.15)' },
        danger: { DEFAULT: '#ef4444', dim: 'rgba(239,68,68,0.15)' },
        teal: { 400: '#2dd4bf', 500: '#14b8a6', 600: '#0d9488' },
        border: 'rgba(255,255,255,0.06)',
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '20px',
        '4xl': '28px',
      },
      backgroundImage: {
        'hero-glow': 'radial-gradient(ellipse at top, rgba(200,168,64,0.15), transparent 60%)',
        'card-tint': 'linear-gradient(135deg, rgba(200,168,64,0.12), rgba(200,168,64,0.04))',
        'gold-grad': 'linear-gradient(135deg, #ebc726, #ebc726)',
        'warn-grad': 'linear-gradient(135deg, rgba(200,168,64,0.2), rgba(200,168,64,0.05))',
        'danger-grad': 'linear-gradient(135deg, rgba(160,64,48,0.2), rgba(160,64,48,0.05))',
      },
      boxShadow: {
        card: '0 8px 32px rgba(0,0,0,0.45)',
        'glow-gold': '0 0 40px rgba(200,168,64,0.2)',
        'glow-warn': '0 0 24px rgba(200,168,64,0.3)',
        'glow-danger': '0 0 24px rgba(160,64,48,0.3)',
      },
      keyframes: {
        'fade-in': { from: { opacity: '0', transform: 'translateY(10px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        'slide-up': { from: { opacity: '0', transform: 'translateY(24px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        'number-pop': { '0%': { transform: 'scale(0.9)', opacity: '0.4' }, '60%': { transform: 'scale(1.04)' }, '100%': { transform: 'scale(1)', opacity: '1' } },
        'pulse-ring': { '0%': { transform: 'scale(1)', opacity: '1' }, '100%': { transform: 'scale(1.6)', opacity: '0' } },
        shimmer: { '0%': { backgroundPosition: '-400px 0' }, '100%': { backgroundPosition: '400px 0' } },
      },
      animation: {
        'fade-in': 'fade-in 0.45s ease-out both',
        'slide-up': 'slide-up 0.4s ease-out both',
        'number-pop': 'number-pop 0.35s cubic-bezier(0.34,1.56,0.64,1)',
        'pulse-ring': 'pulse-ring 1.4s ease-out infinite',
        shimmer: 'shimmer 1.6s linear infinite',
      },
    },
  },
  plugins: [],
}
