/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#08080D',
        card1: '#1F1F23',
        card2: '#0B1D33',
        card3: '#1E3C5A',
        textPrimary: '#F7F5F0',
        textSecondary: '#E8DCCA',
        gold: '#D4AF37'
      }
    },
  },
  plugins: [],
}
