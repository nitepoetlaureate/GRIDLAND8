import { defineConfig } from "vite";
import cesium from "vite-plugin-cesium";

export default defineConfig({
  plugins: [cesium()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": "http://localhost:8000",
      "/ws":  { target: "ws://localhost:8000", ws: true },
    },
  },
  build: {
    target: "es2022",
    sourcemap: true,
  },
});
