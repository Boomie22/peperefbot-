import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',  // Ensures assets are loaded correctly
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  server: {
    headers: {
      "Content-Type": "application/javascript"
    }
  }
});
