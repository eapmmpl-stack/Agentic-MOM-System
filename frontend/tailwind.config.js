/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        // Updated to explicitly match the #399dff from Botivate B PNG.png logo
        brand: {
          50:  '#eef7ff',
          100: '#d9ecff',
          200: '#bcdeff',
          300: '#8ecbff',
          400: '#5ab0ff',
          500: '#399dff', // Exact logo match #399dff
          600: '#1b80f5', // slightly darker for hover
          700: '#1266e1',
          800: '#1552b6',
          900: '#16478f',
        },
      },
    },
  },
  plugins: [],
};
