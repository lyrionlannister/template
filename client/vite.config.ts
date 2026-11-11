import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// TLS para app.pulso.local lo termina nginx (infra/nginx/), que le
// proxyea a este contenedor en http plano -- Vite no maneja certificado.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    allowedHosts: ["app.pulso.local", "localhost"],
  },
});
