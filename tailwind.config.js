/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'whatsapp-green': '#DCF8C6',
        'whatsapp-gray': '#E5E5EA',
        'whatsapp-bg': '#F0F2F5',
        'whatsapp-accent': '#25D366',
      },
    },
  },
  plugins: [],
}
