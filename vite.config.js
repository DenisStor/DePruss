import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  build: {
    outDir: 'static/dist',
    emptyOutDir: true,
    cssCodeSplit: false,
    rollupOptions: {
      input: {
        admin: resolve(__dirname, 'static/css/admin/admin.css'),
        base: resolve(__dirname, 'static/css/base/base.css'),
        main: resolve(__dirname, 'static/css/main/main.css'),
      },
      output: {
        assetFileNames: (assetInfo) => {
          if (assetInfo.name.endsWith('.css')) {
            return 'css/[name].css'
          }
          return 'assets/[name].[hash][extname]'
        }
      }
    }
  },
  css: {
    devSourcemap: true
  }
})
