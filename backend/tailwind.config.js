/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './templates/**/*.html',
  ],
  theme: {
    container: {
      center: true,
      padding: {
          DEFAULT: '1rem',
          sm: '1.5rem',
          lg: '2rem',
      },
    },
    fontFamily: {
      sans: [
        'Inter, sans-serif',
      ],
    },
    extend: {},
  },
  plugins: [],
}

