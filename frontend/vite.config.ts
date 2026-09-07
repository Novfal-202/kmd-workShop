import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Lets the dev server talk to the real backend (uvicorn on :8000) without
    // hitting browser CORS, when VITE_ENABLE_MOCKS=false — see frontend/README.md.
    proxy: {
      '/claims': 'http://localhost:8000',
      '/receipts': 'http://localhost:8000',
    },
  },
})
