import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Vite configuration. The dev server proxies `/api` to the FastAPI backend so
// the frontend can use same-origin relative URLs and avoid CORS in development.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        // Use 127.0.0.1 (not "localhost"): on Windows "localhost" resolves to
        // IPv6 ::1 first, but uvicorn listens on IPv4 127.0.0.1 by default,
        // which causes ECONNREFUSED ::1:8000.
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Split heavy, rarely-changing libraries into their own cacheable chunks.
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          charts: ["recharts"],
          motion: ["framer-motion"],
          query: ["@tanstack/react-query", "axios"],
          radix: [
            "@radix-ui/react-dialog",
            "@radix-ui/react-select",
            "@radix-ui/react-tabs",
            "@radix-ui/react-switch",
            "@radix-ui/react-label",
            "@radix-ui/react-slot",
          ],
          forms: ["react-hook-form", "@hookform/resolvers", "zod"],
        },
      },
    },
  },
});
