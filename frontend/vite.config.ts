import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      // Proxy TTS service for development (outside Docker)
      '/api/tts': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path, // Keep /api/tts/... as-is
      },
      '/api/audio': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path, // Keep /api/audio/... as-is
      },
    },
  },
})
