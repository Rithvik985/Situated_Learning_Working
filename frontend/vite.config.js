import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 80,
    allowedHosts: ['situated-learning.wilp-connect.net'], // 👈 Add this

    proxy: {
      '/uploadAss': {
        target: process.env.VITE_UPLOAD_TARGET || 'http://upload-sla:8020',
        changeOrigin: true,
        secure: false,
      },
      '/generation': {
        target: process.env.VITE_GENERATION_TARGET || 'http://generation-sla:8021',
        changeOrigin: true,
        secure: false,
      },
      '/evaluation': {
        target: process.env.VITE_EVALUATION_TARGET || 'http://evaluation-sla:8022',
        changeOrigin: true,
        secure: false,
      },
      '/analytics': {
        target: process.env.VITE_ANALYTICS_TARGET || 'http://analytics-sla:8023',
        changeOrigin: true,
        secure: false,
      },
      '/sla': {
        target: process.env.VITE_AUTH_TARGET || 'http://auth-sla:8024',
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
