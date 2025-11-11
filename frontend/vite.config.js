import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: ['situated-learning.wilp-connect.net'], // 👈 Add this
    
    // Handle client-side routing
    historyApiFallback: {
      rewrites: [
        { from: /^\/student-workflow/, to: '/index.html' },
        { from: /^\/faculty-dashboard/, to: '/index.html' }
      ]
    },

    proxy: {
      '/uploadAss': {
        target: process.env.VITE_UPLOAD_TARGET || 'http://localhost:8020',
        changeOrigin: true,
        secure: false,
      },
      '/generation': {
        target: process.env.VITE_GENERATION_TARGET || 'http://localhost:8021',
        changeOrigin: true,
        secure: false,
      },
      '/evaluation': {
        target: process.env.VITE_EVALUATION_TARGET || 'http://localhost:8022',
        changeOrigin: true,
        secure: false,
      },
      '/api/student': {
        target: process.env.VITE_STUDENT_TARGET || 'http://localhost:8024',
        changeOrigin: true,
        secure: false,
      },
      '/api/faculty': {
        target: process.env.VITE_FACULTY_TARGET || 'http://localhost:8025',
        changeOrigin: true,
        secure: false,
      },
      '/analytics': {
        target: process.env.VITE_ANALYTICS_TARGET || 'http://localhost:8023',
        changeOrigin: true,
        secure: false,
      },
      '/sla': {
        target: process.env.VITE_AUTH_TARGET || 'http://localhost:8008',
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
