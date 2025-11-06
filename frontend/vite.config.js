import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/create_event': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/confirm_event': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/create_bulk_events': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/confirm_bulk_events': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/import_events': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

