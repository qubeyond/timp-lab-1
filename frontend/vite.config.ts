import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    // Используем переменную из Docker, если её нет — дефолт 5173
    port: Number(process.env.FRONTEND_PORT) || 5173,
    strictPort: true,
    hmr: {
      clientPort: 5173, 
    },
    proxy: {
      '/api': {
        // Мы берем BACKEND_PORT из окружения контейнера
        target: `http://backend:${process.env.BACKEND_PORT || '8000'}`,
        changeOrigin: true,
        secure: false,
      }
    },
    watch: {
      usePolling: true,
    },
  }
})