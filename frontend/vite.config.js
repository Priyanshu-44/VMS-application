import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
// Backend endpoints have no /api prefix (matches PRD Section 11 exactly, and
// FastAPI's /docs), so the frontend calls the backend's absolute origin
// directly (see src/lib/api.js) rather than proxying through Vite. CORS is
// enabled on the backend for the dev server's origin.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
  },
})
