/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surveillance: {
          950: '#07090e',
          900: '#0d1117',
          850: '#131822',
          800: '#1a2234',
          700: '#253248',
          accent: '#00f0ff',
          alert: '#ef4444',
          warning: '#f59e0b',
          success: '#10b981'
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif']
      }
    },
  },
  plugins: [],
}
