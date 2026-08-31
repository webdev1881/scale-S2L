import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// Две точки входа: киоск (покупатель) и админка (оператор). Общий код — в src/shared.
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
        admin: fileURLToPath(new URL('./admin.html', import.meta.url)),
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      // ws: true — тот же префикс обслуживает и поток веса /api/ws/weight
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true, ws: true },
      '/labels': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
