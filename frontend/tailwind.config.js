/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          base:  '#0A0A0F',   // near-black background
          card:  '#12121A',   // card surface
          hover: '#1A1A26',   // hover state
        },
        border: '#1E1E2E',    // subtle border colour
        accent: {
          purple: '#7C6DDD',  // disruption signals
          teal:   '#1D9E75',  // safe / healthy SKUs
          amber:  '#EF9F27',  // medium risk
          danger: '#E24B4A',  // critical risk
        },
        text: {
          primary:   '#E8E8F0',  // main text
          secondary: '#6E6E8A',  // muted / secondary text
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
      },
      borderRadius: {
        card: '16px',
      },
      width: {
        sidebar: '240px',
        'sidebar-collapsed': '60px',
      },
      height: {
        topbar: '56px',
      },
    },
  },
  plugins: [],
};
