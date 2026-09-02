import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Dev server proxies API + WebSocket traffic to the FastAPI backend on :8000,
 * so the browser only ever talks to the Vite origin and there are no CORS
 * concerns during development.
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws": { target: "http://localhost:8000", ws: true, changeOrigin: true },
    },
  },
});
