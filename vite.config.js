import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  root: '.', // Keep index.html in root
  base: './', // Fix asset loading
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
});
