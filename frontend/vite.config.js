import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // Proxy API calls to backend — avoids CORS issues in dev
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path,
      },
      '/ws': {
        target: process.env.VITE_WS_URL || 'ws://127.0.0.1:8000',
        ws: true,
        changeOrigin: true,
      },
      '/health': {
        target: process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  define: {
    // Expose environment variables to the app
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
})
