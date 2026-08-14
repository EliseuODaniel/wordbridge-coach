import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

import { createDevProxy } from './viteProxy.ts'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: createDevProxy(),
  },
})
