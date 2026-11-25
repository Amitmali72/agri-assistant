import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/query': 'http://localhost:8000',
      '/voice-query': 'http://localhost:8000',
      '/weather': 'http://localhost:8000',
      '/mandi-prices': 'http://localhost:8000',
      '/schemes': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/languages': 'http://localhost:8000',
      '/feedback': 'http://localhost:8000',
      '/settings': 'http://localhost:8000',
      '/documents': 'http://localhost:8000',
      '/admin': 'http://localhost:8000',
      '/whatsapp': 'http://localhost:8000',
      '/conversation-history': 'http://localhost:8000',
      '/audio': 'http://localhost:8000',
    },
  },
})
