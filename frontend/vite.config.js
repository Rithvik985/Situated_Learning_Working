import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/uploadAss': {
        target: process.env.VITE_UPLOAD_TARGET || 'http://upload:8020',
        changeOrigin: true,
        secure: false,
      },
      '/generation': {
        target: process.env.VITE_GENERATION_TARGET || 'http://generation:8021',
        changeOrigin: true,
        secure: false,
      },
      '/evaluation': {
        target: process.env.VITE_EVALUATION_TARGET || 'http://evaluation:8022',
        changeOrigin: true,
        secure: false,
      },
      '/analytics': {
        target: process.env.VITE_ANALYTICS_TARGET || 'http://analytics:8023',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
