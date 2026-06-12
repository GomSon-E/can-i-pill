import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/ocr': 'http://localhost:8000',
      '/label': 'http://localhost:8000',
      '/analyze': 'http://localhost:8000',
      '/user': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/health-info': 'http://localhost:8000',
      '/prescriptions': 'http://localhost:8000',
      '/supplements': 'http://localhost:8000',
      '/history': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/tests/setup.ts',
  },
})
