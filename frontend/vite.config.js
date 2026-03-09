import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.ico"],
      injectRegister: false,
      srcDir: "src",
      filename: "sw.js",
      strategies: "injectManifest",
      manifest: {
        name: "ClipAI - Shorts Generator",
        short_name: "ClipAI",
        description: "Transforme tes videos YouTube en Shorts viraux en 2 minutes",
        start_url: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#080812",
        theme_color: "#6366F1",
        icons: [
          { src: "/icons/icon-72.png", sizes: "72x72", type: "image/png", purpose: "maskable any" },
          { src: "/icons/icon-96.png", sizes: "96x96", type: "image/png", purpose: "maskable any" },
          { src: "/icons/icon-128.png", sizes: "128x128", type: "image/png", purpose: "maskable any" },
          { src: "/icons/icon-144.png", sizes: "144x144", type: "image/png", purpose: "maskable any" },
          { src: "/icons/icon-152.png", sizes: "152x152", type: "image/png", purpose: "maskable any" },
          { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png", purpose: "maskable any" },
          { src: "/icons/icon-384.png", sizes: "384x384", type: "image/png", purpose: "maskable any" },
          { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable any" }
        ]
      }
    })
  ],
  server: {
    host: "127.0.0.1",
    port: 5173
  }
});
