/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/*.py",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '-apple-system', 'BlinkMacSystemFont', '"SF Pro Text"',
          '"SF Pro Display"', '"Helvetica Neue"', 'Helvetica', 'Arial', 'sans-serif'
        ],
      },
      colors: {
        apple: {
          canvas:    '#f5f5f7',
          white:     '#ffffff',
          dark:      '#1d1d1f',
          gray:      '#6e6e73',
          subtle:    '#86868b',
          light:     '#f5f5f7',
          blue:      '#0071e3',
          bluehover: '#0077ed',
          card:      '#ffffff',
        }
      },
      boxShadow: {
        'apple':       '0 4px 20px rgba(0, 0, 0, 0.04)',
        'apple-hover': '0 8px 30px rgba(0, 0, 0, 0.08)',
      }
    }
  },
  plugins: [],
}
