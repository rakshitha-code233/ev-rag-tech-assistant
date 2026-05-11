import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    css: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Enable minification for production builds (use esbuild by default)
    minify: 'esbuild',
    // Configure chunk size limits for code splitting
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        // Manual chunks for route-based code splitting
        manualChunks: {
          // Vendor dependencies in separate chunk
          vendor: ['react', 'react-dom', 'react-router-dom'],
          // Auth pages in separate chunk
          auth: ['./src/pages/RegisterPage.jsx', './src/pages/LoginPage.jsx'],
          // Main app pages in separate chunks
          chat: ['./src/pages/ChatPage.jsx'],
          history: ['./src/pages/HistoryPage.jsx'],
          upload: ['./src/pages/UploadPage.jsx'],
          dashboard: ['./src/pages/DashboardPage.jsx'],
        },
      },
    },
    // Enable tree-shaking to remove unused code
    treeshake: true,
  },
})
