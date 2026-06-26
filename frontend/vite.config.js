import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 前端请求这些路径时，自动转发到 FastAPI 后端
      '/health': 'http://127.0.0.1:8000',
      '/chats': 'http://127.0.0.1:8000',
      '/files': 'http://127.0.0.1:8000',
      '/query': 'http://127.0.0.1:8000',
    },
  },
})
