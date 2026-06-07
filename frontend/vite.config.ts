import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // 支持 SSE 流式响应，禁用缓冲
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // 确保请求头支持流式传输
            if (req.headers.accept === 'text/event-stream') {
              proxyReq.setHeader('Accept', 'text/event-stream')
            }
          })
        }
      }
    }
  }
})
