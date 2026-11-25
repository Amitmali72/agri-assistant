/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', '"Noto Sans Devanagari"', 'sans-serif'],
      },
      colors: {
        agri: {
          50: '#F2F9F4',
          100: '#D8F3DC',
          200: '#B7E4C7',
          300: '#95D5B2',
          500: '#40916C',
          600: '#2D6A4F',
          700: '#1B4332',
          800: '#133124',
          900: '#0B1F17',
        },
        harvest: {
          50: '#FEFCE8',
          100: '#FEF3C7',
          500: '#D97706',
          600: '#B45309',
        },
      },
    },
  },
  plugins: [],
}
