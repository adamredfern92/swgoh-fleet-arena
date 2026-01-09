import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ command, mode }) => {
  // Load environment variables from parent directory (.env file)
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')

  const frontendPort = parseInt(env.FRONTEND_PORT || '3000')
  const backendHost = env.BACKEND_HOST || 'localhost'
  const backendPort = env.BACKEND_PORT || '8000'

  return {
    plugins: [vue()],
    server: {
      port: frontendPort,
      proxy: {
        '/api': {
          target: `http://${backendHost}:${backendPort}`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    }
  }
})

