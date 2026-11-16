import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Ship only English chart labels, regardless of the browser locale.
    alias: [{
      find: /^(?:\.\.\/i18n\/langZH\.js|echarts\/lib\/i18n\/langZH\.js)$/,
      replacement: new URL('./node_modules/echarts/lib/i18n/langEN.js', import.meta.url).pathname,
    }],
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8765',
    },
  },
  // Escape non-ASCII literals in generated JavaScript without changing Unicode rendering.
  esbuild: { charset: 'ascii' },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'echarts-vendor': ['echarts', 'echarts-for-react'],
        },
      },
    },
  },
})
