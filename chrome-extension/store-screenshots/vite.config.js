// Builds the store screenshot page; see capture.py.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  root: __dirname,
  base: "./",
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, "build"),
    emptyOutDir: true,
  },
});
